"""Real Multi-Target Track Fusion Engine for Project Rakshak 2.0.

Provides defense-grade multi-sensor kinematic state estimation:
1. WGS84 Geodetic to Local Tangent Plane (ENU) metric coordinate conversion.
2. Constant-Velocity (CV) Kalman filtering with class-tuned process noise (Vessel vs Ground Vehicle).
3. Multimodal sensor fusion (AIS, SAR, Optical) with per-sensor measurement covariances.
4. Gated data association: Mahalanobis gating + Hungarian assignment + Joint Probabilistic Data Association (JPDA).
5. Comprehensive track lifecycle management (TENTATIVE -> CONFIRMED -> COASTING -> DELETED).
6. Continuous covariance ellipse derivation (semi-major, semi-minor, orientation angle).
"""
from __future__ import annotations
import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


# ── 1. Geodesy: WGS84 Geodetic <-> Local Tangent Plane (ENU) ────────────────
WGS84_A = 6378137.0          # Equatorial semi-major axis (meters)
WGS84_F = 1.0 / 298.257223563 # Flattening factor
WGS84_E2 = 2.0 * WGS84_F - WGS84_F ** 2  # First eccentricity squared


def geodetic_to_enu(
    lat: float,
    lon: float,
    alt: float,
    ref_lat: float,
    ref_lon: float,
    ref_alt: float = 0.0
) -> Tuple[float, float, float]:
    """Convert WGS84 geodetic coordinates to local East-North-Up (ENU) Cartesian frame in meters.
    
    Uses standard local tangent plane projection centered at (ref_lat, ref_lon, ref_alt).
    """
    phi = math.radians(lat)
    lam = math.radians(lon)
    phi0 = math.radians(ref_lat)
    lam0 = math.radians(ref_lon)

    # Prime vertical radius of curvature
    sin_phi0 = math.sin(phi0)
    cos_phi0 = math.cos(phi0)
    n0 = WGS84_A / math.sqrt(1.0 - WGS84_E2 * (sin_phi0 ** 2))

    # Meridian radius of curvature
    m0 = (WGS84_A * (1.0 - WGS84_E2)) / ((1.0 - WGS84_E2 * (sin_phi0 ** 2)) ** 1.5)

    d_phi = phi - phi0
    d_lam = lam - lam0

    # Local tangent plane metric coordinates
    east = (n0 + alt) * cos_phi0 * d_lam
    north = (m0 + alt) * d_phi
    up = alt - ref_alt

    return float(east), float(north), float(up)


def enu_to_geodetic(
    east: float,
    north: float,
    up: float,
    ref_lat: float,
    ref_lon: float,
    ref_alt: float = 0.0
) -> Tuple[float, float, float]:
    """Convert local East-North-Up (ENU) coordinates in meters back to WGS84 geodetic coordinates."""
    phi0 = math.radians(ref_lat)
    sin_phi0 = math.sin(phi0)
    cos_phi0 = math.cos(phi0)

    n0 = WGS84_A / math.sqrt(1.0 - WGS84_E2 * (sin_phi0 ** 2))
    m0 = (WGS84_A * (1.0 - WGS84_E2)) / ((1.0 - WGS84_E2 * (sin_phi0 ** 2)) ** 1.5)

    d_phi = north / (m0 + up)
    d_lam = east / ((n0 + up) * cos_phi0) if abs(cos_phi0) > 1e-9 else 0.0

    lat = ref_lat + math.degrees(d_phi)
    lon = ref_lon + math.degrees(d_lam)
    alt = ref_alt + up

    return float(lat), float(lon), float(alt)


# ── 2. Sensor Types & Measurement Representation ────────────────────────────
class SensorType(str, Enum):
    AIS = "AIS"
    SAR = "SAR"
    OPTICAL = "OPTICAL"
    RADAR = "RADAR"
    DEFAULT = "DEFAULT"


# Sensor Measurement Noise Covariance Matrix R (meters^2)
# AIS: High precision GNSS transponder (10-15m std)
# Optical: Medium precision pixel resolution (20-30m std)
# SAR: Lower precision radar Doppler / azimuth resolution (50-80m std)
SENSOR_COVARIANCES: Dict[SensorType, np.ndarray] = {
    SensorType.AIS: np.diag([12.0 ** 2, 12.0 ** 2]),       # sigma = 12m
    SensorType.OPTICAL: np.diag([25.0 ** 2, 25.0 ** 2]),   # sigma = 25m
    SensorType.SAR: np.diag([65.0 ** 2, 65.0 ** 2]),       # sigma = 65m
    SensorType.RADAR: np.diag([40.0 ** 2, 40.0 ** 2]),     # sigma = 40m
    SensorType.DEFAULT: np.diag([30.0 ** 2, 30.0 ** 2])
}


