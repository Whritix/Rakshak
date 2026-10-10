import re, random, shutil
from pathlib import Path
import yaml
from ultralytics import YOLO

ROOT = Path('.').resolve()

def main():
    def extract_scenes(folder):
        scenes = set()
        if not folder.exists(): return scenes
        for p in folder.glob('*.*'):
            m = re.match(r'^([0-9]+)_', p.name)
            if m: scenes.add(m.group(1))
        return scenes

    yt = extract_scenes(ROOT / 'runs' / 'xview_yolo' / 'images' / 'train')
    yv = extract_scenes(ROOT / 'runs' / 'xview_yolo' / 'images' / 'val')
    vt = extract_scenes(ROOT / 'runs' / 'xview_vessel' / 'images' / 'train')
    vv = extract_scenes(ROOT / 'runs' / 'xview_vessel' / 'images' / 'val')
    pure_val = sorted(list(yv.union(vv) - yt.union(vt)), key=lambda x: int(x))
    rng = random.Random(42)
    shuffled = list(pure_val)
    rng.shuffle(shuffled)
    val_report = set(shuffled[37:])

    val_labels_dir = ROOT / 'runs' / 'xview_yolo' / 'labels' / 'val'
    val_images_dir = ROOT / 'runs' / 'xview_yolo' / 'images' / 'val'

    vessel_eval_dir = ROOT / 'evaluation' / 'vessel_head_to_head'
    vessel_lbl_dir = vessel_eval_dir / 'labels'
    vessel_img_dir = vessel_eval_dir / 'images'
    vessel_lbl_dir.mkdir(parents=True, exist_ok=True)
    vessel_img_dir.mkdir(parents=True, exist_ok=True)

    vessel_tiles = []
    gt_vessels = 0
    for img_p in sorted(list(val_images_dir.glob('*.jpg'))):
        m = re.match(r'^([0-9]+)_', img_p.name)
        if m and m.group(1) in val_report:
            lbl_p = val_labels_dir / (img_p.stem + '.txt')
            vessel_lines = []
            if lbl_p.exists():
                for line in lbl_p.read_text().splitlines():
                    parts = line.strip().split()
                    if parts and int(parts[0]) == 0:
                        coords = " ".join(parts[1:])
                        vessel_lines.append(f"0 {coords}")
            if vessel_lines:
                vessel_tiles.append(str(img_p).replace('\\', '/'))
                gt_vessels += len(vessel_lines)
                (vessel_lbl_dir / (img_p.stem + '.txt')).write_text('\n'.join(vessel_lines))
                dst_img = vessel_img_dir / img_p.name
                if not dst_img.exists():
                    shutil.copy2(img_p, dst_img)

    print(f'Vessel tiles: {len(vessel_tiles)}, GT vessels: {gt_vessels}')

    v_cfg = {
        'path': str(vessel_eval_dir).replace('\\', '/'),
        'train': 'images',
        'val': 'images',
        'names': {0: 'Vessel'}
    }
    v_cfg_path = vessel_eval_dir / 'vessel_eval.yaml'
    with open(v_cfg_path, 'w') as f:
        yaml.dump(v_cfg, f)

    # 1. Primary Model (YOLO11m) on Vessel Only
    m_prim = YOLO('runs/train/xview_yolo11m_military/weights/best.pt')
    res_prim = m_prim.val(data=str(v_cfg_path), imgsz=1024, batch=4, device=0, workers=0, plots=False)
    p_map50 = float(res_prim.box.map50)
    p_prec = float(res_prim.box.p.mean()) if hasattr(res_prim.box.p, 'mean') else float(res_prim.box.p[0])
    p_rec = float(res_prim.box.r.mean()) if hasattr(res_prim.box.r, 'mean') else float(res_prim.box.r[0])
    print(f'PRIMARY YOLO11m: mAP50={p_map50:.4f}, Precision={p_prec:.4f}, Recall={p_rec:.4f}')

    # 2. Specialist Model (YOLO11n vessel) on Vessel Only
    m_spec = YOLO('runs/train/xview_vessel_1024_extended/weights/best.pt')
    res_spec = m_spec.val(data=str(v_cfg_path), imgsz=1024, batch=4, device=0, workers=0, plots=False)
    s_map50 = float(res_spec.box.map50)
    s_prec = float(res_spec.box.p.mean()) if hasattr(res_spec.box.p, 'mean') else float(res_spec.box.p[0])
    s_rec = float(res_spec.box.r.mean()) if hasattr(res_spec.box.r, 'mean') else float(res_spec.box.r[0])
    print(f'SPECIALIST YOLO11n: mAP50={s_map50:.4f}, Precision={s_prec:.4f}, Recall={s_rec:.4f}')

if __name__ == '__main__':
    main()
