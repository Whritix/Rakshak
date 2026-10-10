"""DDIL (Denied, Degraded, Intermittent, Limited) Store-and-Forward Sync Engine.

Provides air-gapped, offline-first tactical synchronization between edge nodes
(e.g., Jetson AGX Orin deployed on UAV/patrol vessel) and the Command Node:
1. Edge Outbox: Local SQLite WAL queue storing detections with monotonic sequence numbers.
   Inference never pauses when the RF link drops (100% detection uptime).
2. Command Inbox: Central receiving store with unique alert_id deduplication,
   in-order reconciliation, and delivery latency accounting.
3. Resilience Channel: Models physical link states (CONNECTED, DEGRADED, DENIED)
   with packet loss, latency jitter, and bandwidth rate-limiting.
"""
import contextlib
import sqlite3
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EDGE_DB = ROOT / "backend" / "edge_outbox.db"
DEFAULT_CMD_DB = ROOT / "backend" / "command_inbox.db"


class EdgeOutbox:
    """Edge-side persistent SQLite outbox for store-and-forward queuing."""

    def __init__(self, db_path: Path = DEFAULT_EDGE_DB, node_id: str = "EDGE-JETSON-ORIN-01", max_capacity: Optional[int] = None):
        self.db_path = Path(db_path)
        self.node_id = node_id
        self.max_capacity = max_capacity
        self.dropped_count = 0
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.execute("PRAGMA busy_timeout = 5000")
        return self._conn

    @contextlib.contextmanager
    def _get_conn(self):
        conn = self._get_connection()
        with conn:
            yield conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS edge_outbox (
                seq_num INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                node_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                threat_score INTEGER DEFAULT 0,
                threat_level TEXT DEFAULT 'LOW',
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, SYNCED, DROPPED_CAPACITY
                synced_at TEXT,
                retry_count INTEGER DEFAULT 0
            )
            """)
            # Idempotent column migration
            cur = conn.execute("PRAGMA table_info(edge_outbox)")
            cols = {row[1] for row in cur.fetchall()}
            if "threat_score" not in cols:
                conn.execute("ALTER TABLE edge_outbox ADD COLUMN threat_score INTEGER DEFAULT 0")
            if "threat_level" not in cols:
                conn.execute("ALTER TABLE edge_outbox ADD COLUMN threat_level TEXT DEFAULT 'LOW'")
            if "status" not in cols:
                conn.execute("ALTER TABLE edge_outbox ADD COLUMN status TEXT NOT NULL DEFAULT 'PENDING'")
            if "synced_at" not in cols:
                conn.execute("ALTER TABLE edge_outbox ADD COLUMN synced_at TEXT")
            if "retry_count" not in cols:
                conn.execute("ALTER TABLE edge_outbox ADD COLUMN retry_count INTEGER DEFAULT 0")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_edge_outbox_status_seq ON edge_outbox(status, seq_num)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edge_outbox_prio ON edge_outbox(status, threat_level, seq_num)")
            conn.commit()

    def write_alert(
        self,
        alert_id: Optional[str],
        payload: Dict[str, Any],
        threat_score: int = 0,
        threat_level: str = "LOW",
        created_at: Optional[str] = None
    ) -> Tuple[int, str]:
        """Write an alert to local outbox. Enforces capacity cap and drop policy if configured."""
        aid = alert_id or f"ALT-{uuid.uuid4().hex[:10].upper()}"
        ts = created_at or datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload)

        with self._get_conn() as conn:
            # Capacity check & priority drop policy
            if self.max_capacity is not None:
                cur_pending = conn.execute("SELECT COUNT(*) FROM edge_outbox WHERE status = 'PENDING'").fetchone()[0]
                if cur_pending >= self.max_capacity:
                    # Drop policy: 1. Oldest LOW -> 2. Oldest MEDIUM -> 3. Oldest HIGH
                    row_to_drop = conn.execute(
                        """
                        SELECT seq_num, alert_id FROM edge_outbox
                        WHERE status = 'PENDING'
                        ORDER BY 
                            CASE threat_level 
                                WHEN 'LOW' THEN 1 
                                WHEN 'MEDIUM' THEN 2 
                                WHEN 'HIGH' THEN 3 
                                ELSE 4 
                            END ASC,
                            seq_num ASC
                        LIMIT 1
                        """
                    ).fetchone()
                    if row_to_drop:
                        conn.execute("DELETE FROM edge_outbox WHERE seq_num = ?", (row_to_drop["seq_num"],))
                        self.dropped_count += 1

            cur = conn.execute(
                """
                INSERT OR REPLACE INTO edge_outbox (alert_id, node_id, payload, threat_score, threat_level, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
                """,
                (aid, self.node_id, payload_str, threat_score, threat_level, ts)
            )
            seq = cur.lastrowid
            conn.commit()
            return seq, aid

    def get_pending_alerts(
        self,
        limit: int = 50,
        prioritized: bool = False,
        aging_threshold_sec: float = 600.0,
        as_of_time: Optional[Union[str, float, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch pending alerts.
        
        If prioritized=True:
            Drains HIGH first, then MEDIUM, then LOW.
            Aging Rule: Promotes LOW alerts older than aging_threshold_sec (default 600s = 10 min)
            to MEDIUM priority tier to prevent starvation during sustained high-tempo operations.
        """
        if prioritized:
            if as_of_time is None:
                ref_dt = datetime.now(timezone.utc)
            elif isinstance(as_of_time, str):
                try:
                    ref_dt = datetime.fromisoformat(as_of_time)
                except Exception:
                    ref_dt = datetime.now(timezone.utc)
            elif isinstance(as_of_time, (int, float)):
                ref_dt = datetime.fromtimestamp(as_of_time, timezone.utc)
            elif isinstance(as_of_time, datetime):
                ref_dt = as_of_time
            else:
                ref_dt = datetime.now(timezone.utc)

            cutoff_iso = (ref_dt - timedelta(seconds=aging_threshold_sec)).isoformat()

            order_clause = """
            CASE 
                WHEN threat_level = 'HIGH' THEN 1 
                WHEN threat_level = 'MEDIUM' THEN 2 
                WHEN threat_level = 'LOW' AND created_at <= ? THEN 2 
                WHEN threat_level = 'LOW' THEN 3 
                ELSE 4 
            END ASC,
            seq_num ASC
            """
            params: Tuple[Any, ...] = (cutoff_iso, limit)
        else:
            order_clause = "seq_num ASC"
            params = (limit,)

        with self._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT seq_num, alert_id, node_id, payload, threat_score, threat_level, created_at, retry_count
                FROM edge_outbox
                WHERE status = 'PENDING'
                ORDER BY {order_clause}
                LIMIT ?
                """,
                params
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["payload"] = json.loads(item["payload"])
                except Exception:
                    pass
                results.append(item)
            return results

    def acknowledge_batch(self, seq_nums: List[int], synced_at: Optional[str] = None) -> int:
        """Mark a batch of sequence numbers as successfully synced."""
        if not seq_nums:
            return 0
        now_ts = synced_at or datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            placeholders = ",".join("?" for _ in seq_nums)
            cur = conn.execute(
                f"""
                UPDATE edge_outbox
                SET status = 'SYNCED', synced_at = ?
                WHERE seq_num IN ({placeholders}) AND status = 'PENDING'
                """,
                [now_ts] + seq_nums
            )
            updated = cur.rowcount
            conn.commit()
            return updated

    def increment_retries(self, seq_nums: List[int]) -> None:
        """Increment retry counter on transmission failure."""
        if not seq_nums:
            return
        with self._get_conn() as conn:
            placeholders = ",".join("?" for _ in seq_nums)
            conn.execute(
                f"""
                UPDATE edge_outbox
                SET retry_count = retry_count + 1
                WHERE seq_num IN ({placeholders})
                """,
                seq_nums
            )
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Return outbox queue statistics."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM edge_outbox").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM edge_outbox WHERE status = 'PENDING'").fetchone()[0]
            synced = conn.execute("SELECT COUNT(*) FROM edge_outbox WHERE status = 'SYNCED'").fetchone()[0]
            oldest_pending = conn.execute(
                "SELECT created_at FROM edge_outbox WHERE status = 'PENDING' ORDER BY seq_num ASC LIMIT 1"
            ).fetchone()
            return {
                "node_id": self.node_id,
                "total_alerts": total,
                "queued_alerts": pending,
                "synced_alerts": synced,
                "oldest_queued_timestamp": oldest_pending[0] if oldest_pending else None
            }

    def clear(self) -> None:
        """Clear outbox tables (for test/simulation harness)."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM edge_outbox")
            try:
                conn.execute("DELETE FROM sqlite_sequence WHERE name = 'edge_outbox'")
            except Exception:
                pass
            conn.commit()


