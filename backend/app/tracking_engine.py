"""Kinematic Multi-Target Tracking & Kalman / Dead-Reckoning Trajectory Prediction Engine.

Features:
- Class-aware Circular Error Probable (CEP) growth modeling (Vessel, Aircraft, Vehicle).
- Kinematic spherical dead-reckoning projection (WGS84 curvature-aware).
- Confidence ellipse estimation (semi-major, semi-minor, track orientation).
- Multi-interval trajectory vectors with cumulative distance calculation.
"""
from __future__ import annotations
import math
from typing import List, Dict, Any, Optional

# ── Class-Aware Uncertainty Calibration ─────────────────────────────────────
# Aircraft exhibit rapid uncertainty divergence due to high velocity & 3D maneuvering.
# Vessels diverge moderately due to ocean currents, drift, and course alterations.
# Tactical vehicles are constrained by terrain/road defiles, with lower baseline dispersion.
BASE_CEP: Dict[str, float] = {
    'Vessel': 80.0,       # Initial drift & radar resolution uncertainty (m)
    'Aircraft': 120.0,    # Airspace sensor resolution & track initiation jitter (m)
    'Vehicle': 60.0,      # High-resolution UAV track baseline uncertainty (m)
    'default': 50.0
}

GROWTH_RATE: Dict[str, float] = {
    'Vessel': 15.0,       # Meters of dispersion per minute of projection
    'Aircraft': 35.0,     # Meters per minute (high velocity & evasive turn rate)
    'Vehicle': 20.0,      # Meters per minute (road network branch uncertainty)
    'default': 18.5
}


def predict_future_position(
    lat: float,
    lon: float,
    speed_knots: float,
    heading_deg: float,
    minutes_ahead: float,
    target_class: str = 'default'
) -> tuple[float, float, float]:
    """Dead reckoning projection of moving contact based on speed and heading.

    Args:
        lat: Current latitude in decimal degrees.
        lon: Current longitude in decimal degrees.
        speed_knots: Target speed in knots (1 knot = 1.852 km/h).
        heading_deg: Direction of travel in degrees clockwise from true north.
        minutes_ahead: Forward projection time window in minutes.
        target_class: Target category ('Vessel', 'Aircraft', 'Vehicle', or 'default').

    Returns:
        Tuple of (predicted_lat, predicted_lon, cep_meters).
    """
    # 1 knot = 1.852 km/h
    distance_km = (speed_knots * 1.852) * (minutes_ahead / 60.0)

    r = 6371.0  # Earth radius in km
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(heading_deg)

    dist_ratio = distance_km / r

    pred_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(dist_ratio) +
        math.cos(lat_rad) * math.sin(dist_ratio) * math.cos(bearing_rad)
    )

    pred_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(dist_ratio) * math.cos(lat_rad),
        math.cos(dist_ratio) - math.sin(lat_rad) * math.sin(pred_lat_rad)
    )

    pred_lat = math.degrees(pred_lat_rad)
    pred_lon = math.degrees(pred_lon_rad)

    # Class-aware Circular Error Probable (CEP) growth
    base_cep = BASE_CEP.get(target_class, BASE_CEP['default'])
    growth = GROWTH_RATE.get(target_class, GROWTH_RATE['default'])
    cep_meters = base_cep + (minutes_ahead * growth)

    return round(pred_lat, 5), round(pred_lon, 5), round(cep_meters, 1)


def compute_track_vector(
    contact_id: str,
    lat: float,
    lon: float,
    speed_knots: float,
    heading_deg: float,
    intervals: Optional[List[int]] = None,
    target_class: str = 'default'
) -> Dict[str, Any]:
    """Generate multi-interval kinematic trajectory projections with confidence ellipses.

    Args:
        contact_id: Unique contact or track identifier.
        lat: Current latitude.
        lon: Current longitude.
        speed_knots: Velocity in knots.
        heading_deg: Heading angle in degrees.
        intervals: List of forward projection intervals in minutes. Defaults to [15, 30, 60].
        target_class: Target category ('Vessel', 'Aircraft', 'Vehicle', etc.).

    Returns:
        Dictionary containing current position, total projected distance, and waypoints.
    """
    intervals = intervals or [15, 30, 60]
    waypoints = []
    max_interval = max(intervals) if intervals else 0.0
    total_distance_km = round((speed_knots * 1.852) * (max_interval / 60.0), 3)

    for m in intervals:
        p_lat, p_lon, cep = predict_future_position(
            lat, lon, speed_knots, heading_deg, m, target_class=target_class
        )
        # Confidence ellipse approximation: 1.2x semi-major along bearing, 0.8x cross-track
        waypoints.append({
            'minutes_ahead': m,
            'predicted_lat': p_lat,
            'predicted_lon': p_lon,
            'cep_meters': cep,
            'confidence_ellipse': {
                'semi_major_m': round(cep * 1.2, 1),
                'semi_minor_m': round(cep * 0.8, 1),
                'orientation_deg': heading_deg
            }
        })

    return {
        'contact_id': contact_id,
        'target_class': target_class,
        'current_pos': {'lat': lat, 'lon': lon},
        'speed_knots': speed_knots,
        'heading_deg': heading_deg,
        'total_distance_km': total_distance_km,
        'trajectory': waypoints
    }


