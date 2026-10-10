"""Unit and Integration Test Suite for DDIL Store-and-Forward Sync Engine."""
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.ddil_sync import EdgeOutbox, CommandInbox

TEST_DB_DIR = ROOT / "tests" / "test_dbs"
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)


def safe_unlink(p: Path):
    """Safely unlink database file ignoring Windows locks if still held by GC."""
    try:
        if p.exists():
            p.unlink()
    except (PermissionError, OSError):
        pass


@pytest.fixture
def edge_outbox():
    db_file = TEST_DB_DIR / "test_edge_outbox.db"
    outbox = EdgeOutbox(db_path=db_file, node_id="TEST-EDGE-01")
    outbox.clear()
    yield outbox
    outbox.clear()


@pytest.fixture
def command_inbox():
    db_file = TEST_DB_DIR / "test_command_inbox.db"
    inbox = CommandInbox(db_path=db_file)
    inbox.clear()
    yield inbox
    inbox.clear()


def test_edge_outbox_sequential_writing(edge_outbox):
    """Verify monotonic sequence numbers and PENDING status."""
    seq1, aid1 = edge_outbox.write_alert(None, {"vessel": "FPB-01"}, threat_score=85, threat_level="HIGH")
    seq2, aid2 = edge_outbox.write_alert(None, {"vessel": "FPB-02"}, threat_score=35, threat_level="LOW")
    seq3, aid3 = edge_outbox.write_alert("MANUAL-AID-99", {"vessel": "FPB-03"}, threat_score=60, threat_level="MEDIUM")

    assert seq1 == 1
    assert seq2 == 2
    assert seq3 == 3
    assert aid3 == "MANUAL-AID-99"

    stats = edge_outbox.get_stats()
    assert stats["total_alerts"] == 3
    assert stats["queued_alerts"] == 3
    assert stats["synced_alerts"] == 0

    pending = edge_outbox.get_pending_alerts(limit=2)
    assert len(pending) == 2
    assert pending[0]["seq_num"] == 1
    assert pending[1]["seq_num"] == 2


def test_edge_outbox_acknowledgment(edge_outbox):
    """Verify in-order batch acknowledgment marks alerts SYNCED."""
    seq1, aid1 = edge_outbox.write_alert(None, {"target": "Alpha"})
    seq2, aid2 = edge_outbox.write_alert(None, {"target": "Bravo"})
    seq3, aid3 = edge_outbox.write_alert(None, {"target": "Charlie"})

    acked = edge_outbox.acknowledge_batch([seq1, seq2])
    assert acked == 2

    stats = edge_outbox.get_stats()
    assert stats["queued_alerts"] == 1
    assert stats["synced_alerts"] == 2

    remaining = edge_outbox.get_pending_alerts(limit=10)
    assert len(remaining) == 1
    assert remaining[0]["seq_num"] == 3


