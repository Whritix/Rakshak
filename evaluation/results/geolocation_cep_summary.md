# Project Rakshak 2.0: Task B — Geolocation CEP Benchmark (Dual-IoU)

- **Timestamp UTC**: 2026-10-10T14:42:14.571014+00:00
- **Evaluated Partition**: 540 tiles across **38 distinct scenes** (val_report holdout)
- **Model Checkpoint**: `xview_yolo11m_military` (1024×1024 static resolution)
- **Total Ground Truth Instances**: **66,521 targets** across 4 defense domains

> [!IMPORTANT]
> **Conditional Match Disclosure**: Geolocation CEP is **conditional on an IoU bounding-box match**. Ground-truth targets that are undetected have no predicted bounding box regression, and thus have undefined centre localisation error.
> **Truth Scope Disclosure**: Localisation error is evaluated strictly against the dataset's own GeoTIFF georeferencing (bounding box regression and affine transform fidelity into local UTM CRS), **not independent external GPS truth**.

---

## 1. Dual-IoU Geolocation Accuracy & Match Coverage (Metric UTM CRS)

### At IoU $\ge 0.3$ (Candidate Match Standard)

| Target Class | Ground Truth (GT) | Matched Instances | % GT Matched | CEP50 (50% Probable) | CEP90 (90% Probable) | Mean Error | RMSE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Vessel** | 280 | 78 | **27.9%** | **0.92 m** | **6.54 m** | 2.74 m | 7.10 m |
| **Aircraft** | 45 | 39 | **86.7%** | **1.46 m** | **5.22 m** | 2.14 m | 2.79 m |
| **Vehicle** | 23,372 | 16,009 | **68.5%** | **0.49 m** | **1.01 m** | 0.56 m | 0.66 m |
| **Infrastructure** | 42,824 | 21,174 | **49.4%** | **1.00 m** | **3.51 m** | 1.62 m | 2.59 m |
| **OVERALL** | **66,521** | **37,300** | **56.1%** | **0.70 m** | **2.43 m** | **1.17 m** | **2.03 m** |

### At IoU $\ge 0.5$ (Tight Physical Intersection Standard)

| Target Class | Ground Truth (GT) | Matched Instances | % GT Matched | CEP50 (50% Probable) | CEP90 (90% Probable) | Mean Error | RMSE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Vessel** | 280 | 40 | **14.3%** | **0.64 m** | **2.07 m** | 1.82 m | 6.26 m |
| **Aircraft** | 45 | 39 | **86.7%** | **1.46 m** | **5.22 m** | 2.14 m | 2.79 m |
| **Vehicle** | 23,372 | 12,048 | **51.5%** | **0.47 m** | **0.93 m** | 0.52 m | 0.60 m |
| **Infrastructure** | 42,824 | 15,733 | **36.7%** | **0.93 m** | **2.71 m** | 1.32 m | 1.89 m |
| **OVERALL** | **66,521** | **27,860** | **41.9%** | **0.67 m** | **1.99 m** | **0.97 m** | **1.50 m** |

---

## 2. Sensitivity to Subpixel Registration Offsets (at IoU $\ge 0.3$)

At xView's ~0.3 m Ground Sample Distance (GSD), subpixel and multi-pixel platform registration jitter impacts localisation error as follows:

| Injected Registration Offset | Resulting CEP50 | Resulting CEP90 | Resulting Mean Error | Resulting RMSE |
| :---: | :---: | :---: | :---: | :---: |
| **0.0 px (Baseline)** | **0.70 m** | **2.43 m** | 1.17 m | 2.03 m |
| **0.5 px Offset** | **0.72 m** | **2.45 m** | 1.18 m | 2.04 m |
| **1.0 px Offset** | **0.77 m** | **2.51 m** | 1.23 m | 2.07 m |
| **2.0 px Offset** | **0.97 m** | **2.64 m** | 1.39 m | 2.16 m |

---
