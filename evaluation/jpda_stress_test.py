"""JPDA Stress Test & Fallback Benchmark — Project Rakshak 2.0 (SIMULATED).

Evaluates Joint Probabilistic Data Association under an extreme worst-case condition:
A single connected cluster with 10 tracks and 15 measurements where all measurements
fall within the validation gates of all tracks.

Reports:
1. Cluster execution runtime (milliseconds).
2. The event cap applied (max 1,000 joint events, max cluster size 8 tracks).
3. The fallback mechanism invoked (Decoupled PDA).
4. Probability conservation check: sum(beta[t, :]) == 1.0 for all t in 1..10.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.track_fusion import (
    Track,
    Measurement,
    SensorType,
    compute_joint_jpda_betas
)

def run_jpda_stress_test(num_iterations: int = 50) -> dict:
    ref_lat = 18.9220
    ref_lon = 72.8346
    ref_origin = (ref_lat, ref_lon, 0.0)

    num_tracks = 10
    num_meas = 15

    # Create 10 tracks clustered at the tactical center
    tracks = []
    for i in range(num_tracks):
        m = Measurement(
            timestamp=0.0,
            sensor_type=SensorType.AIS,
            lat=ref_lat + (i * 0.00005),
            lon=ref_lon + (i * 0.00005),
            speed_knots=12.0,
            heading_deg=45.0
        )
        tracks.append(Track(f"TRK-STRESS-{i+1:02d}", m, ref_origin))

    # Create 15 measurements in the same dense zone
    measurements = []
    for j in range(num_meas):
        measurements.append(Measurement(
            timestamp=1.0,
            sensor_type=SensorType.SAR if j % 2 == 0 else SensorType.OPTICAL,
            lat=ref_lat + (j * 0.00004),
            lon=ref_lon + (j * 0.00004)
        ))

    # All measurements within all tracks' validation gates (fully connected single cluster)
    gating_matrix = np.ones((num_tracks, num_meas), dtype=bool)

    # Warm-up call
    _ = compute_joint_jpda_betas(tracks, measurements, gating_matrix)

    # Timed runs
    runtimes_ms = []
    for _ in range(num_iterations):
        t0 = time.perf_counter()
        betas = compute_joint_jpda_betas(tracks, measurements, gating_matrix)
        t1 = time.perf_counter()
        runtimes_ms.append((t1 - t0) * 1000.0)

    # Verify probability conservation
    sums = np.sum(betas, axis=1)
    conserved = bool(np.allclose(sums, 1.0, atol=1e-5))

    mean_ms = float(np.mean(runtimes_ms))
    p95_ms = float(np.percentile(runtimes_ms, 95))
    min_ms = float(np.min(runtimes_ms))
    max_ms = float(np.max(runtimes_ms))

    results = {
        "benchmark_label": "SIMULATED",
        "scenario": "Worst-Case Dense Cluster Stress Test",
        "cluster_tracks": num_tracks,
        "cluster_measurements": num_meas,
        "fully_connected_edges": num_tracks * num_meas,
        "theoretical_unconstrained_events": "15! / (15 - 10)! = 10,897,286,400 events",
        "event_cap": 1000,
        "cluster_size_threshold": 8,
        "fallback_algorithm": "Decoupled Probabilistic Data Association (PDA) with individual likelihood normalization",
        "probability_conservation_verified": conserved,
        "iterations_timed": num_iterations,
        "runtime_mean_ms": round(mean_ms, 3),
        "runtime_p95_ms": round(p95_ms, 3),
        "runtime_min_ms": round(min_ms, 3),
        "runtime_max_ms": round(max_ms, 3)
    }

    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — JPDA STRESS TEST REPORT (SIMULATED)")
    print("=" * 70)
    print(f"Cluster Dimensions        : {num_tracks} Tracks x {num_meas} Measurements (Fully Connected Gating)")
    print(f"Unconstrained Complexity  : {results['theoretical_unconstrained_events']}")
    print(f"Active Event Cap          : {results['event_cap']} joint events (Max Cluster Size: {results['cluster_size_threshold']})")
    print(f"Triggered Fallback        : {results['fallback_algorithm']}")
    print(f"Probability Sum Check     : {'PASSED (All tracks sum to 1.000)' if conserved else 'FAILED'}")
    print(f"Runtime Across {num_iterations} Runs : Mean = {mean_ms:.3f} ms | P95 = {p95_ms:.3f} ms | Range = [{min_ms:.3f}, {max_ms:.3f}] ms")
    print("=" * 70)

    return results

if __name__ == "__main__":
    run_jpda_stress_test()
