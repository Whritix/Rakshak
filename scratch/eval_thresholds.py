import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios, evaluate_tracking_run

scs = generate_scenarios(seed=42)
methods = ['nn', 'hungarian', 'jpda']
thresholds = [30.0, 80.0]

for thresh in thresholds:
    print(f"\n=======================================================")
    print(f"  MATCHING DISTANCE THRESHOLD: {thresh} METERS (SIMULATED)")
    print(f"=======================================================")
    for sc_name, sc_data in scs.items():
        print(f"\n[{sc_name}]")
        for m in methods:
            r = evaluate_tracking_run(sc_data, method=m, distance_threshold_m=thresh)
            print(f"  {m.upper():<9} MOTA: {r['mota_pct']:>5.1f}% | IDSW: {r['id_switch_count']:>2} | IDF1: {r['idf1_pct']:>5.1f}% | TP: {r['total_matched_points']:>3} | FP: {r['false_positives']:>2} | FN: {r['false_negatives']:>2} | MOTP: {r['motp_m']:>4.1f}m")
