import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.track_sim import generate_scenarios
from backend.app.track_fusion import MultiTargetTrackFusion

sc = generate_scenarios(seed=42)['High_Density_Chokepoint']

for method in ['hungarian', 'jpda']:
    tracker = MultiTargetTrackFusion(
        ref_lat=18.9220, ref_lon=72.8346,
        association_method=method,
        m_confirm_hits=3,
        n_confirm_window=5,
        max_misses_deletion=5
    )
    for t in sc['time_steps']:
        tracker.process_cycle(t, sc['measurements'].get(t, []))
        
    print(f"=== {method.upper()} TRACKS ===")
    for tid, trk in tracker.tracks.items():
        print(f"  {tid}: state={trk.state_lifecycle.name}, updates={trk.total_updates}, misses={trk.consecutive_misses}, hits_hist={trk.hit_history}, class={trk.target_class}, id={trk.identity}")
