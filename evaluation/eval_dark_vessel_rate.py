"""Synthetic Evaluation of Spaceborne SAR CA-CFAR & AIS Cross-Sensor Correlation.

Task A: Empirical benchmarking of dark-vessel detection rate, false-dark rate,
cross-sensor Haversine correlation radius, density sweep, time-offset sweep,
and stress cases (AIS gaps, wrong kinematics) across 20 independent seeds.

Dataset Status: SIMULATED (No local xView3-SAR dataset present in repository).
Protocol:
- 20 independent random seeds (seeds 1 through 20).
- Minimum 500 contacts per cell across ALL sweeps (10,000 total contacts evaluated per condition).
- Statistical metrics reported per cell: Mean ± Std, 95% Student-t Confidence Interval [low, high], min, max.
"""
from __future__ import annotations

import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.sar_engine import (
    haversine_km,
    cfar_detect,
    classify_vessel_by_length,
    correlate_sar_with_ais,
)

RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_JSON = RESULTS_DIR / "dark_vessel_eval_report.json"
SUMMARY_MD = RESULTS_DIR / "dark_vessel_summary.md"

# Student's t-value for df = 19 (N = 20), two-sided 95% confidence level
T_CRIT_DF19_95 = 2.093024


def generate_synthetic_maritime_set(
    n_contacts: int = 500,
    dark_fraction: float = 0.30,
    n_decoy_ais: int = 50,
    n_clutter_sar: int = 40,
    max_time_offset_min: float = 30.0,
    ais_missing_prob: float = 0.0,
    kinematic_corruption_prob: float = 0.0,
    area_km2: float = 70000.0,  # ~265 x 265 km corridor
    center_lat: float = 19.25,
    center_lon: float = 72.25,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generate synthetic maritime ground truth contacts, AIS pings, and SAR targets."""
    rng = random.Random(seed)
    contacts: List[Dict[str, Any]] = []
    ais_pings_raw: List[Dict[str, Any]] = []
    ais_pings_propagated: List[Dict[str, Any]] = []

    # Calculate geographic degree span from area in km²
    side_km = math.sqrt(area_km2)
    d_lat_deg = side_km / 111.0
    d_lon_deg = side_km / (111.0 * math.cos(math.radians(center_lat)))

    min_lat = center_lat - d_lat_deg / 2.0
    max_lat = center_lat + d_lat_deg / 2.0
    min_lon = center_lon - d_lon_deg / 2.0
    max_lon = center_lon + d_lon_deg / 2.0

    n_dark = int(round(n_contacts * dark_fraction))
    n_coop = n_contacts - n_dark

    is_dark_list = [True] * n_dark + [False] * n_coop
    rng.shuffle(is_dark_list)

    for i in range(n_contacts):
        contact_id = f"VESSEL-{i+1:04d}"
        is_dark = is_dark_list[i]

        lat = rng.uniform(min_lat, max_lat)
        lon = rng.uniform(min_lon, max_lon)

        sog_knots = rng.uniform(5.0, 24.0)
        cog_deg = rng.uniform(0.0, 360.0)
        length_m = rng.uniform(15.0, 280.0)
        vessel_class = classify_vessel_by_length(length_m)

        # Radar backscatter
        base_rcs = -8.0 if length_m > 60 else -13.0
        rcs_sigma0_db = round(rng.gauss(base_rcs, 2.5), 2)
        cfar_detected, cfar_conf = cfar_detect(
            rcs_sigma0_db, sea_clutter_db=-22.0, threshold_factor=3.5
        )

        contact = {
            "contact_id": contact_id,
            "is_dark_ground_truth": is_dark,
            "true_lat": lat,
            "true_lon": lon,
            "sog_knots": round(sog_knots, 1),
            "cog_deg": round(cog_deg, 1),
            "length_m": round(length_m, 1),
            "vessel_class": vessel_class,
            "rcs_sigma0_db": rcs_sigma0_db,
            "cfar_detected": cfar_detected,
            "cfar_confidence": cfar_conf,
        }
        contacts.append(contact)

        # Cooperative vessels generate AIS pings
        if not is_dark:
            # Check for simulated AIS gap (missing ping)
            if rng.random() < ais_missing_prob:
                continue

            delta_t_min = rng.uniform(-max_time_offset_min, max_time_offset_min)
            delta_t_hours = delta_t_min / 60.0

            # True physical motion
            dist_km = sog_knots * 1.852 * delta_t_hours
            rad_cog = math.radians(cog_deg)
            dy_km = dist_km * math.cos(rad_cog)
            dx_km = dist_km * math.sin(rad_cog)

            d_lat = dy_km / 111.0
            d_lon = dx_km / (111.0 * math.cos(math.radians(lat)))

            ais_past_lat = lat - d_lat
            ais_past_lon = lon - d_lon

            # GPS position error (~150m standard deviation)
            gps_err_lat = rng.gauss(0, 0.15) / 111.0
            gps_err_lon = rng.gauss(0, 0.15) / (111.0 * math.cos(math.radians(lat)))

            raw_lat = ais_past_lat + gps_err_lat
            raw_lon = ais_past_lon + gps_err_lon

            # Kinematic corruption (wrong SOG/COG reported)
            reported_sog = sog_knots
            reported_cog = cog_deg
            if rng.random() < kinematic_corruption_prob:
                reported_sog = max(0.0, sog_knots + rng.choice([-15.0, 15.0]))
                reported_cog = (cog_deg + 180.0) % 360.0

            mmsi = f"419{rng.randint(100000, 999999)}"
            ais_pings_raw.append({
                "mmsi": mmsi,
                "lat": round(raw_lat, 6),
                "lon": round(raw_lon, 6),
                "sog_knots": round(reported_sog, 1),
                "cog_deg": round(reported_cog, 1),
                "delta_t_min": round(delta_t_min, 1),
                "source_vessel_id": contact_id,
            })

            # Dead-reckoning propagation using reported SOG/COG
            dr_dist_km = reported_sog * 1.852 * (delta_t_min / 60.0)
            dr_rad_cog = math.radians(reported_cog)
            dr_dy = dr_dist_km * math.cos(dr_rad_cog)
            dr_dx = dr_dist_km * math.sin(dr_rad_cog)
            prop_lat = raw_lat + (dr_dy / 111.0)
            prop_lon = raw_lon + (dr_dx / (111.0 * math.cos(math.radians(lat))))

            ais_pings_propagated.append({
                "mmsi": mmsi,
                "lat": round(prop_lat, 6),
                "lon": round(prop_lon, 6),
                "sog_knots": round(reported_sog, 1),
                "cog_deg": round(reported_cog, 1),
                "delta_t_min": round(delta_t_min, 1),
                "source_vessel_id": contact_id,
            })

    # Add Decoy AIS tracks
    for d in range(n_decoy_ais):
        decoy_mmsi = f"41999{d+1:04d}"
        decoy_lat = rng.uniform(min_lat, max_lat)
        decoy_lon = rng.uniform(min_lon, max_lon)
        decoy_ping = {
            "mmsi": decoy_mmsi,
            "lat": round(decoy_lat, 6),
            "lon": round(decoy_lon, 6),
            "sog_knots": round(rng.uniform(2.0, 15.0), 1),
            "cog_deg": round(rng.uniform(0.0, 360.0), 1),
            "delta_t_min": 0.0,
            "source_vessel_id": None,
            "is_decoy": True,
        }
        ais_pings_raw.append(decoy_ping)
        ais_pings_propagated.append(decoy_ping)

    return contacts, ais_pings_raw, ais_pings_propagated


def evaluate_matcher_metrics(
    contacts: List[Dict[str, Any]],
    ais_pings: List[Dict[str, Any]],
    radius_km: float = 2.0,
) -> Dict[str, Any]:
    """Evaluate Haversine matching and compute both end-to-end and post-detection recall."""
    total_dark_gt = sum(1 for c in contacts if c["is_dark_ground_truth"])
    total_coop_gt = sum(1 for c in contacts if not c["is_dark_ground_truth"])

    cfar_detected_dark = 0
    cfar_detected_coop = 0

    tp = 0  # GT Dark detected by CFAR AND flagged Dark (no AIS matched)
    fp = 0  # GT Coop detected by CFAR AND flagged Dark (false dark alert)
    tn = 0  # GT Coop detected by CFAR AND matched to AIS (correctly deemed cooperative)
    fn = 0  # GT Dark detected by CFAR BUT matched to AIS (missed dark)

    for c in contacts:
        is_dark_gt = c["is_dark_ground_truth"]
        if not c["cfar_detected"]:
            continue

        if is_dark_gt:
            cfar_detected_dark += 1
        else:
            cfar_detected_coop += 1

        matched, _ = correlate_sar_with_ais(
            sar_lat=c["true_lat"],
            sar_lon=c["true_lon"],
            ais_targets=ais_pings,
            tolerance_km=radius_km,
        )
        declared_dark = not matched

        if is_dark_gt and declared_dark:
            tp += 1
        elif not is_dark_gt and declared_dark:
            fp += 1
        elif not is_dark_gt and not declared_dark:
            tn += 1
        elif is_dark_gt and not declared_dark:
            fn += 1

    # End-to-end capture = (CFAR detected AND flagged dark) / all ground truth dark
    end_to_end_recall = tp / total_dark_gt if total_dark_gt > 0 else 0.0
    # Post-detection recall = (CFAR detected AND flagged dark) / CFAR detected dark
    post_det_recall = tp / cfar_detected_dark if cfar_detected_dark > 0 else 0.0

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = (2 * precision * post_det_recall) / (precision + post_det_recall) if (precision + post_det_recall) > 0 else 0.0
    false_dark_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "radius_km": radius_km,
        "total_dark_gt": total_dark_gt,
        "total_coop_gt": total_coop_gt,
        "cfar_detected_dark": cfar_detected_dark,
        "cfar_detected_coop": cfar_detected_coop,
        "cfar_dark_detection_rate_pct": round((cfar_detected_dark / total_dark_gt) * 100.0, 2) if total_dark_gt > 0 else 0.0,
        "true_positives_tp": tp,
        "false_positives_fp": fp,
        "true_negatives_tn": tn,
        "false_negatives_fn": fn,
        "end_to_end_capture_rate_pct": round(end_to_end_recall * 100.0, 2),
        "post_detection_recall_pct": round(post_det_recall * 100.0, 2),
        "precision_pct": round(precision * 100.0, 2),
        "f1_score": round(f1, 4),
        "false_dark_rate_pct": round(false_dark_rate * 100.0, 2),
    }


def aggregate_metrics_across_seeds(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute mean, std, 95% Student-t CI, min, and max across independent seed runs."""
    k = len(runs)
    if k == 0:
        return {}
    t_crit = T_CRIT_DF19_95 if k == 20 else 1.96

    stat_keys = [
        "end_to_end_capture_rate_pct",
        "post_detection_recall_pct",
        "cfar_dark_detection_rate_pct",
        "precision_pct",
        "false_dark_rate_pct",
        "f1_score",
        "true_positives_tp",
        "false_positives_fp",
        "true_negatives_tn",
        "false_negatives_fn",
        "cfar_detected_dark",
        "total_dark_gt",
    ]

    agg: Dict[str, Any] = {
        "n_seeds": k,
    }

    for key in stat_keys:
        vals = [float(r[key]) for r in runs if key in r]
        if not vals:
            continue
        mean_v = sum(vals) / k
        if k > 1:
            var_v = sum((x - mean_v) ** 2 for x in vals) / (k - 1)
            std_v = math.sqrt(max(0.0, var_v))
        else:
            std_v = 0.0

        sem = std_v / math.sqrt(k)
        me = t_crit * sem
        ci_low = max(0.0, mean_v - me)
        ci_high = min(100.0, mean_v + me) if ("pct" in key or "rate" in key or "score" in key) else (mean_v + me)

        decimals = 4 if key == "f1_score" else 2
        agg[key] = {
            "mean": round(mean_v, decimals),
            "std": round(std_v, decimals),
            "ci_95_low": round(ci_low, decimals),
            "ci_95_high": round(ci_high, decimals),
            "min": round(min(vals), decimals),
            "max": round(max(vals), decimals),
            "formatted": f"{mean_v:.{decimals}f} ± {std_v:.{decimals}f} [{ci_low:.{decimals}f}, {ci_high:.{decimals}f}]"
        }

    return agg


def main():
    print("=" * 76)
    print("  PROJECT RAKSHAK 2.0 — TASK A: 20-SEED DARK-VESSEL EVALUATION")
    print("  (N >= 500 contacts per cell, 20 independent seeds, 95% Confidence Intervals)")
    print("=" * 76)

    SEEDS = list(range(1, 21))
    N_PER_CELL = 500
    DARK_FRACTION = 0.30  # 150 Dark, 350 Cooperative per seed

    # -------------------------------------------------------------------------
    # 1. Baseline Multi-Seed Evaluation (Radius = 1, 2, 5, 10 km)
    # -------------------------------------------------------------------------
    print(f"\n[1/5] Running Baseline 20-Seed Suite (N={N_PER_CELL} contacts/seed, ±30 min offset)...")
    radii = [1.0, 2.0, 5.0, 10.0]
    baseline_runs_prop: Dict[float, List[Dict[str, Any]]] = {r: [] for r in radii}
    baseline_runs_unprop: Dict[float, List[Dict[str, Any]]] = {r: [] for r in radii}

    for s_idx, s in enumerate(SEEDS, 1):
        contacts, ais_raw, ais_prop = generate_synthetic_maritime_set(
            n_contacts=N_PER_CELL,
            dark_fraction=DARK_FRACTION,
            n_decoy_ais=50,
            n_clutter_sar=40,
            max_time_offset_min=30.0,
            seed=s,
        )
        for r in radii:
            res_p = evaluate_matcher_metrics(contacts, ais_prop, radius_km=r)
            res_u = evaluate_matcher_metrics(contacts, ais_raw, radius_km=r)
            res_p["seed"] = s
            res_u["seed"] = s
            baseline_runs_prop[r].append(res_p)
            baseline_runs_unprop[r].append(res_u)

    baseline_agg_prop = {f"{r:.1f}_km": aggregate_metrics_across_seeds(baseline_runs_prop[r]) for r in radii}
    baseline_agg_unprop = {f"{r:.1f}_km": aggregate_metrics_across_seeds(baseline_runs_unprop[r]) for r in radii}

    op_stats = baseline_agg_prop["2.0_km"]
    print(f"  • Ground Truth Dark per Seed    : {op_stats['total_dark_gt']['mean']:.0f} (Total evaluated: {int(op_stats['total_dark_gt']['mean'] * len(SEEDS))})")
    print(f"  • Headline End-to-End Capture   : {op_stats['end_to_end_capture_rate_pct']['formatted']}%")
    print(f"  • Post-Detection Recall         : {op_stats['post_detection_recall_pct']['formatted']}%")
    print(f"  • CA-CFAR Radar Detection Rate  : {op_stats['cfar_dark_detection_rate_pct']['formatted']}%")
    print(f"  • Precision                     : {op_stats['precision_pct']['formatted']}%")
    print(f"  • False-Dark Rate               : {op_stats['false_dark_rate_pct']['formatted']}%")

    # -------------------------------------------------------------------------
    # 2. Density Sweep (5, 20, 50, 100, 200 contacts per 10,000 km²)
    # To guarantee >= 500 contacts per cell, sector area is scaled proportionally:
    #   area_km2 = (500 / density) * 10,000 km²
    # -------------------------------------------------------------------------
    print(f"\n[2/5] Running Density Sweep across 20 Seeds (N={N_PER_CELL} contacts per cell)...")
    densities = [5, 20, 50, 100, 200]
    density_runs: Dict[int, List[Dict[str, Any]]] = {d: [] for d in densities}
    density_areas: Dict[int, float] = {}

    for d in densities:
        # Scale area so contacts = N_PER_CELL at exact target density
        area_km2 = (N_PER_CELL / float(d)) * 10000.0
        density_areas[d] = area_km2

        for s in SEEDS:
            c_dens, _, ais_dens = generate_synthetic_maritime_set(
                n_contacts=N_PER_CELL,
                dark_fraction=DARK_FRACTION,
                n_decoy_ais=max(10, int(N_PER_CELL * 0.10)),
                n_clutter_sar=max(10, int(N_PER_CELL * 0.08)),
                max_time_offset_min=30.0,
                area_km2=area_km2,
                seed=s * 100 + d,
            )
            res_d = evaluate_matcher_metrics(c_dens, ais_dens, radius_km=2.0)
            res_d["density_per_10k_km2"] = d
            res_d["seed"] = s
            density_runs[d].append(res_d)

    density_agg = {}
    for d in densities:
        agg = aggregate_metrics_across_seeds(density_runs[d])
        agg["density_per_10k_km2"] = d
        agg["area_km2"] = density_areas[d]
        agg["contacts_per_seed"] = N_PER_CELL
        agg["total_contacts_evaluated"] = N_PER_CELL * len(SEEDS)
        density_agg[f"{d}_per_10k_km2"] = agg

        e2e_fmt = agg["end_to_end_capture_rate_pct"]["formatted"]
        pdet_fmt = agg["post_detection_recall_pct"]["formatted"]
        prec_fmt = agg["precision_pct"]["formatted"]
        fd_fmt = agg["false_dark_rate_pct"]["formatted"]
        print(f"  Density {d:3d}/10k km² (Area: {density_areas[d]:9.0f} km², N={N_PER_CELL}x20={N_PER_CELL*len(SEEDS)}):")
        print(f"    -> End-to-End: {e2e_fmt}% | Post-Det: {pdet_fmt}% | Prec: {prec_fmt}% | False-Dark: {fd_fmt}%")

    # -------------------------------------------------------------------------
    # 3. Time-Offset Sweep (±5, ±15, ±30 min) across 20 Seeds
    # -------------------------------------------------------------------------
    print(f"\n[3/5] Running Time-Offset Sweep across 20 Seeds (N={N_PER_CELL} contacts per cell)...")
    time_windows = [5.0, 15.0, 30.0]
    time_runs_prop: Dict[float, List[Dict[str, Any]]] = {tw: [] for tw in time_windows}
    time_runs_unprop: Dict[float, List[Dict[str, Any]]] = {tw: [] for tw in time_windows}

    for tw in time_windows:
        for s in SEEDS:
            c_t, ais_raw_t, ais_prop_t = generate_synthetic_maritime_set(
                n_contacts=N_PER_CELL,
                dark_fraction=DARK_FRACTION,
                n_decoy_ais=50,
                n_clutter_sar=40,
                max_time_offset_min=tw,
                seed=s * 1000 + int(tw),
            )
            res_p = evaluate_matcher_metrics(c_t, ais_prop_t, radius_km=2.0)
            res_u = evaluate_matcher_metrics(c_t, ais_raw_t, radius_km=2.0)
            res_p["window_min"] = tw
            res_u["window_min"] = tw
            res_p["seed"] = s
            res_u["seed"] = s
            time_runs_prop[tw].append(res_p)
            time_runs_unprop[tw].append(res_u)

    time_agg_prop = {}
    time_agg_unprop = {}
    for tw in time_windows:
        k = f"pm_{int(tw)}_min"
        p_agg = aggregate_metrics_across_seeds(time_runs_prop[tw])
        u_agg = aggregate_metrics_across_seeds(time_runs_unprop[tw])
        p_agg["window_min"] = tw
        u_agg["window_min"] = tw
        p_agg["contacts_per_seed"] = N_PER_CELL
        u_agg["contacts_per_seed"] = N_PER_CELL
        time_agg_prop[k] = p_agg
        time_agg_unprop[k] = u_agg

        print(f"  Window ±{int(tw):2d} min (N={N_PER_CELL}x20):")
        print(f"    WITH SOG/COG Prop : E2E = {p_agg['end_to_end_capture_rate_pct']['formatted']}% | False-Dark = {p_agg['false_dark_rate_pct']['formatted']}%")
        print(f"    WITHOUT Prop (Raw): E2E = {u_agg['end_to_end_capture_rate_pct']['formatted']}% | False-Dark = {u_agg['false_dark_rate_pct']['formatted']}%")

    # -------------------------------------------------------------------------
    # 4. Stress Cases (10% AIS Gaps & 10% Wrong SOG/COG) across 20 Seeds
    # -------------------------------------------------------------------------
    print(f"\n[4/5] Running Stress Cases across 20 Seeds (N={N_PER_CELL} contacts per cell)...")
    stress_runs_gap: List[Dict[str, Any]] = []
    stress_runs_kin: List[Dict[str, Any]] = []

    for s in SEEDS:
        # Case A: 10% AIS packet loss
        c_gap, _, ais_gap = generate_synthetic_maritime_set(
            n_contacts=N_PER_CELL,
            dark_fraction=DARK_FRACTION,
            n_decoy_ais=50,
            n_clutter_sar=40,
            max_time_offset_min=30.0,
            ais_missing_prob=0.10,
            seed=s * 5000 + 1,
        )
        res_g = evaluate_matcher_metrics(c_gap, ais_gap, radius_km=2.0)
        res_g["seed"] = s
        stress_runs_gap.append(res_g)

        # Case B: 10% corrupted kinematics
        c_kin, _, ais_kin = generate_synthetic_maritime_set(
            n_contacts=N_PER_CELL,
            dark_fraction=DARK_FRACTION,
            n_decoy_ais=50,
            n_clutter_sar=40,
            max_time_offset_min=30.0,
            kinematic_corruption_prob=0.10,
            seed=s * 5000 + 2,
        )
        res_k = evaluate_matcher_metrics(c_kin, ais_kin, radius_km=2.0)
        res_k["seed"] = s
        stress_runs_kin.append(res_k)

    stress_agg_gap = aggregate_metrics_across_seeds(stress_runs_gap)
    stress_agg_kin = aggregate_metrics_across_seeds(stress_runs_kin)

    print(f"  • Stress A (10% AIS Gaps):")
    print(f"    -> E2E Capture: {stress_agg_gap['end_to_end_capture_rate_pct']['formatted']}% | Prec: {stress_agg_gap['precision_pct']['formatted']}% | False-Dark: {stress_agg_gap['false_dark_rate_pct']['formatted']}%")
    print(f"  • Stress B (10% Wrong SOG/COG Kinematics):")
    print(f"    -> E2E Capture: {stress_agg_kin['end_to_end_capture_rate_pct']['formatted']}% | Prec: {stress_agg_kin['precision_pct']['formatted']}% | False-Dark: {stress_agg_kin['false_dark_rate_pct']['formatted']}%")

    # -------------------------------------------------------------------------
    # 5. Assemble Comprehensive 20-Seed Report
    # -------------------------------------------------------------------------
    mean_e2e = op_stats["end_to_end_capture_rate_pct"]["mean"]
    std_e2e = op_stats["end_to_end_capture_rate_pct"]["std"]
    ci_e2e = [op_stats["end_to_end_capture_rate_pct"]["ci_95_low"], op_stats["end_to_end_capture_rate_pct"]["ci_95_high"]]

    mean_pdet = op_stats["post_detection_recall_pct"]["mean"]
    std_pdet = op_stats["post_detection_recall_pct"]["std"]
    ci_pdet = [op_stats["post_detection_recall_pct"]["ci_95_low"], op_stats["post_detection_recall_pct"]["ci_95_high"]]

    mean_cfar = op_stats["cfar_dark_detection_rate_pct"]["mean"]
    mean_prec = op_stats["precision_pct"]["mean"]
    mean_false = op_stats["false_dark_rate_pct"]["mean"]
    mean_f1 = op_stats["f1_score"]["mean"]

    report: Dict[str, Any] = {
        "benchmark_title": "Project Rakshak 2.0 — Task A: Multi-Seed Dark-Vessel Rate & Statistical Sweeps",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_provenance": "SIMULATED",
        "data_availability_note": "No local xView3-SAR dataset present in repository. Evaluated on 20 independent seeds of synthetic maritime contacts (N = 500 per cell, 10,000 contacts evaluated per sweep condition) with SOG/COG temporal kinematics and Gaussian GPS noise.",
        "n_seeds": len(SEEDS),
        "sample_size_per_cell": N_PER_CELL,
        "total_contacts_evaluated_per_cell": N_PER_CELL * len(SEEDS),
        "dark_fraction_pct": DARK_FRACTION * 100.0,
        "headline_metrics": {
            "end_to_end_dark_vessel_capture_pct": mean_e2e,
            "end_to_end_capture_std": std_e2e,
            "end_to_end_capture_ci_95": ci_e2e,
            "end_to_end_capture_formatted": op_stats["end_to_end_capture_rate_pct"]["formatted"],
            "post_detection_recall_pct": mean_pdet,
            "post_detection_recall_std": std_pdet,
            "post_detection_recall_ci_95": ci_pdet,
            "post_detection_recall_formatted": op_stats["post_detection_recall_pct"]["formatted"],
            "cfar_radar_detection_rate_pct": mean_cfar,
            "precision_pct": mean_prec,
            "precision_std": op_stats["precision_pct"]["std"],
            "false_dark_rate_pct": mean_false,
            "false_dark_rate_std": op_stats["false_dark_rate_pct"]["std"],
            "f1_score": mean_f1,
            "operational_matching_radius_km": 2.0,
            "temporal_propagation_enabled": True,
            "sample_size_n": N_PER_CELL,
            "n_seeds": len(SEEDS),
            "status_label": f"SIMULATED (20 seeds, N={N_PER_CELL}/cell, total {N_PER_CELL*len(SEEDS)} contacts/cell)",
            "stats": op_stats,
        },
        "baseline_matching_radius_sweep": {
            "with_temporal_propagation": baseline_agg_prop,
            "without_temporal_propagation": baseline_agg_unprop,
        },
        "density_sweep": density_agg,
        "density_sweep_per_10k_km2": density_agg,  # Backwards compatibility key
        "time_offset_sweep": {
            "with_temporal_propagation": time_agg_prop,
            "without_temporal_propagation": time_agg_unprop,
        },
        "temporal_offset_drift_sweep": {  # Backwards compatibility key
            "with_temporal_propagation": time_agg_prop,
            "without_temporal_propagation": time_agg_unprop,
        },
        "stress_case_evaluations": {
            "ais_gaps_10_pct_missing": {
                "description": "10% of cooperative vessels suffer RF packet loss / no AIS ping received (N=500 x 20 seeds)",
                "end_to_end_capture_rate_pct": stress_agg_gap["end_to_end_capture_rate_pct"]["mean"],
                "post_detection_recall_pct": stress_agg_gap["post_detection_recall_pct"]["mean"],
                "precision_pct": stress_agg_gap["precision_pct"]["mean"],
                "false_dark_rate_pct": stress_agg_gap["false_dark_rate_pct"]["mean"],
                "stats": stress_agg_gap,
            },
            "kinematic_corruption_10_pct_wrong_sog_cog": {
                "description": "10% of cooperative vessels report corrupted SOG/COG (spoofing / degraded GPS) (N=500 x 20 seeds)",
                "end_to_end_capture_rate_pct": stress_agg_kin["end_to_end_capture_rate_pct"]["mean"],
                "post_detection_recall_pct": stress_agg_kin["post_detection_recall_pct"]["mean"],
                "precision_pct": stress_agg_kin["precision_pct"]["mean"],
                "false_dark_rate_pct": stress_agg_kin["false_dark_rate_pct"]["mean"],
                "stats": stress_agg_kin,
            },
        },
        "stress_cases": {  # Backwards compatibility key
            "ais_gaps_10_pct_missing": stress_agg_gap,
            "kinematic_corruption_10_pct_wrong_sog_cog": stress_agg_kin,
        },
        "seed_runs_baseline_2km": [
            {
                "seed": r["seed"],
                "end_to_end_capture_rate_pct": r["end_to_end_capture_rate_pct"],
                "post_detection_recall_pct": r["post_detection_recall_pct"],
                "precision_pct": r["precision_pct"],
                "false_dark_rate_pct": r["false_dark_rate_pct"],
                "tp": r["true_positives_tp"],
                "fp": r["false_positives_fp"],
                "total_dark_gt": r["total_dark_gt"],
            }
            for r in baseline_runs_prop[2.0]
        ],
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[OK] Raw report saved to: {REPORT_JSON}")

    # Generate Formatted Summary Markdown
    md_content = f"""# Project Rakshak 2.0: Task A — Multi-Seed Dark-Vessel Rate & Statistical Sweeps

- **Provenance**: `SIMULATED` (Multi-seed synthetic maritime dataset, $N = 500$ contacts/cell $\\times 20$ seeds $= 10,000$ contacts/cell)
- **Seeds Evaluated**: 20 independent seeds (`seed=1` to `seed=20`)
- **Statistical Framework**: Mean $\\pm$ Standard Deviation with 95% Confidence Intervals via two-tailed Student's t-distribution ($t_{{19, 0.975}} = 2.0930$)
- **Local xView3-SAR Status**: Not present in repository. Evaluated on calibrated maritime kinematics set.
- **Dark Fraction**: **30.0%** ($N_{{\\text{{dark}}}} = 150$, $N_{{\\text{{coop}}}} = 350$ per seed; $3,000$ dark vessels evaluated per sweep cell)

---

## 1. Headline Dark-Vessel Performance (Operational Radius: 2.0 km, ±30 min Offset)

| Metric | Mean $\\pm$ Std | 95% Confidence Interval | Min / Max | Operational Definition |
| :--- | :---: | :---: | :---: | :--- |
| **Headline End-to-End Dark Vessel Capture** | **{op_stats['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {op_stats['end_to_end_capture_rate_pct']['std']:.2f}%** | **[{op_stats['end_to_end_capture_rate_pct']['ci_95_low']:.2f}%, {op_stats['end_to_end_capture_rate_pct']['ci_95_high']:.2f}%]** | {op_stats['end_to_end_capture_rate_pct']['min']:.2f}% / {op_stats['end_to_end_capture_rate_pct']['max']:.2f}% | $\\frac{{\\text{{CFAR-Detected AND Flagged Dark}}}}{{\\text{{All Ground-Truth Dark Vessels}}}}$ |
| **Post-Detection Recall** | **{op_stats['post_detection_recall_pct']['mean']:.2f} $\\pm$ {op_stats['post_detection_recall_pct']['std']:.2f}%** | **[{op_stats['post_detection_recall_pct']['ci_95_low']:.2f}%, {op_stats['post_detection_recall_pct']['ci_95_high']:.2f}%]** | {op_stats['post_detection_recall_pct']['min']:.2f}% / {op_stats['post_detection_recall_pct']['max']:.2f}% | $\\frac{{\\text{{CFAR-Detected AND Flagged Dark}}}}{{\\text{{CFAR-Detected Dark}}}}$ |
| **CA-CFAR Radar Detection Rate** | **{op_stats['cfar_dark_detection_rate_pct']['mean']:.2f} $\\pm$ {op_stats['cfar_dark_detection_rate_pct']['std']:.2f}%** | **[{op_stats['cfar_dark_detection_rate_pct']['ci_95_low']:.2f}%, {op_stats['cfar_dark_detection_rate_pct']['ci_95_high']:.2f}%]** | {op_stats['cfar_dark_detection_rate_pct']['min']:.2f}% / {op_stats['cfar_dark_detection_rate_pct']['max']:.2f}% | Radar detectability across vessel RCS distribution |
| **Precision** | **{op_stats['precision_pct']['mean']:.2f} $\\pm$ {op_stats['precision_pct']['std']:.2f}%** | **[{op_stats['precision_pct']['ci_95_low']:.2f}%, {op_stats['precision_pct']['ci_95_high']:.2f}%]** | {op_stats['precision_pct']['min']:.2f}% / {op_stats['precision_pct']['max']:.2f}% | $\\frac{{\\text{{True Dark Alerts}}}}{{\\text{{All Declared Dark Alerts}}}}$ |
| **False-Dark Alarm Rate** | **{op_stats['false_dark_rate_pct']['mean']:.2f} $\\pm$ {op_stats['false_dark_rate_pct']['std']:.2f}%** | **[{op_stats['false_dark_rate_pct']['ci_95_low']:.2f}%, {op_stats['false_dark_rate_pct']['ci_95_high']:.2f}%]** | {op_stats['false_dark_rate_pct']['min']:.2f}% / {op_stats['false_dark_rate_pct']['max']:.2f}% | False alarms on cooperative tracks |
| **F1 Score** | **{op_stats['f1_score']['mean']:.4f} $\\pm$ {op_stats['f1_score']['std']:.4f}** | **[{op_stats['f1_score']['ci_95_low']:.4f}, {op_stats['f1_score']['ci_95_high']:.4f}]** | {op_stats['f1_score']['min']:.4f} / {op_stats['f1_score']['max']:.4f} | Harmonic mean of precision and post-det recall |

---

## 2. Density Sweep (5, 20, 50, 100, 200 Contacts per 10,000 km²)

Evaluated across 20 independent seeds. In each density condition, sector area was scaled so that **$N = 500$ contacts per seed** ($10,000$ total contacts per cell):

| Contact Density | Sector Area | Total Contacts (20 Seeds) | End-to-End Capture (Mean $\\pm$ Std [95% CI]) | Post-Det Recall (Mean $\\pm$ Std [95% CI]) | Precision (Mean $\\pm$ Std) | False-Dark Rate (Mean $\\pm$ Std) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for d in densities:
        d_val = density_agg[f"{d}_per_10k_km2"]
        e2e_str = f"**{d_val['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {d_val['end_to_end_capture_rate_pct']['std']:.2f}%** [{d_val['end_to_end_capture_rate_pct']['ci_95_low']:.2f}%, {d_val['end_to_end_capture_rate_pct']['ci_95_high']:.2f}%]"
        pdet_str = f"**{d_val['post_detection_recall_pct']['mean']:.2f} $\\pm$ {d_val['post_detection_recall_pct']['std']:.2f}%** [{d_val['post_detection_recall_pct']['ci_95_low']:.2f}%, {d_val['post_detection_recall_pct']['ci_95_high']:.2f}%]"
        prec_str = f"{d_val['precision_pct']['mean']:.2f} $\\pm$ {d_val['precision_pct']['std']:.2f}%"
        fd_str = f"{d_val['false_dark_rate_pct']['mean']:.2f} $\\pm$ {d_val['false_dark_rate_pct']['std']:.2f}%"
        md_content += f"| **{d} / 10k km²** | {density_areas[d]:,.0f} km² | {N_PER_CELL * len(SEEDS):,} | {e2e_str} | {pdet_str} | {prec_str} | {fd_str} |\n"

    md_content += """
---

## 3. Time-Offset Sweep (Temporal Drift Window: ±5, ±15, ±30 min)

Evaluated across 20 independent seeds ($N = 500$ contacts/seed, $10,000$ total contacts per cell). Comparing dead-reckoning temporal propagation against unpropagated raw AIS pings:

| Time Window | WITH SOG/COG Dead-Reckoning (E2E Capture) | WITH Propagation (False-Dark Rate) | WITHOUT Propagation (E2E Capture) | WITHOUT Propagation (False-Dark Rate) | Operational Significance |
| :---: | :---: | :---: | :---: | :---: | :--- |
"""
    for tw in time_windows:
        k = f"pm_{int(tw)}_min"
        p_res = time_agg_prop[k]
        u_res = time_agg_unprop[k]
        p_e2e_str = f"**{p_res['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {p_res['end_to_end_capture_rate_pct']['std']:.2f}%** [{p_res['end_to_end_capture_rate_pct']['ci_95_low']:.2f}%, {p_res['end_to_end_capture_rate_pct']['ci_95_high']:.2f}%]"
        p_fd_str = f"{p_res['false_dark_rate_pct']['mean']:.2f} $\\pm$ {p_res['false_dark_rate_pct']['std']:.2f}%"
        u_e2e_str = f"{u_res['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {u_res['end_to_end_capture_rate_pct']['std']:.2f}%"
        u_fd_str = f"**{u_res['false_dark_rate_pct']['mean']:.2f} $\\pm$ {u_res['false_dark_rate_pct']['std']:.2f}%**"
        md_content += f"| **±{int(tw)} min** | {p_e2e_str} | {p_fd_str} | {u_e2e_str} | {u_fd_str} | Unpropagated pings drift out of tolerance, causing false alerts |\n"

    md_content += f"""
---

## 4. Stress Cases (AIS Gaps & Degraded Kinematics, 20 Seeds)

Evaluated across 20 independent seeds with $N = 500$ contacts per seed ($10,000$ total contacts per scenario):

| Stress Scenario | Operational Description | End-to-End Capture (Mean $\\pm$ Std [95% CI]) | Precision (Mean $\\pm$ Std) | False-Dark Rate (Mean $\\pm$ Std) |
| :--- | :--- | :---: | :---: | :---: |
| **Nominal Baseline** | Continuous AIS, valid SOG/COG, ±30 min | **{op_stats['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {op_stats['end_to_end_capture_rate_pct']['std']:.2f}%** [{op_stats['end_to_end_capture_rate_pct']['ci_95_low']:.2f}%, {op_stats['end_to_end_capture_rate_pct']['ci_95_high']:.2f}%] | **{op_stats['precision_pct']['mean']:.2f} $\\pm$ {op_stats['precision_pct']['std']:.2f}%** | **{op_stats['false_dark_rate_pct']['mean']:.2f} $\\pm$ {op_stats['false_dark_rate_pct']['std']:.2f}%** |
| **AIS Gaps (10% Missing)** | RF packet collisions / shadow loss of pings | **{stress_agg_gap['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {stress_agg_gap['end_to_end_capture_rate_pct']['std']:.2f}%** [{stress_agg_gap['end_to_end_capture_rate_pct']['ci_95_low']:.2f}%, {stress_agg_gap['end_to_end_capture_rate_pct']['ci_95_high']:.2f}%] | **{stress_agg_gap['precision_pct']['mean']:.2f} $\\pm$ {stress_agg_gap['precision_pct']['std']:.2f}%** | **{stress_agg_gap['false_dark_rate_pct']['mean']:.2f} $\\pm$ {stress_agg_gap['false_dark_rate_pct']['std']:.2f}%** |
| **Corrupted Kinematics (10%)** | Spoofed or erroneous SOG/COG | **{stress_agg_kin['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {stress_agg_kin['end_to_end_capture_rate_pct']['std']:.2f}%** [{stress_agg_kin['end_to_end_capture_rate_pct']['ci_95_low']:.2f}%, {stress_agg_kin['end_to_end_capture_rate_pct']['ci_95_high']:.2f}%] | **{stress_agg_kin['precision_pct']['mean']:.2f} $\\pm$ {stress_agg_kin['precision_pct']['std']:.2f}%** | **{stress_agg_kin['false_dark_rate_pct']['mean']:.2f} $\\pm$ {stress_agg_kin['false_dark_rate_pct']['std']:.2f}%** |

---

## 5. Matching Radius Sweep (20 Seeds)

| Matching Radius | End-to-End Capture (Mean $\\pm$ Std) | Post-Det Recall (Mean $\\pm$ Std) | Precision (Mean $\\pm$ Std) | False-Dark Rate (Mean $\\pm$ Std) |
| :---: | :---: | :---: | :---: | :---: |
"""
    for r in radii:
        r_res = baseline_agg_prop[f"{r:.1f}_km"]
        md_content += f"| **{r:.1f} km** | {r_res['end_to_end_capture_rate_pct']['mean']:.2f} $\\pm$ {r_res['end_to_end_capture_rate_pct']['std']:.2f}% | {r_res['post_detection_recall_pct']['mean']:.2f} $\\pm$ {r_res['post_detection_recall_pct']['std']:.2f}% | {r_res['precision_pct']['mean']:.2f} $\\pm$ {r_res['precision_pct']['std']:.2f}% | {r_res['false_dark_rate_pct']['mean']:.2f} $\\pm$ {r_res['false_dark_rate_pct']['std']:.2f}% |\n"

    md_content += "\n---\n"
    SUMMARY_MD.write_text(md_content, encoding="utf-8")
    print(f"[OK] Summary markdown saved to: {SUMMARY_MD}")


if __name__ == "__main__":
    main()
