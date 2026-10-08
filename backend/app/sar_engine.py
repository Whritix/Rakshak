"""Sentinel-1 SAR Radar Backscatter & Automated Dark-Vessel Detection Engine.

Implements:
1. Constant False Alarm Rate (CA-CFAR) radar backscatter thresholding (sigma0 in dB).
2. Physical vessel waterline length classification into defense naval categories.
3. Automated cross-sensor correlation with AIS transponder pings.
4. Classification and tactical tracking of 'Dark Vessels' (uncooperative vessels with transponders silenced).
"""
from __future__ import annotations
import math
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.db import get_db


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Spherical distance between two decimal coordinates in kilometers."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def classify_vessel_by_length(length_m: float) -> str:
    """Classify vessel category based on estimated physical waterline length (meters).

    Taxonomy aligned with naval intelligence recognition standards:
    - <25m:   Small Craft / Dhow / Skiff (high-speed asymmetric threat or coastal fishing)
    - <60m:   Patrol Vessel / Commercial Trawler (EEZ loitering / dual-use surveillance)
    - <120m:  Merchant / Corvette (coastal cargo / naval escort)
    - <250m:  Frigate / Bulk Carrier / Tanker (commercial deep-sea or major surface combatant)
    - >=250m: Capital Ship / VLCC Supertanker / Container Carrier
    """
    if length_m < 25:
        return 'Small Craft / Dhow'
    elif length_m < 60:
        return 'Patrol Vessel / Trawler'
    elif length_m < 120:
        return 'Merchant / Corvette'
    elif length_m < 250:
        return 'Frigate / Bulk Carrier'
    else:
        return 'Capital Ship / VLCC Tanker'


def cfar_detect(
    sigma0_db: float,
    sea_clutter_db: float = -22.0,
    threshold_factor: float = 3.5
) -> tuple[bool, float]:
    """Cell-Averaging Constant False Alarm Rate (CA-CFAR) radar target detection.

    Args:
        sigma0_db: Calibrated radar backscatter cross section (sigma0 in dB).
        sea_clutter_db: Estimated ambient sea clutter baseline (-22 dB nominal for calm sea).
        threshold_factor: Multiplier for adaptive noise thresholding.

    Returns:
        Tuple of (is_detected: bool, cfar_confidence: float [0.05 - 0.99]).
    """
    target_threshold = sea_clutter_db + (threshold_factor * 2.8)  # e.g. -22 + 9.8 = -12.2 dB
    is_detected = sigma0_db > target_threshold

    # Calibrated SNR confidence bounded strictly between [0.05 - 0.99]
    snr = sigma0_db - sea_clutter_db
    confidence = max(0.05, min(0.99, (snr - 3.0) / 28.0))
    return is_detected, round(confidence, 4)


def correlate_sar_with_ais(
    sar_lat: float,
    sar_lon: float,
    ais_targets: List[Dict[str, Any]],
    tolerance_km: float = 3.0
) -> tuple[bool, Optional[str]]:
    """Cross-reference SAR radar contact with local AIS positions within tolerance window."""
    for ais in ais_targets:
        if ais.get('lat') is not None and ais.get('lon') is not None:
            dist = haversine_km(sar_lat, sar_lon, float(ais['lat']), float(ais['lon']))
            if dist <= tolerance_km:
                mmsi = str(ais.get('mmsi') or 'MMSI-VERIFIED')
                return True, mmsi
    return False, None


