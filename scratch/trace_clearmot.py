import sys
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios
from backend.app.track_fusion import MultiTargetTrackFusion, geodetic_to_enu
import numpy as np

sc = generate_scenarios(seed=42)['Control_Clean_NoClutter']
tracker = MultiTargetTrackFusion(ref_lat=18.9220, ref_lon=72.8346, association_method='hungarian')

gt_by_t = {}
for g in sc['ground_truth']:
    gt_by_t.setdefault(g.t, []).append(g)

prev_gt_to_track = {}
total_idsw = 0

for t in sc['time_steps']:
    m_list = sc['measurements'].get(t, [])
    active = tracker.process_cycle(t, m_list)
    trks = {}
    for trk in active:
        if trk["state"] in {"CONFIRMED", "COASTING"}:
            e, n, _ = geodetic_to_enu(trk["lat"], trk["lon"], 0.0, 18.9220, 72.8346)
            trks[trk["track_id"]] = (e, n)
    
    gts = gt_by_t.get(t, [])
    trk_ids = list(trks.keys())
    if not gts or not trk_ids:
        continue
    
    dist_mat = np.zeros((len(gts), len(trk_ids)), dtype=float)
    for i, g in enumerate(gts):
        for j, tid in enumerate(trk_ids):
            te, tn = trks[tid]
            d = math.sqrt((g.east - te) ** 2 + (g.north - tn) ** 2)
            dist_mat[i, j] = d
            
    # Greedy matching in evaluate_tracking_run:
    cost_eval = dist_mat.copy()
    matched = []
    for _ in range(min(len(gts), len(trk_ids))):
        r, c = np.unravel_index(np.argmin(cost_eval), cost_eval.shape)
        matched.append((gts[r].gt_id, trk_ids[c], dist_mat[r, c]))
        cost_eval[r, :] = 1e6
        cost_eval[:, c] = 1e6
        
    for gid, tid, d in matched:
        sw = False
        if gid in prev_gt_to_track and prev_gt_to_track[gid] != tid:
            sw = True
            total_idsw += 1
            print(f"t={t:4.1f}: ID SWITCH for {gid}! Was {prev_gt_to_track[gid]}, now {tid}. dist={d:.2f}")
        prev_gt_to_track[gid] = tid

print(f"Total ID switches computed by CLEAR-MOT: {total_idsw}")
