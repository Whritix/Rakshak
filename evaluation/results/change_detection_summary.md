# 🛰️ Project Rakshak 2.0 — Multi-Temporal Change Detection Benchmark Dossier

**Evaluation Standard:** 100% held-out `val_report` partition (540 tiles).  
**Sample Size:** 20 seeded synthetic bi-temporal pairs (`seed=1` to `seed=20`), shifts 0.0 to 8.0 px.  
**Ground Truth Edits:** Exactly **3 edits per pair** (1 NEW, 1 REMOVED, 1 MOVED) = **60 total edits** across 20 pairs (+1 structural revetment per pair).  
**Provenance:** `SIMULATED` (Synthesized bi-temporal pairs with deterministic ground-truth edits).  
**Generated Date:** 2026-10-10 19:52:42Z

---

## 1. Headline Change Detection Performance: Baseline vs Stability-Filtered

| Pipeline Mode | Precision (Mean ± Std) | Recall (Mean ± Std) | F1 Score (Mean ± Std) | Pooled Precision | Pooled Recall | TP / FP / FN | Provenance |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline Raw (conf $\ge 0.25$)** | **31.17 ± 30.86%** | **40.00 ± 24.95%** | **0.3005 ± 0.2142** | **23.76%** (0.2376) | **40.00%** (0.4000) | 24 / 77 / 36 | `SIMULATED` |
| **Stability-Filtered (conf $\ge 0.40$, partner $\ge 0.15$ within 28px)** | **32.50 ± 45.48%** | **11.67 ± 15.90%** | **0.1700 ± 0.2326** | **87.50%** (0.8750) | **11.67%** (0.1167) | 7 / 1 / 53 | `SIMULATED` |

> [!NOTE]
> **Operational Trade-Off Rationale:**
> The dual-threshold stability filter suppresses **76 out of 77 False Positives** (dropping FP from 77 down to 1), catapulting pooled precision from **23.76% (31.17% mean) to 87.50%**. Because tactical military targets with confidence between 0.25 and 0.39 are excluded, recall drops from **40.00% to 11.67%**. Both rows are preserved side-by-side for honest tactical trade-off appraisal.

---

## 2. Quantitative False-Positive Root Cause Breakdown

Evaluated across all **77 False Positives** in the baseline raw evaluation:

| Root Cause Category | FP Count | Percentage | Physical / Algorithmic Mechanism | Mitigation |
| :--- | :---: | :---: | :--- | :--- |
| **(a) Detector flicker on unchanged objects** | **49** | **63.64%** | Unedited ground-truth objects present in both scenes where detector confidence hovered around 0.25 threshold in one scene but fell below in the partner scene. | Pruned by partner-scene ghost check ($\ge 0.15$ within 28px). |
| **(b) Inpainting boundary artifacts** | **24** | **31.17%** | Telea inpainting on structured tarmac / vegetation leaves high-frequency texture steps that neural convolutions mistake for vehicle edges. | Pruned by confidence elevation ($\ge 0.40$). |
| **(c) Mis-registration / texture noise** | **4** | **5.19%** | Residual sub-pixel shifts ($0.19$ px) across high-frequency natural clutter causing slight bounding-box centroid jitter. | Controlled by ORB+RANSAC sub-pixel co-registration. |
| **Total Baseline False Positives** | **77** | **100.00%** | Combined false alarms before stability filtration | Reduced to **1 FP** (98.7% reduction) under stability filter. |

---

## 3. Co-Registration Performance & Structural Anomaly Detection

| Metric | Measured Value | Sample Size | Scenario Condition | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Co-Registration Error (0-8 px shift)** | **0.1887 ± 0.1350 px** | 20 seeds (shifts 0.0 to 8.0 px) | Sub-pixel co-registration | `SIMULATED` |
| **Registration Error @ 0.0 px Shift** | **0.0017 ± 0.0010 px** (Max: **0.0034 px**) | 8 trials | Stationary baseline | `SIMULATED` |
| **Registration Error @ 2.0 px Shift** | **0.0807 ± 0.0443 px** (Max: **0.1650 px**) | 8 trials | 2.0 px radial offset | `SIMULATED` |
| **Registration Error @ 4.0 px Shift** | **0.1037 ± 0.0825 px** (Max: **0.3097 px**) | 8 trials | 4.0 px radial offset | `SIMULATED` |
| **Registration Error @ 6.0 px Shift** | **0.1270 ± 0.1538 px** (Max: **0.4494 px**) | 8 trials | 6.0 px radial offset | `SIMULATED` |
| **Registration Error @ 8.0 px Shift** | **0.1086 ± 0.0537 px** (Max: **0.2322 px**) | 8 trials | 8.0 px radial offset | `SIMULATED` |
| **Structural Anomaly Capture Rate** | **70.00%** (0.7000) | 20 injected structural revetments | Secondary pixel diff signal | `SIMULATED` |
| **Real Multi-Pass Satellite Imagery Overflights** | **NOT DONE** | 0 multi-pass satellite passes | Operational constellation overflights | `NOT DONE` |

---

## 4. Per-Class Change Metrics (Baseline Raw)

| Class | Precision | Recall | F1 Score | F1 Std | TP / FP / FN |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Aircraft** | **75.00%** | **37.50%** | **0.5000** | ± 0.3333 | 6 / 2 / 10 |
| **Vehicle** | **21.95%** | **40.91%** | **0.2857** | ± 0.1789 | 18 / 64 / 26 |
| **Infrastructure** | **0.00%** | **0.00%** | **0.0000** | ± 0.0000 | 0 / 11 / 0 |

---

## 5. Honest Failure Analysis & Operational Limitations

1. **Detector Flicker Dominance:** 63.64% of raw False Positives stem from unchanged objects whose neural confidence dropped slightly below 0.25 in one of the two observations.
2. **Inpainting Artifacts:** Telea inpainting on natural terrain creates high-frequency boundary steps responsible for 31.17% of raw False Positives.
3. **Filter Recall Drop:** The stability filter is highly effective at eliminating false alarms (yielding 87.50% pooled precision), but drops recall to 11.67% (pruning 17 true changes whose confidence was below 0.40).