@dataclass
class Measurement:
    """A single sensor observation at timestamp t."""
    timestamp: float
    sensor_type: SensorType
    lat: float
    lon: float
    alt: float = 0.0
    east: float = 0.0
    north: float = 0.0
    identity: Optional[str] = None          # MMSI or Call-sign
    detected_class: Optional[str] = None    # Vessel, Vehicle, Aircraft
    confidence: float = 1.0
    speed_knots: Optional[float] = None
    heading_deg: Optional[float] = None
    raw_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_vector(self) -> np.ndarray:
        return np.array([self.east, self.north], dtype=float)

    def get_r(self) -> np.ndarray:
        return SENSOR_COVARIANCES.get(self.sensor_type, SENSOR_COVARIANCES[SensorType.DEFAULT]).copy()


# ── 3. Target Class Dynamic Process Noise Tuning ────────────────────────────
# Continuous white noise acceleration spectral density q (m^2 / s^3)
# Vessels: High mass / ocean drag, limited lateral acceleration (q ~ 0.05 - 0.20)
# Vehicles: Agile, braking, tactical defile maneuvering (q ~ 1.5 - 4.0)
# Aircraft: High speed airspace turns (q ~ 4.0 - 10.0)
PROCESS_NOISE_Q: Dict[str, float] = {
    "Vessel": 0.08,        # Smooth ocean tracks
    "Merchant / Corvette": 0.08,
    "Frigate / Bulk Carrier": 0.06,
    "Capital Ship / VLCC Tanker": 0.04,
    "Small Craft / Dhow": 0.15,
    "Patrol Vessel / Trawler": 0.12,
    "Vehicle": 1.80,       # High agility ground vehicle
    "TACTICAL_CONVOY": 1.20,
    "Aircraft": 6.00,      # Aerial vehicle
    "default": 0.25
}


def get_process_noise_q(target_class: str) -> float:
    return PROCESS_NOISE_Q.get(target_class, PROCESS_NOISE_Q["default"])


# ── 4. Track Lifecycle State ────────────────────────────────────────────────
class TrackState(str, Enum):
    TENTATIVE = "TENTATIVE"    # Track initiated, awaiting M-of-N confirmation
    CONFIRMED = "CONFIRMED"    # Fully confirmed multi-sensor track
    COASTING = "COASTING"      # Missed detection in current cycle, predicted via KF
    DELETED = "DELETED"        # Expired or pruned track


@dataclass
class TrackHistoryPoint:
    timestamp: float
    lat: float
    lon: float
    east: float
    north: float
    vx: float
    vy: float
    speed_knots: float
    heading_deg: float
    cep_m: float
    sensor_type: str


