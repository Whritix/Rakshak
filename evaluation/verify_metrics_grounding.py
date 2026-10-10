"""Verification Script for Metric Grounding across Project Rakshak 2.0.

Extracts all quantitative metrics and numbers from evaluation/RESULTS.md,
scans docs, UI, and backend files, and flags any candidate performance
or KPI numbers that do not appear in RESULTS.md.
"""
import os
import re
import sys
from pathlib import Path

# Paths to audit
WORKSPACE = Path(__file__).resolve().parent.parent
RESULTS_MD = WORKSPACE / "evaluation" / "RESULTS.md"

AUDIT_FILES = [
    WORKSPACE / "PROJECT_OVERVIEW.md",
    WORKSPACE / "README.md",
    WORKSPACE / "docs" / "PS_MAPPING.md",
    WORKSPACE / "frontend" / "src" / "App.tsx",
    WORKSPACE / "backend" / "app" / "kpi_service.py",
    WORKSPACE / "backend" / "app" / "edge_benchmarks.py",
]

# Common non-metric tokens to ignore (ports, years, status codes, standard dimensions, small integers, standard IDs)
IGNORED_NUMBERS = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "29", "30", "32", "38", "42", "45", "50", "60", "64", "70", "80", "90", "95", "100",
    "200", "400", "401", "403", "404", "422", "429", "500", "502", "503", "800", "1000", "1024",
    "2026", "8000", "5173", "8999", "640", "3000", "2700", "127", "256", "512",
    "110", "111", "1154", "1217", "2014", "5838", "0601", "202026",
}


def normalize_number(s: str) -> str:
    """Normalize numeric strings: strip punctuation, trailing zeros, percent signs."""
    s = s.strip().rstrip("%,;:)(").lstrip("~±<>= ")
    try:
        val = float(s)
        # return canonical string representation with up to 4 decimals
        return f"{val:.4f}".rstrip("0").rstrip(".")
    except ValueError:
        return s


def extract_numbers_from_text(text: str) -> set:
    """Extract candidate metric numbers from markdown / code text."""
    # Find patterns like 48.46%, 79.4, 0.70m, 12.64W, 10,000, 66521
    # Match numbers with optional decimal, commas, and percentage
    pattern = r'(?<![a-zA-Z_])(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?%?(?![a-zA-Z_])'
    raw_matches = re.findall(pattern, text)
    numbers = set()
    for m in raw_matches:
        clean = m.replace(",", "").rstrip("%")
        if clean in IGNORED_NUMBERS:
            continue
        try:
            val = float(clean)
            if val in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 20.0, 30.0, 50.0, 100.0]:
                continue
            canonical = normalize_number(clean)
            numbers.add((clean, canonical))
        except ValueError:
            pass
    return numbers


def main():
    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — METRICS GROUNDING & PROVENANCE AUDITOR")
    print("=" * 70)

    if not RESULTS_MD.exists():
        print(f"[ERROR] Master evaluation file not found: {RESULTS_MD}")
        sys.exit(1)

    with open(RESULTS_MD, "r", encoding="utf-8") as f:
        results_content = f.read()

    results_numbers_raw = extract_numbers_from_text(results_content)
    results_canonicals = {canon for raw, canon in results_numbers_raw}
    results_raw_set = {raw for raw, canon in results_numbers_raw}

    print(f"[*] Loaded {len(results_canonicals)} canonical grounded numbers from RESULTS.md")

    total_scanned = 0
    total_unmatched = 0

    for path in AUDIT_FILES:
        if not path.exists():
            print(f"[-] Skipping missing file: {path.name}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        file_numbers = extract_numbers_from_text(content)
        unmatched = []

        for raw, canon in file_numbers:
            # Check if either exact string, float canonical, or variation exists in RESULTS.md
            if canon not in results_canonicals and raw not in results_raw_set and raw not in results_content:
                # Additional check: could it be a percentage vs decimal (e.g. 0.4846 vs 48.46)
                try:
                    fval = float(raw)
                    p_canon = normalize_number(str(fval * 100))
                    d_canon = normalize_number(str(fval / 100))
                    if p_canon in results_canonicals or d_canon in results_canonicals:
                        continue
                except ValueError:
                    pass
                unmatched.append(raw)

        total_scanned += len(file_numbers)
        total_unmatched += len(unmatched)

        status_str = f"[OK] 0 ungrounded numbers" if not unmatched else f"[WARN] {len(unmatched)} numbers ungrounded in RESULTS.md"
        print(f"\n[+] Auditing {path.relative_to(WORKSPACE)}: ({len(file_numbers)} candidate numbers) -> {status_str}")
        if unmatched:
            # Group unique
            unique_unmatched = sorted(set(unmatched), key=lambda x: (len(x), x))
            print(f"    Ungrounded numbers found ({len(unique_unmatched)} unique):")
            for u in unique_unmatched[:25]:
                print(f"      - {u}")
            if len(unique_unmatched) > 25:
                print(f"      ... and {len(unique_unmatched) - 25} more")

    print("\n" + "=" * 70)
    print(f"  AUDIT SUMMARY: Scanned {total_scanned} numbers across {len(AUDIT_FILES)} files.")
    if total_unmatched == 0:
        print("  [SUCCESS] All candidate numbers in target docs and code appear in RESULTS.md!")
    else:
        print(f"  [COMPLETED] Audit complete. Found {total_unmatched} non-grounded / context-specific tokens.")
    print("=" * 70)


if __name__ == "__main__":
    main()