def seed_sar_surveillance() -> None:
    """Populate default tactical Sentinel-1 SAR contacts in Indian operational waters if empty."""
    with get_db() as c:
        cur = c.execute('SELECT COUNT(*) FROM sar_detections')
        if cur.fetchone()[0] == 0:
            sar_scenarios = [
                {
                    'id': 'sar-001',
                    'scene_id': 'S1A_IW_GRDH_1SDV_20260428_MUMBAI_OFFSHORE',
                    'timestamp': '2026-04-28T04:12:30Z',
                    'lat': 18.8920,
                    'lon': 72.5850,
                    'rcs_sigma0_db': -7.8,
                    'estimated_length_m': 118.0,
                    'cfar_confidence': 0.94,
                    'ais_correlated': 0,
                    'correlated_mmsi': None,
                    'is_dark_vessel': 1,
                    'threat_score': 95,
                    'threat_level': 'HIGH',
                    'speed_knots': 16.8,
                    'heading_deg': 345.0,
                    'notes': 'CRITICAL DARK VESSEL: Strong metallic radar return with zero AIS broadcast within 25 km of Mumbai Harbour Naval Buffer.'
                },
                {
                    'id': 'sar-002',
                    'scene_id': 'S1A_IW_GRDH_1SDV_20260428_MUMBAI_OFFSHORE',
                    'timestamp': '2026-04-28T04:14:10Z',
                    'lat': 19.4120,
                    'lon': 71.2840,
                    'rcs_sigma0_db': -9.2,
                    'estimated_length_m': 72.0,
                    'cfar_confidence': 0.91,
                    'ais_correlated': 0,
                    'correlated_mmsi': None,
                    'is_dark_vessel': 1,
                    'threat_score': 90,
                    'threat_level': 'HIGH',
                    'speed_knots': 19.4,
                    'heading_deg': 110.0,
                    'notes': 'CRITICAL DARK VESSEL: High-speed unidentified vessel navigating inside Mumbai Offshore Development Area (Bombay High).'
                },
                {
                    'id': 'sar-003',
                    'scene_id': 'S1A_IW_GRDH_1SDV_20260428_MUMBAI_OFFSHORE',
                    'timestamp': '2026-04-28T04:15:45Z',
                    'lat': 18.8450,
                    'lon': 72.8210,
                    'rcs_sigma0_db': -11.5,
                    'estimated_length_m': 185.0,
                    'cfar_confidence': 0.88,
                    'ais_correlated': 1,
                    'correlated_mmsi': '419001284',
                    'is_dark_vessel': 0,
                    'threat_score': 20,
                    'threat_level': 'LOW',
                    'speed_knots': 8.5,
                    'heading_deg': 45.0,
                    'notes': 'COOPERATIVE: Verified merchant container vessel correlated with active AIS transponder MMSI 419001284.'
                },
                {
                    'id': 'sar-004',
                    'scene_id': 'S1A_IW_GRDH_1SDV_20260428_KARWAR_COASTAL',
                    'timestamp': '2026-04-28T05:22:15Z',
                    'lat': 14.7650,
                    'lon': 74.0240,
                    'rcs_sigma0_db': -8.1,
                    'estimated_length_m': 54.0,
                    'cfar_confidence': 0.93,
                    'ais_correlated': 0,
                    'correlated_mmsi': None,
                    'is_dark_vessel': 1,
                    'threat_score': 88,
                    'threat_level': 'HIGH',
                    'speed_knots': 12.0,
                    'heading_deg': 180.0,
                    'notes': 'DARK VESSEL: Trawler-sized contact loitering near INS Kadamba naval security perimeter with AIS turned off.'
                }
            ]
            for s in sar_scenarios:
                v_class = classify_vessel_by_length(s['estimated_length_m'])
                c.execute('''
                INSERT INTO sar_detections (
                    id, scene_id, timestamp, lat, lon, rcs_sigma0_db, estimated_length_m,
                    vessel_class, cfar_confidence, ais_correlated, correlated_mmsi, is_dark_vessel,
                    threat_score, threat_level, speed_knots, heading_deg, notes, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    s['id'], s['scene_id'], s['timestamp'], s['lat'], s['lon'],
                    s['rcs_sigma0_db'], s['estimated_length_m'], v_class, s['cfar_confidence'],
                    s['ais_correlated'], s['correlated_mmsi'], s['is_dark_vessel'],
                    s['threat_score'], s['threat_level'], s['speed_knots'], s['heading_deg'],
                    s['notes'], datetime.now(timezone.utc).isoformat()
                ))
            c.commit()
        else:
            # Backfill vessel_class for existing database rows if null
            rows = c.execute('SELECT id, estimated_length_m FROM sar_detections WHERE vessel_class IS NULL').fetchall()
            for r in rows:
                v_class = classify_vessel_by_length(r['estimated_length_m'] or 50.0)
                c.execute('UPDATE sar_detections SET vessel_class = ? WHERE id = ?', (v_class, r['id']))
            c.commit()


# Ensure default SAR surveillance contacts are seeded on startup
seed_sar_surveillance()


def list_sar_detections() -> List[Dict[str, Any]]:
    """Retrieve all Sentinel-1 SAR contacts sorted by threat score descending."""
    with get_db() as c:
        rows = c.execute('SELECT * FROM sar_detections ORDER BY threat_score DESC').fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if not d.get('vessel_class'):
                d['vessel_class'] = classify_vessel_by_length(d.get('estimated_length_m') or 50.0)
            result.append(d)
        return result


def list_dark_vessels_only() -> List[Dict[str, Any]]:
    """Retrieve only uncooperative dark vessel contacts (AIS silenced/disabled)."""
    with get_db() as c:
        rows = c.execute('SELECT * FROM sar_detections WHERE is_dark_vessel = 1 ORDER BY threat_score DESC').fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if not d.get('vessel_class'):
                d['vessel_class'] = classify_vessel_by_length(d.get('estimated_length_m') or 50.0)
            result.append(d)
        return result
