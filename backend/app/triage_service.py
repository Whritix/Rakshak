"""Automated Workload Triage Engine & Analyst Time Reduction Service — Project Rakshak 2.0.

Provides:
1. Entity Aggregator / Denominator Consolidation (500m convoy clustering, temporal de-duplication, known-static baseline).
2. Configurable defense auto-triage rules for maritime vessels AND non-vessel entities.
3. Rigorous Safety Anomaly Verification (AIS spoofing detection, kinematic violations, stale heartbeats, geofence breaches).
4. Time-reduction estimation model with explicit assumption labeling (default 120.0s manual review per item).
5. SQLite WAL persistent audit log (auto_triage_audit table) with sticky human overrides and zero duplicate rows.
6. RBAC operator role restriction on overrides.
"""
from __future__ import annotations
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from contextlib import contextmanager
from backend.app.db import get_db

@contextmanager
def db_session():
    c = get_db()
    try:
        yield c
    finally:
        c.close()

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'backend' / 'app' / 'triage_config.json'

DEFAULT_CONFIG: Dict[str, Any] = {
    "thresholds": {
        "low_threat_max": 39,
        "medium_threat_min": 40,
        "medium_threat_max": 69,
        "high_threat_min": 70
    },
    "rules": {
        "auto_close_requires_ais_match_for_vessels": True,
        "auto_close_requires_transponder_for_aircraft": True,
        "allowed_auto_close_classes": [
            "Vessel", "Merchant / Corvette", "Frigate / Bulk Carrier",
            "Capital Ship / VLCC Tanker", "Small Craft / Dhow", "Patrol Vessel / Trawler",
            "Vehicle"
        ],
        "disallowed_auto_close_classes": [
            "TACTICAL_CONVOY", "Military Vehicle Convoy", "Aircraft"
        ],
        "non_vessel_auto_close_policies": {
            "known_static_infrastructure": {
                "enabled": True,
                "require_known_static_baseline": True,
                "max_threat_score": 39,
                "require_outside_geofences": True,
                "require_non_cluster": True,
                "description": "Auto-close infrastructure ONLY when verified against multi-temporal historical baseline (is_known_static=true). Class-based static assumption on single-pass non-overlapping scenes is removed."
            },
            "transient_isolated_low_confidence": {
                "enabled": True,
                "max_threat_score": 35,
                "max_confidence": 0.45,
                "require_isolated_distance_m": 500.0,
                "require_outside_geofences": True,
                "description": "Single low-confidence transient observation outside geofences is auto-closed"
            },
            "routine_civilian_vehicle": {
                "enabled": True,
                "max_threat_score": 30,
                "require_outside_geofences": True,
                "require_non_cluster": True,
                "description": "Single isolated civilian vehicle outside all geofences not part of convoy is auto-closed"
            }
        },
        "safety_checks": {
            "enforce_ais_position_plausibility": True,
            "max_ais_spatial_deviation_m": 1500.0,
            "subtle_spoof_review_deviation_m": 300.0,
            "enforce_kinematic_speed_ceiling_knots": 45.0,
            "commercial_cargo_speed_ceiling_knots": 28.0,
            "max_ais_heartbeat_age_hours": 4.0,
            "strictly_block_geofence_breaches": True,
            "enable_dead_reckoning": True
        }
    },
    "entity_consolidation": {
        "convoy_cluster_radius_m": 500.0,
        "temporal_dedup_radius_m": 35.0,
        "static_infrastructure_baseline_radius_m": 50.0
    },
    "time_model_assumptions": {
        "manual_screening_minutes_per_scene_baseline": 40.0,
        "manual_review_seconds_per_item": 120.0,
        "working_hours_per_shift": 8.0,
        "scenes_per_hour_standard_rate": 12,
        "methodology_note": "ASSUMPTION: Baseline manual screening is 40.0 min (2,400s) per scene. At 12 scenes/hr, baseline analyst workload is 8.0 hours per surveillance hour. Remaining workload is calculated as human-review items multiplied by review seconds per item."
    }
}


def haversine_dist_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance between decimal coordinates in meters."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def load_triage_config() -> Dict[str, Any]:
    """Load configurable triage thresholds and time model parameters."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged = dict(DEFAULT_CONFIG)
                merged.update(data)
                return merged
        except Exception:
            pass
    return DEFAULT_CONFIG


def save_triage_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """Persist updated triage configuration."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, indent=2)
    return new_config


