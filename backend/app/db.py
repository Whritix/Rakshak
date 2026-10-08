"""Database connection, schema management, and tactical data indexing for Project Rakshak.

Key enhancements:
- Enforces PRAGMA foreign_keys = ON and PRAGMA cache_size = -32000 (32MB cache) per connection.
- PRAGMA journal_mode=WAL and PRAGMA synchronous=NORMAL for concurrent air-gapped performance.
- Connection busy_timeout=5000 to prevent locking contention under concurrent tactical requests.
- High-performance query indexes on threat_score, image_name, is_dark_vessel, domain, created_at, lat/lon.
- Clean idempotent column migration helper _ensure_column.
- Unifies rag_knowledge_base table creation alongside all other sovereign defense tables.
"""
from __future__ import annotations
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / 'backend' / 'rakshak.db'


def get_db() -> sqlite3.Connection:
    """Establish and configure an optimized SQLite connection with WAL & foreign keys."""
    c = sqlite3.connect(DB_PATH, timeout=10.0)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    c.execute('PRAGMA cache_size = -32000')  # 32MB cache (-32000 KiB)
    c.execute('PRAGMA busy_timeout = 5000')
    return c


def _ensure_column(c: sqlite3.Connection, table: str, col: str, col_def: str) -> None:
    """Idempotently add a column to an existing table if not already present."""
    existing_cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    if col not in existing_cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")


