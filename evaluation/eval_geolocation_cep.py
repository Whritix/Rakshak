"""Empirical Geolocation Circular Error Probable (CEP) Evaluation.

Task B: Evaluates center localisation error in meters in a local UTM CRS
against the xView dataset's GeoTIFF georeferencing on the held-out val_report partition.

Matches YOLO11m detections to ground-truth bounding boxes at:
1. IoU >= 0.3 (broad candidate match)
2. IoU >= 0.5 (strict tight match)

Reports:
- CEP50, CEP90, Mean error, RMSE, matched counts, and % of ground truth matched per class
- Explicit disclosure that CEP is conditional on a bounding box match
- Sensitivity to 0.5, 1.0, and 2.0 px registration offsets
"""
from __future__ import annotations

import json
import math
import sys
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import rasterio
from rasterio.warp import transform as warp_transform
from rasterio.crs import CRS

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from ultralytics import YOLO

VAL_TILES_PATH = ROOT / "evaluation" / "val_report_tiles.txt"
MODEL_PATH = ROOT / "runs" / "train" / "xview_yolo11m_military" / "weights" / "best.pt"
LABELS_DIR = ROOT / "runs" / "xview_yolo" / "labels" / "val"
TRAIN_IMAGES_DIR = ROOT / "train_images" / "train_images"
VAL_IMAGES_DIR = ROOT / "val_images" / "val_images"

RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_JSON = RESULTS_DIR / "geolocation_cep_report.json"
SUMMARY_MD = RESULTS_DIR / "geolocation_cep_summary.md"

CLASS_NAMES = {
    0: "Vessel",
    1: "Aircraft",
    2: "Vehicle",
    3: "Infrastructure"
}


def get_utm_epsg(lon: float, lat: float) -> int:
    """Calculate UTM EPSG code from longitude and latitude."""
    zone = int((lon + 180.0) / 6.0) + 1
    return 32600 + zone if lat >= 0 else 32700 + zone


def box_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """Calculate Intersection over Union (IoU) of two boxes in xyxy format."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def match_boxes_class_aware(
    dt_boxes: List[Dict[str, Any]],
    gt_boxes: List[Dict[str, Any]],
    iou_threshold: float = 0.3
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Greedy one-to-one, class-aware matching between detections and ground truth."""
    matches = []
    if not dt_boxes or not gt_boxes:
        return matches

    for cls_id in CLASS_NAMES.keys():
        cls_dts = [d for d in dt_boxes if d["cls"] == cls_id]
        cls_gts = [g for g in gt_boxes if g["cls"] == cls_id]
        if not cls_dts or not cls_gts:
            continue

        cls_dts = sorted(cls_dts, key=lambda d: d.get("conf", 0.0), reverse=True)
        matched_gt_indices = set()

        for dt in cls_dts:
            best_iou = 0.0
            best_gt_idx = -1
            dt_box = dt["bbox_xyxy"]

            for idx, gt in enumerate(cls_gts):
                if idx in matched_gt_indices:
                    continue
                iou = box_iou(dt_box, gt["bbox_xyxy"])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = idx

            if best_iou >= iou_threshold and best_gt_idx >= 0:
                matched_gt_indices.add(best_gt_idx)
                matches.append((dt, cls_gts[best_gt_idx]))

    return matches


def find_scene_geotiff(scene_id: str) -> Optional[Path]:
    """Locate the full GeoTIFF scene file."""
    for base_dir in [TRAIN_IMAGES_DIR, VAL_IMAGES_DIR]:
        candidate = base_dir / f"{scene_id}.tif"
        if candidate.exists():
            return candidate
    matches = list(ROOT.glob(f"**/{scene_id}.tif"))
    if matches:
        return matches[0]
    return None


