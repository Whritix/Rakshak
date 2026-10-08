#!/usr/bin/env python3
"""Small xView-to-YOLO training and satellite-image detection workflow.

This hackathon MVP groups the xView fine-grained labels into four visual classes:
vessel, aircraft, vehicle, and infrastructure. It is a research/demo tool, not an
operational threat classifier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
# Keep Ultralytics settings inside this project. This also works in restricted
# Windows environments where the default per-user roaming directory is denied.
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT))
IMAGE_ROOT = ROOT / "train_images"
LABEL_FILE = ROOT / "train_labels" / "xView_train.geojson"
DATA_ROOT = ROOT / "runs" / "xview_yolo"
VESSEL_DATA_ROOT = ROOT / "runs" / "xview_vessel"
NAMES = ["Vessel", "Aircraft", "Vehicle", "Infrastructure"]
CLASS_GROUPS = {
    0: {40, 41, 42, 44, 45, 47, 49, 50, 51, 52},
    1: {11, 12, 13, 15},
    2: set(range(17, 39)) | {53, 60, 61, 62, 63, 64, 65, 66},
    3: {71, 72, 73, 74, 76, 77, 79, 83, 84, 86, 89, 91, 93, 94},
}


def image_files() -> dict[str, Path]:
    return {
        p.name: p for p in IMAGE_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}
        and "__MACOSX" not in p.parts and not p.name.startswith("._")
    }


def load_labels() -> dict[str, list[tuple[int, float, float, float, float]]]:
    if not LABEL_FILE.exists():
        raise FileNotFoundError(f"Missing {LABEL_FILE}")
    with LABEL_FILE.open("r", encoding="utf-8") as f:
        geo = json.load(f)
    grouped: dict[str, list[tuple[int, float, float, float, float]]] = defaultdict(list)
    for feature in geo.get("features", []):
        props = feature.get("properties", {})
        try:
            image_id = str(props["image_id"])
            x1, y1, x2, y2 = map(float, props["bounds_imcoords"].split(","))
            type_id = int(props["type_id"])
        except (KeyError, TypeError, ValueError):
            continue
        class_id = next((i for i, ids in CLASS_GROUPS.items() if type_id in ids), None)
        if class_id is not None and x2 > x1 and y2 > y1:
            grouped[image_id].append((class_id, x1, y1, x2, y2))
    return grouped


def prepare(args: argparse.Namespace) -> None:
    files, labels = image_files(), load_labels()
    ids = sorted(files.keys() & labels.keys())
    if not ids:
        raise RuntimeError("No training TIFFs matched the xView labels.")
    random.Random(args.seed).shuffle(ids)
    val_ids = set(ids[:max(1, round(len(ids) * args.val_fraction))])
    for split in ("train", "val"):
        (DATA_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATA_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)

    positives: dict[str, list[tuple[Path, str]]] = {"train": [], "val": []}
    negatives: dict[str, list[tuple[Path, str]]] = {"train": [], "val": []}
    print(f"Tiling {len(ids)} matched scenes at {args.tile}px; this may take a while.")
    for image_id in ids:
        split = "val" if image_id in val_ids else "train"
        try:
            with Image.open(files[image_id]) as source:
                image = source.convert("RGB")
                width, height = image.size
                step = max(1, args.tile - args.overlap)
                starts_x = list(range(0, max(1, width - args.tile + 1), step))
                starts_y = list(range(0, max(1, height - args.tile + 1), step))
                if not starts_x or starts_x[-1] + args.tile < width:
                    starts_x.append(max(0, width - args.tile))
                if not starts_y or starts_y[-1] + args.tile < height:
                    starts_y.append(max(0, height - args.tile))
                for y0 in sorted(set(starts_y)):
                    for x0 in sorted(set(starts_x)):
                        xend, yend = min(width, x0 + args.tile), min(height, y0 + args.tile)
                        tile_name = f"{Path(image_id).stem}_{x0}_{y0}"
                        out_image = DATA_ROOT / "images" / split / f"{tile_name}.jpg"
                        out_label = DATA_ROOT / "labels" / split / f"{tile_name}.txt"
                        rows = []
                        for cls, x1, y1, x2, y2 in labels[image_id]:
                            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                            if x0 <= cx < xend and y0 <= cy < yend:
                                left, top = max(x0, x1), max(y0, y1)
                                right, bottom = min(xend, x2), min(yend, y2)
                                if right > left and bottom > top:
                                    bw, bh = xend - x0, yend - y0
                                    xc, yc = ((left + right) / 2 - x0) / bw, ((top + bottom) / 2 - y0) / bh
                                    nw, nh = (right - left) / bw, (bottom - top) / bh
                                    rows.append(f"{cls} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")
                        if rows:
                            image.crop((x0, y0, xend, yend)).save(out_image, quality=92)
                            out_label.write_text("\n".join(rows) + "\n", encoding="utf-8")
                            positives[split].append((out_image, out_label))
                        else:
                            negatives[split].append((out_image, out_label))
        except Exception as exc:
            print(f"Skipping {image_id}: {exc}", file=sys.stderr)

    # A bounded sample of empty tiles teaches background without creating a huge dataset.
    rng = random.Random(args.seed)
    for split in ("train", "val"):
        rng.shuffle(negatives[split])
        keep = min(len(negatives[split]), max(8, len(positives[split]) // 4))
        for image_path, label_path in negatives[split][:keep]:
            # Recreate only the selected empty crops to limit temporary disk use.
            stem = image_path.stem
            _, sx, sy = stem.rsplit("_", 2)
            image_id = next((name for name, path in files.items() if Path(name).stem == stem.rsplit("_", 2)[0]), None)
            if image_id is None:
                continue
            with Image.open(files[image_id]) as source:
                source.convert("RGB").crop((int(sx), int(sy), int(sx) + args.tile, int(sy) + args.tile)).save(image_path, quality=92)
            label_path.write_text("", encoding="utf-8")

    config = DATA_ROOT / "data.yaml"
    config.write_text(
        f"path: {DATA_ROOT.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n"
        + "\n".join(f"  {i}: {name}" for i, name in enumerate(NAMES)) + "\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(positives['train'])} train and {len(positives['val'])} validation positive tiles.")
    print(f"Sampled up to 1:4 empty tiles. Dataset config: {config}")


def prepare_vessel(args: argparse.Namespace) -> None:
    """Build a vessel-only dataset with a controlled number of hard negatives."""
    source_root = DATA_ROOT
    output_root = Path(args.output).expanduser().resolve()
    if not (source_root / "data.yaml").exists():
        raise SystemExit("Prepare the xView tiles first: python satellite_detector.py prepare")
    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f"Output already exists and is non-empty: {output_root}; choose another --output.")

    rng = random.Random(args.seed)
    for split in ("train", "val"):
        image_dir = source_root / "images" / split
        label_dir = source_root / "labels" / split
        positive: list[tuple[Path, list[str]]] = []
        negative: list[Path] = []
        for label_path in label_dir.glob("*.txt"):
            image_path = image_dir / f"{label_path.stem}.jpg"
            if not image_path.is_file():
                continue
            rows = [line for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            vessel_rows = [line for line in rows if line.split(maxsplit=1)[0] == "0"]
            if vessel_rows:
                positive.append((image_path, vessel_rows))
            else:
                negative.append(image_path)

        rng.shuffle(negative)
        selected_negatives = negative[:min(len(negative), len(positive) * args.negative_ratio)]
        selected = [(image, rows) for image, rows in positive]
        selected.extend((image, []) for image in selected_negatives)
        rng.shuffle(selected)
        out_images = output_root / "images" / split
        out_labels = output_root / "labels" / split
        out_images.mkdir(parents=True, exist_ok=True)
        out_labels.mkdir(parents=True, exist_ok=True)
        for image_path, rows in selected:
            destination = out_images / image_path.name
            try:
                os.link(image_path, destination)
            except OSError:
                # Cross-volume or policy restrictions: preserve correctness with a regular copy.
                import shutil
                shutil.copy2(image_path, destination)
            (out_labels / f"{image_path.stem}.txt").write_text(
                "\n".join(rows) + ("\n" if rows else ""), encoding="utf-8"
            )
        print(f"{split}: {len(positive)} vessel tiles + {len(selected_negatives)} sampled hard negatives")

    config = output_root / "data.yaml"
    config.write_text(
        f"path: {output_root.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: Vessel\n",
        encoding="utf-8",
    )
    print(f"Vessel-only dataset config: {config}")


def train(args: argparse.Namespace) -> None:
    if args.epochs < 1 or args.imgsz < 32 or args.batch < 1 or args.patience < 0 or args.max_det < 1:
        raise SystemExit("epochs, batch, and max-det must be positive; imgsz must be at least 32; patience cannot be negative")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install dependencies first: python -m pip install -r requirements-detector.txt") from exc
    config = Path(args.data).expanduser().resolve()
    if not config.exists():
        raise SystemExit("Prepare the xView tiles first: python satellite_detector.py prepare")
    model = YOLO(args.weights)
    close_mosaic = args.close_mosaic if args.close_mosaic is not None else min(10, max(0, args.epochs // 5))
    model.train(data=str(config), imgsz=args.imgsz, epochs=args.epochs, batch=args.batch,
                workers=0, device=args.device, project=str(ROOT / "runs" / "train"),
                name=args.name, patience=args.patience, close_mosaic=close_mosaic,
                max_det=args.max_det, plots=True)


def detect(args: argparse.Namespace) -> None:
    if args.tile < 32 or not 0 <= args.overlap < args.tile:
        raise SystemExit("tile must be at least 32 pixels and overlap must be between 0 and tile-1")
    if args.imgsz < 32 or args.max_det < 1:
        raise SystemExit("imgsz must be at least 32 and max-det must be positive")
    if not 0.0 < args.conf < 1.0 or not 0.0 < args.iou <= 1.0:
        raise SystemExit("conf must be between 0 and 1, and iou must be greater than 0 and at most 1")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install dependencies first: python -m pip install -r requirements-detector.txt") from exc
    image_path = Path(args.image).expanduser().resolve()
    model_path = Path(args.model).expanduser().resolve()
    if not image_path.is_file():
        raise SystemExit(f"Image not found: {image_path}")
    if not model_path.is_file():
        raise SystemExit(f"Model not found: {model_path}. Train it first.")
    model = YOLO(str(model_path))
    predictions = []
    tile, overlap = args.tile, args.overlap
    with Image.open(image_path) as src:
        image = src.convert("RGB")
        width, height = image.size
        stride = max(1, tile - overlap)
        xs = list(range(0, max(1, width - tile + 1), stride))
        ys = list(range(0, max(1, height - tile + 1), stride))
        if not xs or xs[-1] + tile < width: xs.append(max(0, width - tile))
        if not ys or ys[-1] + tile < height: ys.append(max(0, height - tile))
        for y0 in sorted(set(ys)):
            for x0 in sorted(set(xs)):
                crop = image.crop((x0, y0, min(width, x0 + tile), min(height, y0 + tile)))
                result = model.predict(source=crop, imgsz=args.imgsz, conf=args.conf, iou=args.iou,
                                       max_det=args.max_det, verbose=False)[0]
                if result.boxes is None:
                    continue
                for box, cls, score in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.cls.cpu().tolist(), result.boxes.conf.cpu().tolist()):
                    x1, y1, x2, y2 = box
                    predictions.append({"box": [x1 + x0, y1 + y0, x2 + x0, y2 + y0],
                                        "class": int(cls), "name": NAMES[int(cls)], "confidence": float(score)})
        # Greedy global NMS removes duplicate detections in the overlapping tiles.
        predictions.sort(key=lambda item: item["confidence"], reverse=True)
        kept = []
        for item in predictions:
            if all(item["class"] != other["class"] or _iou(item["box"], other["box"]) < args.iou for other in kept):
                kept.append(item)
        output = Path(args.output).expanduser().resolve() if args.output else image_path.with_name(image_path.stem + "_detections.jpg")
        output.parent.mkdir(parents=True, exist_ok=True)
        annotated = image.copy()
        draw = ImageDraw.Draw(annotated)
        for item in kept:
            box = tuple(round(v) for v in item["box"])
            label = f"{item['name']} {item['confidence']:.2f}"
            draw.rectangle(box, outline="#ff4d4f", width=max(2, width // 1500))
            draw.text((box[0], max(0, box[1] - 16)), label, fill="#ff4d4f", stroke_width=1, stroke_fill="white")
        annotated.save(output, quality=94)
    print(f"Found {len(kept)} objects. Annotated image: {output}")
    for item in kept:
        print(f"{item['name']}: {item['confidence']:.2f} at {tuple(round(v) for v in item['box'])}")


def _iou(a: list[float], b: list[float]) -> float:
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, right - left) * max(0, bottom - top)
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    return inter / max(1e-9, area_a + area_b - inter)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="tile and convert the xView labels to YOLO format")
    prep.add_argument("--tile", type=int, default=1024)
    prep.add_argument("--overlap", type=int, default=256)
    prep.add_argument("--val-fraction", type=float, default=0.2)
    prep.add_argument("--seed", type=int, default=42)
    prep.set_defaults(func=prepare)
    vessel_prep = commands.add_parser("prepare-vessel", help="build a balanced vessel-only dataset from prepared xView tiles")
    vessel_prep.add_argument("--output", default=str(VESSEL_DATA_ROOT))
    vessel_prep.add_argument("--negative-ratio", type=int, default=2,
                             help="sample this many non-vessel tiles per positive vessel tile")
    vessel_prep.add_argument("--seed", type=int, default=42)
    vessel_prep.set_defaults(func=prepare_vessel)
    fit = commands.add_parser("train", help="fine-tune a compact YOLO detector")
    fit.add_argument("--weights", default="yolo11n.pt")
    fit.add_argument("--data", default=str(DATA_ROOT / "data.yaml"))
    fit.add_argument("--name", default="xview_hackathon")
    fit.add_argument("--epochs", type=int, default=30)
    fit.add_argument("--imgsz", type=int, default=1024)
    fit.add_argument("--batch", type=int, default=2)
    fit.add_argument("--patience", type=int, default=8)
    fit.add_argument("--close-mosaic", type=int, default=None,
                     help="mosaic is disabled for this many final epochs; default scales with total epochs")
    fit.add_argument("--max-det", type=int, default=500,
                     help="maximum detections per tile for training validation")
    fit.add_argument("--device", default="cpu", help="cpu or a CUDA device such as 0")
    fit.set_defaults(func=train)
    infer = commands.add_parser("detect", help="detect and label objects on a satellite TIFF/image")
    infer.add_argument("image")
    infer.add_argument("--model", default=str(ROOT / "runs" / "train" / "xview_hackathon" / "weights" / "best.pt"))
    infer.add_argument("--output")
    infer.add_argument("--tile", type=int, default=1024)
    infer.add_argument("--overlap", type=int, default=256)
    infer.add_argument("--imgsz", type=int, default=1024)
    infer.add_argument("--conf", type=float, default=0.25)
    infer.add_argument("--iou", type=float, default=0.5)
    infer.add_argument("--max-det", type=int, default=500,
                       help="maximum detections per tile")
    infer.set_defaults(func=detect)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
