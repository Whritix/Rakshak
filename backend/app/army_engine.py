"""Army Multimodal Intelligence Feeds: Tactical Drone FMV, Ground Sensors (UGS), and SIGINT.

Manages multimodal sensor streams:
1. Tactical Drone EO/IR feeds (UAVDT / VisDrone surrogate surveillance).
2. Unattended Ground Sensors (UGS seismic geophone & acoustic tripwires).
3. SIGINT Direction-Finding (DF) tactical burst intercepts.
4. Operational lifecycle state transitions (ACTIVE -> ACKNOWLEDGED -> RESOLVED).
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.db import get_db


def _ensure_schema_migrations() -> None:
    """Ensure updated_at column exists in army_feeds table."""
    with get_db() as c:
        cols = [r[1] for r in c.execute("PRAGMA table_info(army_feeds)").fetchall()]
        if 'updated_at' not in cols:
            c.execute("ALTER TABLE army_feeds ADD COLUMN updated_at TEXT")
            c.commit()


def seed_army_feeds() -> None:
    """Seed tactical Army multimodal surveillance feeds if empty."""
    _ensure_schema_migrations()
    with get_db() as c:
        cur = c.execute('SELECT COUNT(*) FROM army_feeds')
        if cur.fetchone()[0] == 0:
            feeds = [
                # Drone UAV detections (VisDrone / UAVDT surrogates)
                {
                    'id': 'army-uav-01',
                    'domain': 'DRONE_UAV',
                    'source_ref': 'UAV-GARUDA-04 (Thermal/EO)',
                    'target_class': 'Military Vehicle Convoy',
                    'confidence': 0.92,
                    'lat': 32.5480,
                    'lon': 74.8120,
                    'signal_strength': 0.95,
                    'alert_summary': 'Tactical UAV detected 4-vehicle convoy in blackout mode moving towards Sector Alpha FOB buffer.',
                    'raw_payload': '{"vehicles": 4, "formation": "column", "speed_kmh": 38, "payload_detected": true, "heading": 135}',
                    'threat_score': 88,
                    'threat_level': 'HIGH',
                    'status': 'ACTIVE'
                },
                {
                    'id': 'army-uav-02',
                    'domain': 'DRONE_UAV',
                    'source_ref': 'UAV-NETRA-02 (Long Range)',
                    'target_class': 'Camouflaged Artillery Position',
                    'confidence': 0.86,
                    'lat': 32.6120,
                    'lon': 74.7450,
                    'signal_strength': 0.88,
                    'alert_summary': 'Thermal signature indicates heat bloom consistent with freshly repositioned tactical artillery.',
                    'raw_payload': '{"thermal_delta_c": 14.2, "tarp_coverage": "partial", "crew_count": 6}',
                    'threat_score': 82,
                    'threat_level': 'HIGH',
                    'status': 'ACTIVE'
                },
                # Unattended Ground Sensors (UGS)
                {
                    'id': 'army-ugs-01',
                    'domain': 'UGS_GROUND',
                    'source_ref': 'UGS-SEISMIC-NODE-14',
                    'target_class': 'Heavy Tracked Vehicle Vibration',
                    'confidence': 0.95,
                    'lat': 32.5390,
                    'lon': 74.8210,
                    'signal_strength': 0.98,
                    'alert_summary': 'Seismic ground sensor tripped: frequency response peak 18 Hz indicates heavy tracked armored movement.',
                    'raw_payload': '{"sensor_type": "3-axis geophone", "peak_velocity_mms": 4.8, "frequency_peak_hz": 18.2, "tripwire_zone": "Forward Defile 2"}',
                    'threat_score': 90,
                    'threat_level': 'HIGH',
                    'status': 'ACTIVE'
                },
                {
                    'id': 'army-ugs-02',
                    'domain': 'UGS_GROUND',
                    'source_ref': 'UGS-PIR-ACOUSTIC-09',
                    'target_class': 'Dismounted Infiltration Alert',
                    'confidence': 0.84,
                    'lat': 32.5530,
                    'lon': 74.7950,
                    'signal_strength': 0.82,
                    'alert_summary': 'Dual acoustic/passive-infrared tripwire trigger along ridge line infiltration trail.',
                    'raw_payload': '{"sensor_type": "PIR + Beam Acoustic", "footstep_cadence_bpm": 110, "estimated_group_size": "3-5"}',
                    'threat_score': 74,
                    'threat_level': 'MEDIUM',
                    'status': 'ACTIVE'
                },
                # SIGINT / Electronic Intelligence intercepts
                {
                    'id': 'army-sigint-01',
                    'domain': 'SIGINT_TEXT',
                    'source_ref': 'EW-DIRECTION-FINDER-02',
                    'target_class': 'Tactical VHF Frequency Burst',
                    'confidence': 0.89,
                    'lat': 32.5850,
                    'lon': 74.7700,
                    'signal_strength': 0.91,
                    'alert_summary': 'Tactical frequency-hopping burst transmission detected; line-of-bearing intersects with detected convoy track.',
                    'raw_payload': '{"frequency_mhz": 142.85, "modulation": "FHSS", "bearing_deg": 312.4, "transcription_surrogate": "Delta elements confirmed at waypoint charlie, await breach order."}',
                    'threat_score': 85,
                    'threat_level': 'HIGH',
                    'status': 'ACTIVE'
                }
            ]
            now_iso = datetime.now(timezone.utc).isoformat()
            for f in feeds:
                c.execute('''
                INSERT INTO army_feeds (
                    id, domain, source_ref, target_class, confidence, lat, lon,
                    signal_strength, alert_summary, raw_payload, threat_score, threat_level, status, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    f['id'], f['domain'], f['source_ref'], f['target_class'], f['confidence'],
                    f['lat'], f['lon'], f['signal_strength'], f['alert_summary'],
                    f['raw_payload'], f['threat_score'], f['threat_level'], f['status'],
                    now_iso, now_iso
                ))
            c.commit()


# Seed default tactical Army surveillance feeds on startup
seed_army_feeds()


def list_army_feeds(domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve tactical Army feeds filtered optionally by sensor domain."""
    with get_db() as c:
        if domain:
            rows = c.execute(
                'SELECT * FROM army_feeds WHERE domain = ? ORDER BY threat_score DESC',
                (domain,)
            ).fetchall()
        else:
            rows = c.execute('SELECT * FROM army_feeds ORDER BY threat_score DESC').fetchall()
        return [dict(r) for r in rows]


