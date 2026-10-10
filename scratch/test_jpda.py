import numpy as np
import math

def solve_joint_events(track_indices, meas_indices, gating_matrix, likelihood_matrix, p_d=0.90, lambda_clutter=1e-5):
    """
    Enumerate all valid joint association events for a cluster of tracks and measurements.
    Returns: beta matrix of shape (len(track_indices), len(meas_indices) + 1)
             where column 0 is beta_0 (miss).
    """
    num_tracks = len(track_indices)
    num_meas = len(meas_indices)
    
    # Precompute miss likelihood per track
    p_miss = (1.0 - p_d) * lambda_clutter
    
    events = [] # list of (assignment_tuple, likelihood)
    
    # Recursive event enumeration
    # assignment: tuple of length num_tracks, where assignment[i] in {0, 1, ..., num_meas}
    # 0 = miss, m in {1, ..., num_meas} = measurement m-1
    def generate_events(t_idx, current_assign, used_meas, current_like):
        if t_idx == num_tracks:
            events.append((current_assign, current_like))
            return
        
        # Option 1: Track t_idx misses
        generate_events(t_idx + 1, current_assign + (0,), used_meas, current_like * p_miss)
        
        # Option 2: Track t_idx associates with measurement m
        for m in range(num_meas):
            if m not in used_meas and gating_matrix[t_idx, m]:
                l_tm = p_d * likelihood_matrix[t_idx, m]
                generate_events(t_idx + 1, current_assign + (m + 1,), used_meas | {m}, current_like * l_tm)
                
    generate_events(0, (), set(), 1.0)
    
    total_like = sum(like for _, like in events)
    if total_like <= 1e-30:
        # Fallback: all miss
        betas = np.zeros((num_tracks, num_meas + 1), dtype=float)
        betas[:, 0] = 1.0
        return betas
        
    betas = np.zeros((num_tracks, num_meas + 1), dtype=float)
    for assign, like in events:
        prob = like / total_like
        for t_idx, a in enumerate(assign):
            betas[t_idx, a] += prob
            
    return betas

print("JPDA function test:")
# 2 tracks, 2 measurements (crossing paths)
gating = np.array([[True, True], [True, True]])
likes = np.array([[0.8, 0.2], [0.2, 0.8]])
b = solve_joint_events([0, 1], [0, 1], gating, likes)
print("Betas (Track 0):", b[0])
print("Betas (Track 1):", b[1])
