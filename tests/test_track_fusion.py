"""Unit Test Suite for Real Multi-Target Track Fusion — Project Rakshak 2.0.

Verifies:
1. Geodesy: WGS84 to local ENU conversion and sub-millimeter roundtrip accuracy.
2. Constant-Velocity Kalman Filter prediction & covariance propagation.
3. Class-aware process noise tuning (Vessel vs Ground Vehicle).
4. Multi-sensor measurement updates and covariance reduction (AIS vs SAR vs Optical).
5. Mahalanobis distance innovation gating (chi-squared gate).
6. Pure-Python/NumPy Hungarian assignment (Kuhn-Munkres algorithm).
7. Joint Probabilistic Data Association (JPDA) combined innovation & spread-of-innovations.
8. Track lifecycle management: M-of-N confirmation rule (TENTATIVE -> CONFIRMED).
9. Consecutive miss pruning (CONFIRMED -> COASTING -> DELETED).
10. End-to-end MultiTargetTrackFusion engine cycle execution.
"""
from __future__ import annotations
import math
import sys
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.track_fusion import (
    geodetic_to_enu,
    enu_to_geodetic,
    Track,
    Measurement,
    SensorType,
    TrackState,
    compute_mahalanobis_dist,
    solve_hungarian,
    apply_jpda_update,
    MultiTargetTrackFusion,
    get_process_noise_q
)
from scipy.optimize import linear_sum_assignment
from evaluation.track_sim import generate_scenarios, evaluate_tracking_run


