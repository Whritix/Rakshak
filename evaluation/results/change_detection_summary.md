# 🛰️ Project Rakshak 2.0 — Multi-Temporal Change Detection Benchmark Dossier (Held-out seeds 21–60)

**Evaluation Standard:** 100% held-out `val_report` partition (540 tiles).  
**Sample Size:** 40 seeded synthetic bi-temporal pairs (`seed=21` to `seed=60`), shifts 0.0 to 8.0 px.  
**Ground Truth Edits:** Exactly **3 edits per pair** (1 NEW, 1 REMOVED, 1 MOVED) = **120 total edits** across 40 pairs (+1 structural revetment per pair).  
**Provenance:** `SIMULATED` (Synthesized bi-temporal pairs with deterministic ground-truth edits).  
**Generated Date:** 2026-10-10 20:02:11Z

---

## 1. Headline Change Detection Performance: Baseline vs Stability-Filtered (Seeds 21–60)

| Pipeline Mode | Precision (Mean ± Std) | Recall (Mean ± Std) | F1 Score (Mean ± Std) | Pooled Precision | Pooled Recall | TP / FP / FN | Provenance |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline Raw (conf $\ge 0.25$)** | **28.04 ± 31.57%** | **37.50 ± 31.79%** | **0.2812 ± 0.2610** | **20.93%** (0.2093) | **37.50%** (0.3750) | 45 / 170 / 75 | `SIMULATED` |
| **Stability-Filtered (conf $\ge 0.40$, partner $\ge 0.15$ within 28px)** | **30.00 ± 45.83%** | **14.17 ± 25.70%** | **0.1825 ± 0.2982** | **80.95%** (0.8095) | **14.17%** (0.1417) | 17 / 4 / 103 | `SIMULATED` |

> [!NOTE]
> **Operational Trade-Off on Held-Out Seeds 21–60:**
> The frozen stability filter suppresses **166 of 170 False Positives** (dropping FP from 170 to 4), maintaining **80.95% pooled precision** (17/21) on held-out test seeds. True-change recall settles at **14.17%** (17/120).

---

## 2. Quantitative False-Positive Root Cause Breakdown (Seeds 21–60)

Evaluated across all **170 False Positives** in the baseline raw evaluation:

| Root Cause Category | FP Count | Percentage | Physical / Algorithmic Mechanism | Mitigation |
| :--- | :---: | :---: | :--- | :--- |
| **(a) Detector flicker on unchanged objects** | **128** | **75.29%** | Unedited ground-truth objects present in both scenes where detector confidence hovered around 0.25 threshold in one scene but fell below in the partner scene. | Pruned by partner-scene ghost filter ($\ge 0.15$ within 28px). |
| **(b) Inpainting boundary artifacts** | **35** | **20.59%** | Telea inpainting on structured tarmac / vegetation leaves high-frequency texture steps that neural convolutions mistake for vehicle edges. | Pruned by confidence elevation ($\ge 0.40$). |
| **(c) Mis-registration / texture noise** | **7** | **4.12%** | Residual sub-pixel displacement noise (0.1449 px) across high-frequency natural clutter causing slight bounding-box centroid jitter. | Controlled by ORB+RANSAC sub-pixel co-registration. |
| **Total Baseline False Positives** | **170** | **100.00%** | Combined false alarms before stability filtration | Reduced to **4 FP** under stability filter. |

---

## 3. Co-Registration Performance & Structural Anomaly Detection

| Metric | Measured Value | Sample Size | Scenario Condition | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Co-Registration Error (0-8 px shift)** | **0.1449 ± 0.1034 px** | 40 seeds (shifts 0.0 to 8.0 px) | Sub-pixel co-registration | `SIMULATED` |
| **Registration Error @ 0.0 px Shift** | **0.0017 ± 0.0010 px** (Max: **0.0034 px**) | 8 trials | Stationary baseline | `SIMULATED` |
| **Registration Error @ 2.0 px Shift** | **0.0807 ± 0.0443 px** (Max: **0.1650 px**) | 8 trials | 2.0 px radial offset | `SIMULATED` |
| **Registration Error @ 4.0 px Shift** | **0.1037 ± 0.0825 px** (Max: **0.3097 px**) | 8 trials | 4.0 px radial offset | `SIMULATED` |
| **Registration Error @ 6.0 px Shift** | **0.1270 ± 0.1538 px** (Max: **0.4494 px**) | 8 trials | 6.0 px radial offset | `SIMULATED` |
| **Registration Error @ 8.0 px Shift** | **0.1086 ± 0.0537 px** (Max: **0.2322 px**) | 8 trials | 8.0 px radial offset | `SIMULATED` |
| **Structural Anomaly Capture Rate** | **65.00%** (0.6500) | 40 injected structural revetments | Secondary pixel diff signal | `SIMULATED` |
| **Real Multi-Pass Satellite Imagery Overflights** | **NOT DONE** | 0 multi-pass satellite passes | Operational constellation overflights | `NOT DONE` |
