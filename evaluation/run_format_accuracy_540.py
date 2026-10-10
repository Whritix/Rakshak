"""Multi-Format Accuracy Evaluation on ALL 540 val_report Holdout Tiles.

Evaluates:
- Formats: PyTorch FP32, PyTorch FP16 (.half()), ONNX Runtime (CPU baseline)
- Models: Primary YOLO11m Military
- Dataset: All 540 val_report tiles (66,521 ground-truth instances)
- Reports per-class Precision, Recall, mAP@50, mAP@50-95, and GT counts.
"""
import os
import sys
import json
import time
from pathlib import Path
from collections import Counter
from typing import Dict, Any
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_YAML = ROOT / "evaluation" / "val_report_data.yaml"
OUTPUT_JSON = ROOT / "evaluation" / "results" / "format_accuracy_540_report.json"
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = {0: "Vessel", 1: "Aircraft", 2: "Vehicle", 3: "Infrastructure"}

def count_ground_truth() -> Dict[str, int]:
    manifest = ROOT / "evaluation" / "val_report_tiles.txt"
    labels_dir = ROOT / "runs" / "xview_yolo" / "labels" / "val"
    counts = Counter()
    with open(manifest) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stem = Path(line).stem
            lbl = labels_dir / f"{stem}.txt"
            if lbl.exists():
                for row in lbl.read_text().splitlines():
                    parts = row.strip().split()
                    if parts:
                        counts[int(parts[0])] += 1
    return {
        "Vessel": counts[0],
        "Aircraft": counts[1],
        "Vehicle": counts[2],
        "Infrastructure": counts[3],
        "total": sum(counts.values())
    }

def extract_metrics(res) -> Dict[str, Any]:
    box = res.box
    # Ultralytics maps array gives per-class mAP50-95
    # Per-class P, R, mAP50 are in box.p, box.r, box.ap50 (or box.class_result(i))
    overall = {
        "precision": round(float(box.p.mean() if hasattr(box.p, 'mean') else box.p[0]), 4),
        "recall": round(float(box.r.mean() if hasattr(box.r, 'mean') else box.r[0]), 4),
        "map50": round(float(box.map50), 4),
        "map50_95": round(float(box.map), 4)
    }
    
    per_class = {}
    for i, name in CLASS_NAMES.items():
        try:
            # box.class_result(i) returns (p, r, ap50, ap)
            c_p, c_r, c_ap50, c_ap = box.class_result(i)
            per_class[name] = {
                "precision": round(float(c_p), 4),
                "recall": round(float(c_r), 4),
                "map50": round(float(c_ap50), 4),
                "map50_95": round(float(c_ap), 4)
            }
        except Exception:
            per_class[name] = {
                "precision": round(float(box.p[i]), 4) if i < len(box.p) else 0.0,
                "recall": round(float(box.r[i]), 4) if i < len(box.r) else 0.0,
                "map50": round(float(box.ap50[i]), 4) if hasattr(box, 'ap50') and i < len(box.ap50) else 0.0,
                "map50_95": round(float(box.maps[i]), 4) if i < len(box.maps) else 0.0
            }

    return {"overall": overall, "per_class": per_class}

def main():
    print("=" * 70)
    print("  MULTI-FORMAT ACCURACY EVALUATION — ALL 540 VAL_REPORT TILES")
    print("=" * 70)
    gt_counts = count_ground_truth()
    print(f"Ground Truth Target Counts (540 tiles): {gt_counts}")

    results = {
        "eval_manifest": "evaluation/val_report_tiles.txt",
        "tiles_evaluated": 540,
        "ground_truth_counts": gt_counts,
        "formats": {}
    }

    # 1. PyTorch FP32
    print("\n[*] Evaluating Format 1: PyTorch FP32 on CUDA (batch=8)...")
    t0 = time.time()
    m_fp32 = YOLO("runs/train/xview_yolo11m_military/weights/best.pt")
    res_fp32 = m_fp32.val(data=str(DATA_YAML), imgsz=1024, batch=8, device=0, half=False, workers=0, plots=False)
    t_fp32 = round(time.time() - t0, 2)
    results["formats"]["pytorch_fp32"] = {
        "format": "PyTorch FP32",
        "eval_time_seconds": t_fp32,
        **extract_metrics(res_fp32)
    }
    print(f"    PyTorch FP32 Overall: mAP50={results['formats']['pytorch_fp32']['overall']['map50']} in {t_fp32}s")

    # 2. PyTorch FP16 (.half())
    print("\n[*] Evaluating Format 2: PyTorch FP16 (.half()) on CUDA (batch=8)...")
    t0 = time.time()
    m_fp16 = YOLO("runs/train/xview_yolo11m_military/weights/best.pt")
    res_fp16 = m_fp16.val(data=str(DATA_YAML), imgsz=1024, batch=8, device=0, half=True, workers=0, plots=False)
    t_fp16 = round(time.time() - t0, 2)
    results["formats"]["pytorch_fp16_half"] = {
        "format": "PyTorch FP16 (.half())",
        "eval_time_seconds": t_fp16,
        **extract_metrics(res_fp16)
    }
    print(f"    PyTorch FP16 Overall: mAP50={results['formats']['pytorch_fp16_half']['overall']['map50']} in {t_fp16}s")

    # 3. ONNX Runtime (CPU baseline)
    print("\n[*] Evaluating Format 3: ONNX Runtime Static 1024x1024 on CPU (batch=1)...")
    t0 = time.time()
    m_onnx = YOLO("runs/train/xview_yolo11m_military/weights/best_1024.onnx")
    res_onnx = m_onnx.val(data=str(DATA_YAML), imgsz=1024, batch=1, device="cpu", workers=0, plots=False)
    t_onnx = round(time.time() - t0, 2)
    results["formats"]["onnx_runtime_cpu"] = {
        "format": "ONNX Runtime (CPU baseline)",
        "eval_time_seconds": t_onnx,
        **extract_metrics(res_onnx)
    }
    print(f"    ONNX Runtime Overall: mAP50={results['formats']['onnx_runtime_cpu']['overall']['map50']} in {t_onnx}s")

    OUTPUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n[+] Saved full 540-tile multi-format report to: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
