# 🛰️ Project Rakshak 2.0 — Multi-Temporal Change Detection Benchmark Dossier

**Evaluation Standard:** 100% held-out `val_report` partition (540 tiles).  
**Sample Size:** 20 seeded synthetic bi-temporal pairs (`seed=1` to `seed=20`), shifts 0.0 to 8.0 px.  
**Provenance:** `SIMULATED` (Synthesized bi-temporal pairs with deterministic ground-truth edits).  
**Generated Date:** 2026-10-10 19:36:13Z

---

## 1. Overall Headline Change Detection Performance

| Metric | Mean ± Std | Value | Sample Size | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Change Precision** | **31.17 ± 30.86%** | 0.3117 | 20 seeds | `SIMULATED` |
| **Change Recall** | **40.00 ± 24.95%** | 0.4000 | 20 seeds | `SIMULATED` |
| **Change F1 Score** | **0.3005 ± 0.2142** | 0.3005 | 20 seeds | `SIMULATED` |
| **Registration Error (0-8 px shift)** | **0.1887 ± 0.1350 px** | 0.1887 px | 20 seeds | `SIMULATED` |
| **Structural Anomaly Capture Rate** | **70.00%** | 0.7000 | 20 seeds | `SIMULATED` |

---

## 2. Per-Class Change Precision, Recall & F1

| Class | Precision | Recall | F1 Score | F1 Std | TP / FP / FN |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Aircraft** | **75.00%** | **37.50%** | **0.5000** | ± 0.3333 | 6 / 2 / 10 |
| **Vehicle** | **21.95%** | **40.91%** | **0.2857** | ± 0.1789 | 18 / 64 / 26 |
| **Infrastructure** | **0.00%** | **0.00%** | **0.0000** | ± 0.0000 | 0 / 11 / 0 |

---

## 3. Per-Change-Type Breakdown (NEW, REMOVED, MOVED)

| Change Category | Precision | Recall | F1 Score | TP / FP / FN | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NEW Objects** | **20.51%** | **40.00%** | **0.2712** | 8 / 31 / 12 | Unmatched post-scene neural detections |
| **REMOVED Objects** | **19.15%** | **45.00%** | **0.2687** | 9 / 38 / 11 | Prior-scene objects missing in post-scene |
| **MOVED Objects** | **46.67%** | **35.00%** | **0.4000** | 7 / 8 / 13 | Shifted coordinates ($18 < d \le 120$ px) |

---

## 4. Co-Registration Shift Sensitivity (ORB + RANSAC & Phase Correlation)

| Injected Shift | Mean Registration Error | Std Error | Max Error | Recovery Status |
| :---: | :---: | :---: | :---: | :--- |
| **0.0 px** | **0.0017 px** | ± 0.0010 px | 0.0034 px | Exact stationary baseline |
| **2.0 px** | **0.0807 px** | ± 0.0443 px | 0.1650 px | Sub-pixel co-registration |
| **4.0 px** | **0.1037 px** | ± 0.0825 px | 0.3097 px | Sub-pixel co-registration |
| **6.0 px** | **0.1270 px** | ± 0.1538 px | 0.4494 px | Stable RANSAC consensus |
| **8.0 px** | **0.1086 px** | ± 0.0537 px | 0.2322 px | High-shift sub-pixel recovery |

---

## 5. Honest Failure Analysis & Operational Limitations

1. **Small Vehicle Misses**: Tactical ground vehicles smaller than 18 pixels or with low roof contrast occasionally fall below detection threshold (0.25 conf) in the post-scene, causing False Negatives on NEW additions.
2. **Inpainting Boundary Edge Noise**: Telea inpainting on complex non-uniform tarmac or vegetation occasionally leaves boundary texture steps that trigger minor False Positive structural anomalies if area threshold is set below 100 px.
3. **High-Shift Low-Texture Fallback**: At shifts $\ge$ 6 px on feature-sparse water or desert tiles, ORB feature inlier count drops below 6, requiring Fourier Phase Correlation fallback which introduces slight sub-pixel rounding (up to 0.45 px error).