def test_command_inbox_deduplication(command_inbox):
    """Verify central deduplication of duplicate alert IDs."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    past_iso = (now - timedelta(seconds=15)).isoformat()

    batch_1 = [
        {"alert_id": "ALT-001", "seq_num": 1, "node_id": "EDGE-1", "payload": {}, "threat_score": 80, "threat_level": "HIGH", "created_at": past_iso},
        {"alert_id": "ALT-002", "seq_num": 2, "node_id": "EDGE-1", "payload": {}, "threat_score": 40, "threat_level": "MEDIUM", "created_at": past_iso}
    ]

    res1 = command_inbox.receive_batch(batch_1, received_at=now_iso)
    assert res1["newly_inserted"] == 2
    assert res1["duplicates"] == 0
    assert len(res1["acknowledged_seqs"]) == 2

    # Retransmit ALT-002 along with a new alert ALT-003
    batch_2 = [
        {"alert_id": "ALT-002", "seq_num": 2, "node_id": "EDGE-1", "payload": {}, "threat_score": 40, "threat_level": "MEDIUM", "created_at": past_iso},
        {"alert_id": "ALT-003", "seq_num": 3, "node_id": "EDGE-1", "payload": {}, "threat_score": 90, "threat_level": "HIGH", "created_at": past_iso}
    ]

    res2 = command_inbox.receive_batch(batch_2, received_at=now_iso)
    assert res2["newly_inserted"] == 1
    assert res2["duplicates"] == 1  # ALT-002 detected as duplicate
    assert 2 in res2["acknowledged_seqs"]  # Duplicate is still acknowledged to edge

    stats = command_inbox.get_stats()
    assert stats["total_delivered"] == 3
    assert stats["total_duplicates_filtered"] == 1
    assert stats["delivery_delay_sec"]["min"] >= 14.9


@pytest.mark.live_backend
def test_ddil_api_endpoints():
    """Verify live server integration for DDIL endpoints."""
    import urllib.request
    import urllib.error

    base_url = "http://127.0.0.1:8000"

    # Verify live backend is responding
    try:
        req_check = urllib.request.Request(f"{base_url}/api/ddil/status")
        with urllib.request.urlopen(req_check, timeout=1.0) as resp:
            pass
    except Exception:
        pytest.skip("Live backend on 127.0.0.1:8000 not reachable (start with .\\run_rakshak.bat)")

    # 1. Status
    req = urllib.request.Request(f"{base_url}/api/ddil/status")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "link_status" in data
        assert "channel_telemetry" in data
        assert "edge_node" in data

    # 2. Inject Alert
    inj_bytes = json.dumps({
        "alert_id": "TEST-INJECT-01",
        "threat_score": 88,
        "threat_level": "HIGH",
        "domain": "NAVAL_PATROL"
    }).encode("utf-8")
    req_inj = urllib.request.Request(
        f"{base_url}/api/ddil/edge/inject-alert",
        data=inj_bytes,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_inj) as resp:
        assert resp.status == 200
        inj_data = json.loads(resp.read().decode("utf-8"))
        assert inj_data["alert_id"] == "TEST-INJECT-01"

    # 3. Channel Update
    ch_bytes = json.dumps({
        "status": "DEGRADED",
        "latency_ms": 150.0,
        "packet_loss_pct": 10.0,
        "bandwidth_kbps": 64.0
    }).encode("utf-8")
    req_ch = urllib.request.Request(
        f"{base_url}/api/ddil/set-channel",
        data=ch_bytes,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_ch) as resp:
        assert resp.status == 200
        ch_data = json.loads(resp.read().decode("utf-8"))
        assert ch_data["channel"]["link_status"] == "DEGRADED"

    # Reset back to CONNECTED
    reset_bytes = json.dumps({"status": "CONNECTED"}).encode("utf-8")
    req_reset = urllib.request.Request(
        f"{base_url}/api/ddil/set-channel",
        data=reset_bytes,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_reset) as resp:
        assert resp.status == 200


def test_forced_ack_loss_exactly_once(edge_outbox, command_inbox):
    """Verify exactly-once inbox delivery semantics under forced reverse ACK loss."""
    # 1. Edge generates 5 alerts
    aids = []
    for i in range(5):
        seq, aid = edge_outbox.write_alert(None, {"target": f"FPB-{i}"}, threat_score=75, threat_level="HIGH")
        aids.append(aid)

    pending_1 = edge_outbox.get_pending_alerts(limit=10)
    assert len(pending_1) == 5

    # 2. Transmit batch to Command Inbox
    res1 = command_inbox.receive_batch(pending_1, phase="DEGRADED")
    assert res1["newly_inserted"] == 5
    assert res1["duplicates"] == 0

    # 3. Simulate Reverse ACK Loss: Edge never receives the ACK!
    # Alerts remain PENDING in outbox
    edge_stats_mid = edge_outbox.get_stats()
    assert edge_stats_mid["queued_alerts"] == 5

    # 4. Edge timeout triggers retransmission of the EXACT same batch
    res2 = command_inbox.receive_batch(pending_1, phase="DEGRADED")
    # Command inbox identifies all 5 as duplicates and logs them
    assert res2["newly_inserted"] == 0
    assert res2["duplicates"] == 5
    assert len(res2["acknowledged_seqs"]) == 5

    # 5. This time ACK arrives at edge
    edge_outbox.acknowledge_batch(res2["acknowledged_seqs"])
    assert edge_outbox.get_stats()["queued_alerts"] == 0

    # 6. Verify Command Inbox integrity: exactly 1 row per alert, 5 duplicate attempts logged
    with command_inbox._get_conn() as conn:
        inbox_count = conn.execute("SELECT COUNT(*) FROM command_inbox").fetchone()[0]
        assert inbox_count == 5
        dup_count = conn.execute("SELECT COUNT(*) FROM command_duplicate_log").fetchone()[0]
        assert dup_count == 5


def test_edge_restart_mid_drain():
    """Verify outbox durability and recovery across sudden edge node restart mid-drain."""
    db_file = TEST_DB_DIR / "test_edge_restart.db"
    safe_unlink(db_file)

    # Process 1: Edge queues 20 alerts and drains 10
    edge_1 = EdgeOutbox(db_path=db_file, node_id="EDGE-TEST-ORIN")
    for i in range(20):
        edge_1.write_alert(None, {"vessel_id": f"VESSEL-{i}"}, threat_score=50, threat_level="MEDIUM")

    batch_1 = edge_1.get_pending_alerts(limit=10)
    assert len(batch_1) == 10
    acked_seqs = [item["seq_num"] for item in batch_1]
    edge_1.acknowledge_batch(acked_seqs)

    # Simulate sudden edge power cycle / process crash
    edge_1.close()
    del edge_1

    # Process 2: Edge reboots, initializes new instance on same SQLite WAL db
    edge_2 = EdgeOutbox(db_path=db_file, node_id="EDGE-TEST-ORIN")
    stats_after_reboot = edge_2.get_stats()
    assert stats_after_reboot["total_alerts"] == 20
    assert stats_after_reboot["synced_alerts"] == 10
    assert stats_after_reboot["queued_alerts"] == 10

    remaining = edge_2.get_pending_alerts(limit=20)
    assert len(remaining) == 10
    # Must preserve correct sequence numbers (11 through 20)
    assert remaining[0]["seq_num"] == 11
    assert remaining[-1]["seq_num"] == 20

    # Drain remaining after reboot
    edge_2.acknowledge_batch([item["seq_num"] for item in remaining])
    assert edge_2.get_stats()["queued_alerts"] == 0
    assert edge_2.get_stats()["synced_alerts"] == 20

    edge_2.close()
    safe_unlink(db_file)


def test_command_restart():
    """Verify command receiving store durability and deduplication across node restart."""
    db_file = TEST_DB_DIR / "test_cmd_restart.db"
    safe_unlink(db_file)

    # Process 1: Command receives batch of 10 alerts
    cmd_1 = CommandInbox(db_path=db_file)
    now_iso = datetime.now(timezone.utc).isoformat()
    batch_1 = [
        {"alert_id": f"ALT-RESTART-{i}", "seq_num": i + 1, "node_id": "EDGE-1", "payload": {}, "threat_score": 60, "threat_level": "MEDIUM", "created_at": now_iso}
        for i in range(10)
    ]
    r1 = cmd_1.receive_batch(batch_1)
    assert r1["newly_inserted"] == 10

    # Simulate Command C2 node crash / restart
    cmd_1.close()
    del cmd_1

    # Process 2: Command reboots, re-receives duplicate ALT-RESTART-9 + new ALT-RESTART-10
    cmd_2 = CommandInbox(db_path=db_file)
    batch_2 = [
        {"alert_id": "ALT-RESTART-9", "seq_num": 10, "node_id": "EDGE-1", "payload": {}, "threat_score": 60, "threat_level": "MEDIUM", "created_at": now_iso},
        {"alert_id": "ALT-RESTART-10", "seq_num": 11, "node_id": "EDGE-1", "payload": {}, "threat_score": 70, "threat_level": "HIGH", "created_at": now_iso}
    ]
    r2 = cmd_2.receive_batch(batch_2)
    assert r2["newly_inserted"] == 1
    assert r2["duplicates"] == 1
    assert 10 in r2["acknowledged_seqs"]
    assert 11 in r2["acknowledged_seqs"]

    stats = cmd_2.get_stats()
    assert stats["total_delivered"] == 11
    assert stats["total_duplicates_filtered"] == 1

    cmd_2.close()
    safe_unlink(db_file)


def test_outbox_capacity_cap_drop_low_first():
    """Verify outbox capacity cap policy: drops oldest LOW threat first upon buffer overflow."""
    db_file = TEST_DB_DIR / "test_capacity_drop.db"
    safe_unlink(db_file)

    outbox = EdgeOutbox(db_path=db_file, node_id="EDGE-CAP-TEST", max_capacity=5)

    # 1. Fill buffer to capacity (5 items): 3 LOW, 2 MEDIUM
    s1, a1 = outbox.write_alert("LOW-01", {}, threat_score=20, threat_level="LOW")
    s2, a2 = outbox.write_alert("LOW-02", {}, threat_score=25, threat_level="LOW")
    s3, a3 = outbox.write_alert("LOW-03", {}, threat_score=30, threat_level="LOW")
    s4, a4 = outbox.write_alert("MED-01", {}, threat_score=60, threat_level="MEDIUM")
    s5, a5 = outbox.write_alert("MED-02", {}, threat_score=65, threat_level="MEDIUM")

    assert outbox.get_stats()["queued_alerts"] == 5

    # 2. Insert HIGH threat alert into full buffer
    s6, a6 = outbox.write_alert("HIGH-01", {}, threat_score=95, threat_level="HIGH")

    # Queue size must remain constrained at max_capacity (5)
    assert outbox.get_stats()["queued_alerts"] == 5

    # 3. Verify that the OLDEST LOW alert ("LOW-01") was dropped, and HIGH-01 is present
    pending = outbox.get_pending_alerts(limit=10)
    pending_aids = [item["alert_id"] for item in pending]
    assert "LOW-01" not in pending_aids  # Dropped!
    assert "LOW-02" in pending_aids
    assert "LOW-03" in pending_aids
    assert "MED-01" in pending_aids
    assert "MED-02" in pending_aids
    assert "HIGH-01" in pending_aids

    # 4. Fill with more HIGH alerts to force dropping remaining LOWs then MEDIUMs
    outbox.write_alert("HIGH-02", {}, threat_score=90, threat_level="HIGH")  # Should drop LOW-02
    outbox.write_alert("HIGH-03", {}, threat_score=92, threat_level="HIGH")  # Should drop LOW-03

    pending_after = [item["alert_id"] for item in outbox.get_pending_alerts(limit=10)]
    assert "LOW-02" not in pending_after
    assert "LOW-03" not in pending_after
    assert "MED-01" in pending_after
    assert "MED-02" in pending_after
    assert "HIGH-01" in pending_after
    assert "HIGH-02" in pending_after
    assert "HIGH-03" in pending_after

    outbox.close()
    safe_unlink(db_file)


def test_clock_skew_resilience(command_inbox):
    """Verify delivery delay handling under +/- 5 second clock skew between edge and command."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Case A: Edge clock ahead by +5.0 seconds (future timestamp relative to command)
    future_iso = (now + timedelta(seconds=5.0)).isoformat()
    batch_skew_ahead = [
        {"alert_id": "SKEW-AHEAD-01", "seq_num": 1, "node_id": "EDGE-1", "payload": {}, "threat_score": 80, "threat_level": "HIGH", "created_at": future_iso}
    ]
    res_a = command_inbox.receive_batch(batch_skew_ahead, received_at=now_iso)
    assert res_a["newly_inserted"] == 1

    # Delivery delay should be safely clamped to >= 0.0s (no negative delay bug)
    with command_inbox._get_conn() as conn:
        delay_a = conn.execute("SELECT delivery_delay_sec FROM command_inbox WHERE alert_id = 'SKEW-AHEAD-01'").fetchone()[0]
        assert delay_a == 0.0

    # Case B: Edge clock behind by -5.0 seconds (older timestamp relative to command)
    past_iso = (now - timedelta(seconds=5.0)).isoformat()
    batch_skew_behind = [
        {"alert_id": "SKEW-BEHIND-01", "seq_num": 2, "node_id": "EDGE-1", "payload": {}, "threat_score": 50, "threat_level": "MEDIUM", "created_at": past_iso}
    ]
    res_b = command_inbox.receive_batch(batch_skew_behind, received_at=now_iso)
    assert res_b["newly_inserted"] == 1

    with command_inbox._get_conn() as conn:
        delay_b = conn.execute("SELECT delivery_delay_sec FROM command_inbox WHERE alert_id = 'SKEW-BEHIND-01'").fetchone()[0]
        assert 4.9 <= delay_b <= 5.1


