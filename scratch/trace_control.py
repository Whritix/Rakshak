import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios, evaluate_tracking_run
from backend.app.track_fusion import MultiTargetTrackFusion

sc = generate_scenarios(seed=42)['Control_Clean_NoClutter']
tracker = MultiTargetTrackFusion(ref_lat=18.9220, ref_lon=72.8346, association_method='hungarian')

for t in sc['time_steps']:
    m_list = sc['measurements'].get(t, [])
    tracks = tracker.process_cycle(t, m_list)
    if 24 <= t <= 36:
        print(f"t={t:4.1f}:")
        for x in tracks:
            print(f"  trk={x['track_id']} id={x.get('identity')} st={x['state']} vx={x['vx_mps']:.1f} vy={x['vy_mps']:.1f}")

res = evaluate_tracking_run(sc, method='hungarian')
print("Evaluation result:", res)
