"""Generate Tile-Level Oversampling Weights for xView Surveillance Training.

Calculates an importance weight for each training tile in runs/xview_yolo/images/train/
based on inverse-frequency weighting of its annotated classes. Tiles containing rare
Vessel or Aircraft objects receive high sampling weights (up to 50.0), while empty background
or common infrastructure-only tiles receive baseline weights.

Outputs:
  runs/xview_yolo/train_weights.txt
"""
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / 'runs' / 'xview_yolo' / 'images' / 'train'
LBL_DIR = ROOT / 'runs' / 'xview_yolo' / 'labels' / 'train'
OUT_FILE = ROOT / 'runs' / 'xview_yolo' / 'train_weights.txt'

# Baseline class frequencies from original xView training set
DEFAULT_CLASS_FREQ = {
    0: 3392,    # Vessel
    1: 644,     # Aircraft
    2: 160496,  # Vehicle
    3: 222974   # Infrastructure
}
TOTAL_BOXES = 387506
MAX_WEIGHT = 50.0
BACKGROUND_WEIGHT = 0.1


def compute_tile_weight(label_path: Path, class_freq: dict, total: int) -> float:
    """Compute oversampling weight for a single tile label file."""
    if not label_path.exists():
        return BACKGROUND_WEIGHT

    lines = [l.strip() for l in label_path.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not lines:
        return BACKGROUND_WEIGHT

    classes = []
    for l in lines:
        parts = l.split()
        if parts:
            try:
                classes.append(int(parts[0]))
            except ValueError:
                pass

    if not classes:
        return BACKGROUND_WEIGHT

    weights = [total / max(1, class_freq.get(c, 1000)) for c in classes]
    return min(max(weights), MAX_WEIGHT)


def build_sampler_weights():
    if not IMG_DIR.exists() or not LBL_DIR.exists():
        print(f"ERROR: Dataset directories missing:\n  Images: {IMG_DIR}\n  Labels: {LBL_DIR}", file=sys.stderr)
        sys.exit(1)

    print("=" * 68)
    print("  RAKSHAK C4ISR - TILE-LEVEL OVERSAMPLING WEIGHT CALCULATOR")
    print("=" * 68)

    # Get sorted list of images to ensure deterministic matching order
    image_paths = sorted(
        [p for p in IMG_DIR.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.tif', '.tiff')]
    )

    if not image_paths:
        print(f"ERROR: No image files found in {IMG_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Indexing {len(image_paths)} training tiles...")

    tile_weights = []
    high_weight_count = 0
    bg_count = 0

    for img_p in image_paths:
        lbl_p = LBL_DIR / (img_p.stem + '.txt')
        w = compute_tile_weight(lbl_p, DEFAULT_CLASS_FREQ, TOTAL_BOXES)
        tile_weights.append(w)
        if w >= 20.0:
            high_weight_count += 1
        elif w == BACKGROUND_WEIGHT:
            bg_count += 1

    # Write out weights file (one float per line)
    OUT_FILE.write_text('\n'.join(f"{w:.4f}" for w in tile_weights) + '\n', encoding='utf-8')

    avg_w = sum(tile_weights) / len(tile_weights)
    print("\n[OVERSAMPLING STATS]")
    print(f"  Total tiles evaluated      : {len(tile_weights)}")
    print(f"  High-priority rare tiles   : {high_weight_count} ({high_weight_count / len(tile_weights) * 100:.1f}%)")
    print(f"  Background tiles (w=0.1)   : {bg_count} ({bg_count / len(tile_weights) * 100:.1f}%)")
    print(f"  Average sampling weight    : {avg_w:.2f}")
    print(f"\n[OUTPUT] Written sampling weights to:\n  {OUT_FILE}")
    print("=" * 68)


if __name__ == '__main__':
    build_sampler_weights()
