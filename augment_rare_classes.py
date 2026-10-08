"""Triple rare-class (Vessel, Aircraft) training images via geometric augmentation.

Finds all training tiles in xView containing Vessel (cls 0) or Aircraft (cls 1),
generates 3 geometrically rotated copies (90 deg, 180 deg, 270 deg), and applies
exact coordinate transformations to the YOLO bounding box annotations so that
rare class representations are multiplied 4x without synthetic label noise.
"""
import sys
import argparse
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / 'runs' / 'xview_yolo' / 'images' / 'train'
LBL_DIR = ROOT / 'runs' / 'xview_yolo' / 'labels' / 'train'
RARE_CLASSES = {0, 1}  # 0: Vessel, 1: Aircraft


def rotate_yolo_bbox(cls_id: int, xc: float, yc: float, w: float, h: float, angle_deg: int):
    """Transform normalized YOLO bounding box [xc, yc, w, h] under CCW image rotation."""
    if angle_deg == 90:
        xc_new = yc
        yc_new = 1.0 - xc
        w_new = h
        h_new = w
    elif angle_deg == 180:
        xc_new = 1.0 - xc
        yc_new = 1.0 - yc
        w_new = w
        h_new = h
    elif angle_deg in (270, -90):
        xc_new = 1.0 - yc
        yc_new = xc
        w_new = h
        h_new = w
    else:
        raise ValueError(f"Unsupported rotation angle: {angle_deg}")

    # Clamp to valid normalized range
    xc_new = max(0.001, min(0.999, xc_new))
    yc_new = max(0.001, min(0.999, yc_new))
    w_new = max(0.001, min(0.999, w_new))
    h_new = max(0.001, min(0.999, h_new))
    return f"{cls_id} {xc_new:.6f} {yc_new:.6f} {w_new:.6f} {h_new:.6f}"


def augment_rare_classes(dry_run: bool = False):
    if not IMG_DIR.exists() or not LBL_DIR.exists():
        print(f"ERROR: Dataset directories missing:\n  Images: {IMG_DIR}\n  Labels: {LBL_DIR}", file=sys.stderr)
        sys.exit(1)

    print("=" * 68)
    print("  RAKSHAK C4ISR - RARE CLASS GEOMETRIC AUGMENTATION PIPELINE")
    print("=" * 68)
    print(f"Scanning labels in: {LBL_DIR}")
    print(f"Targeting rare classes: {RARE_CLASSES} (0: Vessel, 1: Aircraft)\n")

    candidates = []
    # Identify label files that have rare classes (and are not already augmented files)
    for lbl_file in sorted(LBL_DIR.glob('*.txt')):
        if '_aug_' in lbl_file.name:
            continue

        lines = [l.strip() for l in lbl_file.read_text(encoding='utf-8').splitlines() if l.strip()]
        if not lines:
            continue

        classes_in_file = set()
        for line in lines:
            parts = line.split()
            if parts:
                classes_in_file.add(int(parts[0]))

        if classes_in_file.intersection(RARE_CLASSES):
            candidates.append((lbl_file, lines, classes_in_file))

    print(f"Found {len(candidates)} tiles containing Vessel and/or Aircraft.")
    if not candidates:
        print("No candidates found or dataset already processed.")
        return

    if dry_run:
        print(f"[DRY RUN] Would generate {len(candidates) * 3} augmented images & labels.")
        return

    augmented_images = 0
    augmented_boxes = 0

    rotations = [
        (90, 'rot90'),
        (180, 'rot180'),
        (270, 'rot270'),
    ]

    for idx, (lbl_file, lines, classes) in enumerate(candidates, 1):
        # Find matching image file
        img_file = IMG_DIR / (lbl_file.stem + '.jpg')
        if not img_file.exists():
            img_file = IMG_DIR / (lbl_file.stem + '.png')
        if not img_file.exists():
            img_file = IMG_DIR / (lbl_file.stem + '.tif')
        if not img_file.exists():
            continue

        try:
            with Image.open(img_file) as img:
                img_rgb = img.convert('RGB')
                for angle, suffix in rotations:
                    aug_stem = f"{lbl_file.stem}_aug_{suffix}"
                    target_img = IMG_DIR / f"{aug_stem}.jpg"
                    target_lbl = LBL_DIR / f"{aug_stem}.txt"

                    # Skip if already generated
                    if target_img.exists() and target_lbl.exists():
                        continue

                    # 1. Rotate image
                    aug_img = img_rgb.rotate(angle, expand=True)
                    aug_img.save(target_img, format='JPEG', quality=95)

                    # 2. Transform bounding boxes
                    aug_lines = []
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 5:
                            cls_id = int(parts[0])
                            xc = float(parts[1])
                            yc = float(parts[2])
                            w = float(parts[3])
                            h = float(parts[4])
                            transformed = rotate_yolo_bbox(cls_id, xc, yc, w, h, angle)
                            aug_lines.append(transformed)
                            augmented_boxes += 1

                    target_lbl.write_text('\n'.join(aug_lines) + '\n', encoding='utf-8')
                    augmented_images += 1

        except Exception as e:
            print(f"Warning: Failed to process {img_file.name}: {e}", file=sys.stderr)

        if idx % 100 == 0 or idx == len(candidates):
            print(f"Processed {idx}/{len(candidates)} tiles... (created {augmented_images} augmented images)")

    print("=" * 68)
    print(f"SUCCESS: Generated {augmented_images} augmented tiles ({augmented_boxes} transformed boxes).")
    print(f"Vessel and Aircraft training samples have been quadrupled.")
    print("=" * 68)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Augment rare classes (Vessel, Aircraft) in xView dataset")
    parser.add_argument('--dry-run', action='store_true', help="Scan and report counts without writing files")
    args = parser.parse_args()
    augment_rare_classes(dry_run=args.dry_run)
