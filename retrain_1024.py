"""
RAKSHAK C4ISR - YOLO11m Improved Training Pipeline
RTX 4060 Laptop GPU (8GB VRAM)
Upgrades over initial run:
  - Pure resume handling without argument collision (ultralytics resume=True compatibility)
  - Optional --fresh flag for starting a new 1024x1024 50-epoch run
  - imgsz=1024 (was 640) => detects small satellite targets
  - batch=2 with AMP FP16 (safely fits within 8GB VRAM at 1024px)
  - workers=0 (Windows multiprocessing stability)
  - Augmentation: mosaic, flipud, fliplr, HSV jitter, rotation
  - Cosine LR decay with warmup
"""
import os
import sys
import time
import argparse
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
os.environ["YOLO_CONFIG_DIR"] = str(ROOT)

DATA_CONFIG = ROOT / "runs" / "xview_yolo" / "data.yaml"
LAST_WEIGHTS = ROOT / "runs" / "train" / "xview_yolo11m_military" / "weights" / "last.pt"
BASE_WEIGHTS = ROOT / "yolo11m.pt"

if not DATA_CONFIG.exists():
    print(f"ERROR: Missing dataset configuration at {DATA_CONFIG}", file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser(description="RAKSHAK YOLO11m Training Pipeline")
parser.add_argument("--fresh", action="store_true", help="Force fresh 1024px training from base model instead of resuming")
cli_args, _ = parser.parse_known_args()

# Decide whether to resume or start fresh
if LAST_WEIGHTS.exists() and not cli_args.fresh:
    print(f"\n[RESUME] Found existing training checkpoint at {LAST_WEIGHTS}")
    model = YOLO(str(LAST_WEIGHTS))
    resume = True
else:
    print(f"\n[FRESH] Starting fresh 1024px training from base model {BASE_WEIGHTS}")
    model = YOLO(str(BASE_WEIGHTS))
    resume = False

print("=" * 65)
print("  RAKSHAK - YOLO11m HIGH-PRECISION RETRAINING RUN")
print("=" * 65)
print(f"  Dataset:       {DATA_CONFIG}")
print(f"  Image size:    {'1024x1024' if not resume else 'Reading from args.yaml'}")
print(f"  Batch size:    {'2 (AMP FP16 on RTX 4060)' if not resume else 'Reading from args.yaml'}")
print(f"  Epochs target: {'50' if not resume else 'Resuming to configured target'}")
print(f"  Resume mode:   {resume}")
print("=" * 65)

t0 = time.time()

if resume:
    # Pure resume — no extra conflicting arguments passed.
    # Ultralytics reads hyperparameter state directly from args.yaml.
    results = model.train(resume=True)
else:
    results = model.train(
        data=str(DATA_CONFIG),
        epochs=50,
        imgsz=1024,
        batch=2,
        device=0,
        workers=0,  # Windows process stability
        project=str(ROOT / "runs" / "train"),
        name="xview_yolo11m_military",
        exist_ok=True,
        patience=10,
        plots=True,
        save=True,
        amp=True,
        cos_lr=True,
        close_mosaic=8,
        # Augmentations for satellite overhead imagery
        flipud=0.3,
        fliplr=0.5,
        degrees=15.0,  # Small angle rotation for aerial sensors
        scale=0.6,
        mosaic=1.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        # Loss weights tuned for imbalanced classes
        box=7.5,
        cls=0.5,
        dfl=1.5,
        # Regularization & learning rate
        weight_decay=0.0005,
        lr0=0.01,
        lrf=0.01,
    )

elapsed = (time.time() - t0) / 3600
print(f"\n[DONE] Training finished in {elapsed:.2f} hours")
print("Best checkpoint saved at: runs/train/xview_yolo11m_military/weights/best.pt")

# Display final best validation metrics
try:
    import csv
    csv_path = ROOT / "runs" / "train" / "xview_yolo11m_military" / "results.csv"
    if csv_path.exists():
        rows = list(csv.DictReader(open(csv_path)))
        if rows:
            best = max(rows, key=lambda r: float(r.get("metrics/mAP50(B)", 0) or 0))
            print("\n[BEST VALIDATION METRICS]")
            for k in ["epoch", "metrics/precision(B)", "metrics/recall(B)", "metrics/mAP50(B)", "metrics/mAP50-95(B)"]:
                if k in best:
                    print(f"  {k:35s}: {best[k]}")
except Exception as e:
    print(f"Could not parse results.csv: {e}")
