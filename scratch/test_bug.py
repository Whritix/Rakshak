import sys
from pathlib import Path
ROOT = Path(r"c:\Users\awhri\OneDrive\Desktop\DEF")
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios
from backend.app.track_fusion import MultiTargetTrackFusion, geodetic_to_enu, TrackState, Track
import math
import numpy as np

scenarios = generate_scenarios(seed=42)

for sc_name, sc_data in scenarios.items():
    print("=" * 70)
    print("SCENARIO:", sc_name)
    time_steps = sc_data["time_steps"]
    ground_truth = sc_data["ground_truth"]
    measurements = sc_data["measurements"]
    gt_targets = len(set(g.gt_id for g in ground_truth))
    total_gt = len(ground_truth)

    gt_by_t = {}
    for g in ground_truth:
        gt_by_t.setdefault(g.t, []).append(g)

    # Let's test what happens if TENTATIVE tracks never coast
    # and duplicate track initiation is suppressed
    tracker = MultiTargetTrackFusion(18.922, 72.8346, association_method="hungarian")
    tracks_by_t = {}
    for t in time_steps:
        m_list = measurements.get(t, [])
        # Only evaluate confirmed and coasting tracks that were actually confirmed
        active_tracks = tracker.process_cycle(t, m_list)
        tracks_by_t[t] = {}
        for trk in active_tracks:
            # Check if track has been confirmed at least once
            tid = trk["track_id"]
            track_obj = tracker.tracks[tid]
            if trk["state"] in {"CONFIRMED", "COASTING"}:
                e, n, _ = geodetic_to_enu(trk["lat"], trk["lon"], 0.0, 18.922, 72.8346)
                tracks_by_t[t][trk["track_id"]] = (e, n)

    total_fn = 0
    total_fp = 0
    total_tp = 0
    total_id_switches = 0
    prev_gt_to_track = {}

    for t in time_steps:
        gts = gt_by_t.get(t, [])
        trks = tracks_by_t.get(t, {})
        num_gt = len(gts)
        num_tr = len(trks)
        if num_gt == 0 and num_tr == 0:
            continue
        if num_gt == 0:
            total_fp += num_tr
            continue
        if num_tr == 0:
            total_fn += num_gt
            continue

        trk_ids = list(trks.keys())
        dist_mat = np.zeros((num_gt, num_tr), dtype=float)
        for i, g in enumerate(gts):
            for j, tid in enumerate(trk_ids):
                te, tn = trks[tid]
                d = math.sqrt((g.east - te) ** 2 + (g.north - tn) ** 2)
                dist_mat[i, j] = d

        large_dist = 1e6
        cost_eval = np.where(dist_mat <= 80.0, dist_mat, large_dist)
        matched_pairs = []
        unmatched_gt = set(range(num_gt))
        unmatched_tr = set(range(num_tr))

        for _ in range(min(num_gt, num_tr)):
            min_val = np.min(cost_eval)
            if min_val >= large_dist:
                break
            r, c = np.unravel_index(np.argmin(cost_eval), cost_eval.shape)
            matched_pairs.append((r, c))
            unmatched_gt.discard(r)
            unmatched_tr.discard(c)
            cost_eval[r, :] = large_dist
            cost_eval[:, c] = large_dist

        total_tp += len(matched_pairs)
        total_fn += len(unmatched_gt)
        total_fp += len(unmatched_tr)

        for r, c in matched_pairs:
            g_id = gts[r].gt_id
            t_id = trk_ids[c]
            if g_id in prev_gt_to_track and prev_gt_to_track[g_id] != t_id:
                total_id_switches += 1
            prev_gt_to_track[g_id] = t_id

    mota = 1.0 - (total_fn + total_fp + total_id_switches) / max(total_gt, 1)
    print(f"MOTA: {mota*100:5.2f}% | TP: {total_tp} | FP: {total_fp} | FN: {total_fn} | IDSW: {total_id_switches} | Tracks created: {len(tracker.tracks)}")
