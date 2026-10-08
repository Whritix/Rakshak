#!/usr/bin/env python3
"""Offline xView image/label audit and browser for the Harborwatch prototype."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import threading
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT))
LABEL_PATH = ROOT / "train_labels" / "xView_train.geojson"
SPLIT_DIRS = {"train": ROOT / "train_images", "val": ROOT / "val_images"}
S2_IMAGE_DIR = ROOT / "IMAGES" / "Browser_images"
S2_CSV_DIR = ROOT / "sentinal2"  # Retain the folder's supplied spelling.
VESSEL_MODEL = ROOT / "runs" / "train" / "xview_vessel_1024_extended" / "weights" / "best.pt"


def discover_images() -> dict[str, dict[str, Path]]:
    """Discover TIFFs recursively, tolerating the extra archive wrapper folders."""
    result: dict[str, dict[str, Path]] = {"train": {}, "val": {}}
    for split, folder in SPLIT_DIRS.items():
        for path in folder.rglob("*"):
            # macOS zip extraction leaves AppleDouble metadata files named like
            # ._109.tif inside __MACOSX; they are not raster images.
            if "__MACOSX" in path.parts or path.name.startswith("._"):
                continue
            if path.is_file() and path.suffix.lower() in {".tif", ".tiff"}:
                # Keep the first deterministic match if an archive contains duplicates.
                result[split].setdefault(path.name, path)
    return result


def load_dataset() -> tuple[dict, dict[str, dict[str, Path]]]:
    images = discover_images()
    if not LABEL_PATH.exists():
        raise FileNotFoundError(f"Expected xView labels at {LABEL_PATH}")

    print(f"Reading {LABEL_PATH.name} (this may take a little while)...", flush=True)
    with LABEL_PATH.open("r", encoding="utf-8") as source:
        geojson = json.load(source)

    by_image: dict[str, list[dict]] = defaultdict(list)
    category_counts: Counter = Counter()
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        image_id = props.get("image_id")
        category = props.get("type_id")
        raw_box = props.get("bounds_imcoords", "")
        try:
            box = [float(part.strip()) for part in raw_box.split(",")]
            if len(box) != 4:
                continue
        except (AttributeError, ValueError):
            continue
        if image_id:
            by_image[image_id].append({"class": category, "box": box})
            category_counts[str(category)] += 1

    present_train = set(images["train"])
    present_val = set(images["val"])
    label_ids = set(by_image)
    all_image_names = set(images["train"]) | set(images["val"])
    category_summary = [
        {"id": int(category), "count": count}
        for category, count in sorted(category_counts.items(), key=lambda item: int(item[0]))
    ]
    summary = {
        "title": "xView dataset audit",
        "label_file": str(LABEL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "label_features": sum(category_counts.values()),
        "label_image_ids": len(label_ids),
        "train_images": len(present_train),
        "validation_images": len(present_val),
        "train_images_with_labels": len(present_train & label_ids),
        "train_images_without_labels": len(present_train - label_ids),
        "label_ids_without_train_image": len(label_ids - present_train),
        "label_ids_found_in_validation": len(label_ids & present_val),
        "all_present_tiff_images": len(all_image_names),
        "classes": category_summary,
        "notes": [
            "xView is overhead imagery; it does not provide AIS vessel tracks or Sentinel-2 imagery.",
            "Class IDs are shown as numeric IDs because this GeoJSON does not include class names.",
            "Image coordinates in bounds_imcoords are used for the detection overlays.",
        ],
    }
    dataset = {"summary": summary, "labels": dict(by_image)}
    return dataset, images


def sentinel_catalog() -> tuple[list[dict], list[dict]]:
    """Read georeferencing from local TIFF tags and catalog CSVs without loading them."""
    assets = []
    for path in sorted(S2_IMAGE_DIR.glob("*.tif*")):
        try:
            with Image.open(path) as image:
                width, height = image.size
                scale = image.tag_v2.get(33550)
                tie = image.tag_v2.get(33922)
                geo_keys = image.tag_v2.get(34735, ())
                crs = "Unknown"
                # GeoKeyDirectory entries are groups of four; GeographicTypeGeoKey is 2048.
                for offset in range(4, len(geo_keys), 4):
                    if geo_keys[offset] == 2048 and geo_keys[offset + 1] == 0:
                        crs = f"EPSG:{geo_keys[offset + 3]}"
                        break
                bounds = None
                if scale and tie and len(scale) >= 2 and len(tie) >= 6:
                    x0, y0 = float(tie[3]), float(tie[4])
                    sx, sy = float(scale[0]), float(scale[1])
                    bounds = [x0, y0 - height * sy, x0 + width * sx, y0]
                stem = path.stem
                band = "True color" if "True_color" in stem else next(
                    (f"Band {code}" for code in ("B02", "B03", "B04", "B08", "B11", "B12") if code in stem),
                    "Unknown band",
                )
                assets.append({"name": path.name, "band": band, "width": width, "height": height,
                               "mode": image.mode, "crs": crs, "bounds": bounds,
                               "date": (re.search(r"20\d{2}-\d{2}-\d{2}", path.name) or [None])[0],
                               "bytes": path.stat().st_size})
        except Exception as exc:
            assets.append({"name": path.name, "band": "Unreadable", "error": str(exc), "bytes": path.stat().st_size})
    csv_files = []
    for path in sorted(S2_CSV_DIR.glob("*.csv")):
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                columns = reader.fieldnames or []
                sample = []
                for row in reader:
                    sample.append({key: row.get(key, "") for key in (
                        "scene_id", "lat", "lon", "detect_timestamp", "presence_score", "nonvessel_score",
                        "cloud_score", "mmsi", "matching_confidence",
                    )})
                    if len(sample) == 8:
                        break
            csv_files.append({"name": path.name, "bytes": path.stat().st_size, "columns": columns, "sample": sample})
        except Exception as exc:
            csv_files.append({"name": path.name, "bytes": path.stat().st_size, "error": str(exc)})
    return assets, csv_files


class ExplorerHandler(BaseHTTPRequestHandler):
    dataset: dict | None = None
    images: dict[str, dict[str, Path]] | None = None
    s2_assets: list[dict] = []
    s2_csv_files: list[dict] = []
    s2_detection_cache: dict[tuple, dict] = {}
    s2_detection_lock = threading.Lock()
    dataset_lock = threading.Lock()
    vessel_model = None
    vessel_model_lock = threading.Lock()
    inference_lock = threading.Lock()

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_bytes(self, body: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, value, status: int = 200):
        self.send_bytes(json.dumps(value, separators=(",", ":")).encode(), "application/json; charset=utf-8", status)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/":
            page = ROOT / "dataset_explorer.html"
            self.send_bytes(page.read_bytes(), "text/html; charset=utf-8")
            return
        if parsed.path == "/dashboard":
            page = ROOT / "index.html"
            self.send_bytes(page.read_bytes(), "text/html; charset=utf-8")
            return
        if parsed.path == "/sentinel2":
            page = ROOT / "sentinel2_explorer.html"
            self.send_bytes(page.read_bytes(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/s2/catalog":
            self.send_json({"assets": self.s2_assets, "csv_files": self.s2_csv_files})
            return
        if parsed.path == "/api/s2/detections":
            name = params.get("name", [""])[0]
            asset_name = params.get("asset", [""])[0]
            csv_asset = next((item for item in self.s2_csv_files if item["name"] == name), None)
            image_asset = next((item for item in self.s2_assets if item["name"] == asset_name), None)
            if not csv_asset or "pipev4" not in name.lower() or not image_asset or not image_asset.get("bounds"):
                self.send_json({"error": "Choose a local Pipe V4 CSV and a georeferenced Sentinel-2 image."}, 400)
                return
            west, south, east, north = image_asset["bounds"]
            # Cache repeated requests for the same footprint. Keep only one result,
            # since the source CSVs are very large and this is a local demo server.
            cache_key = (name, asset_name)
            if cache_key in type(self).s2_detection_cache:
                self.send_json(type(self).s2_detection_cache[cache_key])
                return
            path = S2_CSV_DIR / name
            result = []
            matches = 0
            try:
                with type(self).s2_detection_lock:
                    if cache_key in type(self).s2_detection_cache:
                        self.send_json(type(self).s2_detection_cache[cache_key])
                        return
                    with path.open("r", encoding="utf-8-sig", newline="") as stream:
                        for row in csv.DictReader(stream):
                            try:
                                lat, lon = float(row["lat"]), float(row["lon"])
                            except (KeyError, TypeError, ValueError):
                                continue
                            if west <= lon <= east and south <= lat <= north:
                                matches += 1
                                result.append({key: row.get(key, "") for key in (
                                    "detect_id", "scene_id", "detect_timestamp", "presence_score",
                                    "nonvessel_score", "cloud_score", "length_m_inferred",
                                    "speed_kn_inferred", "heading_deg_inferred", "matching_score",
                                    "matching_confidence", "mmsi",
                                )} | {"lat": lat, "lon": lon})
                # Return the strongest 5,000 if a busy footprint contains more points.
                result.sort(key=lambda item: float(item.get("presence_score") or 0), reverse=True)
                limited = len(result) > 5000
                result = result[:5000]
                payload = {"asset": name, "image": asset_name, "image_date": image_asset.get("date"),
                           "bounds": image_asset["bounds"], "count_in_footprint": matches,
                           "truncated": limited, "detections": result}
                type(self).s2_detection_cache.clear()
                type(self).s2_detection_cache[cache_key] = payload
                self.send_json(payload)
            except Exception as exc:
                self.send_json({"error": f"Could not scan detection CSV: {exc}"}, 500)
            return
        if parsed.path == "/api/s2/preview":
            image_name = params.get("name", [""])[0]
            asset = next((item for item in self.s2_assets if item["name"] == image_name), None)
            path = S2_IMAGE_DIR / image_name
            if not asset or not path.is_file() or path.parent.resolve() != S2_IMAGE_DIR.resolve():
                self.send_bytes(b"Image not found", "text/plain", 404)
                return
            try:
                with Image.open(path) as source:
                    source.thumbnail((1400, 1000), Image.Resampling.LANCZOS)
                    if source.mode in {"I;16", "I;16B", "I;16L", "I"}:
                        import numpy as np
                        values = np.asarray(source, dtype=np.float32)
                        low, high = np.percentile(values, (2, 98))
                        if not math.isfinite(float(low)) or not math.isfinite(float(high)) or high <= low:
                            low, high = float(values.min()), float(values.max())
                        scaled = np.zeros(values.shape, dtype=np.uint8) if high <= low else np.clip((values - low) * (255 / (high - low)), 0, 255).astype(np.uint8)
                        image = Image.fromarray(scaled, mode="L").convert("RGB")
                    else:
                        image = source.convert("RGB")
                    from io import BytesIO
                    output = BytesIO()
                    image.save(output, format="JPEG", quality=90)
                    self.send_bytes(output.getvalue(), "image/jpeg")
            except Exception as exc:
                self.send_bytes(str(exc).encode(), "text/plain", 422)
            return
        if parsed.path in {"/api/summary", "/api/images", "/api/image", "/api/detect"} and type(self).dataset is None:
            with type(self).dataset_lock:
                if type(self).dataset is None:
                    try:
                        type(self).dataset, type(self).images = load_dataset()
                    except Exception as exc:
                        self.send_json({"error": f"Could not load xView data: {exc}"}, 500)
                        return
        if parsed.path == "/api/summary":
            self.send_json(self.dataset["summary"])
            return
        if parsed.path == "/api/images":
            split = params.get("split", ["train"])[0]
            class_id = params.get("class", ["all"])[0]
            query = params.get("q", [""])[0].strip().lower()
            if split not in self.images:
                self.send_json({"error": "Unknown split"}, 400)
                return
            items = []
            for image_id, path in self.images[split].items():
                labels = self.dataset["labels"].get(image_id, [])
                if class_id != "all" and not any(str(label["class"]) == class_id for label in labels):
                    continue
                if query and query not in image_id.lower():
                    continue
                items.append({"id": image_id, "objects": len(labels), "path": path.relative_to(ROOT).as_posix()})
            items.sort(key=lambda item: item["id"].lower())
            self.send_json(items)
            return
        if parsed.path == "/api/image":
            split = params.get("split", ["train"])[0]
            image_id = params.get("id", [""])[0]
            path = self.images.get(split, {}).get(image_id)
            if not path:
                self.send_json({"error": "Image not found"}, 404)
                return
            try:
                with Image.open(path) as image:
                    width, height = image.size
            except Exception as exc:
                self.send_json({"error": f"Could not read TIFF: {exc}"}, 422)
                return
            self.send_json({"id": image_id, "split": split, "width": width, "height": height,
                            "objects": self.dataset["labels"].get(image_id, [])})
            return
        if parsed.path == "/api/detect":
            split = params.get("split", ["train"])[0]
            image_id = params.get("id", [""])[0]
            try:
                confidence = float(params.get("conf", ["0.25"])[0])
            except ValueError:
                self.send_json({"error": "Confidence must be a number from 0.01 to 0.99."}, 400)
                return
            if not 0.01 <= confidence <= 0.99:
                self.send_json({"error": "Confidence must be between 0.01 and 0.99."}, 400)
                return
            path = self.images.get(split, {}).get(image_id) if self.images else None
            if not path:
                self.send_json({"error": "Image not found."}, 404)
                return
            if not VESSEL_MODEL.is_file():
                self.send_json({"error": "Vessel model is not available. Train it with the command in DETECTOR_MVP.md."}, 503)
                return
            try:
                from ultralytics import YOLO
                if type(self).vessel_model is None:
                    with type(self).vessel_model_lock:
                        if type(self).vessel_model is None:
                            type(self).vessel_model = YOLO(str(VESSEL_MODEL))
                model = type(self).vessel_model
                predictions = []
                tile, overlap = 1024, 256
                with Image.open(path) as source:
                    image = source.convert("RGB")
                    width, height = image.size
                    stride = tile - overlap
                    xs = list(range(0, max(1, width - tile + 1), stride))
                    ys = list(range(0, max(1, height - tile + 1), stride))
                    if not xs or xs[-1] + tile < width: xs.append(max(0, width - tile))
                    if not ys or ys[-1] + tile < height: ys.append(max(0, height - tile))
                    with type(self).inference_lock:
                        for y0 in sorted(set(ys)):
                            for x0 in sorted(set(xs)):
                                crop = image.crop((x0, y0, min(width, x0 + tile), min(height, y0 + tile)))
                                result = model.predict(source=crop, imgsz=1024, conf=confidence,
                                                       iou=0.5, max_det=500, verbose=False)[0]
                                if result.boxes is None:
                                    continue
                                for box, score in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist()):
                                    x1, y1, x2, y2 = box
                                    predictions.append({"box": [x1 + x0, y1 + y0, x2 + x0, y2 + y0],
                                                        "class": 0, "name": "Vessel", "confidence": float(score)})
                predictions.sort(key=lambda item: item["confidence"], reverse=True)
                kept = []
                for item in predictions:
                    if all(_box_iou(item["box"], other["box"]) < 0.5 for other in kept):
                        kept.append(item)
                self.send_json({"id": image_id, "split": split, "model": VESSEL_MODEL.relative_to(ROOT).as_posix(),
                                "confidence_threshold": confidence, "width": width, "height": height,
                                "count": len(kept), "detections": kept})
            except Exception as exc:
                self.send_json({"error": f"Vessel inference failed: {exc}"}, 500)
            return
        if parsed.path == "/thumb":
            split = params.get("split", ["train"])[0]
            image_id = params.get("id", [""])[0]
            path = self.images.get(split, {}).get(image_id)
            if not path:
                self.send_bytes(b"Image not found", "text/plain", 404)
                return
            try:
                with Image.open(path) as source:
                    image = source.convert("RGB")
                    image.thumbnail((1100, 850), Image.Resampling.LANCZOS)
                    from io import BytesIO
                    out = BytesIO()
                    image.save(out, format="JPEG", quality=88, optimize=True)
                    self.send_bytes(out.getvalue(), "image/jpeg")
            except Exception as exc:
                self.send_bytes(str(exc).encode(), "text/plain", 422)
            return
        self.send_bytes(b"Not found", "text/plain", 404)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="write dataset_audit.json and exit")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    s2_assets, s2_csv_files = sentinel_catalog()
    if args.audit:
        dataset, _ = load_dataset()
        dataset["summary"].update(sentinel_summary(s2_assets, s2_csv_files))
        out = ROOT / "dataset_audit.json"
        out.write_text(json.dumps(dataset["summary"], indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out}")
        print(json.dumps(dataset["summary"], indent=2))
        return
    ExplorerHandler.dataset = None
    ExplorerHandler.images = None
    ExplorerHandler.s2_assets, ExplorerHandler.s2_csv_files = s2_assets, s2_csv_files
    server = ThreadingHTTPServer((args.host, args.port), ExplorerHandler)
    print(f"Harborwatch dataset explorer: http://{args.host}:{args.port}/", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def sentinel_summary(assets: list[dict], csv_files: list[dict]) -> dict:
    return {
        "sentinel2_geotiff_assets": len(assets),
        "sentinel2_csv_files": len(csv_files),
        "sentinel2_csv_total_bytes": sum(item["bytes"] for item in csv_files),
        "sentinel2_asset_catalog": [
            {key: item.get(key) for key in ("name", "band", "width", "height", "crs", "bounds", "bytes")}
            for item in assets
        ],
        "sentinel2_csv_catalog": [
            {"name": item["name"], "bytes": item["bytes"], "columns": len(item.get("columns", []))}
            for item in csv_files
        ],
    }


def _box_iou(a: list[float], b: list[float]) -> float:
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    return intersection / max(1e-9, area_a + area_b - intersection)


if __name__ == "__main__":
    main()