# ── 5. Constant-Velocity (CV) Kalman Filter Track ───────────────────────────
class Track:
    """Multi-target Constant-Velocity Kalman Filter in local metric ENU frame."""

    def __init__(
        self,
        track_id: str,
        initial_meas: Measurement,
        ref_origin: Tuple[float, float, float],
        target_class: str = "Vessel"
    ):
        self.track_id = track_id
        self.ref_origin = ref_origin
        self.target_class = target_class
        self.state_lifecycle = TrackState.TENTATIVE

        # Initial metric position
        e, n, _ = geodetic_to_enu(
            initial_meas.lat, initial_meas.lon, initial_meas.alt,
            ref_origin[0], ref_origin[1], ref_origin[2]
        )
        initial_meas.east = e
        initial_meas.north = n

        # Initial velocity from measurement if provided, else 0
        vx = 0.0
        vy = 0.0
        v_var = 100.0  # Default velocity variance 100 m^2/s^2 (std = 10 m/s ~ 19.4 knots) for unkinematic sensors
        if initial_meas.speed_knots is not None and initial_meas.heading_deg is not None:
            spd_mps = initial_meas.speed_knots * 0.514444
            hdg_rad = math.radians(initial_meas.heading_deg)
            vx = spd_mps * math.sin(hdg_rad)
            vy = spd_mps * math.cos(hdg_rad)
            v_var = 9.0  # Directly measured SOG/COG: std = 3 m/s

        # State vector x = [east, north, vx, vy]^T
        self.x = np.array([e, n, vx, vy], dtype=float)

        # Initial covariance P
        r_init = initial_meas.get_r()
        self.P = np.array([
            [r_init[0, 0], 0.0, 0.0, 0.0],
            [0.0, r_init[1, 1], 0.0, 0.0],
            [0.0, 0.0, v_var, 0.0],
            [0.0, 0.0, 0.0, v_var]
        ], dtype=float)

        # Identity & Metadata
        self.identity = initial_meas.identity
        self.sensor_contributions: Dict[str, int] = {
            initial_meas.sensor_type.value: 1
        }
        self.total_updates = 1
        self.consecutive_misses = 0
        self.hit_history: List[int] = [1]  # 1 for hit, 0 for miss (last N steps)
        self.created_at = initial_meas.timestamp
        self.last_updated_at = initial_meas.timestamp

        # Trajectory history trail
        self.history: List[TrackHistoryPoint] = []
        self._record_history(initial_meas.timestamp, initial_meas.sensor_type.value)

    @property
    def east(self) -> float:
        return float(self.x[0])

    @property
    def north(self) -> float:
        return float(self.x[1])

    @property
    def vx(self) -> float:
        return float(self.x[2])

    @property
    def vy(self) -> float:
        return float(self.x[3])

    @property
    def speed_mps(self) -> float:
        return float(math.sqrt(self.vx ** 2 + self.vy ** 2))

    @property
    def speed_knots(self) -> float:
        return float(self.speed_mps / 0.514444)

    @property
    def heading_deg(self) -> float:
        if self.speed_mps < 0.2:
            return 0.0
        deg = math.degrees(math.atan2(self.vx, self.vy))
        return float((deg + 360.0) % 360.0)

    @property
    def lat_lon(self) -> Tuple[float, float]:
        lat, lon, _ = enu_to_geodetic(
            self.east, self.north, 0.0,
            self.ref_origin[0], self.ref_origin[1], self.ref_origin[2]
        )
        return lat, lon

    def compute_ellipse(self) -> Dict[str, float]:
        """Derive 1-sigma positional uncertainty ellipse from covariance block P[0:2, 0:2]."""
        p_pos = self.P[0:2, 0:2]
        # Eigenvalue decomposition of 2D position covariance
        vals, vecs = np.linalg.eigh(p_pos)
        vals = np.maximum(vals, 1e-4)
        order = vals.argsort()[::-1]
        vals = vals[order]
        vecs = vecs[:, order]

        semi_major = math.sqrt(vals[0])
        semi_minor = math.sqrt(vals[1])
        # Angle from North (Y axis) clockwise to major axis
        angle_rad = math.atan2(vecs[0, 0], vecs[1, 0])
        orientation_deg = (math.degrees(angle_rad) + 360.0) % 360.0

        # Circular Error Probable (CEP50 approximation: 0.59 * (semi_major + semi_minor))
        cep_50 = 0.5887 * semi_major + 0.5887 * semi_minor

        return {
            "semi_major_m": round(float(semi_major), 2),
            "semi_minor_m": round(float(semi_minor), 2),
            "orientation_deg": round(float(orientation_deg), 1),
            "cep_m": round(float(cep_50), 2)
        }

    def _record_history(self, timestamp: float, sensor_name: str) -> None:
        lat, lon = self.lat_lon
        ellipse = self.compute_ellipse()
        self.history.append(TrackHistoryPoint(
            timestamp=timestamp,
            lat=round(lat, 6),
            lon=round(lon, 6),
            east=round(self.east, 2),
            north=round(self.north, 2),
            vx=round(self.vx, 2),
            vy=round(self.vy, 2),
            speed_knots=round(self.speed_knots, 1),
            heading_deg=round(self.heading_deg, 1),
            cep_m=ellipse["cep_m"],
            sensor_type=sensor_name
        ))
        if len(self.history) > 100:
            self.history.pop(0)

    # ── Kalman Predict Step ─────────────────────────────────────────────────
    def predict(self, dt: float) -> None:
        """Constant-Velocity Kalman Filter Prediction for time interval dt (seconds)."""
        if dt <= 0.0:
            return

        # State transition F(dt)
        f_mat = np.array([
            [1.0, 0.0, dt, 0.0],
            [0.0, 1.0, 0.0, dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

        # Process noise covariance Q(dt) derived from white noise acceleration spectral density q
        q = get_process_noise_q(self.target_class)
        dt2 = dt * dt
        dt3 = dt2 * dt
        q_mat = q * np.array([
            [dt3 / 3.0, 0.0, dt2 / 2.0, 0.0],
            [0.0, dt3 / 3.0, 0.0, dt2 / 2.0],
            [dt2 / 2.0, 0.0, dt, 0.0],
            [0.0, dt2 / 2.0, 0.0, dt]
        ], dtype=float)

        # Predict state & covariance
        self.x = f_mat @ self.x
        self.P = f_mat @ self.P @ f_mat.T + q_mat

    # ── Kalman Update Step (Single Measurement) ─────────────────────────────
    def update(self, meas: Measurement) -> Tuple[np.ndarray, np.ndarray]:
        """Standard Kalman Filter update step with measurement z."""
        h_mat = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=float)
        r_mat = meas.get_r()

        z = meas.to_vector()
        y = z - h_mat @ self.x  # Innovation
        s_mat = h_mat @ self.P @ h_mat.T + r_mat  # Innovation covariance

        k_gain = self.P @ h_mat.T @ np.linalg.inv(s_mat)  # Kalman Gain

        # State update
        self.x = self.x + k_gain @ y

        # Joseph stabilized covariance update
        i_kh = np.eye(4) - k_gain @ h_mat
        self.P = i_kh @ self.P @ i_kh.T + k_gain @ r_mat @ k_gain.T

        # Update metadata
        st_name = meas.sensor_type.value
        self.sensor_contributions[st_name] = self.sensor_contributions.get(st_name, 0) + 1
        if meas.identity and not self.identity:
            self.identity = meas.identity
        if meas.detected_class and self.target_class in {"default", "Vessel"}:
            self.target_class = meas.detected_class

        self.consecutive_misses = 0
        self.hit_history.append(1)
        if len(self.hit_history) > 10:
            self.hit_history.pop(0)

        self.total_updates += 1
        self.last_updated_at = meas.timestamp
        self._record_history(meas.timestamp, st_name)

        return y, s_mat

    def mark_miss(self, timestamp: float) -> None:
        """Mark detection miss for track in this update cycle."""
        self.consecutive_misses += 1
        self.hit_history.append(0)
        if len(self.hit_history) > 10:
            self.hit_history.pop(0)
        if self.state_lifecycle == TrackState.CONFIRMED:
            self.state_lifecycle = TrackState.COASTING
            self._record_history(timestamp, "COASTING")


# ── 6. Gating & Assignment Algorithms ───────────────────────────────────────
def compute_mahalanobis_dist(track: Track, meas: Measurement) -> Tuple[float, np.ndarray, np.ndarray]:
    """Calculate 2D Mahalanobis distance squared d_M^2 between track prediction and measurement."""
    h_mat = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ], dtype=float)
    z = meas.to_vector()
    y = z - h_mat @ track.x
    s_mat = h_mat @ track.P @ h_mat.T + meas.get_r()
    s_inv = np.linalg.inv(s_mat)
    d_m2 = float(y.T @ s_inv @ y)
    return d_m2, y, s_mat