def run_cep_evaluation():
    print("=" * 70)
    print("PROJECT RAKSHAK 2.0 — TASK B: DUAL-IOU GEOLOCATION CEP BENCHMARK")
    print("=" * 70)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {MODEL_PATH}")
    if not VAL_TILES_PATH.exists():
        raise FileNotFoundError(f"Validation tiles list not found at: {VAL_TILES_PATH}")

    tiles = [p.strip() for p in VAL_TILES_PATH.read_text(encoding="utf-8").splitlines() if p.strip()]
    print(f"\n[1/4] Loaded {len(tiles)} tiles from held-out val_report partition.")

    # Pre-cache GeoTIFF transforms and CRS for all distinct scenes
    scene_cache: Dict[str, Dict[str, Any]] = {}
    distinct_scenes = set(Path(t).stem.split("_")[0] for t in tiles)
    print(f"[2/4] Indexing georeferencing for {len(distinct_scenes)} distinct source scenes...")

    for s_id in distinct_scenes:
        tif_path = find_scene_geotiff(s_id)
        if not tif_path:
            continue
        with rasterio.open(tif_path) as src:
            transform = src.transform
            crs = src.crs
            ctr_lon, ctr_lat = transform * (src.width / 2.0, src.height / 2.0)
            utm_epsg = get_utm_epsg(ctr_lon, ctr_lat)
            scene_cache[s_id] = {
                "path": str(tif_path),
                "transform": transform,
                "crs": crs,
                "width": src.width,
                "height": src.height,
                "utm_epsg": utm_epsg,
            }

    print(f"  • Successfully indexed {len(scene_cache)} of {len(distinct_scenes)} GeoTIFF scenes.")

    # Count total ground truth instances across all tiles
    total_gt_counts: Dict[str, int] = {name: 0 for name in CLASS_NAMES.values()}
    for t_str in tiles:
        lbl_file = LABELS_DIR / f"{Path(t_str).stem}.txt"
        if lbl_file.exists():
            for line in lbl_file.read_text(encoding="utf-8").splitlines():
                toks = line.strip().split()
                if toks:
                    c_id = int(toks[0])
                    if c_id in CLASS_NAMES:
                        total_gt_counts[CLASS_NAMES[c_id]] += 1
    total_gt_all = sum(total_gt_counts.values())
    print(f"  • Ground Truth Inventory: {total_gt_counts} (Total: {total_gt_all})")

    # Load YOLO Model
    print(f"\n[3/4] Loading fine-tuned YOLO11m model checkpoint from {MODEL_PATH.name}...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = YOLO(str(MODEL_PATH))
    print(f"  • Inference device: {device} (FP16 mode)")

    # Data structures for IoU >= 0.3 and IoU >= 0.5
    raw_errors_iou03: Dict[str, List[float]] = {name: [] for name in CLASS_NAMES.values()}
    raw_errors_iou05: Dict[str, List[float]] = {name: [] for name in CLASS_NAMES.values()}

    # Registration sensitivity containers (evaluated at IoU 0.3)
    reg_errors_05px: Dict[str, List[float]] = {name: [] for name in CLASS_NAMES.values()}
    reg_errors_10px: Dict[str, List[float]] = {name: [] for name in CLASS_NAMES.values()}
    reg_errors_20px: Dict[str, List[float]] = {name: [] for name in CLASS_NAMES.values()}

    src_crs_4326 = CRS.from_epsg(4326)
    batch_size = 16
    print(f"\n[4/4] Executing inference & dual bipartite matching (IoU >= 0.3 and IoU >= 0.5)...")

    for b_start in range(0, len(tiles), batch_size):
        b_end = min(b_start + batch_size, len(tiles))
        batch_paths = tiles[b_start:b_end]

        results = model(batch_paths, imgsz=1024, conf=0.25, iou=0.45, verbose=False, half=(device != "cpu"))

        for i, tile_path_str in enumerate(batch_paths):
            tile_p = Path(tile_path_str)
            parts = tile_p.stem.split("_")
            scene_id = parts[0]
            col_offset = int(parts[1])
            row_offset = int(parts[2])

            if scene_id not in scene_cache:
                continue

            scene_info = scene_cache[scene_id]
            scene_transform = scene_info["transform"]
            utm_epsg = scene_info["utm_epsg"]
            dst_utm_crs = CRS.from_epsg(utm_epsg)

            res = results[i]
            dt_boxes = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                classes = res.boxes.cls.cpu().numpy().astype(int)
                confs = res.boxes.conf.cpu().numpy()
                for b_idx in range(len(xyxy)):
                    dt_boxes.append({
                        "bbox_xyxy": xyxy[b_idx],
                        "cls": int(classes[b_idx]),
                        "conf": float(confs[b_idx]),
                        "ctr_tile": np.array([(xyxy[b_idx][0] + xyxy[b_idx][2]) / 2.0, (xyxy[b_idx][1] + xyxy[b_idx][3]) / 2.0])
                    })

            lbl_file = LABELS_DIR / f"{tile_p.stem}.txt"
            gt_boxes = []
            if lbl_file.exists():
                for line in lbl_file.read_text(encoding="utf-8").splitlines():
                    toks = line.strip().split()
                    if len(toks) >= 5:
                        cls_id = int(toks[0])
                        xc = float(toks[1]) * 1024.0
                        yc = float(toks[2]) * 1024.0
                        w = float(toks[3]) * 1024.0
                        h = float(toks[4]) * 1024.0
                        gt_boxes.append({
                            "bbox_xyxy": np.array([xc - w/2.0, yc - h/2.0, xc + w/2.0, yc + h/2.0]),
                            "cls": cls_id,
                            "ctr_tile": np.array([xc, yc])
                        })

            # Bipartite matching at IoU >= 0.3
            matches_03 = match_boxes_class_aware(dt_boxes, gt_boxes, iou_threshold=0.3)
            for dt, gt in matches_03:
                cls_name = CLASS_NAMES[dt["cls"]]
                dt_scene_x = dt["ctr_tile"][0] + col_offset
                dt_scene_y = dt["ctr_tile"][1] + row_offset
                gt_scene_x = gt["ctr_tile"][0] + col_offset
                gt_scene_y = gt["ctr_tile"][1] + row_offset

                dt_lon, dt_lat = scene_transform * (dt_scene_x, dt_scene_y)
                gt_lon, gt_lat = scene_transform * (gt_scene_x, gt_scene_y)

                dt_utm_x, dt_utm_y = warp_transform(src_crs_4326, dst_utm_crs, [dt_lon], [dt_lat])
                gt_utm_x, gt_utm_y = warp_transform(src_crs_4326, dst_utm_crs, [gt_lon], [gt_lat])

                dist_m = math.hypot(dt_utm_x[0] - gt_utm_x[0], dt_utm_y[0] - gt_utm_y[0])
                raw_errors_iou03[cls_name].append(dist_m)

                # Registration Sensitivity Perturbations
                for shift_px, err_dict in [(0.5, reg_errors_05px), (1.0, reg_errors_10px), (2.0, reg_errors_20px)]:
                    diag = shift_px / math.sqrt(2.0)
                    s_lon, s_lat = scene_transform * (dt_scene_x + diag, dt_scene_y + diag)
                    s_utm_x, s_utm_y = warp_transform(src_crs_4326, dst_utm_crs, [s_lon], [s_lat])
                    dist_pert_m = math.hypot(s_utm_x[0] - gt_utm_x[0], s_utm_y[0] - gt_utm_y[0])
                    err_dict[cls_name].append(dist_pert_m)

            # Bipartite matching at IoU >= 0.5
            matches_05 = match_boxes_class_aware(dt_boxes, gt_boxes, iou_threshold=0.5)
            for dt, gt in matches_05:
                cls_name = CLASS_NAMES[dt["cls"]]
                dt_scene_x = dt["ctr_tile"][0] + col_offset
                dt_scene_y = dt["ctr_tile"][1] + row_offset
                gt_scene_x = gt["ctr_tile"][0] + col_offset
                gt_scene_y = gt["ctr_tile"][1] + row_offset

                dt_lon, dt_lat = scene_transform * (dt_scene_x, dt_scene_y)
                gt_lon, gt_lat = scene_transform * (gt_scene_x, gt_scene_y)

                dt_utm_x, dt_utm_y = warp_transform(src_crs_4326, dst_utm_crs, [dt_lon], [dt_lat])
                gt_utm_x, gt_utm_y = warp_transform(src_crs_4326, dst_utm_crs, [gt_lon], [gt_lat])

                dist_m = math.hypot(dt_utm_x[0] - gt_utm_x[0], dt_utm_y[0] - gt_utm_y[0])
                raw_errors_iou05[cls_name].append(dist_m)

        if (b_end % 80 == 0) or b_end == len(tiles):
            total_03 = sum(len(v) for v in raw_errors_iou03.values())
            total_05 = sum(len(v) for v in raw_errors_iou05.values())
            print(f"  Processed {b_end}/{len(tiles)} tiles | Matched: {total_03} (IoU>=0.3), {total_05} (IoU>=0.5)")

    def calc_stats(errs: List[float], total_gt: int) -> Dict[str, Any]:
        if not errs:
            return {"matched_count": 0, "total_gt_count": total_gt, "gt_matched_pct": 0.0, "cep50_m": 0.0, "cep90_m": 0.0, "mean_m": 0.0, "rmse_m": 0.0}
        arr = np.array(errs)
        return {
            "matched_count": len(arr),
            "total_gt_count": total_gt,
            "gt_matched_pct": round((len(arr) / total_gt * 100.0) if total_gt > 0 else 0.0, 2),
            "cep50_m": round(float(np.percentile(arr, 50)), 2),
            "cep90_m": round(float(np.percentile(arr, 90)), 2),
            "mean_m": round(float(np.mean(arr)), 2),
            "rmse_m": round(float(np.sqrt(np.mean(arr**2))), 2),
        }

    # Aggregate for IoU >= 0.3
    all_03 = [e for sub in raw_errors_iou03.values() for e in sub]
    overall_03 = calc_stats(all_03, total_gt_all)
    per_class_03 = {c: calc_stats(raw_errors_iou03[c], total_gt_counts[c]) for c in CLASS_NAMES.values()}

    # Aggregate for IoU >= 0.5
    all_05 = [e for sub in raw_errors_iou05.values() for e in sub]
    overall_05 = calc_stats(all_05, total_gt_all)
    per_class_05 = {c: calc_stats(raw_errors_iou05[c], total_gt_counts[c]) for c in CLASS_NAMES.values()}

    # Sensitivity at IoU 0.3
    all_reg05 = [e for sub in reg_errors_05px.values() for e in sub]
    all_reg10 = [e for sub in reg_errors_10px.values() for e in sub]
    all_reg20 = [e for sub in reg_errors_20px.values() for e in sub]

    sensitivity = {
        "offset_0_0_px": overall_03,
        "offset_0_5_px": calc_stats(all_reg05, total_gt_all),
        "offset_1_0_px": calc_stats(all_reg10, total_gt_all),
        "offset_2_0_px": calc_stats(all_reg20, total_gt_all),
    }

    report = {
        "benchmark_title": "Project Rakshak 2.0 — Task B: Empirical Geolocation CEP Benchmark (Dual-IoU)",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_partition": "Strictly val_report holdout (540 tiles across 38 distinct scenes)",
        "total_ground_truth_targets": total_gt_all,
        "ground_truth_inventory": total_gt_counts,
        "conditional_matching_disclosure": (
            "IMPORTANT SCOPE DISCLOSURE: Geolocation CEP is strictly conditional on an IoU bounding-box match. "
            "Undetected ground-truth targets have no predicted bounding box regression, and thus have undefined "
            "centre localisation error. Matched percentages indicate detection coverage at each IoU threshold."
        ),
        "truth_scope_disclaimer": (
            "TRUTH BOUNDARY: This measurement quantifies the localisation error of neural network bounding box "
            "regressions evaluated strictly against the xView dataset's own internal GeoTIFF georeferencing metadata. "
            "It does NOT represent an evaluation against independent external physical GPS ground truth."
        ),
        "iou_0_3_metrics": {
            "overall": overall_03,
            "per_class": per_class_03,
        },
        "iou_0_5_metrics": {
            "overall": overall_05,
            "per_class": per_class_05,
        },
        "registration_sensitivity_at_iou_0_3": sensitivity,
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[OK] Raw report saved to: {REPORT_JSON}")

    # Summary Markdown
    md_content = f"""# Project Rakshak 2.0: Task B — Geolocation CEP Benchmark (Dual-IoU)

- **Timestamp UTC**: {report['timestamp_utc']}
- **Evaluated Partition**: 540 tiles across **{len(distinct_scenes)} distinct scenes** (val_report holdout)
- **Model Checkpoint**: `xview_yolo11m_military` (1024×1024 static resolution)
- **Total Ground Truth Instances**: **{total_gt_all:,} targets** across 4 defense domains

> [!IMPORTANT]
> **Conditional Match Disclosure**: Geolocation CEP is **conditional on an IoU bounding-box match**. Ground-truth targets that are undetected have no predicted bounding box regression, and thus have undefined centre localisation error.
> **Truth Scope Disclosure**: Localisation error is evaluated strictly against the dataset's own GeoTIFF georeferencing (bounding box regression and affine transform fidelity into local UTM CRS), **not independent external GPS truth**.

---

## 1. Dual-IoU Geolocation Accuracy & Match Coverage (Metric UTM CRS)

### At IoU $\\ge 0.3$ (Candidate Match Standard)

| Target Class | Ground Truth (GT) | Matched Instances | % GT Matched | CEP50 (50% Probable) | CEP90 (90% Probable) | Mean Error | RMSE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for c_name, st in per_class_03.items():
        md_content += f"| **{c_name}** | {st['total_gt_count']:,} | {st['matched_count']:,} | **{st['gt_matched_pct']:.1f}%** | **{st['cep50_m']:.2f} m** | **{st['cep90_m']:.2f} m** | {st['mean_m']:.2f} m | {st['rmse_m']:.2f} m |\n"

    md_content += f"""| **OVERALL** | **{total_gt_all:,}** | **{overall_03['matched_count']:,}** | **{overall_03['gt_matched_pct']:.1f}%** | **{overall_03['cep50_m']:.2f} m** | **{overall_03['cep90_m']:.2f} m** | **{overall_03['mean_m']:.2f} m** | **{overall_03['rmse_m']:.2f} m** |

### At IoU $\\ge 0.5$ (Tight Physical Intersection Standard)

| Target Class | Ground Truth (GT) | Matched Instances | % GT Matched | CEP50 (50% Probable) | CEP90 (90% Probable) | Mean Error | RMSE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for c_name, st in per_class_05.items():
        md_content += f"| **{c_name}** | {st['total_gt_count']:,} | {st['matched_count']:,} | **{st['gt_matched_pct']:.1f}%** | **{st['cep50_m']:.2f} m** | **{st['cep90_m']:.2f} m** | {st['mean_m']:.2f} m | {st['rmse_m']:.2f} m |\n"

    md_content += f"""| **OVERALL** | **{total_gt_all:,}** | **{overall_05['matched_count']:,}** | **{overall_05['gt_matched_pct']:.1f}%** | **{overall_05['cep50_m']:.2f} m** | **{overall_05['cep90_m']:.2f} m** | **{overall_05['mean_m']:.2f} m** | **{overall_05['rmse_m']:.2f} m** |

---

## 2. Sensitivity to Subpixel Registration Offsets (at IoU $\\ge 0.3$)

At xView's ~0.3 m Ground Sample Distance (GSD), subpixel and multi-pixel platform registration jitter impacts localisation error as follows:

| Injected Registration Offset | Resulting CEP50 | Resulting CEP90 | Resulting Mean Error | Resulting RMSE |
| :---: | :---: | :---: | :---: | :---: |
| **0.0 px (Baseline)** | **{sensitivity['offset_0_0_px']['cep50_m']:.2f} m** | **{sensitivity['offset_0_0_px']['cep90_m']:.2f} m** | {sensitivity['offset_0_0_px']['mean_m']:.2f} m | {sensitivity['offset_0_0_px']['rmse_m']:.2f} m |
| **0.5 px Offset** | **{sensitivity['offset_0_5_px']['cep50_m']:.2f} m** | **{sensitivity['offset_0_5_px']['cep90_m']:.2f} m** | {sensitivity['offset_0_5_px']['mean_m']:.2f} m | {sensitivity['offset_0_5_px']['rmse_m']:.2f} m |
| **1.0 px Offset** | **{sensitivity['offset_1_0_px']['cep50_m']:.2f} m** | **{sensitivity['offset_1_0_px']['cep90_m']:.2f} m** | {sensitivity['offset_1_0_px']['mean_m']:.2f} m | {sensitivity['offset_1_0_px']['rmse_m']:.2f} m |
| **2.0 px Offset** | **{sensitivity['offset_2_0_px']['cep50_m']:.2f} m** | **{sensitivity['offset_2_0_px']['cep90_m']:.2f} m** | {sensitivity['offset_2_0_px']['mean_m']:.2f} m | {sensitivity['offset_2_0_px']['rmse_m']:.2f} m |

---
"""
    SUMMARY_MD.write_text(md_content, encoding="utf-8")
    print(f"[OK] Summary markdown saved to: {SUMMARY_MD}")


if __name__ == "__main__":
    run_cep_evaluation()
