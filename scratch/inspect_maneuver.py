import sys
from pathlib import Path
ROOT = Path(r"c:\Users\awhri\OneDrive\Desktop\DEF")
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios
from backend.app.track_fusion import MultiTargetTrackFusion

scenarios = generate_scenarios(seed=42)
sc = scenarios["Maneuvering_Tactical_Vessel"]

tr = MultiTargetTrackFusion(18.922, 72.8346, association_method="jpda")
for t in sc["time_steps"]:
    meas = sc["measurements"].get(t, [])
    active = tr.process_cycle(t, meas)
    if meas:
        print(f"t={t:4.1f}s: meas={len(meas)}, active_tracks={[t['track_id'] for t in active]}, states={[t['state'] for t in active]}")
        # check misses
        for tid, trk in tr.tracks.items():
            print(f"   {tid}: state={trk.state_lifecycle}, consec_misses={trk.consecutive_misses}, hit_hist={trk.hit_history[-5:]}")
