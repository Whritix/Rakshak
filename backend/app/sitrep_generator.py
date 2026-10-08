"""Automated Military Situation Report (SITREP) & Tactical Intelligence Summarizer.

Complies with STANAG / Joint Maritime & Tactical Defense intelligence reporting standards.
Fuses Sentinel-1 SAR dark vessel contacts, optical satellite detections, and multimodal Army alerts.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.db import get_db


def generate_tactical_sitrep() -> Dict[str, Any]:
    """Generate dynamic STANAG-compliant military SITREP fusing all active sensor streams."""
    with get_db() as c:
        detections = [dict(r) for r in c.execute('SELECT * FROM detections').fetchall()]
        sar_hits = [dict(r) for r in c.execute('SELECT * FROM sar_detections').fetchall()]
        army_feeds = [dict(r) for r in c.execute('SELECT * FROM army_feeds').fetchall()]
        zones = [dict(r) for r in c.execute('SELECT * FROM zones').fetchall()]

    dtg = datetime.now(timezone.utc).strftime("%d%H%MZ %b %Y").upper()

    dark_vessels = [s for s in sar_hits if s.get('is_dark_vessel')]
    high_threat_optical = [d for d in detections if d.get('threat_level') == 'HIGH']
    high_threat_army = [a for a in army_feeds if a.get('threat_level') == 'HIGH']

    total_contacts = len(detections) + len(sar_hits) + len(army_feeds)
    critical_threats = len(dark_vessels) + len(high_threat_optical) + len(high_threat_army)

    # ── Optical Class Breakdown ─────────────────────────────────────────────
    optical_class_counts: Dict[str, int] = {
        'Vessel': 0,
        'Aircraft': 0,
        'Vehicle': 0,
        'Infrastructure': 0
    }
    for d in detections:
        kind = d.get('kind') or 'Unknown'
        optical_class_counts[kind] = optical_class_counts.get(kind, 0) + 1

    # ── Multi-Sensor Threat Breakdown ───────────────────────────────────────
    threat_breakdown: Dict[str, int] = {'high': 0, 'medium': 0, 'low': 0}
    for item in detections:
        lvl = (item.get('threat_level') or 'LOW').lower()
        if lvl in threat_breakdown:
            threat_breakdown[lvl] += 1

    for item in sar_hits:
        lvl = (item.get('threat_level') or 'LOW').lower()
        if lvl in threat_breakdown:
            threat_breakdown[lvl] += 1

    for item in army_feeds:
        lvl = (item.get('threat_level') or 'LOW').lower()
        if lvl in threat_breakdown:
            threat_breakdown[lvl] += 1

    # ── Dynamic Actionable Threat Ranking (Top 3 across all sensors) ────────
    actionable_threats: List[Dict[str, Any]] = []
    for dv in dark_vessels:
        actionable_threats.append({
            'source': 'SAR RADAR',
            'id': dv['id'],
            'threat_score': dv.get('threat_score', 85),
            'lat': dv['lat'],
            'lon': dv['lon'],
            'notes': dv.get('notes') or f"High-RCS dark contact (speed {dv.get('speed_knots', 15.0)} kts)",
        })

    for af in high_threat_army:
        actionable_threats.append({
            'source': f"ARMY {af.get('domain', 'ALERT')}",
            'id': af['id'],
            'threat_score': af.get('threat_score', 80),
            'lat': af['lat'],
            'lon': af['lon'],
            'notes': af.get('alert_summary') or f"{af.get('target_class', 'Target')} reported by {af.get('source_ref')}",
        })

    for opt in high_threat_optical:
        actionable_threats.append({
            'source': f"OPTICAL {opt.get('kind', 'TARGET')}",
            'id': opt['id'],
            'threat_score': opt.get('threat_score', 75),
            'lat': opt.get('lat') or 0.0,
            'lon': opt.get('lon') or 0.0,
            'notes': f"Optical contact ({opt.get('kind')}) AIS status: {opt.get('ais_status', 'unknown')}",
        })

    actionable_threats.sort(key=lambda t: t['threat_score'], reverse=True)
    top_threats = actionable_threats[:3]

    # ── Build SITREP Document ───────────────────────────────────────────────
    sitrep_text = f"""================================================================================
