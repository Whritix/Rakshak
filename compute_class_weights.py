"""Compute Class-Weighted Loss Weights for Imbalanced xView Aerial Surveillance.

Scans the xView YOLO training label directory, calculates per-class instance distributions,
computes inverse-frequency weights to counterbalance severe class imbalance (e.g. Vessel and
Aircraft rarity), and prints the recommended weights configuration.
"""
import sys
import argparse
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
LABELS_DIR = ROOT / 'runs' / 'xview_yolo' / 'labels' / 'train'
DATA_YAML = ROOT / 'runs' / 'xview_yolo' / 'data.yaml'

CLASS_NAMES = {
    0: 'Vessel',
    1: 'Aircraft',
    2: 'Vehicle',
    3: 'Infrastructure'
}

MAX_CLIP_WEIGHT = 50.0


def compute_weights(apply_to_yaml: bool = False):
    if not LABELS_DIR.exists():
        print(f"ERROR: Labels directory not found at {LABELS_DIR}", file=sys.stderr)
        sys.exit(1)

    print("=" * 65)
    print("  RAKSHAK C4ISR - INVERSE-FREQUENCY CLASS WEIGHT CALCULATOR")
    print("=" * 65)
    print(f"Scanning label directory: {LABELS_DIR} ...")

    counts = Counter()
    total_boxes = 0
    empty_tiles = 0
    total_files = 0

    for label_path in LABELS_DIR.glob('*.txt'):
        total_files += 1
        lines = label_path.read_text(encoding='utf-8').strip().splitlines()
        if not lines:
            empty_tiles += 1
            continue
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            cls_id = int(parts[0])
            counts[cls_id] += 1
            total_boxes += 1

    print(f"\nScanned {total_files} tiles ({empty_tiles} background tiles, {total_boxes} total bounding boxes).\n")
    print(f"{'Class ID':<10} {'Class Name':<18} {'Instance Count':<16} {'Raw Share (%)':<15} {'Raw Inv-Weight':<16} {'Clipped Weight'}")
    print("-" * 90)

    clipped_weights = []
    raw_weights = []

    for cls_id in sorted(CLASS_NAMES.keys()):
        name = CLASS_NAMES[cls_id]
        count = counts[cls_id]
        share = (count / total_boxes * 100) if total_boxes else 0.0
        raw_inv = (total_boxes / count) if count > 0 else MAX_CLIP_WEIGHT
        clipped_inv = min(round(raw_inv, 2), MAX_CLIP_WEIGHT)

        raw_weights.append(round(raw_inv, 2))
        clipped_weights.append(clipped_inv)

        print(f"{cls_id:<10} {name:<18} {count:<16} {share:>6.2f}%         {raw_inv:>8.2f}         {clipped_inv:>6.2f}")

    print("=" * 90)
    print("\n[RECOMMENDED data.yaml WEIGHT CONFIGURATION]")
    print(f"# Inverse-frequency class weights (clipped at {MAX_CLIP_WEIGHT} for loss stability)")
    print(f"weights: {clipped_weights}")

    if apply_to_yaml and DATA_YAML.exists():
        yaml_content = f"""path: {ROOT.as_posix()}/runs/xview_yolo
train: images/train
val: images/val
names:
  0: Vessel
  1: Aircraft
  2: Vehicle
  3: Infrastructure
# Inverse-frequency class weights (clipped at {MAX_CLIP_WEIGHT} for stability)
weights: {clipped_weights}
"""
        DATA_YAML.write_text(yaml_content, encoding='utf-8')
        print(f"\n[APPLIED] Successfully updated {DATA_YAML}")

    return clipped_weights


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calculate class weights for YOLO focal loss")
    parser.add_argument('--apply', action='store_true', help="Write calculated weights directly to data.yaml")
    args = parser.parse_args()
    compute_weights(apply_to_yaml=args.apply)