def init_database() -> None:
    """Initialize database schemas, apply migrations, indexes, and initial seeds."""
    with get_db() as c:
        # WAL mode configuration
        c.execute('PRAGMA journal_mode = WAL')
        c.execute('PRAGMA synchronous = NORMAL')

        # ── 1. Optical Satellite / Aerial Detections ────────────────────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS detections(
            id TEXT PRIMARY KEY,
            source TEXT,
            image_name TEXT,
            preview_path TEXT,
            kind TEXT,
            confidence REAL,
            x REAL, y REAL, w REAL, h REAL,
            lat REAL, lon REAL,
            ais_status TEXT DEFAULT 'unknown',
            mmsi TEXT,
            threat_score INTEGER DEFAULT 0,
            threat_level TEXT DEFAULT 'LOW',
            reasons TEXT DEFAULT '[]',
            review_status TEXT DEFAULT 'pending',
            created_at TEXT
        )''')

        # ── 2. Defense Geofencing & Buffer Zones ────────────────────────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS zones(
            id TEXT PRIMARY KEY,
            name TEXT,
            zone_type TEXT DEFAULT 'DEFENSE_BUFFER',
            lat REAL,
            lon REAL,
            radius_km REAL,
            created_at TEXT
        )''')

        # ── 3. Tactical Command Missions ────────────────────────────────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS missions(
            id TEXT PRIMARY KEY,
            title TEXT,
            notes TEXT,
            created_at TEXT
        )''')

        # ── 4. Commercial Pipeline / Ground Truth Reviews ──────────────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS provider_reviews(
            month TEXT,
            detection_id TEXT,
            status TEXT,
            mmsi TEXT,
            updated_at TEXT,
            PRIMARY KEY(month, detection_id)
        )''')

        # ── 5. Sentinel-1 SAR Radar & Dark Vessel Detections ───────────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS sar_detections(
            id TEXT PRIMARY KEY,
            scene_id TEXT,
            timestamp TEXT,
            lat REAL,
            lon REAL,
            rcs_sigma0_db REAL,
            estimated_length_m REAL,
            cfar_confidence REAL,
            ais_correlated INTEGER DEFAULT 0,
            correlated_mmsi TEXT,
            is_dark_vessel INTEGER DEFAULT 1,
            threat_score INTEGER DEFAULT 85,
            threat_level TEXT DEFAULT 'HIGH',
            speed_knots REAL,
            heading_deg REAL,
            notes TEXT,
            created_at TEXT
        )''')

        # ── 6. Multimodal Army Feeds (UAV Drone, UGS Seismic, SIGINT) ─────
        c.execute('''
        CREATE TABLE IF NOT EXISTS army_feeds(
            id TEXT PRIMARY KEY,
            domain TEXT, -- 'DRONE_UAV', 'UGS_GROUND', 'SIGINT_TEXT'
            source_ref TEXT,
            target_class TEXT,
            confidence REAL,
            lat REAL,
            lon REAL,
            signal_strength REAL,
            alert_summary TEXT,
            raw_payload TEXT,
            threat_score INTEGER DEFAULT 50,
            threat_level TEXT DEFAULT 'MEDIUM',
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT
        )''')

        # ── 7. Sovereign Cryptographic Users & Operators ───────────────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            callsign TEXT,
            rank TEXT,
            role TEXT DEFAULT 'OPERATOR',
            clearance TEXT DEFAULT 'SECRET',
            created_at TEXT
        )''')

        # ── 8. Air-Gapped Defense Doctrine & RoE Knowledge Base ───────────
        c.execute('''
        CREATE TABLE IF NOT EXISTS rag_knowledge_base(
            id TEXT PRIMARY KEY,
            category TEXT,
            title TEXT,
            content TEXT,
            references_code TEXT,
            classification TEXT DEFAULT 'SECRET',
            tags TEXT,
            created_at TEXT
        )''')

        # ── Migrations (Clean, Idempotent Helpers) ──────────────────────────
        _ensure_column(c, 'zones', 'zone_type', "TEXT DEFAULT 'DEFENSE_BUFFER'")
        _ensure_column(c, 'zones', 'created_at', "TEXT")
        _ensure_column(c, 'army_feeds', 'updated_at', "TEXT")
        _ensure_column(c, 'sar_detections', 'vessel_class', "TEXT")

        # ── High-Performance Query Indexes ──────────────────────────────────
        c.execute('CREATE INDEX IF NOT EXISTS idx_detections_threat ON detections(threat_score DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_detections_image ON detections(image_name)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_detections_geo ON detections(lat, lon)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sar_dark ON sar_detections(is_dark_vessel, threat_score DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sar_geo ON sar_detections(lat, lon)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sar_vessel_class ON sar_detections(vessel_class)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_army_domain ON army_feeds(domain, threat_score DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_missions_created ON missions(created_at DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_rag_category ON rag_knowledge_base(category)')

        # ── Seed Strategic Restricted Zones if Empty ────────────────────────
        cur_z = c.execute('SELECT COUNT(*) FROM zones')
        if cur_z.fetchone()[0] == 0:
            default_zones = [
                ('zone-1', 'Mumbai Offshore Development Area (ODA)', 'CRITICAL_OFFSHORE', 19.35, 71.30, 25.0, datetime.now(timezone.utc).isoformat()),
                ('zone-2', 'INS Kadamba (Karwar Naval Base Buffer)', 'NAVAL_EXCLUSION', 14.82, 74.13, 15.0, datetime.now(timezone.utc).isoformat()),
                ('zone-3', 'Mumbai Harbour Naval Anchorage Guard', 'MILITARY_HARBOUR', 18.91, 72.84, 8.0, datetime.now(timezone.utc).isoformat()),
                ('zone-4', 'Strait of Malacca / Nicobar Entry Watch', 'MARITIME_CHOKEPOINT', 6.85, 93.80, 30.0, datetime.now(timezone.utc).isoformat()),
                ('zone-5', 'Forward Defense Sector Alpha (Tactical FOB)', 'ARMY_TACTICAL_BUFFER', 32.55, 74.80, 12.0, datetime.now(timezone.utc).isoformat()),
            ]
            c.executemany(
                'INSERT INTO zones (id, name, zone_type, lat, lon, radius_km, created_at) VALUES (?,?,?,?,?,?,?)',
                default_zones
            )

        # ── Seed Default Tactical Operators if Empty ────────────────────────
        cur_u = c.execute('SELECT COUNT(*) FROM users')
        if cur_u.fetchone()[0] == 0:
            from backend.app.auth import hash_password
            h1, s1 = hash_password('rakshak2026')
            h2, s2 = hash_password('tactical123')
            now_iso = datetime.now(timezone.utc).isoformat()
            default_users = [
                ('commander', h1, s1, 'Cdr. Vikram Sharma', 'TRIDENT-ACTUAL', 'Commander, IN', 'COMMANDER', 'TOP SECRET // COSMIC', now_iso),
                ('analyst', h2, s2, 'Maj. Rajesh Rathore', 'GARUDA-LEAD', 'Major, IA', 'ANALYST', 'SECRET // TACTICAL', now_iso),
            ]
            c.executemany('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)', default_users)

        c.commit()


# Execute idempotent database schema initialization on module import
init_database()
