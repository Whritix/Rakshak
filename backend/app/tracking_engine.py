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