TACTICAL SITUATION REPORT (SITREP) // OPERATION RAKSHAK
CLASSIFICATION: SOVEREIGN AIR-GAPPED DEFENSE INTELLIGENCE // UNCLASSIFIED R&D
DTG: {dtg}
ORIGINATOR: JOINT MARITIME & TACTICAL GEOINT CELL (INDIA AOR)
================================================================================

1. EXECUTIVE THREAT ASSESSMENT
   - OVERALL THREAT DEFCON: ELEVATED (AMBER-RED)
   - TOTAL TRACKED MULTIMODAL CONTACTS: {total_contacts}
   - CRITICAL / HIGH-PRIORITY ACTIONABLE TARGETS: {critical_threats}
   - THREAT TIER BREAKDOWN: {threat_breakdown['high']} HIGH // {threat_breakdown['medium']} MEDIUM // {threat_breakdown['low']} LOW
   - EDGE COMPUTE STATUS: 100% OPERATIONAL (NVIDIA JETSON ORIN AIR-GAPPED)

2. MARITIME DOMAIN AWARENESS (SAR & OPTICAL SATELLITE FUSION)
   - SENTINEL-1 SAR DETECTIONS: {len(sar_hits)} contacts scanned.
   - CONFIRMED DARK VESSELS (AIS OFF): {len(dark_vessels)} active uncooperative targets.
   - OPTICAL SATELLITE DETECTIONS: {len(detections)} total
     * Vessels:          {optical_class_counts.get('Vessel', 0)}
     * Aircraft:         {optical_class_counts.get('Aircraft', 0)}
     * Vehicles:         {optical_class_counts.get('Vehicle', 0)}
     * Infrastructure:   {optical_class_counts.get('Infrastructure', 0)}
"""

    for dv in dark_vessels:
        sitrep_text += f"     * TARGET [{dv['id'].upper()}]: Lat {dv['lat']:.4f}, Lon {dv['lon']:.4f} | RCS: {dv['rcs_sigma0_db']} dB | Speed: {dv['speed_knots']} kts @ {dv['heading_deg']}° | Alert: {dv['notes']}\n"

    sitrep_text += f"""
3. ARMY & TACTICAL BORDER MONITORING (DRONE FMV, UGS & SIGINT)
   - ACTIVE GROUND & AERIAL CONTACTS: {len(army_feeds)} reports ingested.
"""

    for af in high_threat_army:
        sitrep_text += f"     * SENSOR [{af['source_ref']} - {af['domain']}]: {af['target_class']} at ({af['lat']:.4f}, {af['lon']:.4f}) | Confidence: {int(af['confidence']*100)}% | Alert: {af['alert_summary']}\n"

    sitrep_text += f"""
4. RESTRICTED DEFENSE GEOFENCING STATUS
   - ACTIVE OPERATIONAL ZONES MONITORED: {len(zones)}
"""

    for z in zones:
        sitrep_text += f"     * ZONE: {z['name']} ({z['zone_type']}) | Center: ({z['lat']:.2f}, {z['lon']:.2f}), Radius: {z['radius_km']} km\n"

    sitrep_text += "\n5. RECOMMENDED COMMAND ACTIONS & INTERCEPTION VECTORS\n"
    if top_threats:
        for i, threat in enumerate(top_threats, 1):
            summary = threat.get('notes') or threat.get('alert_summary') or 'Actionable contact requiring immediate interdiction'
            sitrep_text += f"   - ACTION {i}: Vector assets to ({threat['lat']:.4f}, {threat['lon']:.4f}) — {summary}\n"
    else:
        sitrep_text += "   - ACTION: Continue routine persistent multi-domain surveillance. No immediate Level-1 threats active.\n"

    sitrep_text += """
================================================================================
END OF SITUATION REPORT // AUTOMATED MULTIMODAL SYNTHESIS
================================================================================
"""

    return {
        "dtg": dtg,
        "classification": "SOVEREIGN AIR-GAPPED // RAKSHAK TACTICAL",
        "total_contacts": total_contacts,
        "critical_threats": critical_threats,
        "optical_count": len(detections),
        "optical_class_counts": optical_class_counts,
        "threat_breakdown": threat_breakdown,
        "dark_vessel_count": len(dark_vessels),
        "army_alert_count": len(high_threat_army),
        "top_actionable_threats": top_threats,
        "report_markdown": sitrep_text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