def acknowledge_feed(feed_id: str) -> bool:
    """Transition feed status to ACKNOWLEDGED with an updated_at timestamp.

    Args:
        feed_id: Unique Army feed ID (e.g. 'army-uav-01').

    Returns:
        True if the feed was found and updated, False otherwise.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as c:
        res = c.execute(
            "UPDATE army_feeds SET status = 'ACKNOWLEDGED', updated_at = ? WHERE id = ?",
            (now_iso, feed_id)
        )
        c.commit()
        return res.rowcount > 0


def resolve_feed(feed_id: str) -> bool:
    """Transition feed status to RESOLVED with an updated_at timestamp.

    Args:
        feed_id: Unique Army feed ID (e.g. 'army-ugs-01').

    Returns:
        True if the feed was found and updated, False otherwise.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as c:
        res = c.execute(
            "UPDATE army_feeds SET status = 'RESOLVED', updated_at = ? WHERE id = ?",
            (now_iso, feed_id)
        )
        c.commit()
        return res.rowcount > 0


def get_feed_stats() -> Dict[str, int]:
    """Aggregate tactical feed counts partitioned by operational status and sensor domain.

    Returns:
        Dictionary containing total, status counts, and domain counts:
        {'total': N, 'active': N, 'acknowledged': N, 'resolved': N,
         'drone_uav': N, 'ugs_ground': N, 'sigint_text': N}
    """
    with get_db() as c:
        rows = [dict(r) for r in c.execute('SELECT domain, status FROM army_feeds').fetchall()]

    stats = {
        'total': len(rows),
        'active': 0,
        'acknowledged': 0,
        'resolved': 0,
        'drone_uav': 0,
        'ugs_ground': 0,
        'sigint_text': 0
    }

    for r in rows:
        status = (r.get('status') or 'ACTIVE').upper()
        domain = (r.get('domain') or '').upper()

        if status == 'ACTIVE':
            stats['active'] += 1
        elif status == 'ACKNOWLEDGED':
            stats['acknowledged'] += 1
        elif status == 'RESOLVED':
            stats['resolved'] += 1

        if domain == 'DRONE_UAV':
            stats['drone_uav'] += 1
        elif domain == 'UGS_GROUND':
            stats['ugs_ground'] += 1
        elif domain == 'SIGINT_TEXT':
            stats['sigint_text'] += 1

    return stats