class CommandInbox:
    """Command-side receiving store with deduplication and delivery accounting."""

    def __init__(self, db_path: Path = DEFAULT_CMD_DB):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.execute("PRAGMA busy_timeout = 5000")
        return self._conn

    @contextlib.contextmanager
    def _get_conn(self):
        conn = self._get_connection()
        with conn:
            yield conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS command_inbox (
                alert_id TEXT PRIMARY KEY,
                seq_num INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                threat_score INTEGER DEFAULT 0,
                threat_level TEXT DEFAULT 'LOW',
                phase TEXT DEFAULT 'UNKNOWN',
                created_at TEXT NOT NULL,
                received_at TEXT NOT NULL,
                delivery_delay_sec REAL NOT NULL
            )
            """)
            # Idempotent column migration
            cur = conn.execute("PRAGMA table_info(command_inbox)")
            cols = {row[1] for row in cur.fetchall()}
            if "threat_score" not in cols:
                conn.execute("ALTER TABLE command_inbox ADD COLUMN threat_score INTEGER DEFAULT 0")
            if "threat_level" not in cols:
                conn.execute("ALTER TABLE command_inbox ADD COLUMN threat_level TEXT DEFAULT 'LOW'")
            if "phase" not in cols:
                conn.execute("ALTER TABLE command_inbox ADD COLUMN phase TEXT DEFAULT 'UNKNOWN'")

            conn.execute("""
            CREATE TABLE IF NOT EXISTS command_duplicate_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                phase TEXT DEFAULT 'UNKNOWN',
                attempted_at TEXT NOT NULL
            )
            """)
            cur_dup = conn.execute("PRAGMA table_info(command_duplicate_log)")
            dup_cols = {row[1] for row in cur_dup.fetchall()}
            if "phase" not in dup_cols:
                conn.execute("ALTER TABLE command_duplicate_log ADD COLUMN phase TEXT DEFAULT 'UNKNOWN'")

            conn.execute("CREATE INDEX IF NOT EXISTS idx_cmd_inbox_seq ON command_inbox(node_id, seq_num)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cmd_inbox_phase ON command_inbox(phase)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cmd_inbox_prio ON command_inbox(threat_level)")
            conn.commit()

    def receive_batch(
        self,
        alerts: List[Dict[str, Any]],
        received_at: Optional[str] = None,
        phase: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """Process incoming batch with deduplication, phase tracking, and latency accounting."""
        now_ts = received_at or datetime.now(timezone.utc).isoformat()
        now_epoch = datetime.fromisoformat(now_ts.replace("Z", "+00:00")).timestamp()

        acknowledged_seqs = []
        newly_inserted = 0
        duplicates = 0

        with self._get_conn() as conn:
            for item in alerts:
                aid = item["alert_id"]
                seq = item["seq_num"]
                nid = item.get("node_id", "UNKNOWN-NODE")
                payload = json.dumps(item.get("payload", {}))
                score = item.get("threat_score", 0)
                level = item.get("threat_level", "LOW")
                cat = item.get("created_at", now_ts)

                try:
                    c_epoch = datetime.fromisoformat(cat.replace("Z", "+00:00")).timestamp()
                    delay_sec = max(0.0, now_epoch - c_epoch)
                except Exception:
                    delay_sec = 0.0

                # Check if already present (deduplication)
                existing = conn.execute("SELECT 1 FROM command_inbox WHERE alert_id = ?", (aid,)).fetchone()
                if existing:
                    duplicates += 1
                    conn.execute(
                        "INSERT INTO command_duplicate_log (alert_id, node_id, phase, attempted_at) VALUES (?, ?, ?, ?)",
                        (aid, nid, phase, now_ts)
                    )
                    # Still acknowledge so edge marks it synced and stops resending
                    acknowledged_seqs.append(seq)
                else:
                    conn.execute(
                        """
                        INSERT INTO command_inbox (alert_id, seq_num, node_id, payload, threat_score, threat_level, phase, created_at, received_at, delivery_delay_sec)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (aid, seq, nid, payload, score, level, phase, cat, now_ts, delay_sec)
                    )
                    newly_inserted += 1
                    acknowledged_seqs.append(seq)

            conn.commit()

        return {
            "acknowledged_seqs": acknowledged_seqs,
            "newly_inserted": newly_inserted,
            "duplicates": duplicates
        }

    @staticmethod
    def _calc_distribution(delays: List[float]) -> Dict[str, float]:
        if not delays:
            return {"min": 0.0, "mean": 0.0, "p50_median": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
        import numpy as np
        return {
            "min": round(float(np.min(delays)), 3),
            "mean": round(float(np.mean(delays)), 3),
            "p50_median": round(float(np.median(delays)), 3),
            "p90": round(float(np.percentile(delays, 90)), 3),
            "p95": round(float(np.percentile(delays, 95)), 3),
            "p99": round(float(np.percentile(delays, 99)), 3),
            "max": round(float(np.max(delays)), 3)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Compute aggregate delivery metrics and delays."""
        with self._get_conn() as conn:
            total_delivered = conn.execute("SELECT COUNT(*) FROM command_inbox").fetchone()[0]
            total_dupes = conn.execute("SELECT COUNT(*) FROM command_duplicate_log").fetchone()[0]
            delays = [r[0] for r in conn.execute("SELECT delivery_delay_sec FROM command_inbox ORDER BY delivery_delay_sec ASC").fetchall()]

            return {
                "total_delivered": total_delivered,
                "total_duplicates_filtered": total_dupes,
                "delivery_delay_sec": self._calc_distribution(delays)
            }

    def get_stats_by_phase(self) -> Dict[str, Any]:
        """Compute delay statistics broken down by mission phase."""
        with self._get_conn() as conn:
            phases = [r[0] for r in conn.execute("SELECT DISTINCT phase FROM command_inbox").fetchall()]
            res = {}
            for p in phases:
                rows = [r[0] for r in conn.execute("SELECT delivery_delay_sec FROM command_inbox WHERE phase = ? ORDER BY delivery_delay_sec ASC", (p,)).fetchall()]
                res[p] = {
                    "count": len(rows),
                    "delays": self._calc_distribution(rows)
                }
            return res

    def get_stats_by_priority(self) -> Dict[str, Any]:
        """Compute delay statistics broken down by threat level (HIGH, MEDIUM, LOW)."""
        with self._get_conn() as conn:
            res = {}
            for p in ["HIGH", "MEDIUM", "LOW"]:
                rows = [r[0] for r in conn.execute("SELECT delivery_delay_sec FROM command_inbox WHERE threat_level = ? ORDER BY delivery_delay_sec ASC", (p,)).fetchall()]
                res[p] = {
                    "count": len(rows),
                    "delays": self._calc_distribution(rows)
                }
            return res

    def get_duplicates_by_phase(self) -> Dict[str, int]:
        """Count filtered duplicate arrivals per phase."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT phase, COUNT(*) FROM command_duplicate_log GROUP BY phase").fetchall()
            return {r[0]: r[1] for r in rows}

    def clear(self) -> None:
        """Clear command inbox tables (for test/simulation harness)."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM command_inbox")
            conn.execute("DELETE FROM command_duplicate_log")
            try:
                conn.execute("DELETE FROM sqlite_sequence WHERE name = 'command_duplicate_log'")
            except Exception:
                pass
            conn.commit()


# Lazy singleton state tracking for live server API
_LAZY_EDGE_OUTBOX: Optional[EdgeOutbox] = None
_LAZY_COMMAND_INBOX: Optional[CommandInbox] = None


def get_edge_outbox() -> EdgeOutbox:
    """Lazy getter for edge outbox singleton."""
    global _LAZY_EDGE_OUTBOX
    if _LAZY_EDGE_OUTBOX is None:
        _LAZY_EDGE_OUTBOX = EdgeOutbox()
    return _LAZY_EDGE_OUTBOX


def get_command_inbox() -> CommandInbox:
    """Lazy getter for command inbox singleton."""
    global _LAZY_COMMAND_INBOX
    if _LAZY_COMMAND_INBOX is None:
        _LAZY_COMMAND_INBOX = CommandInbox()
    return _LAZY_COMMAND_INBOX


class _LazyProxy:
    """Proxy object that delegates to lazy getter upon attribute access."""
    def __init__(self, getter):
        self._getter = getter

    def __getattr__(self, name):
        return getattr(self._getter(), name)


_GLOBAL_EDGE_OUTBOX = _LazyProxy(get_edge_outbox)
_GLOBAL_COMMAND_INBOX = _LazyProxy(get_command_inbox)

_GLOBAL_CHANNEL_STATE = {
    "link_status": "CONNECTED",  # CONNECTED, DEGRADED, DENIED
    "latency_ms": 25.0,
    "packet_loss_pct": 0.0,
    "bandwidth_kbps": 256.0,
    "last_sync_timestamp": datetime.now(timezone.utc).isoformat()
}


def get_live_ddil_status() -> Dict[str, Any]:
    """Retrieve combined live DDIL link state and outbox/inbox stats."""
    edge_stats = get_edge_outbox().get_stats()
    cmd_stats = get_command_inbox().get_stats()
    return {
        "link_status": _GLOBAL_CHANNEL_STATE["link_status"],
        "channel_telemetry": {
            "latency_ms": _GLOBAL_CHANNEL_STATE["latency_ms"],
            "packet_loss_pct": _GLOBAL_CHANNEL_STATE["packet_loss_pct"],
            "bandwidth_kbps": _GLOBAL_CHANNEL_STATE["bandwidth_kbps"],
        },
        "edge_node": {
            "node_id": edge_stats["node_id"],
            "queued_alerts": edge_stats["queued_alerts"],
            "total_alerts": edge_stats["total_alerts"],
            "synced_alerts": edge_stats["synced_alerts"],
            "oldest_queued_timestamp": edge_stats["oldest_queued_timestamp"]
        },
        "command_node": {
            "total_delivered": cmd_stats["total_delivered"],
            "duplicates_filtered": cmd_stats["total_duplicates_filtered"],
            "delivery_delay_sec": cmd_stats["delivery_delay_sec"]
        },
        "last_sync_timestamp": _GLOBAL_CHANNEL_STATE["last_sync_timestamp"]
    }


def set_live_channel_state(status: str, latency_ms: float = 25.0, loss_pct: float = 0.0, bw_kbps: float = 256.0) -> Dict[str, Any]:
    """Dynamically set the simulated channel state."""
    if status not in ("CONNECTED", "DEGRADED", "DENIED"):
        status = "CONNECTED"
    _GLOBAL_CHANNEL_STATE["link_status"] = status
    _GLOBAL_CHANNEL_STATE["latency_ms"] = max(0.0, latency_ms)
    _GLOBAL_CHANNEL_STATE["packet_loss_pct"] = max(0.0, min(100.0, loss_pct))
    _GLOBAL_CHANNEL_STATE["bandwidth_kbps"] = max(1.0, bw_kbps)
    return _GLOBAL_CHANNEL_STATE
