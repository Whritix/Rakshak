"""Export YOLO11 models to 1024x1024 static shape ONNX and prepare TensorRT export scripts."""
import os
import sys
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]

YOLO11M_PT = ROOT / "runs" / "train" / "xview_yolo11m_military" / "weights" / "best.pt"
VESSEL_PT = ROOT / "runs" / "train" / "xview_vessel_1024_extended" / "weights" / "best.pt"

def export_all():
    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — 1024x1024 STATIC SHAPE MODEL EXPORTER")
    print("=" * 70)

    # 1. Primary Model: xview_yolo11m_military
    if YOLO11M_PT.exists():
        print(f"\n[*] Exporting primary model {YOLO11M_PT.name} (1024x1024 static)...")
        m = YOLO(str(YOLO11M_PT))
        out1 = m.export(format="onnx", imgsz=1024, dynamic=False, simplify=False)
        print(f"    Exported to: {out1}")
        # Rename to best_1024.onnx if needed
        p1 = Path(out1)
        target1 = p1.parent / "best_1024.onnx"
        if p1.exists() and p1 != target1:
            if target1.exists():
                target1.unlink()
            import shutil
            shutil.copy2(p1, target1)
            print(f"    Target saved: {target1} ({target1.stat().st_size / (1024*1024):.2f} MB)")
    else:
        print(f"[!] Primary checkpoint not found at {YOLO11M_PT}")

    # 2. Vessel Specialist Model: xview_vessel_1024_extended
    if VESSEL_PT.exists():
        print(f"\n[*] Exporting vessel specialist {VESSEL_PT.name} (1024x1024 static)...")
        mv = YOLO(str(VESSEL_PT))
        out2 = mv.export(format="onnx", imgsz=1024, dynamic=False, simplify=False)
        print(f"    Exported to: {out2}")
        p2 = Path(out2)
        target2 = p2.parent / "best_1024.onnx"
        if p2.exists() and p2 != target2:
            if target2.exists():
                target2.unlink()
            import shutil
            shutil.copy2(p2, target2)
            print(f"    Target saved: {target2} ({target2.stat().st_size / (1024*1024):.2f} MB)")
    else:
        print(f"[!] Vessel checkpoint not found at {VESSEL_PT}")

if __name__ == "__main__":
    export_all()
