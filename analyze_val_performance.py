"""Validate YOLO11m and report per-class precision, recall, mAP50, and F1.

Runs validation on the 1,068 val images in runs/xview_yolo/data.yaml using
the best checkpoint, formats a tactical per-class evaluation table, saves
metrics to JSON, and flags the lowest-performing class for targeted retraining.
"""
import sys
import json
import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = ROOT / 'runs' / 'train' / 'xview_yolo11m_military' / 'weights' / 'best.pt'
DATA = ROOT / 'runs' / 'xview_yolo' / 'data.yaml'
OUT_DIR = ROOT / 'runs' / 'train' / 'xview_yolo11m_military'


def analyze_validation(weights_path: Path, conf: float = 0.25, iou: float = 0.50, imgsz: int = 1024):
    if not weights_path.exists():
        print(f"ERROR: Model checkpoint not found at {weights_path}", file=sys.stderr)
        sys.exit(1)
    if not DATA.exists():
        print(f"ERROR: Dataset config not found at {DATA}", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — TACTICAL VALIDATION ANALYSIS")
    print("=" * 70)
    print(f"  Model checkpoint : {weights_path}")
    print(f"  Dataset config   : {DATA}")
    print(f"  Input resolution : {imgsz}x{imgsz}")
    print(f"  Eval confidence  : {conf}")
    print(f"  IoU threshold    : {iou}")
    print("=" * 70)

    model = YOLO(str(weights_path))
    metrics = model.val(
        data=str(DATA),
        imgsz=imgsz,
        conf=conf,         # Lower threshold = higher sensitivity for rare classes
        iou=iou,
        plots=True,
        save_json=False,
        project=str(OUT_DIR),
        name='val_analysis',
        exist_ok=True,
        workers=0
    )

    class_names = ['Vessel', 'Aircraft', 'Vehicle', 'Infrastructure']
    print('\n' + '=' * 70)
    print('  PER-CLASS VALIDATION PERFORMANCE BREAKDOWN')
    print('=' * 70)
    print(f"  {'Class':<20} {'Precision':>10} {'Recall':>10} {'mAP50':>10} {'F1-Score':>10}")
    print('-' * 70)

    results_dict = {}
    lowest_f1_class = None
    lowest_f1_val = 1.0

    for i, name in enumerate(class_names):
        try:
            p = float(metrics.box.p[i])
            r = float(metrics.box.r[i])
            m = float(metrics.box.ap50[i])
            f1 = (2 * p * r) / (p + r + 1e-8)
            print(f"  {name:<20} {p:>10.4f} {r:>10.4f} {m:>10.4f} {f1:>10.4f}")
            results_dict[name] = {
                'precision': round(p, 4),
                'recall': round(r, 4),
                'mAP50': round(m, 4),
                'F1': round(f1, 4)
            }
            if f1 < lowest_f1_val:
                lowest_f1_val = f1
                lowest_f1_class = name
        except (IndexError, AttributeError):
            print(f"  {name:<20}  (no instances or unindexed)")

    print('=' * 70)
    print(f"  Overall mAP@50     : {metrics.box.map50:.4f}")
    print(f"  Overall mAP@50-95  : {metrics.box.map:.4f}")
    if lowest_f1_class:
        print(f"  Priority Retrain   : {lowest_f1_class} (Lowest F1: {lowest_f1_val:.4f})")
    print('=' * 70)

    out_file = OUT_DIR / 'per_class_metrics.json'
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            'overall_mAP50': round(float(metrics.box.map50), 4),
            'overall_mAP50_95': round(float(metrics.box.map), 4),
            'per_class': results_dict,
            'lowest_f1_class': lowest_f1_class
        }, f, indent=2)

    print(f"\n[SAVED] Per-class metrics persisted to: {out_file}")

    # Copy confusion matrix image
    try:
        import shutil
        val_run_dir = OUT_DIR / 'val_analysis'
        cm_src = val_run_dir / 'confusion_matrix.png'
        if not cm_src.exists():
            cm_src = val_run_dir / 'confusion_matrix_normalized.png'
        if cm_src.exists():
            cm_dst = OUT_DIR / 'confusion_matrix_val.png'
            shutil.copy(cm_src, cm_dst)
            print(f"[SAVED] Confusion matrix saved to: {cm_dst}")
    except Exception as e:
        print(f"Notice: Confusion matrix copy note: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate YOLO11m per-class validation metrics")
    parser.add_argument('--weights', type=str, default=str(DEFAULT_MODEL), help="Path to weights file")
    parser.add_argument('--conf', type=float, default=0.25, help="Confidence threshold")
    parser.add_argument('--iou', type=float, default=0.50, help="IoU threshold")
    parser.add_argument('--imgsz', type=int, default=1024, help="Image resolution")
    args = parser.parse_args()

    analyze_validation(
        weights_path=Path(args.weights),
        conf=args.conf,
        iou=args.iou,
        imgsz=args.imgsz
    )
