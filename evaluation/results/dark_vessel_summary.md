# Project Rakshak 2.0: Task A — Multi-Seed Dark-Vessel Rate & Statistical Sweeps

- **Provenance**: `SIMULATED` (Multi-seed synthetic maritime dataset, $N = 500$ contacts/cell $\times 20$ seeds $= 10,000$ contacts/cell)
- **Seeds Evaluated**: 20 independent seeds (`seed=1` to `seed=20`)
- **Statistical Framework**: Mean $\pm$ Standard Deviation with 95% Confidence Intervals via two-tailed Student's t-distribution ($t_{19, 0.975} = 2.0930$)
- **Local xView3-SAR Status**: Not present in repository. Evaluated on calibrated maritime kinematics set.
- **Dark Fraction**: **30.0%** ($N_{\text{dark}} = 150$, $N_{\text{coop}} = 350$ per seed; $3,000$ dark vessels evaluated per sweep cell)

---

## 1. Headline Dark-Vessel Performance (Operational Radius: 2.0 km, ±30 min Offset)

| Metric | Mean $\pm$ Std | 95% Confidence Interval | Min / Max | Operational Definition |
| :--- | :---: | :---: | :---: | :--- |
| **Headline End-to-End Dark Vessel Capture** | **79.40 $\pm$ 2.80%** | **[78.09%, 80.71%]** | 75.33% / 83.33% | $\frac{\text{CFAR-Detected AND Flagged Dark}}{\text{All Ground-Truth Dark Vessels}}$ |
| **Post-Detection Recall** | **92.63 $\pm$ 2.23%** | **[91.58%, 93.67%]** | 89.15% / 97.66% | $\frac{\text{CFAR-Detected AND Flagged Dark}}{\text{CFAR-Detected Dark}}$ |
| **CA-CFAR Radar Detection Rate** | **85.73 $\pm$ 2.65%** | **[84.49%, 86.97%]** | 81.33% / 92.00% | Radar detectability across vessel RCS distribution |
| **Precision** | **100.00 $\pm$ 0.00%** | **[100.00%, 100.00%]** | 100.00% / 100.00% | $\frac{\text{True Dark Alerts}}{\text{All Declared Dark Alerts}}$ |
| **False-Dark Alarm Rate** | **0.00 $\pm$ 0.00%** | **[0.00%, 0.00%]** | 0.00% / 0.00% | False alarms on cooperative tracks |
| **F1 Score** | **0.9616 $\pm$ 0.0120** | **[0.9560, 0.9672]** | 0.9426 / 0.9881 | Harmonic mean of precision and post-det recall |

---

## 2. Density Sweep (5, 20, 50, 100, 200 Contacts per 10,000 km²)

Evaluated across 20 independent seeds. In each density condition, sector area was scaled so that **$N = 500$ contacts per seed** ($10,000$ total contacts per cell):

| Contact Density | Sector Area | Total Contacts (20 Seeds) | End-to-End Capture (Mean $\pm$ Std [95% CI]) | Post-Det Recall (Mean $\pm$ Std [95% CI]) | Precision (Mean $\pm$ Std) | False-Dark Rate (Mean $\pm$ Std) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **5 / 10k km²** | 1,000,000 km² | 10,000 | **86.07 $\pm$ 2.43%** [84.93%, 87.20%] | **99.62 $\pm$ 0.72%** [99.29%, 99.96%] | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **20 / 10k km²** | 250,000 km² | 10,000 | **83.37 $\pm$ 2.39%** [82.25%, 84.49%] | **97.60 $\pm$ 1.42%** [96.93%, 98.26%] | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **50 / 10k km²** | 100,000 km² | 10,000 | **81.77 $\pm$ 3.18%** [80.28%, 83.26%] | **95.51 $\pm$ 1.53%** [94.80%, 96.23%] | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **100 / 10k km²** | 50,000 km² | 10,000 | **76.73 $\pm$ 3.24%** [75.22%, 78.25%] | **89.36 $\pm$ 1.99%** [88.43%, 90.29%] | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **200 / 10k km²** | 25,000 km² | 10,000 | **68.73 $\pm$ 3.41%** [67.14%, 70.33%] | **80.18 $\pm$ 3.08%** [78.74%, 81.62%] | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |

---

## 3. Time-Offset Sweep (Temporal Drift Window: ±5, ±15, ±30 min)

Evaluated across 20 independent seeds ($N = 500$ contacts/seed, $10,000$ total contacts per cell). Comparing dead-reckoning temporal propagation against unpropagated raw AIS pings:

| Time Window | WITH SOG/COG Dead-Reckoning (E2E Capture) | WITH Propagation (False-Dark Rate) | WITHOUT Propagation (E2E Capture) | WITHOUT Propagation (False-Dark Rate) | Operational Significance |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **±5 min** | **79.13 $\pm$ 3.80%** [77.36%, 80.91%] | 0.00 $\pm$ 0.00% | 79.30 $\pm$ 3.34% | **15.20 $\pm$ 1.76%** | Unpropagated pings drift out of tolerance, causing false alerts |
| **±15 min** | **80.40 $\pm$ 2.76%** [79.11%, 81.69%] | 0.00 $\pm$ 0.00% | 79.93 $\pm$ 2.44% | **61.08 $\pm$ 2.08%** | Unpropagated pings drift out of tolerance, causing false alerts |
| **±30 min** | **80.03 $\pm$ 3.60%** [78.35%, 81.72%] | 0.00 $\pm$ 0.00% | 80.03 $\pm$ 4.39% | **77.45 $\pm$ 1.85%** | Unpropagated pings drift out of tolerance, causing false alerts |

---

## 4. Stress Cases (AIS Gaps & Degraded Kinematics, 20 Seeds)

Evaluated across 20 independent seeds with $N = 500$ contacts per seed ($10,000$ total contacts per scenario):

| Stress Scenario | Operational Description | End-to-End Capture (Mean $\pm$ Std [95% CI]) | Precision (Mean $\pm$ Std) | False-Dark Rate (Mean $\pm$ Std) |
| :--- | :--- | :---: | :---: | :---: |
| **Nominal Baseline** | Continuous AIS, valid SOG/COG, ±30 min | **79.40 $\pm$ 2.80%** [78.09%, 80.71%] | **100.00 $\pm$ 0.00%** | **0.00 $\pm$ 0.00%** |
| **AIS Gaps (10% Missing)** | RF packet collisions / shadow loss of pings | **81.03 $\pm$ 3.67%** [79.32%, 82.75%] | **81.33 $\pm$ 2.02%** | **9.34 $\pm$ 1.14%** |
| **Corrupted Kinematics (10%)** | Spoofed or erroneous SOG/COG | **79.93 $\pm$ 2.60%** [78.72%, 81.15%] | **82.98 $\pm$ 2.70%** | **8.19 $\pm$ 1.55%** |

---

## 5. Matching Radius Sweep (20 Seeds)

| Matching Radius | End-to-End Capture (Mean $\pm$ Std) | Post-Det Recall (Mean $\pm$ Std) | Precision (Mean $\pm$ Std) | False-Dark Rate (Mean $\pm$ Std) |
| :---: | :---: | :---: | :---: | :---: |
| **1.0 km** | 83.63 $\pm$ 3.14% | 97.54 $\pm$ 1.65% | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **2.0 km** | 79.40 $\pm$ 2.80% | 92.63 $\pm$ 2.23% | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **5.0 km** | 55.43 $\pm$ 4.15% | 64.67 $\pm$ 4.70% | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |
| **10.0 km** | 15.30 $\pm$ 2.75% | 17.88 $\pm$ 3.37% | 100.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% |

---
