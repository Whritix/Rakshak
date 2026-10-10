"""Project Rakshak 2.0 — Multi-Temporal Satellite Change Detection Engine.

Provides 100% air-gapped, sovereign change detection for optical satellite & aerial imagery:
1. Synthetic bi-temporal pair generation using held-out val_report partition tiles.
   Injects class-aware object additions (NEW), removals (REMOVED), and displacements (MOVED),
   labeled explicitly as SYNTHETIC with preserved ground-truth edit logs.
2. Sub-pixel spatial co-registration using ORB feature extraction + RANSAC affine estimation,
   with Fourier Phase Correlation fallback for translational alignment under low texture.
3. Class-aware, one-to-one bounding box matching across YOLO detections with distance
   and IoU threshold gating, outputting pixel and WGS84 geographic coordinates.
4. Radiometric normalisation (channel-wise gain & bias calibration) and secondary
   pixel-difference signal to flag structural anomalies independently from object alerts.
5. Zero external network egress; strictly local inference and mathematical execution.
"""
from __future__ import annotations

import base64
import copy
import io
import json
import math
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
VAL_TILES_FILE = ROOT / "evaluation" / "val_report_tiles.txt"
VAL_LABELS_DIR = ROOT / "runs" / "xview_yolo" / "labels" / "val"
VAL_IMAGES_DIR = ROOT / "runs" / "xview_yolo" / "images" / "val"

# YOLO checkpointer paths
YOLO11M_MODEL = ROOT / "runs" / "train" / "xview_yolo11m_military" / "weights" / "best.pt"
HACKATHON_MODEL = ROOT / "runs" / "train" / "xview_hackathon" / "weights" / "best.pt"
PRIMARY_MODEL_PATH = YOLO11M_MODEL if YOLO11M_MODEL.exists() else HACKATHON_MODEL

CLASS_NAMES = {0: "Vessel", 1: "Aircraft", 2: "Vehicle", 3: "Infrastructure"}
INVERSE_CLASSES = {v: k for k, v in CLASS_NAMES.items()}

# Cached YOLO model instance
_CACHED_DETECTOR = None

# Global in-memory cache for last change detection run
_LAST_CHANGE_DETECTION_RESULT: Optional[Dict[str, Any]] = None


def get_detector():
    """Load or retrieve the cached YOLO detector."""
    global _CACHED_DETECTOR
    if _CACHED_DETECTOR is None:
        from ultralytics import YOLO
        if not PRIMARY_MODEL_PATH.exists():
            raise FileNotFoundError(f"No detector checkpoint found at {PRIMARY_MODEL_PATH}")
        _CACHED_DETECTOR = YOLO(str(PRIMARY_MODEL_PATH))
    return _CACHED_DETECTOR