def test_priority_drain_ordering(edge_outbox):
    """Verify prioritized queue retrieval drains HIGH -> MEDIUM -> LOW regardless of FIFO sequence."""
    edge_outbox.write_alert("ORD-LOW-1", {}, threat_score=20, threat_level="LOW")      # seq 1
    edge_outbox.write_alert("ORD-HIGH-1", {}, threat_score=90, threat_level="HIGH")    # seq 2
    edge_outbox.write_alert("ORD-MED-1", {}, threat_score=50, threat_level="MEDIUM")   # seq 3
    edge_outbox.write_alert("ORD-LOW-2", {}, threat_score=15, threat_level="LOW")      # seq 4
    edge_outbox.write_alert("ORD-HIGH-2", {}, threat_score=95, threat_level="HIGH")    # seq 5

    # 1. Standard FIFO order
    fifo_alerts = edge_outbox.get_pending_alerts(limit=5, prioritized=False)
    fifo_ids = [a["alert_id"] for a in fifo_alerts]
    assert fifo_ids == ["ORD-LOW-1", "ORD-HIGH-1", "ORD-MED-1", "ORD-LOW-2", "ORD-HIGH-2"]

    # 2. Prioritized order
    prio_alerts = edge_outbox.get_pending_alerts(limit=5, prioritized=True)
    prio_ids = [a["alert_id"] for a in prio_alerts]
    assert prio_ids == ["ORD-HIGH-1", "ORD-HIGH-2", "ORD-MED-1", "ORD-LOW-1", "ORD-LOW-2"]