def solve_hungarian(cost_matrix: np.ndarray) -> List[Tuple[int, int]]:
    """Pure-Python / NumPy Kuhn-Munkres (Hungarian) assignment algorithm.
    
    Finds minimum weight matching in a bipartite graph with zero third-party dependencies.
    """
    c = np.array(cost_matrix, dtype=float)
    num_rows, num_cols = c.shape
    if num_rows == 0 or num_cols == 0:
        return []

    # Pad matrix to square if rectangular
    dim = max(num_rows, num_cols)
    large_val = 1e8
    pad_c = np.full((dim, dim), large_val, dtype=float)
    pad_c[:num_rows, :num_cols] = c

    # Step 1: Subtract row minima
    for i in range(dim):
        row_min = np.min(pad_c[i, :])
        if row_min < large_val:
            pad_c[i, :] -= row_min

    # Step 2: Subtract column minima
    for j in range(dim):
        col_min = np.min(pad_c[:, j])
        if col_min < large_val:
            pad_c[:, j] -= col_min

    # Dual variable tracking for augmenting paths
    u = np.zeros(dim + 1)
    v = np.zeros(dim + 1)
    p = np.zeros(dim + 1, dtype=int)
    way = np.zeros(dim + 1, dtype=int)

    for i in range(1, dim + 1):
        p[0] = i
        j0 = 0
        minv = np.full(dim + 1, np.inf)
        used = np.zeros(dim + 1, dtype=bool)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = np.inf
            j1 = 0

            for j in range(1, dim + 1):
                if not used[j]:
                    cur = pad_c[i0 - 1, j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(dim + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    assignments: List[Tuple[int, int]] = []
    for j in range(1, dim + 1):
        if p[j] > 0 and p[j] <= num_rows and j <= num_cols:
            r = p[j] - 1
            col = j - 1
            if c[r, col] < 1e7:
                assignments.append((r, col))

    return assignments


# ── 7. Joint Probabilistic Data Association (JPDA) ──────────────────────────
def compute_joint_jpda_betas(
    tracks: List[Track],
    measurements: List[Measurement],
    gating_matrix: np.ndarray,
    p_d: float = 0.90,
    clutter_density: float = 1e-5
) -> np.ndarray:
    """Compute exact marginal association probabilities beta[t_idx, m_idx + 1] via joint event enumeration.
    
    Enforces the strict mutual exclusion constraint (each measurement originates from at most one target),
    preventing track coalescence and identity swapping during close crossings.
    Uses cluster decomposition on the bipartite gating graph to partition independent tracks and measurements.
    """
    num_tracks = len(tracks)
    num_meas = len(measurements)
    if num_tracks == 0:
        return np.empty((0, num_meas + 1))
    if num_meas == 0:
        betas = np.zeros((num_tracks, 1), dtype=float)
        betas[:, 0] = 1.0
        return betas

    # Precompute innovations, S matrices, and measurement likelihoods
    likelihood_matrix = np.zeros((num_tracks, num_meas), dtype=float)
    for i, trk in enumerate(tracks):
        for j, meas in enumerate(measurements):
            if trk.identity and meas.identity and trk.identity != meas.identity:
                gating_matrix[i, j] = False
                continue
            if gating_matrix[i, j]:
                d_m2, _, s_mat = compute_mahalanobis_dist(trk, meas)
                # Identity matching bonus (verified MMSI)
                if trk.identity and meas.identity and trk.identity == meas.identity:
                    d_m2 = min(d_m2, 1.0)
                det_s = float(np.linalg.det(s_mat))
                norm_const = 1.0 / (2.0 * math.pi * math.sqrt(max(det_s, 1e-4)))
                l_j = norm_const * math.exp(-0.5 * min(d_m2, 50.0))
                if trk.identity and meas.identity and trk.identity == meas.identity:
                    l_j *= 50.0
                likelihood_matrix[i, j] = l_j

    p_miss = (1.0 - p_d) * max(clutter_density, 1e-9)
    betas = np.zeros((num_tracks, num_meas + 1), dtype=float)

    # Cluster decomposition via connected components on bipartite gating graph
    adj_tracks = {i: [j for j in range(num_meas) if gating_matrix[i, j]] for i in range(num_tracks)}
    adj_meas = {j: [i for i in range(num_tracks) if gating_matrix[i, j]] for j in range(num_meas)}

    visited_tracks = set()
    clusters = []

    for i in range(num_tracks):
        if i in visited_tracks:
            continue
        if not adj_tracks[i]:
            betas[i, 0] = 1.0
            visited_tracks.add(i)
            continue

        # BFS to discover connected cluster of tracks and measurements
        curr_tracks = {i}
        curr_meas = set(adj_tracks[i])
        queue = list(curr_meas)
        visited_tracks.add(i)

        while queue:
            m_idx = queue.pop()
            for t_idx in adj_meas[m_idx]:
                if t_idx not in curr_tracks:
                    curr_tracks.add(t_idx)
                    visited_tracks.add(t_idx)
                    for next_m in adj_tracks[t_idx]:
                        if next_m not in curr_meas:
                            curr_meas.add(next_m)
                            queue.append(next_m)

        clusters.append((sorted(curr_tracks), sorted(curr_meas)))

    for c_tracks, c_meas in clusters:
        # Fast path: single track with single measurement
        if len(c_tracks) == 1 and len(c_meas) == 1:
            t_idx = c_tracks[0]
            m_idx = c_meas[0]
            l_miss = p_miss
            l_assoc = p_d * likelihood_matrix[t_idx, m_idx]
            tot = l_miss + l_assoc
            if tot > 0:
                betas[t_idx, 0] = l_miss / tot
                betas[t_idx, m_idx + 1] = l_assoc / tot
            else:
                betas[t_idx, 0] = 1.0
            continue

        # Event cap: maximum 1000 feasible joint events. If cluster has > 8 tracks, use PDA fallback
        if len(c_tracks) > 8:
            # Fallback: Decoupled Probabilistic Data Association (PDA) for oversized clusters
            for t_id in c_tracks:
                likes = [p_miss]
                for m_id in c_meas:
                    if gating_matrix[t_id, m_id]:
                        likes.append(p_d * likelihood_matrix[t_id, m_id])
                    else:
                        likes.append(0.0)
                tot = sum(likes)
                if tot > 0:
                    betas[t_id, 0] = likes[0] / tot
                    for idx_m, m_id in enumerate(c_meas):
                        betas[t_id, m_id + 1] = likes[idx_m + 1] / tot
                else:
                    betas[t_id, 0] = 1.0
            continue

        events: List[Tuple[Tuple[int, ...], float]] = []
        max_events = 1000
        event_cap_exceeded = False

        def generate_cluster_events(idx: int, current_assign: Tuple[int, ...], used_meas: set, current_like: float):
            nonlocal event_cap_exceeded
            if len(events) >= max_events:
                event_cap_exceeded = True
                return
            if idx == len(c_tracks):
                events.append((current_assign, current_like))
                return

            t_id = c_tracks[idx]
            # Option 1: Track t_id misses
            generate_cluster_events(idx + 1, current_assign + (0,), used_meas, current_like * p_miss)
            if event_cap_exceeded:
                return

            # Option 2: Track t_id associates with candidate measurement in c_meas
            for m_id in c_meas:
                if m_id not in used_meas and gating_matrix[t_id, m_id]:
                    l_tm = p_d * likelihood_matrix[t_id, m_id]
                    if l_tm > 0:
                        generate_cluster_events(idx + 1, current_assign + (m_id + 1,), used_meas | {m_id}, current_like * l_tm)
                        if event_cap_exceeded:
                            return

        generate_cluster_events(0, (), set(), 1.0)

        if event_cap_exceeded:
            # Fallback to decoupled PDA if event cap was reached
            for t_id in c_tracks:
                likes = [p_miss]
                for m_id in c_meas:
                    if gating_matrix[t_id, m_id]:
                        likes.append(p_d * likelihood_matrix[t_id, m_id])
                    else:
                        likes.append(0.0)
                tot = sum(likes)
                if tot > 0:
                    betas[t_id, 0] = likes[0] / tot
                    for idx_m, m_id in enumerate(c_meas):
                        betas[t_id, m_id + 1] = likes[idx_m + 1] / tot
                else:
                    betas[t_id, 0] = 1.0
            continue

        total_like = sum(like for _, like in events)

        if total_like <= 1e-30:
            for t_id in c_tracks:
                betas[t_id, 0] = 1.0
        else:
            for assign, like in events:
                prob = like / total_like
                for idx, a in enumerate(assign):
                    t_id = c_tracks[idx]
                    betas[t_id, a] += prob

    return betas


def apply_jpda_track_update(
    track: Track,
    measurements: List[Measurement],
    meas_betas: np.ndarray,
    beta_0: float
) -> None:
    """Apply JPDA combined innovation and spread-of-innovations covariance inflation to a single track."""
    h_mat = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0]
    ], dtype=float)

    innovations = []
    s_mats = []
    active_betas = []
    active_measurements = []

    for j, m in enumerate(measurements):
        b_j = float(meas_betas[j])
        if b_j > 1e-4:
            d_m2, y, s_mat = compute_mahalanobis_dist(track, m)
            innovations.append(y)
            s_mats.append(s_mat)
            active_betas.append(b_j)
            active_measurements.append(m)

    if not innovations:
        return

    # Weighted combined innovation y_tilde = sum_j (beta_j * y_j)
    y_tilde = np.zeros(2, dtype=float)
    for b, y in zip(active_betas, innovations):
        y_tilde += b * y

    # Average innovation covariance
    s_avg = np.zeros((2, 2), dtype=float)
    for b, s in zip(active_betas, s_mats):
        s_avg += b * s
    if np.all(s_avg == 0):
        s_avg = s_mats[0]

    k_gain = track.P @ h_mat.T @ np.linalg.inv(s_avg)

    # State update
    track.x = track.x + k_gain @ y_tilde

    # Spread of innovations covariance update:
    # P = beta_0 * P + (1 - beta_0) * P_c + K * (sum(beta_j * y_j * y_j^T) - y_tilde * y_tilde^T) * K^T
    p_c = (np.eye(4) - k_gain @ h_mat) @ track.P
    spread_matrix = np.zeros((2, 2), dtype=float)
    for b, y in zip(active_betas, innovations):
        spread_matrix += b * np.outer(y, y)
    spread_matrix -= np.outer(y_tilde, y_tilde)

    track.P = (
        beta_0 * track.P +
        (1.0 - beta_0) * p_c +
        k_gain @ spread_matrix @ k_gain.T
    )

    # Identify primary sensor contributor
    best_idx = int(np.argmax(active_betas))
    best_meas = active_measurements[best_idx]
    st_name = best_meas.sensor_type.value
    track.sensor_contributions[st_name] = track.sensor_contributions.get(st_name, 0) + 1
    if best_meas.identity and not track.identity:
        track.identity = best_meas.identity

    track.consecutive_misses = 0
    track.hit_history.append(1)
    if len(track.hit_history) > 10:
        track.hit_history.pop(0)

    track.total_updates += 1
    track.last_updated_at = best_meas.timestamp
    track._record_history(best_meas.timestamp, f"JPDA:{st_name}")