# ── Multi-Target Track Fusion Integration ───────────────────────────────────
from datetime import datetime, timezone
from backend.app.track_fusion import (
    MultiTargetTrackFusion,
    Measurement,
    SensorType,
    enu_to_geodetic,
    geodetic_to_enu
)

_GLOBAL_FUSION: Optional[MultiTargetTrackFusion] = None


def get_fusion_engine(
    ref_lat: float = 18.9220,
    ref_lon: float = 72.8346,
    association_method: str = "hungarian"
) -> MultiTargetTrackFusion:
    """Retrieve or initialize the singleton MultiTargetTrackFusion engine."""
    global _GLOBAL_FUSION
    if _GLOBAL_FUSION is None:
        _GLOBAL_FUSION = MultiTargetTrackFusion(
            ref_lat=ref_lat,
            ref_lon=ref_lon,
            association_method=association_method,
            m_confirm_hits=3,
            n_confirm_window=5,
            max_misses_deletion=5
        )
        seed_default_tactical_tracks(_GLOBAL_FUSION)
    return _GLOBAL_FUSION


def reset_fusion_engine(association_method: str = "hungarian") -> MultiTargetTrackFusion:
    """Reset the fusion engine state."""
    global _GLOBAL_FUSION
    _GLOBAL_FUSION = MultiTargetTrackFusion(
        ref_lat=18.9220,
        ref_lon=72.8346,
        association_method=association_method
    )
    seed_default_tactical_tracks(_GLOBAL_FUSION)
    return _GLOBAL_FUSION


def seed_default_tactical_tracks(engine: MultiTargetTrackFusion) -> None:
    """Seed initial tactical tracks from known SAR, AIS, and Army multimodal contacts."""
    t0 = datetime.now(timezone.utc).timestamp() - 60.0
    seeds = [
        {
            "id": "419001234",
            "class": "Merchant / Corvette",
            "lat": 18.9150, "lon": 72.8210,
            "speed": 14.2, "heading": 210.0,
            "sensor": SensorType.AIS
        },
        {
            "id": None,  # Dark Vessel (SAR)
            "class": "Vessel",
            "lat": 18.8820, "lon": 72.7950,
            "speed": 18.5, "heading": 175.0,
            "sensor": SensorType.SAR
        },
        {
            "id": "UAV-GARUDA-01",
            "class": "Vehicle",
            "lat": 18.9410, "lon": 72.8520,
            "speed": 22.0, "heading": 45.0,
            "sensor": SensorType.OPTICAL
        }
    ]

    for step in range(4):
        t_step = t0 + step * 15.0
        step_measurements = []
        for s in seeds:
            dist_km = (s["speed"] * 1.852) * ((step * 15.0) / 3600.0)
            hdg_rad = math.radians(s["heading"])
            d_lat = (dist_km * math.cos(hdg_rad)) / 111.32
            d_lon = (dist_km * math.sin(hdg_rad)) / (111.32 * math.cos(math.radians(s["lat"])))
            step_measurements.append(Measurement(
                timestamp=t_step,
                sensor_type=s["sensor"],
                lat=s["lat"] + d_lat,
                lon=s["lon"] + d_lon,
                identity=s["id"],
                detected_class=s["class"],
                speed_knots=s["speed"],
                heading_deg=s["heading"],
                confidence=0.92
            ))
        engine.process_cycle(t_step, step_measurements)


def get_fused_tracks() -> List[Dict[str, Any]]:
    """Return all active fused multi-target tracks with kinematic covariance ellipses."""
    engine = get_fusion_engine()
    return engine.get_active_tracks()


def fuse_multimodal_step(
    measurements_data: List[Dict[str, Any]],
    timestamp: Optional[float] = None,
    association_method: str = "hungarian"
) -> List[Dict[str, Any]]:
    """Ingest new sensor detections and step the track fusion engine forward."""
    engine = get_fusion_engine(association_method=association_method)
    if association_method and association_method.lower() != engine.association_method:
        engine.association_method = association_method.lower()

    t = timestamp or datetime.now(timezone.utc).timestamp()
    meas_objs = []
    for m in measurements_data:
        st_enum = SensorType.DEFAULT
        st_str = str(m.get("sensor_type", "DEFAULT")).upper()
        if st_str in SensorType.__members__:
            st_enum = SensorType[st_str]

        meas_objs.append(Measurement(
            timestamp=t,
            sensor_type=st_enum,
            lat=float(m["lat"]),
            lon=float(m["lon"]),
            alt=float(m.get("alt", 0.0)),
            identity=m.get("identity"),
            detected_class=m.get("detected_class", "Vessel"),
            confidence=float(m.get("confidence", 1.0)),
            speed_knots=float(m["speed_knots"]) if m.get("speed_knots") is not None else None,
            heading_deg=float(m["heading_deg"]) if m.get("heading_deg") is not None else None,
            raw_id=m.get("raw_id")
        ))

    return engine.process_cycle(t, meas_objs)

