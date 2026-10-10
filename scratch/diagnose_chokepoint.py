import sys
import math
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios, evaluate_tracking_run
from backend.app.track_fusion import MultiTargetTrackFusion, geodetic_to_enu

sc = generate_scenarios(seed=42)['High_Density_Chokepoint']
time_steps = sc['time_steps']
ground_truth = sc['ground_truth']
measurements = sc['measurements']

gt_by_t = defaultdict(list)
for g in ground_truth:
    gt_by_t[g.t].append(g)

for method in ['nn', 'hungarian', 'jpda']:
    tracker = MultiTargetTrackFusion(
        ref_lat=18.9220, ref_lon=72.8346,
        association_method=method,
        m_confirm_hits=3,
        n_confirm_window=5,
        max_misses_deletion=5
    )
    
    spawned_per_cycle = []
    tracks_by_t = {}
    track_states_at_t = {} # t -> {tid: state}
    
    for t in time_steps:
        prev_tids = set(tracker.tracks.keys())
        m_list = measurements.get(t, [])
        active_tracks = tracker.process_cycle(t, m_list)
        new_tids = set(tracker.tracks.keys()) - prev_tids
        spawned_per_cycle.append(len(new_tids))
        
        tracks_by_t[t] = {}
        track_states_at_t[t] = {}
        for trk in active_tracks:
            if trk["state"] in {"CONFIRMED", "COASTING"}:
                e, n, _ = geodetic_to_enu(trk["lat"], trk["lon"], 0.0, 18.9220, 72.8346)
                tracks_by_t[t][trk["track_id"]] = (e, n)
                track_states_at_t[t][trk["track_id"]] = trk["state"]

    # Now evaluate CLEAR-MOT matching with breakdown
    total_gt = 0
    total_fn = 0
    fp_confirmed = 0
    fp_coasting = 0
    id_switches = 0
    total_tp = 0
    prev_matches = {}
    
    distance_threshold_m = 80.0
    
    for t in time_steps:
        gts = gt_by_t.get(t, [])
        trks = tracks_by_t.get(t, {})
        states = track_states_at_t.get(t, {})
        num_gt = len(gts)
        num_tr = len(trks)
        total_gt += num_gt
        
        if num_gt == 0 and num_tr == 0:
            continue
        if num_gt == 0:
            for tid in trks:
                if states[tid] == "CONFIRMED":
                    fp_confirmed += 1
                else:
                    fp_coasting += 1
            continue
        if num_tr == 0:
            total_fn += num_gt
            continue
            
        trk_ids = list(trks.keys())
        dist_mat = np.zeros((num_gt, num_tr), dtype=float)
        for i, g in enumerate(gts):
            for j, tid in enumerate(trk_ids):
                te, tn = trks[tid]
                dist_mat[i, j] = math.sqrt((g.east - te)**2 + (g.north - tn)**2)
                
        large_dist = 1e6
        cost_eval = np.where(dist_mat <= distance_threshold_m, dist_mat, large_dist)
        
        matched_pairs = []
        unmatched_gt = set(range(num_gt))
        unmatched_tr = set(range(num_tr))
        
        # Preserve previous matches
        for r, g in enumerate(gts):
            if g.gt_id in prev_matches:
                prior_tid = prev_matches[g.gt_id]
                if prior_tid in trk_ids:
                    c = trk_ids.index(prior_tid)
                    if c in unmatched_tr and dist_mat[r, c] <= distance_threshold_m:
                        matched_pairs.append((r, c))
                        unmatched_gt.discard(r)
                        unmatched_tr.discard(c)
                        cost_eval[r, :] = large_dist
                        cost_eval[:, c] = large_dist
                        
        for _ in range(min(len(unmatched_gt), len(unmatched_tr))):
            min_val = np.min(cost_eval)
            if min_val >= large_dist:
                break
            r, c = np.unravel_index(np.argmin(cost_eval), cost_eval.shape)
            matched_pairs.append((r, c))
            unmatched_gt.discard(r)
            unmatched_tr.discard(c)
            cost_eval[r, :] = large_dist
            cost_eval[:, c] = large_dist
            
        total_fn += len(unmatched_gt)
        for c in unmatched_tr:
            tid = trk_ids[c]
            if states[tid] == "CONFIRMED":
                fp_confirmed += 1
            else:
                fp_coasting += 1
                
        current_matches = {}
        for r, c in matched_pairs:
            gid = gts[r].gt_id
            tid = trk_ids[c]
            total_tp += 1
            if gid in prev_matches and prev_matches[gid] != tid:
                id_switches += 1
            current_matches[gid] = tid
        prev_matches = current_matches
        
    tot_fp = fp_confirmed + fp_coasting
    mota = 1.0 - (total_fn + tot_fp + id_switches) / max(total_gt, 1)
    
    print(f"=== {method.upper()} ===")
    print(f"  Tracks Created Total: {len(tracker.tracks)}")
    print(f"  Tentative Spawned / Cycle: mean={np.mean(spawned_per_cycle):.2f}, max={max(spawned_per_cycle)}, min={min(spawned_per_cycle)}")
    print(f"  Total TP: {total_tp} / GT={total_gt}")
    print(f"  Total FN: {total_fn}")
    print(f"  Total FP: {tot_fp} (CONFIRMED={fp_confirmed}, COASTING={fp_coasting})")
    print(f"  ID Switches: {id_switches}")
    print(f"  MOTA: {mota*100:.2f}%\n")