def get_val_report_tile_paths() -> List[Path]:
    """Retrieve all valid tile paths from evaluation/val_report_tiles.txt."""
    if not VAL_TILES_FILE.exists():
        # Fallback to scanning VAL_IMAGES_DIR directly
        if VAL_IMAGES_DIR.exists():
            return sorted(list(VAL_IMAGES_DIR.glob("*.jpg")))
        return []

    lines = [line.strip() for line in VAL_TILES_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    paths = []
    for line in lines:
        p = Path(line)
        if not p.is_absolute():
            p = ROOT / p
        if p.exists():
            paths.append(p)
    return paths


def find_parent_geotiff(scene_id: str) -> Optional[Path]:
    """Search for parent GeoTIFF scene file to extract exact WGS84 CRS transform."""
    search_dirs = [
        ROOT / "val_images" / "val_images",
        ROOT / "train_images" / "train_images",
        ROOT / "val_images",
        ROOT / "train_images",
    ]
    for d in search_dirs:
        candidate = d / f"{scene_id}.tif"
        if candidate.exists():
            return candidate
    return None


def get_tile_georeference(tile_path: Path) -> Dict[str, Any]:
    """Extract or derive affine coordinate transformation to WGS84 for a tile."""
    stem = tile_path.stem
    parts = stem.split("_")
    scene_id = parts[0]
    row_offset = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    col_offset = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    parent_tif = find_parent_geotiff(scene_id)
    if parent_tif:
        try:
            import rasterio
            with rasterio.open(parent_tif) as ds:
                return {
                    "has_geotiff": True,
                    "scene_id": scene_id,
                    "row_offset": row_offset,
                    "col_offset": col_offset,
                    "transform": list(ds.transform),
                    "crs": str(ds.crs) if ds.crs else "EPSG:4326",
                    "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
                }
        except Exception:
            pass

    # Default fallback nominal georeference (Western Naval Command / Arabian Sea Sector)
    # 0.3m GSD ~ 2.7e-6 degrees per pixel
    base_lat = 28.6139 + (row_offset * -2.7e-6)
    base_lon = 77.2090 + (col_offset * 2.7e-6)
    return {
        "has_geotiff": False,
        "scene_id": scene_id,
        "row_offset": row_offset,
        "col_offset": col_offset,
        "base_lat": base_lat,
        "base_lon": base_lon,
        "deg_per_px_x": 2.7e-6,
        "deg_per_px_y": -2.7e-6,
    }


def pixel_to_wgs84(px_x: float, px_y: float, geo_meta: Dict[str, Any]) -> Tuple[float, float]:
    """Convert pixel (x, y) coordinates inside a tile to WGS84 (lat, lon)."""
    if geo_meta.get("has_geotiff") and "transform" in geo_meta:
        try:
            import rasterio
            from rasterio.transform import Affine
            aff = Affine(*geo_meta["transform"][:6])
            full_col = geo_meta["col_offset"] + px_x
            full_row = geo_meta["row_offset"] + px_y
            x_geo, y_geo = rasterio.transform.xy(aff, full_row, full_col)
            crs_str = geo_meta.get("crs", "EPSG:4326")
            if "4326" in crs_str:
                return float(y_geo), float(x_geo)
            else:
                from rasterio.warp import transform
                lo, la = transform(crs_str, "EPSG:4326", [x_geo], [y_geo])
                return float(la[0]), float(lo[0])
        except Exception:
            pass

    # Fallback affine formula
    base_lat = geo_meta.get("base_lat", 28.6139)
    base_lon = geo_meta.get("base_lon", 77.2090)
    dy = geo_meta.get("deg_per_px_y", -2.7e-6)
    dx = geo_meta.get("deg_per_px_x", 2.7e-6)
    lat = base_lat + (px_y * dy)
    lon = base_lon + (px_x * dx)
    return round(lat, 6), round(lon, 6)


def load_ground_truth_labels(tile_path: Path, img_w: int = 1024, img_h: int = 1024) -> List[Dict[str, Any]]:
    """Load normalized YOLO labels for tile and return pixel bounding boxes."""
    stem = tile_path.stem
    label_path = VAL_LABELS_DIR / f"{stem}.txt"
    if not label_path.exists():
        return []

    lines = [l.strip() for l in label_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    objects = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 5:
            cls_id = int(parts[0])
            xc = float(parts[1]) * img_w
            yc = float(parts[2]) * img_h
            bw = float(parts[3]) * img_w
            bh = float(parts[4]) * img_h
            x1 = max(0.0, xc - bw / 2.0)
            y1 = max(0.0, yc - bh / 2.0)
            objects.append({
                "class_id": cls_id,
                "class_name": CLASS_NAMES.get(cls_id, f"Class_{cls_id}"),
                "x": round(x1, 1),
                "y": round(y1, 1),
                "w": round(bw, 1),
                "h": round(bh, 1),
                "xc": round(xc, 1),
                "yc": round(yc, 1),
            })
    return objects


def build_synthetic_pair(
    tile_path: Path,
    seed: int = 42,
    num_edits: int = 3,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
) -> Dict[str, Any]:
    """Construct a synthetic bi-temporal before/after pair from a val_report tile.

    Pasting in and removing labelled objects on a copy of the before image,
    and recording the ground truth edit operations explicitly.
    Labeled as SYNTHETIC.
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    img_bgr = cv2.imread(str(tile_path))
    if img_bgr is None:
        raise ValueError(f"Unable to read image at {tile_path}")

    h, w = img_bgr.shape[:2]
    geo_meta = get_tile_georeference(tile_path)
    gt_objects = load_ground_truth_labels(tile_path, w, h)

    before_img = img_bgr.copy()
    after_img = img_bgr.copy()

    edits: List[Dict[str, Any]] = []

    # Filter candidates for removal / displacement: prioritize Vehicle and Aircraft
    tactical_candidates = [obj for obj in gt_objects if obj["class_name"] in {"Vehicle", "Aircraft"}]
    if not tactical_candidates:
        tactical_candidates = [obj for obj in gt_objects if obj["class_name"] in {"Vessel", "Vehicle", "Aircraft"}]
    if not tactical_candidates:
        tactical_candidates = gt_objects

    used_object_indices = set()

    # 1. REMOVE an object (if candidate exists)
    if tactical_candidates:
        idx = rng.randint(0, len(tactical_candidates) - 1)
        used_object_indices.add(idx)
        obj_to_remove = tactical_candidates[idx]
        rx = int(obj_to_remove["x"])
        ry = int(obj_to_remove["y"])
        rw = int(obj_to_remove["w"])
        rh = int(obj_to_remove["h"])

        # Patch / inpaint over the removed object
        mask = np.zeros((h, w), dtype=np.uint8)
        pad = 4
        x0 = max(0, rx - pad)
        y0 = max(0, ry - pad)
        x1 = min(w, rx + rw + pad)
        y1 = min(h, ry + rh + pad)
        mask[y0:y1, x0:x1] = 255

        # Telea inpainting to reconstruct natural terrain / background
        after_img = cv2.inpaint(after_img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

        lat, lon = pixel_to_wgs84(obj_to_remove["xc"], obj_to_remove["yc"], geo_meta)
        edits.append({
            "id": f"gt-rem-{uuid.uuid4().hex[:8]}",
            "change_type": "REMOVED",
            "class_name": obj_to_remove["class_name"],
            "bbox": [obj_to_remove["x"], obj_to_remove["y"], obj_to_remove["w"], obj_to_remove["h"]],
            "lat": lat,
            "lon": lon,
            "details": f"Removed ground-truth {obj_to_remove['class_name']} via inpainting"
        })

    # 2. MOVE an object (relocate to new position)
    remaining_candidates = [obj for i, obj in enumerate(tactical_candidates) if i not in used_object_indices]
    if remaining_candidates:
        idx = rng.randint(0, len(remaining_candidates) - 1)
        obj_to_move = remaining_candidates[idx]
        mx = int(obj_to_move["x"])
        my = int(obj_to_move["y"])
        mw = max(12, int(obj_to_move["w"]))
        mh = max(12, int(obj_to_move["h"]))

        # Extract patch
        patch = before_img[my:my+mh, mx:mx+mw].copy()

        # Inpaint original location in after image
        mask = np.zeros((h, w), dtype=np.uint8)
        pad = 4
        x0 = max(0, mx - pad)
        y0 = max(0, my - pad)
        x1 = min(w, mx + mw + pad)
        y1 = min(h, my + mh + pad)
        mask[y0:y1, x0:x1] = 255
        after_img = cv2.inpaint(after_img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

        # Displace to new location by 40 to 80 px
        disp_dx = rng.choice([-1, 1]) * rng.randint(35, 75)
        disp_dy = rng.choice([-1, 1]) * rng.randint(35, 75)
        target_x = max(20, min(w - mw - 20, mx + disp_dx))
        target_y = max(20, min(h - mh - 20, my + disp_dy))

        actual_disp = math.sqrt((target_x - mx) ** 2 + (target_y - my) ** 2)

        # Paste patch at new location
        if patch.shape[0] > 0 and patch.shape[1] > 0:
            target_roi = after_img[target_y:target_y+mh, target_x:target_x+mw]
            if target_roi.shape == patch.shape:
                # Alpha blend patch borders for seamless edge
                alpha_mask = np.ones((mh, mw), dtype=np.float32)
                cv2.rectangle(alpha_mask, (0, 0), (mw-1, mh-1), 0.5, 1)
                for c in range(3):
                    after_img[target_y:target_y+mh, target_x:target_x+mw, c] = (
                        alpha_mask * patch[:, :, c] + (1.0 - alpha_mask) * target_roi[:, :, c]
                    ).astype(np.uint8)

        lat, lon = pixel_to_wgs84(target_x + mw / 2.0, target_y + mh / 2.0, geo_meta)
        edits.append({
            "id": f"gt-mov-{uuid.uuid4().hex[:8]}",
            "change_type": "MOVED",
            "class_name": obj_to_move["class_name"],
            "bbox": [float(target_x), float(target_y), float(mw), float(mh)],
            "old_bbox": [float(mx), float(my), float(mw), float(mh)],
            "displacement_px": round(actual_disp, 1),
            "lat": lat,
            "lon": lon,
            "details": f"Displaced {obj_to_move['class_name']} by {actual_disp:.1f}px to new coordinate"
        })

    # 3. ADD a NEW object (paste vehicle or aircraft patch from donor)
    # Pick a patch source: either from current candidates or synthesize a tactical vehicle signature
    donor_patch = None
    donor_class = "Vehicle"
    if tactical_candidates:
        donor_obj = rng.choice(tactical_candidates)
        donor_class = donor_obj["class_name"]
        dx0, dy0 = int(donor_obj["x"]), int(donor_obj["y"])
        dw0, dh0 = max(10, int(donor_obj["w"])), max(10, int(donor_obj["h"]))
        if dy0 + dh0 <= h and dx0 + dw0 <= w:
            donor_patch = before_img[dy0:dy0+dh0, dx0:dx0+dw0].copy()

    if donor_patch is None or donor_patch.size == 0:
        # Create tactical vehicle signature box
        pw, ph = 28, 18
        donor_patch = np.full((ph, pw, 3), (85, 95, 90), dtype=np.uint8)
        cv2.rectangle(donor_patch, (4, 4), (pw-5, ph-5), (55, 65, 60), -1)
        donor_class = "Vehicle"
    else:
        ph, pw = donor_patch.shape[:2]

    # Find open position with clearance
    paste_x = rng.randint(80, max(81, w - pw - 80))
    paste_y = rng.randint(80, max(81, h - ph - 80))

    if paste_y + ph <= h and paste_x + pw <= w:
        roi = after_img[paste_y:paste_y+ph, paste_x:paste_x+pw]
        if roi.shape == donor_patch.shape:
            # Paste donor object
            after_img[paste_y:paste_y+ph, paste_x:paste_x+pw] = donor_patch

            lat, lon = pixel_to_wgs84(paste_x + pw / 2.0, paste_y + ph / 2.0, geo_meta)
            edits.append({
                "id": f"gt-new-{uuid.uuid4().hex[:8]}",
                "change_type": "NEW",
                "class_name": donor_class,
                "bbox": [float(paste_x), float(paste_y), float(pw), float(ph)],
                "lat": lat,
                "lon": lon,
                "details": f"Pasted synthetic new {donor_class} into clear sector"
            })

    # 4. Inject simulated new structural anomaly (for secondary radiometric difference signal)
    # e.g. newly paved square revetment or staging pad 45x55 px
    pad_w = rng.randint(40, 60)
    pad_h = rng.randint(40, 60)
    pad_x = rng.randint(100, max(101, w - pad_w - 100))
    pad_y = rng.randint(100, max(101, h - pad_h - 100))
    # Give it concrete/earthworks tint (+40-50 intensity)
    pad_roi = after_img[pad_y:pad_y+pad_h, pad_x:pad_x+pad_w].astype(np.float32)
    tint = np.array([45.0, 50.0, 48.0], dtype=np.float32)
    after_img[pad_y:pad_y+pad_h, pad_x:pad_x+pad_w] = np.clip(pad_roi * 0.75 + tint, 0, 255).astype(np.uint8)

    # 5. Apply spatial misalignment shift if requested
    if abs(shift_x) > 1e-4 or abs(shift_y) > 1e-4:
        M_shift = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        after_img = cv2.warpAffine(after_img, M_shift, (w, h), borderMode=cv2.BORDER_REFLECT)

    return {
        "tile_name": tile_path.name,
        "tile_path": str(tile_path),
        "pair_label": "SYNTHETIC",
        "before_img": before_img,
        "after_img": after_img,
        "injected_shift": (float(shift_x), float(shift_y)),
        "ground_truth_edits": edits,
        "structural_injection": {
            "x": pad_x, "y": pad_y, "w": pad_w, "h": pad_h,
            "area": pad_w * pad_h,
            "type": "SIMULATED_STRUCTURE_REVETMENT"
        },
        "geo_metadata": geo_meta,
    }


def coregister_images(
    before_img: np.ndarray,
    after_img: np.ndarray,
    injected_shift: Optional[Tuple[float, float]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Co-register misaligned satellite pair using ORB + RANSAC and Phase Correlation fallback.

    Returns aligned after_img and registration metrics (shift recovered, error in pixels).
    """
    h, w = before_img.shape[:2]
    gray_before = cv2.cvtColor(before_img, cv2.COLOR_BGR2GRAY)
    gray_after = cv2.cvtColor(after_img, cv2.COLOR_BGR2GRAY)

    recovered_dx = 0.0
    recovered_dy = 0.0
    method_used = "ORB_RANSAC"
    inlier_count = 0

    # 1. Feature Extraction via ORB
    orb = cv2.ORB_create(nfeatures=2500, fastThreshold=12)
    kp1, des1 = orb.detectAndCompute(gray_before, None)
    kp2, des2 = orb.detectAndCompute(gray_after, None)

    affine_matrix = None

    if des1 is not None and des2 is not None and len(kp1) >= 8 and len(kp2) >= 8:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(des2, des1, k=2)
        good = []
        for pair in matches:
            if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance:
                good.append(pair[0])

        if len(good) >= 6:
            src_pts = np.float32([kp2[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp1[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=2.5)
            if M is not None and inliers is not None:
                inlier_count = int(np.sum(inliers))
                # Sanity check: sheer translation/rotation bounds (reject wild skew)
                scale = math.sqrt(M[0, 0]**2 + M[0, 1]**2)
                if 0.90 <= scale <= 1.10 and abs(M[0, 2]) <= 30.0 and abs(M[1, 2]) <= 30.0:
                    affine_matrix = M
                    recovered_dx = -float(M[0, 2])
                    recovered_dy = -float(M[1, 2])

    # 2. Phase Correlation Fallback or Refinement
    if affine_matrix is None:
        method_used = "PHASE_CORRELATION"
        g1 = np.float32(gray_before)
        g2 = np.float32(gray_after)
        hann = cv2.createHanningWindow((w, h), cv2.CV_32F)
        (pc_x, pc_y), resp = cv2.phaseCorrelate(g2, g1, hann)
        affine_matrix = np.float32([[1.0, 0.0, pc_x], [0.0, 1.0, pc_y]])
        recovered_dx = -float(pc_x)
        recovered_dy = -float(pc_y)

    # Warp after image to align with before image
    aligned_after = cv2.warpAffine(
        after_img,
        affine_matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT
    )

    reg_error = 0.0
    if injected_shift is not None:
        true_dx, true_dy = injected_shift
        reg_error = math.sqrt((true_dx - recovered_dx) ** 2 + (true_dy - recovered_dy) ** 2)

    return aligned_after, {
        "status": "CO_REGISTERED",
        "method": method_used,
        "inliers": inlier_count,
        "shift_recovered": [round(recovered_dx, 4), round(recovered_dy, 4)],
        "shift_injected": list(injected_shift) if injected_shift else [0.0, 0.0],
        "registration_error_px": round(reg_error, 4),
        "affine_matrix": affine_matrix.tolist() if affine_matrix is not None else None,
    }


def run_yolo_detection(image_bgr: np.ndarray, confidence: float = 0.25) -> List[Dict[str, Any]]:
    """Execute local YOLO11m detector on the tile image."""
    model = get_detector()
    # Ultralytics expects RGB or BGR numpy array
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    res = model.predict(rgb, conf=confidence, imgsz=1024, verbose=False)[0]

    detections = []
    if res.boxes is not None:
        for b in res.boxes:
            cls_id = int(b.cls[0])
            name = model.names.get(cls_id, str(cls_id))
            conf = float(b.conf[0])
            xy = b.xyxy[0].cpu().tolist()
            x1, y1, x2, y2 = xy
            bw = max(1.0, x2 - x1)
            bh = max(1.0, y2 - y1)
            xc = (x1 + x2) / 2.0
            yc = (y1 + y2) / 2.0

            detections.append({
                "id": uuid.uuid4().hex[:12],
                "class_id": cls_id,
                "class_name": name,
                "confidence": round(conf, 4),
                "x": round(x1, 1),
                "y": round(y1, 1),
                "w": round(bw, 1),
                "h": round(bh, 1),
                "xc": round(xc, 1),
                "yc": round(yc, 1),
            })
    return detections


def match_detections_and_classify_changes(
    dets_before: List[Dict[str, Any]],
    dets_after: List[Dict[str, Any]],
    geo_meta: Dict[str, Any],
    stationary_dist_thr: float = 28.0,
    max_move_dist_thr: float = 120.0,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Match before/after detections one-to-one, class-aware, and output NEW, REMOVED, and MOVED objects.

    Distance thresholds:
    - Stationary (UNCHANGED): centroid distance <= 28 px OR bounding box IoU >= 0.25
    - MOVED: centroid distance between 28 px and 120 px with area similarity (0.35 to 2.8)
    - NEW: detections in after image with no match in before image
    - REMOVED: detections in before image with no match in after image
    """
    def _box_iou(b1: Dict[str, Any], b2: Dict[str, Any]) -> float:
        ix1 = max(b1["x"], b2["x"])
        iy1 = max(b1["y"], b2["y"])
        ix2 = min(b1["x"] + b1["w"], b2["x"] + b2["w"])
        iy2 = min(b1["y"] + b1["h"], b2["y"] + b2["h"])
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        a1 = b1["w"] * b1["h"]
        a2 = b2["w"] * b2["h"]
        return inter / max(1e-8, a1 + a2 - inter)

    changes: List[Dict[str, Any]] = []
    summary = {"NEW": 0, "REMOVED": 0, "MOVED": 0, "UNCHANGED": 0}

    # Group by class
    all_classes = set([d["class_name"] for d in dets_before] + [d["class_name"] for d in dets_after])

    for cname in sorted(all_classes):
        b_class = [d for d in dets_before if d["class_name"] == cname]
        a_class = [d for d in dets_after if d["class_name"] == cname]

        matched_b = set()
        matched_a = set()

        # Step 1: Match stationary objects (distance <= stationary_dist_thr OR IoU >= 0.25)
        dist_pairs = []
        for ib, db in enumerate(b_class):
            for ia, da in enumerate(a_class):
                dist = math.sqrt((db["xc"] - da["xc"]) ** 2 + (db["yc"] - da["yc"]) ** 2)
                iou = _box_iou(db, da)
                if dist <= stationary_dist_thr or iou >= 0.25:
                    dist_pairs.append((dist, ib, ia))

        dist_pairs.sort(key=lambda x: x[0])
        for dist, ib, ia in dist_pairs:
            if ib not in matched_b and ia not in matched_a:
                matched_b.add(ib)
                matched_a.add(ia)
                summary["UNCHANGED"] += 1

        # Step 2: Match MOVED objects (stationary_dist_thr < distance <= max_move_dist_thr)
        move_pairs = []
        for ib, db in enumerate(b_class):
            if ib in matched_b:
                continue
            for ia, da in enumerate(a_class):
                if ia in matched_a:
                    continue
                dist = math.sqrt((db["xc"] - da["xc"]) ** 2 + (db["yc"] - da["yc"]) ** 2)
                if stationary_dist_thr < dist <= max_move_dist_thr:
                    area_b = db["w"] * db["h"]
                    area_a = da["w"] * da["h"]
                    ratio = min(area_b, area_a) / max(1.0, max(area_b, area_a))
                    if ratio >= 0.35:  # area consistency
                        move_pairs.append((dist, ib, ia))

        move_pairs.sort(key=lambda x: x[0])
        for dist, ib, ia in move_pairs:
            if ib not in matched_b and ia not in matched_a:
                matched_b.add(ib)
                matched_a.add(ia)
                summary["MOVED"] += 1
                da = a_class[ia]
                db = b_class[ib]
                lat, lon = pixel_to_wgs84(da["xc"], da["yc"], geo_meta)
                old_lat, old_lon = pixel_to_wgs84(db["xc"], db["yc"], geo_meta)
                changes.append({
                    "id": f"chg-mov-{uuid.uuid4().hex[:8]}",
                    "change_type": "MOVED",
                    "class_name": cname,
                    "confidence": da["confidence"],
                    "x": da["x"],
                    "y": da["y"],
                    "w": da["w"],
                    "h": da["h"],
                    "old_x": db["x"],
                    "old_y": db["y"],
                    "old_w": db["w"],
                    "old_h": db["h"],
                    "displacement_px": round(dist, 1),
                    "lat": lat,
                    "lon": lon,
                    "old_lat": old_lat,
                    "old_lon": old_lon,
                    "details": f"Relocated {cname} by {dist:.1f}px (Bearing {math.degrees(math.atan2(da['yc']-db['yc'], da['xc']-db['xc'])) % 360:.0f}°)"
                })

        # Step 3: Unmatched detections in after -> NEW
        for ia, da in enumerate(a_class):
            if ia not in matched_a:
                summary["NEW"] += 1
                lat, lon = pixel_to_wgs84(da["xc"], da["yc"], geo_meta)
                changes.append({
                    "id": f"chg-new-{uuid.uuid4().hex[:8]}",
                    "change_type": "NEW",
                    "class_name": cname,
                    "confidence": da["confidence"],
                    "x": da["x"],
                    "y": da["y"],
                    "w": da["w"],
                    "h": da["h"],
                    "lat": lat,
                    "lon": lon,
                    "details": f"New tactical {cname} detected in post-scene"
                })

        # Step 4: Unmatched detections in before -> REMOVED
        for ib, db in enumerate(b_class):
            if ib not in matched_b:
                summary["REMOVED"] += 1
                lat, lon = pixel_to_wgs84(db["xc"], db["yc"], geo_meta)
                changes.append({
                    "id": f"chg-rem-{uuid.uuid4().hex[:8]}",
                    "change_type": "REMOVED",
                    "class_name": cname,
                    "confidence": db["confidence"],
                    "x": db["x"],
                    "y": db["y"],
                    "w": db["w"],
                    "h": db["h"],
                    "lat": lat,
                    "lon": lon,
                    "details": f"Tactical {cname} departed / cleared from post-scene"
                })

    return changes, summary


def compute_radiometric_pixel_difference(
    before_img: np.ndarray,
    aligned_after_img: np.ndarray,
    geo_meta: Dict[str, Any],
    min_structure_area: int = 120,
) -> Dict[str, Any]:
    """Compute radiometric-normalised pixel-difference signal to flag structural anomalies.

    Reported separately from object-level detector results.
    """
    h, w = before_img.shape[:2]

    # 1. Radiometric Normalisation (Channel-wise Gain & Bias Alignment)
    norm_after = np.zeros_like(aligned_after_img, dtype=np.float32)
    for c in range(3):
        m1 = float(np.mean(before_img[:, :, c]))
        s1 = float(np.std(before_img[:, :, c]))
        m2 = float(np.mean(aligned_after_img[:, :, c]))
        s2 = float(np.std(aligned_after_img[:, :, c]))
        if s1 < 1.0 or s2 < 1.0:
            norm_after[:, :, c] = np.clip(aligned_after_img[:, :, c].astype(np.float32) - m2 + m1, 0, 255)
        else:
            scale = s1 / (s2 + 1e-5)
            norm_after[:, :, c] = np.clip((aligned_after_img[:, :, c].astype(np.float32) - m2) * scale + m1, 0, 255)
    norm_after_uint8 = norm_after.astype(np.uint8)

    # 2. Absolute Difference
    diff = cv2.absdiff(before_img, norm_after_uint8)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # 3. Gaussian Filtering & Thresholding
    blurred = cv2.GaussianBlur(diff_gray, (5, 5), 0)
    otsu_val, _ = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    active_thr = max(28, int(otsu_val))
    _, mask = cv2.threshold(blurred, active_thr, 255, cv2.THRESH_BINARY)

    # 4. Morphological Opening & Closing (Suppress edge-ringing from subpixel shifts)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)

    # 5. Connected Components / Contours Extraction
    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    structural_anomalies = []
    total_changed_pixels = int(np.count_nonzero(mask_clean))
    total_area_pct = round((total_changed_pixels / float(h * w)) * 100.0, 3)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_structure_area:
            bx, by, bw, bh = cv2.boundingRect(cnt)
            cen_x = bx + bw / 2.0
            cen_y = by + bh / 2.0
            lat, lon = pixel_to_wgs84(cen_x, cen_y, geo_meta)
            roi_diff = diff_gray[by:by+bh, bx:bx+bw]
            mean_delta = float(np.mean(roi_diff))
            structural_anomalies.append({
                "id": f"struct-{uuid.uuid4().hex[:8]}",
                "x": bx,
                "y": by,
                "w": bw,
                "h": bh,
                "area_px": int(area),
                "mean_delta": round(mean_delta, 1),
                "lat": lat,
                "lon": lon,
                "anomaly_type": "NEW_STRUCTURE_SURFACE_MODIFICATION",
                "details": f"Structural surface change: {int(area)}px² (Mean delta: {mean_delta:.1f})"
            })

    # 6. Render Difference Heatmap Base64 Preview
    # Red-tinted overlay on grayscale background
    diff_vis = cv2.applyColorMap(diff_gray, cv2.COLORMAP_JET)
    alpha = 0.45
    blended_preview = cv2.addWeighted(before_img, 1.0 - alpha, diff_vis, alpha, 0)
    for sa in structural_anomalies:
        cv2.rectangle(
            blended_preview,
            (sa["x"], sa["y"]),
            (sa["x"] + sa["w"], sa["y"] + sa["h"]),
            (0, 255, 255),
            2
        )

    return {
        "status": "COMPUTED",
        "changed_pixels_count": total_changed_pixels,
        "changed_area_pct": total_area_pct,
        "radiometric_threshold_used": active_thr,
        "structural_anomalies_count": len(structural_anomalies),
        "structural_anomalies": structural_anomalies,
        "heatmap_overlay_base64": encode_cv2_to_base64_jpeg(blended_preview),
    }


def encode_cv2_to_base64_jpeg(img_bgr: np.ndarray, quality: int = 80) -> str:
    """Encode OpenCV BGR image as base64 JPEG data URL."""
    success, buffer = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def run_change_detection_analysis(
    tile_path_str: Optional[str] = None,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
    seed: int = 42,
    confidence: float = 0.25,
) -> Dict[str, Any]:
    """Execute complete end-to-end change detection on a synthetic pair."""
    global _LAST_CHANGE_DETECTION_RESULT

    # 1. Resolve tile path
    if tile_path_str:
        tile_path = Path(tile_path_str)
        if not tile_path.is_absolute():
            tile_path = ROOT / tile_path
    else:
        # Default to high-density tactical validation tile
        val_tiles = get_val_report_tile_paths()
        if not val_tiles:
            raise FileNotFoundError("No validation tiles found in val_report partition.")
        # Pick a tile that has objects
        tile_path = val_tiles[seed % len(val_tiles)]

    if not tile_path.exists():
        raise FileNotFoundError(f"Tile not found: {tile_path}")

    # 2. Build synthetic pair
    synth_data = build_synthetic_pair(
        tile_path=tile_path,
        seed=seed,
        num_edits=3,
        shift_x=shift_x,
        shift_y=shift_y,
    )
    before_img = synth_data["before_img"]
    after_img = synth_data["after_img"]
    geo_meta = synth_data["geo_metadata"]

    # 3. Spatial Co-Registration
    aligned_after, reg_info = coregister_images(
        before_img=before_img,
        after_img=after_img,
        injected_shift=(shift_x, shift_y)
    )

    # 4. Neural Detection on Both Scenes
    dets_before = run_yolo_detection(before_img, confidence=confidence)
    dets_after = run_yolo_detection(aligned_after, confidence=confidence)

    # 5. One-to-one Class-Aware Matching & Change Classification
    object_changes, obj_summary = match_detections_and_classify_changes(
        dets_before=dets_before,
        dets_after=dets_after,
        geo_meta=geo_meta,
        stationary_dist_thr=18.0,
        max_move_dist_thr=120.0
    )

    # 6. Secondary Radiometric Pixel Difference
    pixel_diff_signal = compute_radiometric_pixel_difference(
        before_img=before_img,
        aligned_after_img=aligned_after,
        geo_meta=geo_meta
    )

    # 7. Render Annotated Before and After Previews
    # Render tactical boxes on before/after for UI display
    annotated_before = before_img.copy()
    for d in dets_before:
        x, y, w, h = int(d["x"]), int(d["y"]), int(d["w"]), int(d["h"])
        cv2.rectangle(annotated_before, (x, y), (x + w, y + h), (0, 200, 255), 2)
        cv2.putText(
            annotated_before, f"{d['class_name']} {d['confidence']:.2f}",
            (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 255), 1
        )

    annotated_after = aligned_after.copy()
    for chg in object_changes:
        x, y, w, h = int(chg["x"]), int(chg["y"]), int(chg["w"]), int(chg["h"])
        color = (0, 255, 120) if chg["change_type"] == "NEW" else (0, 140, 255) if chg["change_type"] == "MOVED" else (0, 0, 255)
        cv2.rectangle(annotated_after, (x, y), (x + w, y + h), color, 2)
        label = f"[{chg['change_type']}] {chg['class_name']}"
        cv2.putText(
            annotated_after, label,
            (x, max(14, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1
        )

    response_payload = {
        "status": "SUCCESS",
        "pair_label": "SYNTHETIC",
        "tile_name": tile_path.name,
        "tile_path": str(tile_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "registration": reg_info,
        "object_summary": obj_summary,
        "object_changes": object_changes,
        "pixel_difference": pixel_diff_signal,
        "ground_truth_edits": synth_data["ground_truth_edits"],
        "detections_count_before": len(dets_before),
        "detections_count_after": len(dets_after),
        "before_preview": encode_cv2_to_base64_jpeg(annotated_before),
        "after_preview": encode_cv2_to_base64_jpeg(annotated_after),
        "diff_preview": pixel_diff_signal.get("heatmap_overlay_base64", ""),
    }

    _LAST_CHANGE_DETECTION_RESULT = response_payload
    return response_payload


def get_last_change_detection_result() -> Dict[str, Any]:
    """Retrieve last analysis run, or synthesize a demo run if uninitialized."""
    global _LAST_CHANGE_DETECTION_RESULT
    if _LAST_CHANGE_DETECTION_RESULT is None:
        _LAST_CHANGE_DETECTION_RESULT = run_change_detection_analysis(shift_x=3.5, shift_y=-2.0, seed=42)
    return _LAST_CHANGE_DETECTION_RESULT
