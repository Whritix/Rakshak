"""
RAKSHAK C4ISR - YOLO11m Military Target Detection Training Pipeline
Optimized for NVIDIA GeForce RTX 4060 Laptop GPU (8GB VRAM)
Classes: 0: Vessel, 1: Aircraft, 2: Vehicle, 3: Infrastructure
"""
import os
import sys
import time
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
os.environ["YOLO_CONFIG_DIR"] = str(ROOT)

DATA_CONFIG = ROOT / "runs" / "xview_yolo" / "data.yaml"
BASE_WEIGHTS = ROOT / "yolo11m.pt"

def main():
    print("=" * 65)
    print("  RAKSHAK DEFENSE C4ISR - YOLO11m HIGH-PRECISION TRAINING")
    print("=" * 65)
    print(f"  Data Config:    {DATA_CONFIG}")
    print(f"  Base Model:     {BASE_WEIGHTS} (20.1M parameters)")
    print(f"  Target Classes: Vessel, Aircraft, Vehicle, Infrastructure")
    print(f"  Batch Size:     4 (AMP FP16, Tensor Cores enabled)")
    print(f"  Image Res:      640x640 tile slices")
    print(f"  Target Epochs:  25 (Patience: 8 epochs early stopping)")
    print("=" * 65)

    if not DATA_CONFIG.exists():
        print(f"ERROR: Missing dataset config at {DATA_CONFIG}", file=sys.stderr)
        sys.exit(1)
    if not BASE_WEIGHTS.exists():
        print(f"ERROR: Missing base model at {BASE_WEIGHTS}", file=sys.stderr)
        sys.exit(1)

    LAST_WEIGHTS = ROOT / "runs" / "train" / "xview_yolo11m_military" / "weights" / "last.pt"
    if LAST_WEIGHTS.exists():
        print(f"  Resuming from checkpoint: {LAST_WEIGHTS}")
        model = YOLO(str(LAST_WEIGHTS))
        start_time = time.time()
        results = model.train(resume=True)
    else:
        model = YOLO(str(BASE_WEIGHTS))
        start_time = time.time()
        results = model.train(
            data=str(DATA_CONFIG),
            epochs=25,
            imgsz=640,
            batch=4,
            device=0,
        workers=0,
        project=str(ROOT / "runs" / "train"),
        name="xview_yolo11m_military",
        exist_ok=True,
        patience=8,
        plots=True,
        save=True,
        amp=True,
        cos_lr=True,
        close_mosaic=5,
        verbose=True
    )

    elapsed_mins = round((time.time() - start_time) / 60, 2)
    print("=" * 65)
    print(f"  YOLO11m TRAINING COMPLETE in {elapsed_mins} minutes!")
    print(f"  Best Weights Saved: runs/train/xview_yolo11m_military/weights/best.pt")
    print("=" * 65)

if __name__ == "__main__":
    main()