def apply_jpda_update(
    track: Track,
    candidate_measurements: List[Measurement],
    p_d: float = 0.90,
    clutter_density: float = 1e-6
) -> None:
    """Convenience wrapper for single-track JPDA / PDA update."""
    if not candidate_measurements:
        return
    gating = np.ones((1, len(candidate_measurements)), dtype=bool)
    betas = compute_joint_jpda_betas([track], candidate_measurements, gating, p_d=p_d, clutter_density=clutter_density)
    beta_0 = float(betas[0, 0])
    meas_betas = betas[0, 1:]
    apply_jpda_track_update(track, candidate_measurements, meas_betas, beta_0)


# ── 8. MultiTargetTrackFusion System ─────────────────────────────────────────
class MultiTargetTrackFusion:
    """Autonomous Multi-Target Tracking & Sensor Fusion Manager.
    
    Coordinates ENU conversion, Kalman prediction, gating, data association,
    and M-of-N track lifecycle management.
    """

    def __init__(
        self,
        ref_lat: float = 18.9220,
        ref_lon: float = 72.8346,
        ref_alt: float = 0.0,
        association_method: str = "hungarian",
        mahalanobis_gate_threshold: float = 9.21,   # chi^2_2(0.99) ~ 9.21
        m_confirm_hits: int = 3,
        n_confirm_window: int = 5,
        max_misses_deletion: int = 5,
        target_class: str = "Vessel"
    ):
        self.ref_origin = (ref_lat, ref_lon, ref_alt)
        self.association_method = association_method.lower()  # "hungarian", "jpda", "nn"
        self.mahalanobis_gate = mahalanobis_gate_threshold
        self.m_confirm = m_confirm_hits
        self.n_window = n_confirm_window
        self.max_misses = max_misses_deletion
        self.default_target_class = target_class

        self.tracks: Dict[str, Track] = {}
        self.track_counter = 1
        self.last_timestamp: Optional[float] = None

    def _next_track_id(self) -> str:
        tid = f"TRK-{self.track_counter:03d}"
        self.track_counter += 1
        return tid

    def process_cycle(
        self,
        timestamp: float,
        measurements: List[Measurement]
    ) -> List[Dict[str, Any]]:
        """Ingest a batch of multimodal measurements at timestamp and step tracking forward.
        
        Returns active confirmed and tentative tracks.
        """
        # Step 1: Calculate dt & predict existing tracks forward
        dt = 1.0
        if self.last_timestamp is not None:
            dt = max(0.01, timestamp - self.last_timestamp)
        self.last_timestamp = timestamp

        for t in list(self.tracks.values()):
            if t.state_lifecycle != TrackState.DELETED:
                t.predict(dt)

        # Step 2: Convert measurement coordinates to local ENU metric frame
        for m in measurements:
            e, n, _ = geodetic_to_enu(
                m.lat, m.lon, m.alt,
                self.ref_origin[0], self.ref_origin[1], self.ref_origin[2]
            )
            m.east = e
            m.north = n

        # Step 3: Prioritized Two-Phase Data Association
        # Phase 1: Established Tracks (CONFIRMED & COASTING) take precedence
        confirmed_ids = [
            tid for tid, t in self.tracks.items()
            if t.state_lifecycle in {TrackState.CONFIRMED, TrackState.COASTING}
        ]
        tentative_ids = [
            tid for tid, t in self.tracks.items()
            if t.state_lifecycle == TrackState.TENTATIVE
        ]

        active_identities = {
            t.identity: tid for tid, t in self.tracks.items()
            if t.identity and t.state_lifecycle != TrackState.DELETED
        }
        assigned_track_ids = set()
        matched_meas_indices = set()

        # --- Phase 1: Association of Confirmed & Coasting Tracks ---
        if confirmed_ids and measurements:
            num_conf = len(confirmed_ids)
            num_meas = len(measurements)
            cost_matrix = np.full((num_conf, num_meas), 1e8, dtype=float)
            gating_matrix = np.zeros((num_conf, num_meas), dtype=bool)

            for i, tid in enumerate(confirmed_ids):
                trk = self.tracks[tid]
                for j, meas in enumerate(measurements):
                    if trk.identity and meas.identity and trk.identity != meas.identity:
                        continue
                    if meas.identity and meas.identity in active_identities and active_identities[meas.identity] != tid:
                        continue

                    d_m2, _, _ = compute_mahalanobis_dist(trk, meas)
                    if trk.identity and meas.identity and trk.identity == meas.identity:
                        d_m2 = min(d_m2, 0.5)

                    if d_m2 <= self.mahalanobis_gate:
                        cost_matrix[i, j] = math.sqrt(d_m2)
                        gating_matrix[i, j] = True

            if self.association_method == "jpda":
                conf_tracks_list = [self.tracks[tid] for tid in confirmed_ids]
                jpda_betas = compute_joint_jpda_betas(conf_tracks_list, measurements, gating_matrix)
                for i, tid in enumerate(confirmed_ids):
                    trk = self.tracks[tid]
                    b0 = jpda_betas[i, 0]
                    m_betas = jpda_betas[i, 1:]
                    if np.sum(m_betas) >= 0.20:
                        apply_jpda_track_update(trk, measurements, m_betas, b0)
                        assigned_track_ids.add(tid)
                    else:
                        trk.mark_miss(timestamp)

                meas_col_sums = np.sum(jpda_betas[:, 1:], axis=0)
                for j in range(num_meas):
                    if meas_col_sums[j] >= 0.20 or any(jpda_betas[i, j + 1] >= 0.15 for i in range(num_conf)):
                        matched_meas_indices.add(j)

            elif self.association_method == "nn":
                for _ in range(min(num_conf, num_meas)):
                    min_val = np.min(cost_matrix)
                    if min_val >= 1e7:
                        break
                    r_idx, c_idx = np.unravel_index(np.argmin(cost_matrix), cost_matrix.shape)
                    tid = confirmed_ids[r_idx]
                    self.tracks[tid].update(measurements[c_idx])
                    assigned_track_ids.add(tid)
                    matched_meas_indices.add(c_idx)
                    cost_matrix[r_idx, :] = 1e8
                    cost_matrix[:, c_idx] = 1e8
                for tid in confirmed_ids:
                    if tid not in assigned_track_ids:
                        self.tracks[tid].mark_miss(timestamp)

            else:
                pairs = solve_hungarian(cost_matrix)
                for r_idx, c_idx in pairs:
                    tid = confirmed_ids[r_idx]
                    self.tracks[tid].update(measurements[c_idx])
                    assigned_track_ids.add(tid)
                    matched_meas_indices.add(c_idx)
                for tid in confirmed_ids:
                    if tid not in assigned_track_ids:
                        self.tracks[tid].mark_miss(timestamp)
        else:
            for tid in confirmed_ids:
                self.tracks[tid].mark_miss(timestamp)

        # --- Phase 2: Association of Tentative Tracks (Unclaimed measurements only) ---
        unclaimed_indices = [j for j in range(len(measurements)) if j not in matched_meas_indices]
        if tentative_ids and unclaimed_indices:
            num_tent = len(tentative_ids)
            num_u = len(unclaimed_indices)
            cost_tent = np.full((num_tent, num_u), 1e8, dtype=float)

            for i, tid in enumerate(tentative_ids):
                trk = self.tracks[tid]
                for k, j in enumerate(unclaimed_indices):
                    meas = measurements[j]
                    if trk.identity and meas.identity and trk.identity != meas.identity:
                        continue
                    if meas.identity and meas.identity in active_identities and active_identities[meas.identity] != tid:
                        continue
                    d_m2, _, _ = compute_mahalanobis_dist(trk, meas)
                    if d_m2 <= self.mahalanobis_gate:
                        cost_tent[i, k] = math.sqrt(d_m2)

            pairs_tent = solve_hungarian(cost_tent)
            for r_idx, c_idx in pairs_tent:
                tid = tentative_ids[r_idx]
                j = unclaimed_indices[c_idx]
                self.tracks[tid].update(measurements[j])
                assigned_track_ids.add(tid)
                matched_meas_indices.add(j)

            for tid in tentative_ids:
                if tid not in assigned_track_ids:
                    self.tracks[tid].mark_miss(timestamp)
        else:
            for tid in tentative_ids:
                self.tracks[tid].mark_miss(timestamp)

        # Step 5: Initiate New Tentative Tracks from Remaining Unassociated Measurements
        for j, meas in enumerate(measurements):
            if j in matched_meas_indices:
                continue

            # Identity deduplication: do not duplicate if an active track already holds this MMSI
            if meas.identity and any(
                t.identity == meas.identity and t.state_lifecycle != TrackState.DELETED
                for t in self.tracks.values()
            ):
                continue

            # Legitimate unassociated contact: initiate tentative track
            # (Allows close secondary targets inside active gates to establish independent tracks)
            new_tid = self._next_track_id()
            t_class = meas.detected_class or self.default_target_class
            new_track = Track(new_tid, meas, self.ref_origin, target_class=t_class)
            self.tracks[new_tid] = new_track

        # Step 6: Track Lifecycle Transitions (M-of-N Confirmation & Miss Pruning)
        for tid, trk in list(self.tracks.items()):
            if trk.state_lifecycle == TrackState.DELETED:
                continue

            # M-of-N confirmation check
            hits_in_window = sum(trk.hit_history[-self.n_window:])
            if trk.state_lifecycle == TrackState.TENTATIVE:
                if hits_in_window >= self.m_confirm:
                    trk.state_lifecycle = TrackState.CONFIRMED
                elif trk.consecutive_misses >= 2:
                    # Prune unconfirmed tentative track (e.g. false alarm clutter)
                    trk.state_lifecycle = TrackState.DELETED

            elif trk.state_lifecycle in {TrackState.CONFIRMED, TrackState.COASTING}:
                # Miss deletion rule for confirmed/coasting tracks
                if trk.consecutive_misses >= self.max_misses:
                    trk.state_lifecycle = TrackState.DELETED

        return self.get_active_tracks()

    def get_active_tracks(self) -> List[Dict[str, Any]]:
        """Return list of serialized active tracks (CONFIRMED, COASTING, TENTATIVE)."""
        res = []
        for tid, trk in self.tracks.items():
            if trk.state_lifecycle == TrackState.DELETED:
                continue

            lat, lon = trk.lat_lon
            ellipse = trk.compute_ellipse()
            res.append({
                "track_id": trk.track_id,
                "identity": trk.identity,
                "target_class": trk.target_class,
                "state": trk.state_lifecycle.value,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "speed_knots": round(trk.speed_knots, 1),
                "heading_deg": round(trk.heading_deg, 1),
                "vx_mps": round(trk.vx, 2),
                "vy_mps": round(trk.vy, 2),
                "covariance_ellipse": ellipse,
                "sensor_contributions": trk.sensor_contributions,
                "total_updates": trk.total_updates,
                "consecutive_misses": trk.consecutive_misses,
                "created_at": trk.created_at,
                "last_updated_at": trk.last_updated_at,
                "trail": [
                    {"lat": h.lat, "lon": h.lon, "timestamp": h.timestamp, "sensor": h.sensor_type}
                    for h in trk.history[-15:]
                ]
            })
        return res
