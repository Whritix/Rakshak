import csv
from collections import defaultdict

mmsi_points = defaultdict(list)
with open('sentinal2/sentinel2_vessel_detections_pipev4_202604.csv', 'r') as f:
    r = csv.DictReader(f)
    for row in r:
        mmsi = row['mmsi'].strip()
        if mmsi and mmsi not in {'0', '1', '123456789', '200000000'}:
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                ts = row['detect_timestamp']
                spd = float(row['speed_kn_inferred']) if row['speed_kn_inferred'] else 10.0
                hdg = float(row['heading_deg_inferred']) if row['heading_deg_inferred'] else 0.0
                mmsi_points[mmsi].append({
                    'lat': lat, 'lon': lon, 'timestamp': ts, 'speed': spd, 'heading': hdg
                })
            except (ValueError, TypeError):
                continue

viable_tracks = {m: pts for m, pts in mmsi_points.items() if len(pts) >= 15}
print(f"Total viable real vessel trajectories with >=15 points: {len(viable_tracks)}")
for m in list(viable_tracks.keys())[:5]:
    print(f"MMSI: {m}, points: {len(viable_tracks[m])}, sample point: {viable_tracks[m][0]}")