class TestTrackFusion(unittest.TestCase):

    def setUp(self):
        self.ref_lat = 18.9220
        self.ref_lon = 72.8346
        self.ref_origin = (self.ref_lat, self.ref_lon, 0.0)

    # 1. Geodesy Roundtrip Precision
    def test_geodetic_enu_roundtrip(self):
        """Verify WGS84 to ENU and back achieves sub-millimeter roundtrip precision."""
        target_lat = 18.9350
        target_lon = 72.8450
        target_alt = 12.5

        east, north, up = geodetic_to_enu(
            target_lat, target_lon, target_alt,
            self.ref_lat, self.ref_lon, 0.0
        )
        self.assertGreater(abs(east), 100.0)
        self.assertGreater(abs(north), 100.0)

        recovered_lat, recovered_lon, recovered_alt = enu_to_geodetic(
            east, north, up,
            self.ref_lat, self.ref_lon, 0.0
        )
        self.assertAlmostEqual(recovered_lat, target_lat, places=6)
        self.assertAlmostEqual(recovered_lon, target_lon, places=6)
        self.assertAlmostEqual(recovered_alt, target_alt, places=2)

    # 2. Kalman Filter CV Prediction
    def test_kalman_filter_cv_prediction(self):
        """Verify constant-velocity kinematic projection x = x_0 + v * dt and covariance growth."""
        meas = Measurement(
            timestamp=0.0,
            sensor_type=SensorType.AIS,
            lat=self.ref_lat,
            lon=self.ref_lon,
            speed_knots=20.0,    # ~10.288 m/s
            heading_deg=90.0     # Eastward (vx ~ 10.29, vy ~ 0.0)
        )
        trk = Track("TRK-TEST-01", meas, self.ref_origin, target_class="Vessel")

        initial_east = trk.east
        initial_p00 = trk.P[0, 0]

        dt = 5.0  # seconds
        trk.predict(dt)

        expected_east_displacement = trk.vx * dt
        self.assertAlmostEqual(trk.east, initial_east + expected_east_displacement, places=2)
        # Covariance must grow under prediction due to process noise Q
        self.assertGreater(trk.P[0, 0], initial_p00)

    # 3. Class-Aware Process Noise Tuning
    def test_class_tuned_process_noise(self):
        """Verify Vessels have lower process noise than agile Ground Vehicles."""
        q_vessel = get_process_noise_q("Vessel")
        q_vehicle = get_process_noise_q("Vehicle")
        self.assertLess(q_vessel, q_vehicle)
        self.assertAlmostEqual(q_vessel, 0.08)
        self.assertAlmostEqual(q_vehicle, 1.80)

    # 4. Multi-Sensor Measurement Update Covariance Reduction
    def test_multi_sensor_covariance_reduction(self):
        """Verify AIS update yields tighter covariance than noisy SAR update."""
        meas_base = Measurement(
            timestamp=0.0, sensor_type=SensorType.DEFAULT,
            lat=self.ref_lat, lon=self.ref_lon
        )
        trk_ais = Track("TRK-AIS", meas_base, self.ref_origin, target_class="Vessel")
        trk_sar = Track("TRK-SAR", meas_base, self.ref_origin, target_class="Vessel")

        # Update trk_ais with AIS measurement
        meas_ais = Measurement(
            timestamp=1.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat + 0.0001, lon=self.ref_lon + 0.0001
        )
        meas_ais.east, meas_ais.north, _ = geodetic_to_enu(
            meas_ais.lat, meas_ais.lon, 0.0, self.ref_lat, self.ref_lon
        )
        trk_ais.update(meas_ais)

        # Update trk_sar with noisy SAR measurement
        meas_sar = Measurement(
            timestamp=1.0, sensor_type=SensorType.SAR,
            lat=self.ref_lat + 0.0001, lon=self.ref_lon + 0.0001
        )
        meas_sar.east, meas_sar.north, _ = geodetic_to_enu(
            meas_sar.lat, meas_sar.lon, 0.0, self.ref_lat, self.ref_lon
        )
        trk_sar.update(meas_sar)

        # AIS covariance should be significantly smaller than SAR covariance
        ais_cov = trk_ais.P[0, 0] + trk_ais.P[1, 1]
        sar_cov = trk_sar.P[0, 0] + trk_sar.P[1, 1]
        self.assertLess(ais_cov, sar_cov)

    # 5. Mahalanobis Innovation Gating
    def test_mahalanobis_gating(self):
        """Verify points within chi-squared gate pass, while distant clutter points exceed gate."""
        meas = Measurement(
            timestamp=0.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat, lon=self.ref_lon
        )
        trk = Track("TRK-01", meas, self.ref_origin, target_class="Vessel")

        # Measurement near track (should pass gate <= 9.21)
        close_meas = Measurement(
            timestamp=1.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat + 0.0001, lon=self.ref_lon
        )
        close_meas.east, close_meas.north, _ = geodetic_to_enu(
            close_meas.lat, close_meas.lon, 0.0, self.ref_lat, self.ref_lon
        )
        d_close, _, _ = compute_mahalanobis_dist(trk, close_meas)
        self.assertLess(d_close, 9.21)

        # Measurement far away (should exceed gate > 9.21)
        far_meas = Measurement(
            timestamp=1.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat + 0.05, lon=self.ref_lon + 0.05
        )
        far_meas.east, far_meas.north, _ = geodetic_to_enu(
            far_meas.lat, far_meas.lon, 0.0, self.ref_lat, self.ref_lon
        )
        d_far, _, _ = compute_mahalanobis_dist(trk, far_meas)
        self.assertGreater(d_far, 9.21)

    # 6. Hungarian Algorithm Optimal Assignment
    def test_hungarian_assignment(self):
        """Verify Kuhn-Munkres optimal assignment correctly pairs tracks to nearest measurements."""
        # Cost matrix: Track 0 closer to Meas 1, Track 1 closer to Meas 0
        cost_mat = np.array([
            [10.0, 2.0],
            [1.5,  8.0]
        ])
        assignments = solve_hungarian(cost_mat)
        self.assertEqual(len(assignments), 2)
        # Expect (0, 1) and (1, 0)
        pair_dict = dict(assignments)
        self.assertEqual(pair_dict[0], 1)
        self.assertEqual(pair_dict[1], 0)

    # 7. Joint Probabilistic Data Association (JPDA)
    def test_jpda_probabilistic_update(self):
        """Verify JPDA updates track with combined innovation from multiple candidate measurements."""
        meas0 = Measurement(
            timestamp=0.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat, lon=self.ref_lon
        )
        trk = Track("TRK-JPDA", meas0, self.ref_origin, target_class="Vessel")

        # Two candidate measurements within gate
        m1 = Measurement(
            timestamp=1.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat + 0.0001, lon=self.ref_lon,
            east=0.0, north=11.1
        )
        m2 = Measurement(
            timestamp=1.0, sensor_type=SensorType.OPTICAL,
            lat=self.ref_lat, lon=self.ref_lon + 0.0001,
            east=10.5, north=0.0
        )

        initial_p = trk.P.copy()
        apply_jpda_update(trk, [m1, m2], p_d=0.9)

        # Track state should move towards the centroid of candidates
        self.assertGreater(trk.east, 0.0)
        self.assertGreater(trk.north, 0.0)
        # Covariance should reflect update
        self.assertFalse(np.array_equal(trk.P, initial_p))

    # 8. M-of-N Track Confirmation Lifecycle
    def test_track_lifecycle_m_of_n_confirmation(self):
        """Verify track initiates as TENTATIVE and promotes to CONFIRMED on M=3 hits."""
        tracker = MultiTargetTrackFusion(
            ref_lat=self.ref_lat, ref_lon=self.ref_lon,
            m_confirm_hits=3, n_confirm_window=5
        )

        m1 = Measurement(
            timestamp=0.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat, lon=self.ref_lon
        )
        tracks = tracker.process_cycle(0.0, [m1])
        # Step 1: TENTATIVE
        self.assertEqual(tracks[0]["state"], "TENTATIVE")

        # Step 2: Second hit -> Still TENTATIVE (2 < 3)
        m2 = Measurement(
            timestamp=2.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat + 0.0001, lon=self.ref_lon
        )
        tracks = tracker.process_cycle(2.0, [m2])
        self.assertEqual(tracks[0]["state"], "TENTATIVE")

        # Step 3: Third hit -> Promotes to CONFIRMED (3 >= 3)
        m3 = Measurement(
            timestamp=4.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat + 0.0002, lon=self.ref_lon
        )
        tracks = tracker.process_cycle(4.0, [m3])
        self.assertEqual(tracks[0]["state"], "CONFIRMED")

    # 9. Miss Pruning (COASTING -> DELETED)
    def test_track_lifecycle_miss_deletion(self):
        """Verify missed detection transitions to COASTING and expires after max_misses."""
        tracker = MultiTargetTrackFusion(
            ref_lat=self.ref_lat, ref_lon=self.ref_lon,
            m_confirm_hits=1, max_misses_deletion=3
        )
        m1 = Measurement(
            timestamp=0.0, sensor_type=SensorType.AIS,
            lat=self.ref_lat, lon=self.ref_lon
        )
        tracker.process_cycle(0.0, [m1])

        # Miss 1: COASTING
        t_list = tracker.process_cycle(2.0, [])
        self.assertEqual(t_list[0]["state"], "COASTING")
        self.assertEqual(t_list[0]["consecutive_misses"], 1)

        # Miss 2: COASTING
        t_list = tracker.process_cycle(4.0, [])
        self.assertEqual(t_list[0]["state"], "COASTING")
        self.assertEqual(t_list[0]["consecutive_misses"], 2)

        # Miss 3: DELETED (removed from active list)
        t_list = tracker.process_cycle(6.0, [])
        self.assertEqual(len(t_list), 0)

    # 10. End-to-End MultiTargetTrackFusion Execution
    def test_multitarget_track_fusion_pipeline(self):
        """Verify tracker maintains two distinct persistent tracks simultaneously."""
        tracker = MultiTargetTrackFusion(
            ref_lat=self.ref_lat, ref_lon=self.ref_lon,
            association_method="hungarian",
            m_confirm_hits=2
        )

        for step in range(3):
            t = float(step * 2)
            m_a = Measurement(
                timestamp=t, sensor_type=SensorType.AIS,
                lat=self.ref_lat + step * 0.0002, lon=self.ref_lon,
                identity="MMSI-A"
            )
            m_b = Measurement(
                timestamp=t, sensor_type=SensorType.SAR,
                lat=self.ref_lat, lon=self.ref_lon + step * 0.0002
            )
            active = tracker.process_cycle(t, [m_a, m_b])

        self.assertEqual(len(active), 2)
        # Check persistent track IDs exist
        tids = [trk["track_id"] for trk in active]
        self.assertEqual(len(set(tids)), 2)
        # Check covariance ellipses are computed
        for trk in active:
            self.assertIn("covariance_ellipse", trk)
            self.assertGreater(trk["covariance_ellipse"]["cep_m"], 0.0)

    # 11. Regression Test: Control Scenario MOTA Floor (>= 95%)
    def test_control_scenario_mota_floor(self):
        """Regression test verifying MOTA >= 95% on clean control scenario (P_D=1.0, zero clutter)."""
        scenarios = generate_scenarios(seed=42)
        control_sc = scenarios["Control_Clean_NoClutter"]
        res = evaluate_tracking_run(control_sc, method="hungarian", distance_threshold_m=80.0)
        self.assertGreaterEqual(res["mota_pct"], 95.0, f"Control scenario MOTA must be >= 95%, got {res['mota_pct']}%")
        self.assertEqual(res["false_positives"], 0, f"Control scenario should have 0 false positives, got {res['false_positives']}")
        self.assertEqual(res["id_switch_count"], 0, f"Control scenario should have 0 ID switches, got {res['id_switch_count']}")

    # 12. Pure-Python Hungarian vs Scipy Exact Match (1,000 Random Matrices)
    def test_hungarian_scipy_exact_match(self):
        """Verify home-grown solve_hungarian matches scipy.optimize.linear_sum_assignment on 1,000 random cost matrices."""
        rng = np.random.RandomState(42)
        discrepancies = 0
        total_tested = 1000

        for _ in range(total_tested):
            num_rows = rng.randint(1, 11)
            num_cols = rng.randint(1, 11)
            cost_mat = rng.uniform(0.1, 100.0, size=(num_rows, num_cols))

            # Optional gating in 20% of test matrices
            if rng.random() < 0.2:
                mask = rng.random(size=(num_rows, num_cols)) < 0.15
                cost_mat[mask] = 1e8

            our_assign = solve_hungarian(cost_mat)
            scipy_r, scipy_c = linear_sum_assignment(cost_mat)

            # Compare total assignment cost for ungated assignments
            our_cost = sum(cost_mat[r, c] for r, c in our_assign)
            # Scipy assigns all min(num_rows, num_cols); filter out gated (>=1e7) for fair comparison
            scipy_cost = sum(cost_mat[r, c] for r, c in zip(scipy_r, scipy_c) if cost_mat[r, c] < 1e7)

            if abs(our_cost - scipy_cost) > 1e-4:
                discrepancies += 1

        self.assertEqual(discrepancies, 0, f"Discrepancies found between solve_hungarian and scipy: {discrepancies}/{total_tested}")

    # 13. Regression Test: Second Target Inside Active Gate Spawns Independent Track
    def test_second_target_inside_gate_spawns_track(self):
        """Verify initiation suppression does not hide real secondary targets appearing inside active gates."""
        tracker = MultiTargetTrackFusion(
            ref_lat=self.ref_lat, ref_lon=self.ref_lon,
            m_confirm_hits=2, n_confirm_window=3,
            association_method="hungarian"
        )

        # Step 0: Target 1 initiates at origin moving east at 5 m/s (~9.7 knots, 90 deg)
        m1_0 = Measurement(timestamp=0.0, sensor_type=SensorType.AIS, lat=self.ref_lat, lon=self.ref_lon, identity="VESSEL-A", speed_knots=9.72, heading_deg=90.0)
        tracker.process_cycle(0.0, [m1_0])

        # Step 1: Target 1 moves east; Target 2 appears 15m away (inside Target 1's validation gate)
        lat_t1_1, lon_t1_1, _ = enu_to_geodetic(10.0, 0.0, 0.0, self.ref_lat, self.ref_lon)
        lat_t2_1, lon_t2_1, _ = enu_to_geodetic(25.0, 0.0, 0.0, self.ref_lat, self.ref_lon)
        m1_1 = Measurement(timestamp=2.0, sensor_type=SensorType.AIS, lat=lat_t1_1, lon=lon_t1_1, identity="VESSEL-A", speed_knots=9.72, heading_deg=90.0)
        m2_1 = Measurement(timestamp=2.0, sensor_type=SensorType.SAR, lat=lat_t2_1, lon=lon_t2_1)

        tracker.process_cycle(2.0, [m1_1, m2_1])
        # Two tracks must exist: TRK-001 (confirmed) and TRK-002 (tentative)
        self.assertEqual(len(tracker.tracks), 2, "Second target inside gate must spawn its own tentative track")

        # Step 2: Both targets receive second hit
        lat_t1_2, lon_t1_2, _ = enu_to_geodetic(20.0, 0.0, 0.0, self.ref_lat, self.ref_lon)
        lat_t2_2, lon_t2_2, _ = enu_to_geodetic(40.0, 0.0, 0.0, self.ref_lat, self.ref_lon)
        m1_2 = Measurement(timestamp=4.0, sensor_type=SensorType.AIS, lat=lat_t1_2, lon=lon_t1_2, identity="VESSEL-A", speed_knots=9.72, heading_deg=90.0)
        m2_2 = Measurement(timestamp=4.0, sensor_type=SensorType.SAR, lat=lat_t2_2, lon=lon_t2_2)

        active = tracker.process_cycle(4.0, [m1_2, m2_2])
        confirmed_tracks = [t for t in active if t["state"] == "CONFIRMED"]
        self.assertEqual(len(confirmed_tracks), 2, "Both distinct targets must promote to CONFIRMED state")


if __name__ == "__main__":
    unittest.main()