# ── 1. Entity Aggregator / Denominator Consolidation ─────────────────────────
def consolidate_detections_into_entities(
    detections: List[Dict[str, Any]],
    zones: Optional[List[Dict[str, Any]]] = None,
    cfg: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Cluster raw bounding box detections into tactical entities.

    Consolidates:
    - Vehicles within 500m -> Single TACTICAL_CONVOY entity.
    - Infrastructure within 500m -> Single FACILITY_COMPOUND entity (with known-static flag).
    - Temporal de-duplication within 35m across repeated passes -> Single re-observed entity.
    - Isolated detections -> Single ISOLATED entity.

    Returns:
        (entities_list, consolidation_stats_dict)
    """
    if cfg is None:
        cfg = load_triage_config()

    params = cfg.get("entity_consolidation", DEFAULT_CONFIG["entity_consolidation"])
    convoy_radius = float(params.get("convoy_cluster_radius_m", 500.0))
    dedup_radius = float(params.get("temporal_dedup_radius_m", 35.0))
    static_radius = float(params.get("static_infrastructure_baseline_radius_m", 50.0))

    if zones is None:
        with db_session() as c:
            zones = [dict(r) for r in c.execute("SELECT * FROM zones").fetchall()]

    raw_count = len(detections)
    if raw_count == 0:
        return [], {"raw_detections": 0, "consolidated_entities": 0, "compression_ratio": 1.0}

    # Partition by broad class
    vessels = [d for d in detections if d.get("kind") in {"Vessel"} or "SAR" in str(d.get("source_type", ""))]
    vehicles = [d for d in detections if d.get("kind") == "Vehicle"]
    infra = [d for d in detections if d.get("kind") == "Infrastructure"]
    aircraft = [d for d in detections if d.get("kind") == "Aircraft"]
    other = [d for d in detections if d not in vessels and d not in vehicles and d not in infra and d not in aircraft]

    entities = []

    # Helper: Check if coordinate falls inside any restricted defense zone
    def check_geofence(lat: Optional[float], lon: Optional[float]) -> Tuple[bool, Optional[str]]:
        if lat is None or lon is None:
            return False, None
        for z in zones:
            dist_km = haversine_dist_m(lat, lon, z["lat"], z["lon"]) / 1000.0
            if dist_km <= z.get("radius_km", 10.0):
                return True, z.get("name", "RESTRICTED_ZONE")
        return False, None

    # Helper: Spatial Connected-Component Clustering
    def cluster_points(items: List[Dict[str, Any]], radius_m: float) -> List[List[Dict[str, Any]]]:
        visited = set()
        clusters = []
        for i, it in enumerate(items):
            if i in visited:
                continue
            visited.add(i)
            cluster = [it]
            queue = [it]
            while queue:
                curr = queue.pop(0)
                if curr.get("lat") is None or curr.get("lon") is None:
                    continue
                for j, other in enumerate(items):
                    if j not in visited and other.get("lat") is not None and other.get("lon") is not None:
                        d = haversine_dist_m(curr["lat"], curr["lon"], other["lat"], other["lon"])
                        if d <= radius_m:
                            visited.add(j)
                            cluster.append(other)
                            queue.append(other)
            clusters.append(cluster)
        return clusters

    # 1. Vehicles: 500m Convoy Clustering
    vehicle_clusters = cluster_points(vehicles, convoy_radius)
    for c in vehicle_clusters:
        c_lats = [x["lat"] for x in c if x.get("lat") is not None]
        c_lons = [x["lon"] for x in c if x.get("lon") is not None]
        avg_lat = sum(c_lats) / len(c_lats) if c_lats else None
        avg_lon = sum(c_lons) / len(c_lons) if c_lons else None
        max_score = max((x.get("threat_score") or 0) for x in c)
        max_conf = max((x.get("confidence") or 0.5) for x in c)
        in_geo, geo_name = check_geofence(avg_lat, avg_lon)

        is_convoy = len(c) >= 3
        ent_type = "TACTICAL_CONVOY" if is_convoy else "ISOLATED_VEHICLE"
        primary_id = c[0].get("id") or c[0].get("item_id")

        entities.append({
            "entity_id": f"ent-veh-{primary_id[:8]}",
            "primary_item_id": primary_id,
            "entity_type": ent_type,
            "kind": "Military Vehicle Convoy" if is_convoy else "Vehicle",
            "source_type": c[0].get("source_type", "OPTICAL_DETECTION"),
            "scene_or_source": c[0].get("scene_or_source") or c[0].get("image_name"),
            "raw_detection_count": len(c),
            "lat": avg_lat,
            "lon": avg_lon,
            "confidence": max_conf,
            "threat_score": min(100, max_score + (20 if is_convoy else 0) + (30 if in_geo else 0)),
            "ais_status": "unknown",
            "matched_identity": None,
            "is_convoy": is_convoy,
            "is_known_static": False,
            "is_in_geofence": in_geo,
            "geofence_name": geo_name,
            "reobserved_count": len(c),
            "constituent_items": [x.get("id") or x.get("item_id") for x in c]
        })

    # 2. Infrastructure: Compound / Known-Static Baseline Clustering
    infra_clusters = cluster_points(infra, convoy_radius)
    for c in infra_clusters:
        c_lats = [x["lat"] for x in c if x.get("lat") is not None]
        c_lons = [x["lon"] for x in c if x.get("lon") is not None]
        avg_lat = sum(c_lats) / len(c_lats) if c_lats else None
        avg_lon = sum(c_lons) / len(c_lons) if c_lons else None
        max_score = max((x.get("threat_score") or 0) for x in c)
        max_conf = max((x.get("confidence") or 0.5) for x in c)
        in_geo, geo_name = check_geofence(avg_lat, avg_lon)

        primary_id = c[0].get("id") or c[0].get("item_id")
        is_compound = len(c) >= 2
        # Static baseline: buildings detected with stable coordinates in imagery
        entities.append({
            "entity_id": f"ent-inf-{primary_id[:8]}",
            "primary_item_id": primary_id,
            "entity_type": "FACILITY_COMPOUND" if is_compound else "STATIC_INFRASTRUCTURE",
            "kind": "Infrastructure",
            "source_type": c[0].get("source_type", "OPTICAL_DETECTION"),
            "scene_or_source": c[0].get("scene_or_source") or c[0].get("image_name"),
            "raw_detection_count": len(c),
            "lat": avg_lat,
            "lon": avg_lon,
            "confidence": max_conf,
            "threat_score": min(100, max_score + (30 if in_geo else 0)),
            "ais_status": "unknown",
            "matched_identity": None,
            "is_convoy": False,
            "is_known_static": False,  # Single-pass non-overlapping scenes lack multi-temporal baseline
            "is_in_geofence": in_geo,
            "geofence_name": geo_name,
            "reobserved_count": len(c),
            "constituent_items": [x.get("id") or x.get("item_id") for x in c]
        })

    # 3. Vessels: Temporal De-duplication (35m) across passes
    vessel_clusters = cluster_points(vessels, dedup_radius)
    for c in vessel_clusters:
        v = c[0]
        primary_id = v.get("id") or v.get("item_id")
        in_geo, geo_name = check_geofence(v.get("lat"), v.get("lon"))
        entities.append({
            "entity_id": f"ent-ves-{primary_id[:8]}",
            "primary_item_id": primary_id,
            "entity_type": "MARITIME_VESSEL",
            "kind": v.get("kind", "Vessel"),
            "source_type": v.get("source_type", "OPTICAL_DETECTION"),
            "scene_or_source": v.get("scene_or_source") or v.get("image_name"),
            "raw_detection_count": len(c),
            "lat": v.get("lat"),
            "lon": v.get("lon"),
            "confidence": v.get("confidence") or 0.85,
            "threat_score": v.get("threat_score") or 20,
            "ais_status": v.get("ais_status") or "unknown",
            "matched_identity": v.get("mmsi") or v.get("matched_identity"),
            "speed_knots": v.get("speed_knots"),
            "ais_timestamp": v.get("ais_timestamp"),
            "is_convoy": False,
            "is_known_static": False,
            "is_in_geofence": in_geo,
            "geofence_name": geo_name,
            "reobserved_count": len(c),
            "constituent_items": [x.get("id") or x.get("item_id") for x in c]
        })

    # 4. Aircraft & Other
    for a in aircraft + other:
        primary_id = a.get("id") or a.get("item_id")
        in_geo, geo_name = check_geofence(a.get("lat"), a.get("lon"))
        entities.append({
            "entity_id": f"ent-oth-{primary_id[:8]}",
            "primary_item_id": primary_id,
            "entity_type": "TACTICAL_AIRCRAFT" if a.get("kind") == "Aircraft" else "SENSOR_ALERT",
            "kind": a.get("kind", "Unknown"),
            "source_type": a.get("source_type", "OPTICAL_DETECTION"),
            "scene_or_source": a.get("scene_or_source") or a.get("image_name"),
            "raw_detection_count": 1,
            "lat": a.get("lat"),
            "lon": a.get("lon"),
            "confidence": a.get("confidence") or 0.8,
            "threat_score": a.get("threat_score") or 30,
            "ais_status": "unknown",
            "matched_identity": None,
            "is_convoy": False,
            "is_known_static": False,
            "is_in_geofence": in_geo,
            "geofence_name": geo_name,
            "reobserved_count": 1,
            "constituent_items": [primary_id]
        })

    entity_count = len(entities)
    comp_ratio = round(raw_count / entity_count, 2) if entity_count else 1.0

    stats = {
        "raw_detections": raw_count,
        "consolidated_entities": entity_count,
        "compression_ratio": comp_ratio,
        "entity_breakdown": {
            "tactical_convoys": sum(1 for e in entities if e["entity_type"] == "TACTICAL_CONVOY"),
            "isolated_vehicles": sum(1 for e in entities if e["entity_type"] == "ISOLATED_VEHICLE"),
            "facility_compounds": sum(1 for e in entities if e["entity_type"] == "FACILITY_COMPOUND"),
            "static_infrastructure": sum(1 for e in entities if e["entity_type"] == "STATIC_INFRASTRUCTURE"),
            "maritime_vessels": sum(1 for e in entities if e["entity_type"] == "MARITIME_VESSEL"),
            "aircraft_and_other": sum(1 for e in entities if e["entity_type"] in {"TACTICAL_AIRCRAFT", "SENSOR_ALERT"})
        }
    }

    return entities, stats


# ── 2. Rigorous Safety & Anomaly Check Matrix ────────────────────────────────
def verify_safety_anomalies(
    contact: Dict[str, Any],
    cfg: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Check for spoofing, kinematic violations, geofence breaches, or dark vessels.

    Returns:
        (is_threat: bool, threat_reason: Optional[str], threat_code: Optional[str])
    """
    if cfg is None:
        cfg = load_triage_config()

    safety = cfg.get("rules", {}).get("safety_checks", DEFAULT_CONFIG["rules"]["safety_checks"])

    # 1. Geofence Breach Check (Strict Prohibit)
    if safety.get("strictly_block_geofence_breaches", True) and contact.get("is_in_geofence"):
        g_name = contact.get("geofence_name", "MILITARY_RESTRICTED_ZONE")
        return True, f"CRITICAL: Target inside restricted defense buffer zone ({g_name})", "GEOFENCE_BREACH"

    # 2. AIS Position Spoofing & Dead-Reckoning Check
    if safety.get("enforce_ais_position_plausibility", True):
        ais_lat = contact.get("ais_lat")
        ais_lon = contact.get("ais_lon")
        det_lat = contact.get("lat")
        det_lon = contact.get("lon")
        if ais_lat is not None and ais_lon is not None and det_lat is not None and det_lon is not None:
            proj_lat, proj_lon = ais_lat, ais_lon
            enable_dr = safety.get("enable_dead_reckoning", True)
            time_offset_s = contact.get("time_offset_s")
            if time_offset_s is None and contact.get("time_offset_min") is not None:
                time_offset_s = float(contact["time_offset_min"]) * 60.0

            speed_kts = contact.get("speed_knots")
            heading = contact.get("heading_deg")
            if heading is None:
                heading = contact.get("heading")
            if heading is None:
                heading = contact.get("course_deg")
            if heading is None:
                heading = contact.get("course")

            if enable_dr and time_offset_s and speed_kts is not None and heading is not None:
                speed_mps = float(speed_kts) * 0.514444
                dist_dr_m = speed_mps * float(time_offset_s)
                rad_h = math.radians(float(heading))
                dlat = (dist_dr_m * math.cos(rad_h)) / 111139.0
                cos_lat = math.cos(math.radians(ais_lat))
                dlon = (dist_dr_m * math.sin(rad_h)) / (111139.0 * (cos_lat if abs(cos_lat) > 1e-6 else 1.0))
                proj_lat = ais_lat + dlat
                proj_lon = ais_lon + dlon

            dev_m = haversine_dist_m(det_lat, det_lon, proj_lat, proj_lon)
            max_dev = float(safety.get("max_ais_spatial_deviation_m", 1500.0))
            subtle_dev = float(safety.get("subtle_spoof_review_deviation_m", 300.0))

            if dev_m > max_dev:
                return True, f"AIS SPOOFING DETECTED: Transponder reported coordinates deviate {dev_m:.0f}m > {max_dev:.0f}m from sensor position", "AIS_SPOOFING_POSITION"
            elif dev_m > subtle_dev:
                return False, f"SUBTLE AIS DEVIATION: Coordinate discrepancy of {dev_m:.0f}m ({subtle_dev:.0f}m–{max_dev:.0f}m) requires human review", "AIS_SUBTLE_SPOOF_REVIEW"

    # 3. Kinematic Speed Ceilings
    speed = contact.get("speed_knots")
    if speed is not None:
        max_speed = float(safety.get("enforce_kinematic_speed_ceiling_knots", 45.0))
        kind = str(contact.get("kind", "")).lower()
        # Commercial cargo/tanker speed threshold
        if any(w in kind for w in ["tanker", "cargo", "bulk", "container", "merchant"]) and speed > 28.0:
            return True, f"IMPLAUSIBLE KINEMATICS: Commercial vessel reported speed {speed:.1f} kts exceeds physical design max 28 kts", "KINEMATIC_VIOLATION"
        elif speed > max_speed:
            return True, f"IMPLAUSIBLE KINEMATICS: Contact velocity {speed:.1f} kts exceeds maritime ceiling {max_speed:.1f} kts", "KINEMATIC_VIOLATION"

    # 4. Stale AIS Heartbeat Check
    ais_ts = contact.get("ais_timestamp")
    age_hrs = contact.get("heartbeat_age_hours")
    if age_hrs is None and ais_ts:
        try:
            ts_dt = datetime.fromisoformat(ais_ts.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            age_hrs = (now_dt - ts_dt).total_seconds() / 3600.0
        except Exception:
            pass
    if age_hrs is not None:
        max_age = float(safety.get("max_ais_heartbeat_age_hours", 4.0))
        if age_hrs > max_age:
            return True, f"STALE AIS: Last transponder transmission is {age_hrs:.1f}h old (> {max_age:.1f}h)", "STALE_AIS_HEARTBEAT"

    # 5. Confirmed Dark Vessel Check
    if contact.get("ais_status") == "unmatched" and contact.get("kind") in {"Vessel", "Merchant / Corvette", "Patrol Vessel / Trawler"}:
        return True, "CONFIRMED DARK VESSEL: Radar/optical maritime contact with AIS transponder silenced/disabled", "DARK_VESSEL"

    return False, None, None


# ── 3. Unified Auto-Triage Decision Engine ──────────────────────────────────
def evaluate_contact(
    item_id: str,
    threat_score: int,
    ais_status: str,
    kind: str,
    source_type: str = "OPTICAL_DETECTION",
    scene_or_source: Optional[str] = None,
    matched_identity: Optional[str] = None,
    contact_meta: Optional[Dict[str, Any]] = None,
    cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Evaluate an entity or contact against configurable defense auto-triage rules.

    Rules Matrix:
    1. Safety Anomaly Violation -> ESCALATED_PRIORITY (Strictly Barred from Auto-Close).
    2. Maritime Vessel: Threat LOW (<= 39) + Matched AIS -> AUTO_CLOSED.
    3. Non-Vessel Entity (Infrastructure / Vehicle):
       - Known Static Infrastructure: threat <= 39, outside geofence, not in cluster -> AUTO_CLOSED.
       - Transient Low-Confidence Isolated: threat <= 35, conf <= 0.45, outside geofence -> AUTO_CLOSED.
       - Routine Civilian Vehicle: threat <= 30, outside geofence, isolated -> AUTO_CLOSED.
    4. Tactical Military Classes (Convoy, Artillery, UGS) -> ESCALATED_PRIORITY / REVIEW.
    5. Moderate Risk / Unverified -> HUMAN_REVIEW_QUEUE.
    """
    if cfg is None:
        cfg = load_triage_config()

    if contact_meta is None:
        contact_meta = {}

    thresholds = cfg.get("thresholds", DEFAULT_CONFIG["thresholds"])
    rules = cfg.get("rules", DEFAULT_CONFIG["rules"])
    non_vessel = rules.get("non_vessel_auto_close_policies", DEFAULT_CONFIG["rules"]["non_vessel_auto_close_policies"])

    low_max = thresholds.get("low_threat_max", 39)
    med_min = thresholds.get("medium_threat_min", 40)
    med_max = thresholds.get("medium_threat_max", 69)
    high_min = thresholds.get("high_threat_min", 70)

    disallowed = set(rules.get("disallowed_auto_close_classes", []))

    # Package contact details for safety check
    eval_pkg = dict(contact_meta)
    eval_pkg.update({
        "item_id": item_id,
        "threat_score": threat_score,
        "ais_status": ais_status,
        "kind": kind,
        "matched_identity": matched_identity
    })

    # Step A: Safety Anomaly Audit
    is_anomaly, anomaly_reason, anomaly_code = verify_safety_anomalies(eval_pkg, cfg)
    if is_anomaly:
        return {
            "item_id": item_id,
            "source_type": source_type,
            "scene_or_source": scene_or_source or "UNKNOWN",
            "kind": kind,
            "threat_score": max(75, threat_score),
            "threat_level": "HIGH",
            "triage_action": "ESCALATED_PRIORITY",
            "queue": "PRIORITY_QUEUE",
            "matched_identity": matched_identity,
            "reason": anomaly_reason,
            "safety_anomaly_flag": anomaly_code
        }
    if anomaly_code == "AIS_SUBTLE_SPOOF_REVIEW":
        return {
            "item_id": item_id,
            "source_type": source_type,
            "scene_or_source": scene_or_source or "UNKNOWN",
            "kind": kind,
            "threat_score": max(50, threat_score),
            "threat_level": "MEDIUM",
            "triage_action": "HUMAN_REVIEW",
            "queue": "HUMAN_REVIEW_QUEUE",
            "matched_identity": matched_identity,
            "reason": anomaly_reason,
            "safety_anomaly_flag": anomaly_code
        }

    # Step B: Disallowed Military Threat Classes (Convoys strictly prohibited)
    if (kind in disallowed and kind != "Aircraft") or "Convoy" in kind:
        return {
            "item_id": item_id,
            "source_type": source_type,
            "scene_or_source": scene_or_source or "UNKNOWN",
            "kind": kind,
            "threat_score": max(70, threat_score),
            "threat_level": "HIGH",
            "triage_action": "ESCALATED_PRIORITY",
            "queue": "PRIORITY_QUEUE",
            "matched_identity": matched_identity,
            "reason": f"Tactical military threat class ({kind}) strictly prohibited from auto-closure.",
            "safety_anomaly_flag": None
        }

    # Step C: High Threat Scores
    if threat_score >= high_min:
        return {
            "item_id": item_id,
            "source_type": source_type,
            "scene_or_source": scene_or_source or "UNKNOWN",
            "kind": kind,
            "threat_score": threat_score,
            "threat_level": "HIGH",
            "triage_action": "ESCALATED_PRIORITY",
            "queue": "PRIORITY_QUEUE",
            "matched_identity": matched_identity,
            "reason": f"High risk score ({threat_score} >= {high_min}). Escalated for priority command review.",
            "safety_anomaly_flag": None
        }

    # Step D1: Aircraft Domain Triage (Requires verified transponder / cooperative identification)
    is_aircraft = kind in {"Aircraft", "TACTICAL_AIRCRAFT"}
    if is_aircraft:
        is_transponder_matched = (ais_status == "matched") or (matched_identity is not None and str(matched_identity).strip() != "" and ais_status != "unmatched")
        if threat_score <= low_max and is_transponder_matched:
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "LOW",
                "triage_action": "AUTO_CLOSED",
                "queue": "AUTO_CLOSED_ARCHIVE",
                "matched_identity": matched_identity or "IFF-VERIFIED",
                "reason": f"Routine cooperative aircraft with verified transponder (Threat {threat_score} <= {low_max}, Identity: {matched_identity or 'IFF-VERIFIED'}). Auto-closed.",
                "safety_anomaly_flag": None
            }
        else:
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "MEDIUM" if threat_score >= med_min else "LOW",
                "triage_action": "HUMAN_REVIEW",
                "queue": "HUMAN_REVIEW_QUEUE",
                "matched_identity": matched_identity,
                "reason": f"Aircraft requires radar/visual track verification (Threat {threat_score}, Transponder: {ais_status}). Strictly barred from uncooperative auto-closure.",
                "safety_anomaly_flag": None
            }

    # Step D2: Maritime Vessel Domain Triage (Requires verified AIS transponder)
    is_vessel = kind in {"Vessel", "Merchant / Corvette", "Frigate / Bulk Carrier", "Capital Ship / VLCC Tanker", "Small Craft / Dhow", "Patrol Vessel / Trawler"} or "SAR" in source_type
    if is_vessel:
        is_ais_matched = (ais_status == "matched") or (matched_identity is not None and str(matched_identity).strip() != "" and ais_status != "unmatched")
        if threat_score <= low_max and is_ais_matched:
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "LOW",
                "triage_action": "AUTO_CLOSED",
                "queue": "AUTO_CLOSED_ARCHIVE",
                "matched_identity": matched_identity or "AIS-VERIFIED",
                "reason": f"Routine cooperative vessel (Threat {threat_score} <= {low_max}, AIS MMSI: {matched_identity or 'VERIFIED'}). Auto-closed by naval defense rule.",
                "safety_anomaly_flag": None
            }
        else:
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "MEDIUM" if threat_score >= med_min else "LOW",
                "triage_action": "HUMAN_REVIEW",
                "queue": "HUMAN_REVIEW_QUEUE",
                "matched_identity": matched_identity,
                "reason": f"Vessel requires visual/kinematic confirmation (Threat: {threat_score}, AIS: {ais_status}). Routed to secondary review.",
                "safety_anomaly_flag": None
            }

    # Step E: Non-Vessel Explainable Auto-Close Policies
    # Policy 1: Known Static Baseline Infrastructure (Requires verified multi-temporal baseline)
    p_infra = non_vessel.get("known_static_infrastructure", {})
    if p_infra.get("enabled", True) and kind == "Infrastructure":
        in_geo = contact_meta.get("is_in_geofence", False)
        is_cluster = contact_meta.get("is_convoy", False)
        is_known_static = contact_meta.get("is_known_static", False)
        if threat_score <= p_infra.get("max_threat_score", 39) and not in_geo and not is_cluster and is_known_static:
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "LOW",
                "triage_action": "AUTO_CLOSED",
                "queue": "AUTO_CLOSED_ARCHIVE",
                "matched_identity": None,
                "reason": f"Known static baseline infrastructure outside military geofences (Threat {threat_score} <= {p_infra.get('max_threat_score', 39)}). Auto-closed.",
                "safety_anomaly_flag": None
            }

    # Policy 2: Transient Isolated Low-Confidence Vehicle Speckle
    p_trans = non_vessel.get("transient_isolated_low_confidence", {})
    if p_trans.get("enabled", True) and kind == "Vehicle":
        conf = contact_meta.get("confidence", 0.5)
        in_geo = contact_meta.get("is_in_geofence", False)
        is_convoy = contact_meta.get("is_convoy", False)
        reobserved = contact_meta.get("reobserved_count", 1)
        if (threat_score <= p_trans.get("max_threat_score", 35) and
            conf <= p_trans.get("max_confidence", 0.45) and
            not in_geo and not is_convoy and reobserved <= 1):
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "LOW",
                "triage_action": "AUTO_CLOSED",
                "queue": "AUTO_CLOSED_ARCHIVE",
                "matched_identity": None,
                "reason": f"Transient isolated low-confidence observation outside geofences (Confidence {conf:.2f} <= {p_trans.get('max_confidence', 0.45)}, Threat {threat_score}). Auto-closed.",
                "safety_anomaly_flag": None
            }

    # Policy 3: Routine Civilian Vehicle Outside Geofences
    p_veh = non_vessel.get("routine_civilian_vehicle", {})
    if p_veh.get("enabled", True) and kind == "Vehicle":
        in_geo = contact_meta.get("is_in_geofence", False)
        is_convoy = contact_meta.get("is_convoy", False)
        if threat_score <= p_veh.get("max_threat_score", 30) and not in_geo and not is_convoy:
            return {
                "item_id": item_id,
                "source_type": source_type,
                "scene_or_source": scene_or_source or "UNKNOWN",
                "kind": kind,
                "threat_score": threat_score,
                "threat_level": "LOW",
                "triage_action": "AUTO_CLOSED",
                "queue": "AUTO_CLOSED_ARCHIVE",
                "matched_identity": None,
                "reason": f"Routine isolated civilian vehicle in benign territory outside exclusion buffers (Threat {threat_score} <= {p_veh.get('max_threat_score', 30)}). Auto-closed.",
                "safety_anomaly_flag": None
            }

    # Fallthrough -> Human Review Queue
    return {
        "item_id": item_id,
        "source_type": source_type,
        "scene_or_source": scene_or_source or "UNKNOWN",
        "kind": kind,
        "threat_score": threat_score,
        "threat_level": "MEDIUM" if threat_score >= med_min else "LOW",
        "triage_action": "HUMAN_REVIEW",
        "queue": "HUMAN_REVIEW_QUEUE",
        "matched_identity": matched_identity,
        "reason": f"Moderate risk target requiring analyst visual verification (Threat {threat_score}).",
        "safety_anomaly_flag": None
    }


# ── 4. Triage Cycle Execution with Sticky Overrides ─────────────────────────
def execute_triage_cycle(persist_audit: bool = True) -> Dict[str, Any]:
    """Execute auto-triage cycle across active database records with sticky overrides."""
    cfg = load_triage_config()
    now_iso = datetime.now(timezone.utc).isoformat()

    items_to_eval = []
    with db_session() as c:
        for r in c.execute('SELECT * FROM detections').fetchall():
            items_to_eval.append({
                'item_id': r['id'],
                'source_type': 'OPTICAL_DETECTION',
                'scene_or_source': r['image_name'],
                'kind': r['kind'],
                'threat_score': r['threat_score'] or 0,
                'ais_status': r['ais_status'] or 'unknown',
                'matched_identity': r['mmsi'],
                'lat': r['lat'],
                'lon': r['lon'],
                'confidence': r['confidence'],
                'existing_review_status': r['review_status']
            })

        for s in c.execute('SELECT * FROM sar_detections').fetchall():
            ais_st = 'matched' if s['ais_correlated'] else 'unmatched' if s['is_dark_vessel'] else 'unknown'
            items_to_eval.append({
                'item_id': s['id'],
                'source_type': 'SAR_RADAR',
                'scene_or_source': s['scene_id'],
                'kind': s['vessel_class'] or 'Vessel Contact',
                'threat_score': s['threat_score'] or 85,
                'ais_status': ais_st,
                'matched_identity': s['correlated_mmsi'],
                'lat': s['lat'],
                'lon': s['lon'],
                'confidence': s['cfar_confidence'],
                'existing_review_status': 'auto_closed' if not s['is_dark_vessel'] and (s['threat_score'] or 0) <= 39 else 'pending'
            })

        for a in c.execute('SELECT * FROM army_feeds').fetchall():
            items_to_eval.append({
                'item_id': a['id'],
                'source_type': f'ARMY_{a["domain"]}',
                'scene_or_source': a['source_ref'],
                'kind': a['target_class'],
                'threat_score': a['threat_score'] or 50,
                'ais_status': 'unknown',
                'matched_identity': None,
                'lat': a['lat'],
                'lon': a['lon'],
                'confidence': a['confidence'],
                'existing_review_status': a['status']
            })

    # Sticky human overrides: Contacts previously marked REOPENED stay in review queue forever!
    reopened_item_ids: Set[str] = set()
    with db_session() as c:
        for row in c.execute("SELECT item_id FROM auto_triage_audit WHERE status = 'REOPENED'").fetchall():
            reopened_item_ids.add(row[0])

    # Consolidate into entities
    entities, entity_stats = consolidate_detections_into_entities(items_to_eval, cfg=cfg)

    evaluated_entities = []
    auto_closed_count = 0
    human_review_count = 0
    escalated_count = 0
    audit_records = []
    det_status_updates = []

    for ent in entities:
        res = evaluate_contact(
            item_id=ent["primary_item_id"],
            threat_score=ent["threat_score"],
            ais_status=ent["ais_status"],
            kind=ent["kind"],
            source_type=ent["source_type"],
            scene_or_source=ent["scene_or_source"],
            matched_identity=ent["matched_identity"],
            contact_meta=ent,
            cfg=cfg
        )

        # Enforce Sticky Reopen
        if ent["primary_item_id"] in reopened_item_ids:
            res["triage_action"] = "HUMAN_REVIEW"
            res["queue"] = "HUMAN_REVIEW_QUEUE"
            res["reason"] = "HUMAN OVERRIDE ACTIVE: Contact previously reopened by operator. Auto-close suppressed."

        act = res["triage_action"]
        if act == "AUTO_CLOSED":
            auto_closed_count += 1
            for cid in ent["constituent_items"]:
                det_status_updates.append(("auto_closed", cid))
            audit_records.append((
                uuid.uuid4().hex,
                ent["primary_item_id"],
                res["source_type"],
                res["scene_or_source"],
                res["kind"],
                res["threat_score"],
                res["threat_level"],
                res["triage_action"],
                "CLOSED",
                res["matched_identity"],
                res["reason"],
                now_iso
            ))
        elif act == "HUMAN_REVIEW":
            human_review_count += 1
            for cid in ent["constituent_items"]:
                det_status_updates.append(("pending", cid))
        else: # ESCALATED_PRIORITY
            escalated_count += 1
            for cid in ent["constituent_items"]:
                det_status_updates.append(("escalated", cid))

        evaluated_entities.append(res)

    total_ent = len(evaluated_entities)
    auto_closed_pct = round((auto_closed_count / total_ent * 100.0), 2) if total_ent else 0.0
    human_review_pct = round((human_review_count / total_ent * 100.0), 2) if total_ent else 0.0
    escalated_pct = round((escalated_count / total_ent * 100.0), 2) if total_ent else 0.0

    # Time model
    time_cfg = cfg.get("time_model_assumptions", DEFAULT_CONFIG["time_model_assumptions"])
    sec_per_item = float(time_cfg.get("manual_review_seconds_per_item", 120.0))
    shift_hours = float(time_cfg.get("working_hours_per_shift", 8.0))
    analyst_hours_saved = round((auto_closed_count * sec_per_item) / 3600.0, 2)
    analyst_shifts_saved = round(analyst_hours_saved / shift_hours, 2)

    # Persist audit idempotently (No Duplicate Rows)
    if persist_audit and audit_records:
        with db_session() as c:
            for rec in audit_records:
                existing = c.execute("SELECT id, status FROM auto_triage_audit WHERE item_id = ?", (rec[1],)).fetchone()
                if existing:
                    if existing["status"] != "REOPENED":
                        c.execute("""
                            UPDATE auto_triage_audit
                            SET threat_score=?, threat_level=?, triage_action=?, status='CLOSED', reason=?, triaged_at=?
                            WHERE item_id=?
                        """, (rec[5], rec[6], rec[7], rec[10], rec[11], rec[1]))
                else:
                    c.execute("""
                        INSERT INTO auto_triage_audit (
                            id, item_id, source_type, scene_or_source, kind, threat_score, threat_level,
                            triage_action, status, matched_identity, reason, triaged_at
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """, rec)

            for st, did in det_status_updates:
                c.execute("UPDATE detections SET review_status = ? WHERE id = ? AND review_status != 'reviewed'", (st, did))

            c.commit()

    return {
        "status": "COMPLETED",
        "evaluated_at": now_iso,
        "entity_consolidation": entity_stats,
        "total_entities": total_ent,
        "queues": {
            "auto_closed": {
                "count": auto_closed_count,
                "percentage": auto_closed_pct,
                "description": "Routine contacts auto-closed by defense rules"
            },
            "human_review": {
                "count": human_review_count,
                "percentage": human_review_pct,
                "description": "Moderate risk or unverified contacts in review queue"
            },
            "escalated_priority": {
                "count": escalated_count,
                "percentage": escalated_pct,
                "description": "High-threat contacts, dark vessels, and tactical targets"
            }
        },
        "time_model": {
            "seconds_per_item": sec_per_item,
            "analyst_hours_saved": analyst_hours_saved,
            "analyst_shifts_saved": analyst_shifts_saved,
            "workload_reduction_pct": auto_closed_pct,
            "assumption_notice": time_cfg.get("methodology_note", "ASSUMPTION: 120.0s manual triage baseline per contact")
        }
    }


def get_audit_trail(limit: int = 50, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve audit log entries of triaged contacts."""
    with db_session() as c:
        query = "SELECT * FROM auto_triage_audit"
        params = []
        if status_filter:
            query += " WHERE status = ?"
            params.append(status_filter.upper())
        query += " ORDER BY triaged_at DESC LIMIT ?"
        params.append(limit)

        rows = c.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def reopen_triaged_item(
    item_id: str,
    operator: str = "OPERATOR",
    reason: str = "Manual override",
    operator_role: str = "OPERATOR"
) -> Dict[str, Any]:
    """Human override action to undo/reopen an auto-closed item with RBAC validation."""
    # RBAC Enforcement: Only authorized operator roles can override
    authorized_roles = {"COMMANDER", "ANALYST", "OPERATOR", "TACTICAL_COMMANDER", "SUPER_ADMIN"}
    if str(operator_role).upper() not in authorized_roles:
        return {
            "success": False,
            "error": f"Access Denied: Role '{operator_role}' is not authorized to override defense triage decisions.",
            "status_code": 403
        }

    now_iso = datetime.now(timezone.utc).isoformat()
    with db_session() as c:
        row = c.execute("SELECT * FROM auto_triage_audit WHERE item_id = ?", (item_id,)).fetchone()
        if not row:
            det = c.execute("SELECT * FROM detections WHERE id = ?", (item_id,)).fetchone()
            if not det:
                return {"success": False, "error": f"Item {item_id} not found in defense registry.", "status_code": 404}
            c.execute("""
                INSERT INTO auto_triage_audit (
                    id, item_id, source_type, scene_or_source, kind, threat_score, threat_level,
                    triage_action, status, matched_identity, reason, triaged_at, reopened_at, reopened_by
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                uuid.uuid4().hex, item_id, 'OPTICAL_DETECTION', det['image_name'], det['kind'],
                det['threat_score'] or 0, det['threat_level'] or 'LOW', 'AUTO_CLOSED', 'REOPENED',
                det['mmsi'], reason, now_iso, now_iso, operator
            ))
        else:
            c.execute("""
                UPDATE auto_triage_audit
                SET status = 'REOPENED', reopened_at = ?, reopened_by = ?, reason = ?
                WHERE item_id = ?
            """, (now_iso, operator, reason, item_id))

        c.execute("UPDATE detections SET review_status = 'reopened' WHERE id = ?", (item_id,))
        c.commit()
        updated_row = dict(c.execute("SELECT * FROM auto_triage_audit WHERE item_id = ?", (item_id,)).fetchone())

    return {
        "success": True,
        "message": f"Contact {item_id} successfully reopened and permanently returned to Human Review Queue.",
        "record": updated_row
    }
