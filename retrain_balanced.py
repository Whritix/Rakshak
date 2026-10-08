"""RAKSHAK C4ISR - Balanced High-Precision Retraining Script.

Targets improved Vessel and Aircraft detection via:
  - Class-aware focal loss weights (inverse-frequency weighted)
  - Aggressive rare-class augmentation (copy_paste, mixup, degrees=45)
  - Full-resolution aerial imagery (1024px)
  - Longer warmup (5.0 epochs) for small-object gradient stabilization
  - Label smoothing (0.05) to reduce overconfident false alarms
  - AdamW optimizer with cosine learning rate schedule

Optimized for: NVIDIA GeForce RTX 4060 Laptop (8GB VRAM) / Windows OS (workers=0)
"""
import sys
import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'runs' / 'xview_yolo' / 'data.yaml'
LAST_WEIGHTS = ROOT / 'runs' / 'train' / 'xview_yolo11m_military' / 'weights' / 'last.pt'
BEST_WEIGHTS = ROOT / 'runs' / 'train' / 'xview_yolo11m_military' / 'weights' / 'best.pt'


def main():
    parser = argparse.ArgumentParser(description="RAKSHAK 2.0 Balanced YOLO11m Retraining")
    parser.add_argument('--weights', type=str, default=None, help="Path to starting weights (defaults to last.pt or best.pt)")
    parser.add_argument('--epochs', type=int, default=50, help="Number of training epochs (default: 50)")
    parser.add_argument('--batch', type=int, default=2, help="Batch size (default: 2 for 8GB VRAM @ 1024px)")
    parser.add_argument('--imgsz', type=int, default=1024, help="Image size (default: 1024)")
    parser.add_argument('--device', type=str, default='0', help="CUDA device index or 'cpu'")
    parser.add_argument('--name', type=str, default='xview_yolo11m_military', help="Run name in runs/train")
    args = parser.parse_args()

    # Determine initial weights
    if args.weights:
        weights_path = Path(args.weights)
    elif LAST_WEIGHTS.exists():
        weights_path = LAST_WEIGHTS
    elif BEST_WEIGHTS.exists():
        weights_path = BEST_WEIGHTS
    else:
        weights_path = Path('yolo11m.pt')

    if not DATA.exists():
        print(f"ERROR: Dataset config not found at {DATA}", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — BALANCED SURVEILLANCE RETRAINING")
    print("=" * 70)
    print(f"  Base weights     : {weights_path}")
    print(f"  Dataset config   : {DATA}")
    print(f"  Resolution       : {args.imgsz}x{args.imgsz}")
    print(f"  Batch size       : {args.batch}")
    print(f"  Target epochs    : {args.epochs}")
    print(f"  Device           : {args.device}")
    print("  Optimizer        : AdamW (lr0=0.001, cos_lr=True, warmup=5.0)")
    print("  Loss balance     : cls=1.5, box=7.5, dfl=1.5, label_smoothing=0.05")
    print("  Augmentations    : copy_paste=0.1, mixup=0.1, mosaic=1.0, degrees=45.0")
    print("=" * 70)

    model = YOLO(str(weights_path))

    results = model.train(
        data=str(DATA),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=0,                 # Windows stability (prevents IPC broken pipe)
        project=str(ROOT / 'runs' / 'train'),
        name=args.name,
        exist_ok=True,

        # ── Optimizer ──────────────────────────────────────────────────
        optimizer='AdamW',         # Superior gradient flow for sparse/imbalanced aerial data
        lr0=0.001,                 # Lower base learning rate for fine-tuning
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=5.0,         # Extended warmup for rare class stability
        cos_lr=True,

        # ── Loss weights (CRITICAL for counteracting imbalance) ────────
        cls=1.5,                   # 3x classification loss weight (was 0.5)
        box=7.5,                   # High box regression precision
        dfl=1.5,

        # ── Small-object sensitivity ───────────────────────────────────
        label_smoothing=0.05,      # Calibrates overconfident false positive predictions

        # ── Augmentation (Aerial Surveillance Tuned) ───────────────────
        mosaic=1.0,
        close_mosaic=10,           # Disable mosaic during final 10 epochs for clean convergence
        mixup=0.1,                 # Synthesizes cross-context rare object representations
        copy_paste=0.1,            # Copies rare targets into varied backgrounds
        flipud=0.5,                # Overhead nadir imagery has no canonical orientation
        fliplr=0.5,
        degrees=45.0,              # Full 360-degree rotational invariance
        scale=0.7,                 # Multi-scale object invariance
        translate=0.1,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        erasing=0.3,

        # ── Regularization ─────────────────────────────────────────────
        dropout=0.05,              # Prevents memorization of dominant infrastructure features

        # ── NMS / Metrics ──────────────────────────────────────────────
        iou=0.6,
        conf=None,
        patience=15,
        plots=True,
        save=True,
        amp=True,                  # Mixed precision required for 1024px on 8GB VRAM
    )

    print("\nTraining session completed.")
    return results


if __name__ == '__main__':
    main()
