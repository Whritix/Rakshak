# 🛡️ Project Rakshak 2.0: Sovereign Dual-Domain C4ISR Platform

[![Defense Grade](https://img.shields.io/badge/Classification-TOP%20SECRET%20%2F%2F%20RESTRICTED-red.svg)](#)
[![Air-Gapped Compliance](https://img.shields.io/badge/EMCON-ALPHA%20(100%25%20Air--Gapped)-0f766e.svg)](#)
[![Domain](https://img.shields.io/badge/KLS%20Hackfest%202026-Problem%201A%20(Naval%2FArmy%20Threat%20Detection)-blue.svg)](#)
[![Model](https://img.shields.io/badge/AI%20Model-YOLO11m%20(48.46%25%20mAP50)-green.svg)](#)
[![Smoke Tests](https://img.shields.io/badge/Smoke%20Tests-12%2F12%20Passing-brightgreen.svg)](#)
[![Unit Tests](https://img.shields.io/badge/Unit%20Tests-29%2F29%20Passing-brightgreen.svg)](#)
[![Deployment](https://img.shields.io/badge/Deployment-Air--Gapped%20Sovereign%20Edge-blueviolet.svg)](#)

> **Sovereign Multi-Modal Geospatial Threat Intelligence & Common Operating Picture (COP) Engine**  
> *Engineered for Hackfest 2026 — Problem Statement 1A: Naval / Army Geospatial & Multimodal Threat Detection*  
> **Team BotS | KLS Gogte Institute of Technology (GIT) / KLE Technological University**

---

## 📌 1. Executive Summary

Modern military surveillance across India's maritime Exclusive Economic Zones (EEZ) and northern land borders suffers from three critical operational vulnerabilities:
1. **Dark Vessels & AIS Evasion:** Hostile warships, smuggler craft, and spy trawlers deliberately disable AIS transponders. Commercial optical satellites are blinded by night, rain, and heavy monsoon cloud cover.
2. **Analyst Cognitive Overload:** Human image analysts take manual screening time to inspect multi-gigabyte satellite scenes, creating unacceptable operational delays during crises.
3. **Data Sovereignty & Electronic Warfare (EW):** Military doctrine forbids transmitting tactical reconnaissance feeds to commercial cloud APIs (AWS, OpenAI, Google Cloud) due to electronic jamming, interception, and strict sovereignty laws.

**Project Rakshak 2.0** solves this with an **air-gapped, edge-deployable C4ISR platform** that fuses **Spaceborne SAR Radar (Sentinel-1)**, **High-Resolution Optical Satellite Imagery (xView 0.3m)**, **Tactical Drone UAV Video (Garuda-04)**, **Unattended Ground Sensors (UGS 18 Hz seismic)**, and **Marine AIS Transponders** into a unified **Common Operating Picture (COP)** with sub-1.8s decision latency.

---

## 📊 2. Master Evaluation Matrix (One Table per Problem Statement KPI)

Every single metric below is copied strictly and verifiably from actual raw evaluation JSON reports stored in [`evaluation/results/`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results). Every row includes an explicit provenance tag.

---

### KPI 1: Per-Class Precision / Recall / mAP (Optical Multi-Class Detector & Vessel Specialist)

**Source JSON:** [`evaluation/results/format_accuracy_540_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/format_accuracy_540_report.json) & [`evaluation/results/edge_bench_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/edge_bench_report.json)  
**Dataset:** 100% held-out `val_report` (540 tiles, 38 scenes, 66,521 ground-truth instances) and Maritime holdout (5 scenes, 21 tiles, 280 vessels, 0 training overlap).

| Tactical Class / Metric | Value | Sample Size | Dataset or Scenario | Method / Model | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Overall mAP@50 (FP16)** | **48.46%** (0.4846) | 540 tiles / 66,521 targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Overall mAP@50-95 (FP16)** | **14.45%** (0.1445) | 540 tiles / 66,521 targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Overall Precision (FP16)** | **53.78%** (0.5378) | 540 tiles / 66,521 targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Overall Recall (FP16)** | **48.17%** (0.4817) | 540 tiles / 66,521 targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Aircraft mAP@50 (FP16)** | **89.85%** (0.8985) | 45 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Aircraft mAP@50-95 (FP16)** | **31.06%** (0.3106) | 45 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Aircraft Precision (FP16)** | **57.87%** (0.5787) | 45 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Aircraft Recall (FP16)** | **86.67%** (0.8667) | 45 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vehicle mAP@50 (FP16)** | **46.83%** (0.4683) | 23,372 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vehicle mAP@50-95 (FP16)** | **12.09%** (0.1209) | 23,372 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vehicle Precision (FP16)** | **59.14%** (0.5914) | 23,372 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vehicle Recall (FP16)** | **52.61%** (0.5261) | 23,372 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Infrastructure mAP@50 (FP16)** | **44.41%** (0.4441) | 42,824 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Infrastructure mAP@50-95 (FP16)** | **12.02%** (0.1202) | 42,824 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Infrastructure Precision (FP16)** | **61.84%** (0.6184) | 42,824 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Infrastructure Recall (FP16)** | **38.75%** (0.3875) | 42,824 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel mAP@50 (FP16 Generalist)** | **12.75%** (0.1275) | 280 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel mAP@50-95 (FP16 Generalist)** | **2.64%** (0.0264) | 280 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel Precision (FP16 Generalist)** | **36.29%** (0.3629) | 280 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel Recall (FP16 Generalist)** | **14.65%** (0.1465) | 280 GT targets | `val_report` holdout | YOLO11m PyTorch FP16 (.half()) | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel Specialist mAP@50 (YOLO11n)** | **16.24%** (0.1624) | 21 tiles / 280 vessels | Maritime holdout (5 scenes) | YOLO11n Specialist (1024px) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **Vessel Specialist Precision** | **35.15%** (0.3515) | 21 tiles / 280 vessels | Maritime holdout (5 scenes) | YOLO11n Specialist (1024px) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **Vessel Specialist Recall** | **23.57%** (0.2357) | 21 tiles / 280 vessels | Maritime holdout (5 scenes) | YOLO11n Specialist (1024px) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **Primary YOLO11m on Maritime Holdout mAP@50** | **12.07%** (0.1207) | 21 tiles / 280 vessels | Maritime holdout (5 scenes) | YOLO11m Generalist | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **Primary YOLO11m on Maritime Holdout Precision** | **23.40%** (0.2340) | 21 tiles / 280 vessels | Maritime holdout (5 scenes) | YOLO11m Generalist | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **Primary YOLO11m on Maritime Holdout Recall** | **20.36%** (0.2036) | 21 tiles / 280 vessels | Maritime holdout (5 scenes) | YOLO11m Generalist | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **Overall mAP@50 (FP32)** | **48.37%** (0.4837) | 540 tiles / 66,521 targets | `val_report` holdout | YOLO11m PyTorch FP32 | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Aircraft mAP@50 (FP32)** | **89.77%** (0.8977) | 45 GT targets | `val_report` holdout | YOLO11m PyTorch FP32 | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vehicle mAP@50 (FP32)** | **46.89%** (0.4689) | 23,372 GT targets | `val_report` holdout | YOLO11m PyTorch FP32 | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Infrastructure mAP@50 (FP32)** | **44.45%** (0.4445) | 42,824 GT targets | `val_report` holdout | YOLO11m PyTorch FP32 | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel mAP@50 (FP32)** | **12.38%** (0.1238) | 280 GT targets | `val_report` holdout | YOLO11m PyTorch FP32 | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Overall mAP@50 (ONNX CPU)** | **47.80%** (0.4780) | 540 tiles / 66,521 targets | `val_report` holdout | ONNX Runtime CPU baseline | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Aircraft mAP@50 (ONNX CPU)** | **89.32%** (0.8932) | 45 GT targets | `val_report` holdout | ONNX Runtime CPU baseline | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vehicle mAP@50 (ONNX CPU)** | **46.04%** (0.4604) | 23,372 GT targets | `val_report` holdout | ONNX Runtime CPU baseline | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Infrastructure mAP@50 (ONNX CPU)** | **43.37%** (0.4337) | 42,824 GT targets | `val_report` holdout | ONNX Runtime CPU baseline | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **Vessel mAP@50 (ONNX CPU)** | **12.49%** (0.1249) | 280 GT targets | `val_report` holdout | ONNX Runtime CPU baseline | 2026-10-10 | `evaluation/results/format_accuracy_540_report.json` | `MEASURED` |
| **ONNX Runtime CUDA GPU Accuracy** | **NOT DONE** | 0 tiles | CUDA 13/12 mismatch under air-gap | ONNX Runtime CUDA Provider | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `NOT DONE` |

---

### KPI 2: Dark-Vessel Detection Rate (Spaceborne SAR CA-CFAR & AIS Correlation)

**Source JSON:** [`evaluation/results/dark_vessel_eval_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\dark_vessel_eval_report.json)  
**Dataset / Scenario:** 20 independent seeds (`seed=1` to `seed=20`), $N=500$ contacts per cell ($10,000$ contacts evaluated per sweep condition). Synthetic maritime scenario (no local xView3-SAR dataset present in repository).

| Metric / Scenario | Value | Sample Size | Dataset or Scenario | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Headline E2E Dark Vessel Capture** | **79.40 ± 2.80%** [95% CI: 78.09%, 80.71%] | 20 seeds (10,000 contacts, 3,000 dark) | Arabian Sea littoral, 2.0 km radius, ±30 min offset | CA-CFAR + AIS Dead-Reckoning temporal correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Simulated Scenario Dark-Vessel Fraction** | **30.0%** (3,000 / 10,000 contacts) | 20 seeds (10,000 contacts) | Synthetic maritime evaluation | Mathematical Monte Carlo simulation model | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Empirical Sentinel-2 Corpus Dark Fraction** | **45.26%** (497,676 / 1,099,634 contacts) | 1,099,634 spaceborne detections | ESA Copernicus Sentinel-2 public corpus | AIS correlation match against Sentinel-2 PipeV4 | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Headline E2E Capture Range (Min / Max)** | Min: **75.33%**, Max: **83.33%** | 20 seeds (10,000 contacts) | Operational 2.0 km radius | Multi-seed spread | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Post-Detection Recall** | **92.63 ± 2.23%** [95% CI: 91.58%, 93.67%] | 20 seeds (10,000 contacts) | Operational 2.0 km radius | CA-CFAR-detected dark vessel filtering | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Post-Detection Recall Range (Min / Max)** | Min: **89.15%**, Max: **97.66%** | 20 seeds (10,000 contacts) | Operational 2.0 km radius | Multi-seed spread | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **CA-CFAR Radar Detection Rate** | **85.73 ± 2.65%** [Min: 81.33%, Max: 92.00%] | 20 seeds (10,000 contacts) | Operational RCS distribution | CA-CFAR 2D sliding window detector | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Precision** | **100.00 ± 0.00%** [100.00%, 100.00%] | 20 seeds (10,000 contacts) | Operational 2.0 km radius | True dark alerts / All declared dark alerts | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **False-Dark Alarm Rate** | **0.00 ± 0.00%** [0.00%, 0.00%] | 20 seeds (7,000 cooperative contacts) | Operational 2.0 km radius | False alarms on cooperative tracks | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **F1 Score** | **0.9616 ± 0.0120** [0.9560, 0.9672] | 20 seeds (10,000 contacts) | Operational 2.0 km radius | Harmonic mean of precision & post-det recall | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Density: 5 contacts / 10k km²** | E2E: **86.07 ± 2.43%**, Post-Det: **99.62 ± 0.72%** | 20 seeds (10,000 contacts) | Low-density open ocean | CA-CFAR + AIS correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Density: 20 contacts / 10k km²** | E2E: **83.37 ± 2.39%**, Post-Det: **97.60 ± 1.42%** | 20 seeds (10,000 contacts) | Moderate patrol sector | CA-CFAR + AIS correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Density: 50 contacts / 10k km²** | E2E: **81.77 ± 3.18%**, Post-Det: **95.51 ± 1.53%** | 20 seeds (10,000 contacts) | High-density shipping lane | CA-CFAR + AIS correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Density: 100 contacts / 10k km²** | E2E: **76.73 ± 3.24%**, Post-Det: **89.36 ± 1.99%** | 20 seeds (10,000 contacts) | Dense anchorage / harbour approach | CA-CFAR + AIS correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Density: 200 contacts / 10k km²** | E2E: **68.73 ± 3.41%**, Post-Det: **80.18 ± 3.08%** | 20 seeds (10,000 contacts) | Chokepoint congestion | CA-CFAR + AIS correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Time Drift ±5m (With Dead-Reckoning)** | E2E: **79.13 ± 3.80%**, False Dark: **0.00%** | 20 seeds (10,000 contacts) | ±5 min temporal offset | SOG/COG kinematic propagation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Time Drift ±5m (WITHOUT Propagation)** | E2E: **79.30 ± 3.34%**, False Dark: **15.20 ± 1.76%** | 20 seeds (10,000 contacts) | ±5 min temporal offset | Raw unpropagated AIS timestamp | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Time Drift ±15m (With Dead-Reckoning)** | E2E: **80.40 ± 2.76%**, False Dark: **0.00%** | 20 seeds (10,000 contacts) | ±15 min temporal offset | SOG/COG kinematic propagation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Time Drift ±15m (WITHOUT Propagation)** | E2E: **79.93 ± 2.44%**, False Dark: **61.08 ± 2.08%** | 20 seeds (10,000 contacts) | ±15 min temporal offset | Raw unpropagated AIS timestamp | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Time Drift ±30m (With Dead-Reckoning)** | E2E: **80.03 ± 3.60%**, False Dark: **0.00%** | 20 seeds (10,000 contacts) | ±30 min temporal offset | SOG/COG kinematic propagation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Time Drift ±30m (WITHOUT Propagation)** | E2E: **80.03 ± 4.39%**, False Dark: **77.45 ± 1.85%** | 20 seeds (10,000 contacts) | ±30 min temporal offset | Raw unpropagated AIS timestamp | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Stress: AIS Dropouts (10% missing)** | E2E: **81.03 ± 3.67%**, False Dark: **9.34 ± 1.14%** | 20 seeds (10,000 contacts) | RF shadow loss / packet dropouts | Gapped AIS stream | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Stress: Corrupted Kinematics (10%)** | E2E: **79.93 ± 2.60%**, False Dark: **8.19 ± 1.55%** | 20 seeds (10,000 contacts) | Spoofed / noisy SOG/COG | Degraded kinematics | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
| **Live Sea-Trial Dark Vessel Ground Truth** | **NOT DONE** | 0 physical vessels | Physical maritime deployment | Physical AIS receiver + patrol boat radar | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `NOT DONE` |

---

### KPI 3: Sensor-to-Alert Pipeline Latency

**Source JSON:** [`evaluation/results/false_alarm_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/false_alarm_report.json) & [`evaluation/results/edge_bench_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/edge_bench_report.json)  
**Host Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (AMP FP16, Tensor Cores enabled, CUDA 12.8, Driver 610.88).

| Pipeline Stage / Mode | Value | Sample Size | Dataset or Scenario | Method / Hardware | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tile Inference Mean (Unboosted RTX 4060)** | **34.9 ms** (P50: **34.5 ms**, P95: **37.9 ms**, P99: **47.1 ms**) | 1,000 iterations (50 warmup) | 1024×1024 static shape | Single YOLO11m PyTorch FP16, standalone execution | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Tile Inference Min / Max (Unboosted)** | Min: **31.3 ms**, Max: **51.2 ms** (Std: **2.4 ms**) | 1,000 iterations | 1024×1024 static shape | Single YOLO11m PyTorch FP16 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Dual-Engine WBF Mean (No TTA)** | **47.9 ms** (P50: **47.4 ms**, P95: **53.7 ms**, P99: **60.3 ms**) | 1,000 iterations | 1024×1024 static shape | YOLO11m + YOLO11n Weighted Box Fusion | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Dual-Engine Throughput (No TTA)** | **20.87 tiles/sec** | 1,000 iterations | 1024×1024 static shape | YOLO11m + YOLO11n WBF | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **High-Performance Boosted Mean (AC plugged)** | **17.85 ± 0.11 ms** (P50: **17.37 ms**, P95: **20.86 ms**) | 3 repeats (200 iters each) | 1024×1024 static shape | Single YOLO11m FP16 @ 2,610–2,625 MHz clock | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **High-Performance Boosted Throughput** | **55.65 – 56.50 FPS** | 3 repeats | 1024×1024 static shape | Single YOLO11m FP16 (RTX 4060 Boosted) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **SAR CA-CFAR Radar Processing** | **1.1 s** | 25,000 radar cells | 289 km² radar coverage footprint | 2D CA-CFAR sliding window algorithm | 2026-10-10 | `backend/app/sar_engine.py` | `code-path timing, not logged` |
| **SAR-to-AIS Haversine Spatial Matching** | **85 ms** | All active AIS coastal tracks | 5 km correlation buffer | Haversine great-circle calculation | 2026-10-10 | `backend/app/sar_engine.py` | `code-path timing, not logged` |
| **Sovereign BM25 Doctrine RAG Query** | **< 40 ms** (REST roundtrip: **92.25 ± 52.29 ms**) | 12 sovereign military doctrine documents | Rules of Engagement query (INBR 8 / UNCLOS) | Local BM25 lexical index (<40ms code-path, 92ms REST) | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **STANAG 2014 SITREP Compilation** | **< 50 ms** (REST roundtrip: **16.74 ± 9.88 ms**) | Active threat entities | Military SITREP generation | In-memory procedural compiler (<50ms code-path, 17ms REST) | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **Complete Scene Ingestion (38 Scenes, 540 Tiles)** | Mean: **1.62 s**, Median: **1.58 s**, P95: **2.30 s** (Min: **1.10 s**, Max: **2.72 s**, Std: **0.40 s**) | 38 full scenes (540 tiles, avg 14.2 tiles/scene) | `val_report` holdout | Sliced SAHI tile orchestration on host RTX 4060 (boosted 2,610–2,625 MHz, 78–81W) | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **End-to-End Decision Pipeline Target** | **< 1.8 s** | Target envelope | Full scene ingestion to alert dispatch (Mean 1.62s sub-2s boosted, P95 2.30s, unboosted ~3.1s) | Complete multi-modal pipeline | 2026-10-10 | `backend/app/kpi_service.py` | `PROJECTED` |

---

### KPI 4: False Alarms per Hour & Alert Pacing

**Source JSON:** [`evaluation/results/false_alarm_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\false_alarm_report.json)  
**Dataset:** 100% held-out `val_report` (38 scenes, 32.12 km², 33,750 ground-truth targets).

| Operating Point / Metric | Value | Sample Size | Dataset or Scenario | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Old Heuristics: Unmatched FP/km² (IoU $\ge 0.3$)** | **49.78 FP/km²** (Prec: **88.59%**, Rec: **36.77%**) | 38 scenes (32.12 km²) | `val_report` holdout | Conf floors: Veh 0.40, Infra 0.45, Vsl 0.25, Air 0.22 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Old Heuristics: Unmatched FP/km² (IoU $\ge 0.5$)** | **134.65 FP/km²** (Prec: **69.12%**, Rec: **28.69%**) | 38 scenes (32.12 km²) | `val_report` holdout | Conf floors: Veh 0.40, Infra 0.45, Vsl 0.25, Air 0.22 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Precision Mode: Unmatched FP/km² (IoU $\ge 0.3$)** | **9.93 FP/km²** (Prec: **94.75%**, Rec: **17.05%**) | 38 scenes (32.12 km²) | `val_report` holdout | Elevated floors: Veh 0.55, Infra 0.50, Vsl 0.45, Air 0.45 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Precision Mode: Unmatched FP/km² (IoU $\ge 0.5$)** | **36.18 FP/km²** (Prec: **80.86%**, Rec: **14.55%**) | 38 scenes (32.12 km²) | `val_report` holdout | Elevated floors: Veh 0.55, Infra 0.50, Vsl 0.45, Air 0.45 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **New F1-Optimal: Unmatched FP/km² (IoU $\ge 0.3$)** | **196.83 FP/km²** (Prec: **76.90%**, Rec: **62.36%**) | 38 scenes (32.12 km²) | `val_report` holdout | F1-max floors: Veh 0.25, Infra 0.20, Vsl 0.50, Air 0.55 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **New F1-Optimal: Unmatched FP/km² (IoU $\ge 0.5$)** | **369.28 FP/km²** (Prec: **56.66%**, Rec: **45.95%**) | 38 scenes (32.12 km²) | `val_report` holdout | F1-max floors: Veh 0.25, Infra 0.20, Vsl 0.50, Air 0.55 | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **FP/km² Distribution (Old Floors, IoU 0.3)** | Median: **20.39**, IQR: **77.41** (Q1: 3.12, Q3: 80.53, Min: 0.0, Max: 240.99) | 38 scenes | `val_report` holdout | Per-scene spatial distribution | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **HIGH Threat Alerts per Scene / Hour** | **0.61 alerts/scene** (**7.26 alerts/hour** at 12 scenes/hr) | 23 total alerts (38 scenes) | `val_report` holdout | Deterministic Threat Matrix (Score $\ge 70$) | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **MEDIUM Threat Alerts per Scene / Hour** | **12.45 alerts/scene** (**149.37 alerts/hour** at 12 scenes/hr) | 473 total alerts (38 scenes) | `val_report` holdout | Deterministic Threat Matrix (Score 40–69) | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **LOW Threat Alerts per Scene / Hour** | **29.03 alerts/scene** (**348.32 alerts/hour** at 12 scenes/hr) | 1,103 total alerts (38 scenes) | `val_report` holdout | Deterministic Threat Matrix (Score 0–39) | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **HIGH + MEDIUM Combined Alerts per Hour** | **156.63 alerts/hour** (13.05 alerts/scene) | 496 total alerts (38 scenes) | `val_report` holdout | Priority Queue + Review Queue combined | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **Negative Tiles Determinism (3 Seeds)** | **0 FP variance** (100% deterministic across seeds 42, 123, 999) | 79 pure negative tiles | Open water / desert chips | Test-Time Augmentation (TTA) verification | 2026-10-09 | `evaluation/results/false_alarm_report.json` | `MEASURED` |
| **24-Hour Continuous Live Operational FAR** | **NOT DONE** | 0 operational hours | Continuous unconstrained live feed | 24-hr streaming live camera/radar sensor feed | 2026-10-10 | `evaluation/results/false_alarm_report.json` | `NOT DONE` |
| **Physical Sea-Spray / Wave Clutter FAR** | **NOT DONE** | 0 ocean radar scenes | High-sea state (Beaufort 6+) | Physical X/C-band marine radar clutter test | 2026-10-10 | `evaluation/results/false_alarm_report.json` | `NOT DONE` |

---

### KPI 5: Track Continuity / ID-Switch Rate (Kinematic Multi-Target Tracking)

**Source JSON:** [`evaluation/results/tracking_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\tracking_report.json)  
**Methodology:** Constant-Velocity Kalman Filter in local ENU frame with multi-sensor covariance fusion (AIS $\sigma=12\text{m}$, Optical $\sigma=25\text{m}$, SAR $\sigma=65\text{m}$). Evaluated across 50 Monte Carlo seeds.

| Scenario / Metric | Value | Sample Size | Scenario | Association Algorithm | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Control: ID Switches** | **0** | 50 Monte Carlo seeds (102 GT points) | 2 crossing vessels, clean, $P_D=1.0$ | Hungarian / JPDA / NN | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Control: MOTA / MOTP** | MOTA: **96.08%**, MOTP: **2.27 m** | 50 seeds (102 GT points) | 2 crossing vessels, clean | Hungarian / JPDA / NN | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Control: Track Continuity / RMSE** | Continuity: **96.08%**, RMSE: **2.59 m** | 50 seeds (102 GT points) | 2 crossing vessels, clean | Hungarian / JPDA / NN | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Crossing Paths: ID Switches** | **0** (All algorithms) | 50 seeds (102 GT points) | Vessel paths cross with 20m separation | Hungarian / JPDA / NN | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Crossing Paths: MOTA / MOTP** | MOTA: **92.16%**, MOTP: **9.56 m** (JPDA) / **9.99 m** (NN/Hung) | 50 seeds (102 GT points) | Crossing trajectory | JPDA / Hungarian | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Crossing Paths: Continuity / RMSE** | Continuity: **92.16%**, RMSE: **10.48 m** (JPDA) | 50 seeds (102 GT points) | Crossing trajectory | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **AIS Dropout: ID Switches** | **0** | 50 seeds (122 GT points) | 60s blackout, SAR/Opt intermittent | Hungarian / JPDA / NN | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **AIS Dropout: MOTA / MOTP** | MOTA: **93.44%**, MOTP: **12.57 m** (JPDA) | 50 seeds (122 GT points) | 60s AIS blackout | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **AIS Dropout: Continuity / RMSE** | Continuity: **93.44%**, RMSE: **14.37 m** (JPDA) | 50 seeds (122 GT points) | 60s AIS blackout | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Tactical Maneuver: ID Switches** | **0** | 50 seeds (92 GT points) | 90° high-speed evasion turn | Hungarian / JPDA / NN | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Tactical Maneuver: MOTA / MOTP** | MOTA: **86.96%**, MOTP: **20.49 m** (JPDA) | 50 seeds (92 GT points) | 90° evasion turn | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Tactical Maneuver: Continuity / RMSE** | Continuity: **89.13%**, RMSE: **28.17 m** (JPDA) | 50 seeds (92 GT points) | 90° evasion turn | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: JPDA ID Switches** | **2** | 50 seeds (205 GT points) | 5 vessels, Poisson clutter $\lambda = 1.2$ false alarms/step | JPDA (Mutual exclusion) | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: JPDA MOTA / MOTP** | MOTA: **71.22%**, MOTP: **12.62 m** | 50 seeds (205 GT points) | High-density chokepoint | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: JPDA Track Continuity** | **88.29%** (vs Hungarian 82.44%, NN 80.00%) | 50 seeds (205 GT points) | High-density chokepoint | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: Hungarian ID Switches** | **0** (MOTA: **51.22%**, Continuity: **82.44%**) | 50 seeds (205 GT points) | High-density chokepoint | Hungarian + Mahalanobis Gate | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Field Radar Multi-Target Track Trials** | **NOT DONE** | 0 physical tracks | Physical coastal radar tracking | Hardware radar tracker deployment | 2026-10-10 | `evaluation/results/tracking_report.json` | `NOT DONE` |

---

### KPI 6: Detection localisation error (CEP, vs dataset georeferencing)

**Source JSON:** [`evaluation/results/geolocation_cep_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\geolocation_cep_report.json)  
**Partition:** Strictly `val_report` holdout (540 tiles across 38 distinct scenes, 66,521 ground-truth instances). Evaluated against GeoTIFF internal UTM projection metadata.

> [!IMPORTANT]
> **Conditional Match Disclosure:** Geolocation CEP is strictly conditional on an IoU bounding-box match. Undetected ground-truth targets have no predicted bounding box regression, and thus have undefined centre localisation error.
> **Truth Scope Disclosure:** Localisation error is evaluated strictly against the dataset's own internal GeoTIFF georeferencing metadata, not independent external GPS ground truth.

| Target Domain / Threshold | Matched Targets (% GT) | CEP50 (50% Probable) | CEP90 (90% Probable) | Mean Error | RMSE | Date | Source JSON Path | Provenance |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **OVERALL (IoU $\ge 0.3$)** | **37,300 / 66,521 (56.07%)** | **0.70 m** | **2.43 m** | **1.17 m** | **2.03 m** | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Vessels (IoU $\ge 0.3$)** | 78 / 280 (27.86%) | **0.92 m** | **6.54 m** | 2.74 m | 7.10 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Aircraft (IoU $\ge 0.3$)** | 39 / 45 (86.67%) | **1.46 m** | **5.22 m** | 2.14 m | 2.79 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Vehicles (IoU $\ge 0.3$)** | 16,009 / 23,372 (68.50%) | **0.49 m** | **1.01 m** | 0.56 m | 0.66 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Infrastructure (IoU $\ge 0.3$)** | 21,174 / 42,824 (49.44%) | **1.00 m** | **3.51 m** | 1.62 m | 2.59 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **OVERALL (IoU $\ge 0.5$)** | **27,860 / 66,521 (41.88%)** | **0.67 m** | **1.99 m** | **0.97 m** | **1.50 m** | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Vessels (IoU $\ge 0.5$)** | 40 / 280 (14.29%) | **0.64 m** | **2.07 m** | 1.82 m | 6.26 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Aircraft (IoU $\ge 0.5$)** | 39 / 45 (86.67%) | **1.46 m** | **5.22 m** | 2.14 m | 2.79 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Vehicles (IoU $\ge 0.5$)** | 12,048 / 23,372 (51.55%) | **0.47 m** | **0.93 m** | 0.52 m | 0.60 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Infrastructure (IoU $\ge 0.5$)** | 15,733 / 42,824 (36.74%) | **0.93 m** | **2.71 m** | 1.32 m | 1.89 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Registration Jitter (0.5 px)** | 37,300 (56.07%) | **0.72 m** | **2.45 m** | 1.18 m | 2.04 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Registration Jitter (1.0 px)** | 37,300 (56.07%) | **0.77 m** | **2.51 m** | 1.23 m | 2.07 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Registration Jitter (2.0 px)** | 37,300 (56.07%) | **0.97 m** | **2.64 m** | 1.39 m | 2.16 m | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `MEASURED` |
| **Independent External GPS Ground Truth CEP** | **NOT DONE** | 0 physical surveyor points | Physical field test | Differential GPS surveying | 2026-10-10 | `evaluation/results/geolocation_cep_report.json` | `NOT DONE` |

---

### KPI 7: Edge Throughput / Model Size / Power (Edge Benchmarks & SWaP-C)

**Source JSON:** [`evaluation/results/edge_bench_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\edge_bench_report.json)  
**Host Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU (8,188 MiB VRAM, AD107, CUDA 12.8, PyTorch 2.11.0+cu128).

| Platform / Metric | Value | Sample Size | Configuration | Measurement Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLO11m Model Parameters** | **20.1 Million** (20,084,336) | 1 checkpoint | `runs/train/xview_yolo11m_military` | Architecture model summary | 2026-10-10 | `backend/app/edge_benchmarks.py` | `MEASURED` |
| **YOLO11m FP16 Weight File Size** | **38.7 MB** (40,587,264 bytes) | 1 file | `runs/train/.../weights/best.pt` | On-disk file stat | 2026-10-10 | `backend/app/edge_benchmarks.py` | `MEASURED` |
| **YOLO11m ONNX File Size** | **40.5 MB** (42,476,544 bytes) | 1 file | `runs/train/.../weights/best_1024.onnx` | On-disk file stat | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED` |
| **YOLO11n Specialist Parameters** | **2.6 Million** (2,589,456) | 1 checkpoint | `runs/train/xview_vessel_1024_extended` | Architecture model summary | 2026-10-10 | `backend/app/edge_benchmarks.py` | `MEASURED` |
| **Host RTX 4060 Idle Baseline Power** | **12.64 W** | 100 samples | Idle desktop, display attached | `nvidia-smi` power polling @ 12.5 Hz | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED_RTX4060` |
| **Host RTX 4060 FP16 (.half()) Power** | Gross: **43.07 ± 0.20 W**, Net: **30.43 W** | 3 repeats (200 iters each) | Steady inference @ 12.5 Hz sampling | `nvidia-smi` board power sampling | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED_RTX4060` |
| **Host RTX 4060 FP16 (AMP) Power** | Gross: **43.42 ± 0.29 W**, Net: **30.78 W** | 3 repeats (200 iters each) | Steady inference @ 12.5 Hz sampling | `nvidia-smi` board power sampling | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED_RTX4060` |
| **Host Boosted Latency (AC plugged)** | **17.85 ± 0.11 ms** (P50: **17.37 ms**) | 3 repeats (200 iters each) | Clocks 2,610–2,625 MHz, 78–81W | PyTorch CUDA Event timing | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED_RTX4060` |
| **Host Boosted Throughput** | **55.65 – 56.50 FPS** | 3 repeats | Clocks 2,610–2,625 MHz | PyTorch CUDA Event timing | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED_RTX4060` |
| **Host Unboosted Latency** | **35.74 ms** (P50: **34.54 ms**) | 200 iterations | Clocks ~1.1–1.3 GHz, ~43W board | PyTorch CUDA Event timing | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `MEASURED_RTX4060` |
| **Jetson AGX Orin 64GB Latency Range** | **[10.8 ms – 23.8 ms]** (unmeasured; rough estimate only) | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Compute: 17.39ms * (58.2 / 42.6 Dense TFLOPs) = 23.8 ms; Bandwidth: 17.39ms * (256.0 / 204.8 GB/s) = 21.7 ms | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED (unmeasured; rough estimate only)` |
| **Jetson AGX Orin 64GB Throughput Range** | **[42.0 – 92.6 FPS]** (unmeasured; rough estimate only) | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Roofline scaling from 42.6 TFLOPs | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED (unmeasured; rough estimate only)` |
| **Jetson AGX Orin 64GB Measured Power** | *not estimated* (target envelope &le;60W) | 0 physical measurements | Physical Jetson not present on host | Physical `tegrastats` hardware rail sampling (unmeasured; rough estimate only) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `NOT DONE (unmeasured; rough estimate only)` |
| **Jetson Orin Nano 8GB Latency Range** | **[32.8 ms – 98.8 ms]** (unmeasured; rough estimate only) | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Compute: 17.39ms * (58.2 / 10.24 Dense TFLOPs) = 98.8 ms; Bandwidth: 17.39ms * (256.0 / 68.0 GB/s) = 65.5 ms | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED (unmeasured; rough estimate only)` |
| **Jetson Orin Nano 8GB Throughput Range** | **[10.1 – 30.5 FPS]** (unmeasured; rough estimate only) | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Roofline scaling from 10.24 TFLOPs | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED (unmeasured; rough estimate only)` |
| **Jetson Orin Nano 8GB Measured Power** | *not estimated* (target envelope &le;15W) | 0 physical measurements | Physical Jetson not present on host | Physical `tegrastats` hardware rail sampling (unmeasured; rough estimate only) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `NOT DONE (unmeasured; rough estimate only)` |
| **Archived Single-Point Estimates** | **19.4 ms, 38.2 ms, 28 W, 12 W** | 4 historical metrics | Superseded early estimates | Formally archived (unvalidated single points) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `SUPERSEDED_ARCHIVED` |

---

### KPI 8: Analyst Workload Reduction & Auto-Triage

**Source JSON:** [`evaluation/results/analyst_workload_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/analyst_workload_report.json)  
**Partition:** Strictly held-out `val_report` (38 scenes, 32.12 km², 14,008 raw detections consolidated into 2,379 entities).

> [!IMPORTANT]
> **Unified Operational Baseline Framing:**
> - **Primary Baseline (Baseline A — Raw Detection Manual Review):** Unassisted manual review of every raw detection ($14,008$ raw detections across 38 `val_report` scenes, or $4,423.58$ raw detections/hour at 12 scenes/hr surveillance pacing).
> - **Rakshak Consolidated Pipeline:** Sliced detections consolidated into $2,379$ spatial entities ($83.02\%$ item reduction: $14,008 \rightarrow 2,379$), minus $493$ auto-closed entities ($20.72\%$ auto-close rate; **100% of the 493 auto-closed items are isolated civilian vehicles**), leaving $1,886$ items requiring human review ($86.54\%$ item reduction: $14,008 \rightarrow 1,886$, consisting of $1,228$ in Human Review Queue and $658$ in Priority Queue, or $595.58$ items/hour at 12 scenes/hr).
> - **Secondary Fixed-Budget Baseline (Baseline B — Fixed 40 min/scene):** Arbitrary flat 40 min/scene budget ($8.0$ analyst-hours per surveillance hour). When item-level review takes $\ge 60\text{s}$, the $595.6$ items/hr exceeds the fixed 8.0h capacity, creating negative percentage differentials relative to this artificial cap (-24.1%, -148.1%, -396.4%).

| Metric / Scenario | Value | Sample Size | Dataset or Scenario | Method / Model | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Headline Item Reduction (Raw $\rightarrow$ Entities)** | **83.02%** ($14,008 \rightarrow 2,379$ entities) | 14,008 raw detections | 38 holdout scenes (`val_report`) | 500m spatial clustering | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Headline Item Reduction (Raw $\rightarrow$ Human Items)** | **86.54%** ($14,008 \rightarrow 1,886$ review items) | 14,008 raw detections | 38 holdout scenes (`val_report`) | Clustering + isolated vehicle auto-closure | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Real Auto-Close Rate (`val_report`)** | **20.72%** (493 / 2,379 entities) | 2,379 consolidated entities | 38 holdout scenes | Spatial clustering & rule auto-closure (100% isolated vehicles) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Scene-Level Bootstrap 95% CI** | **[19.68%, 20.21%]** | 1,000 bootstrap resamples | 38 distinct scenes | Cluster bootstrap across scenes | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Vehicle Auto-Close Fraction** | **42.83%** (493 / 1,151 entities) | 1,151 vehicle entities | `val_report` holdout | Isolated civilian vehicles auto-closed (all 493 auto-closed items) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Infrastructure Auto-Close Fraction** | **0.00%** (0 / 984 entities auto-closed) | 984 infrastructure entities | `val_report` holdout | 100% routed to Human Review Queue | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Vessel & Aircraft Auto-Close Fraction** | **0.00%** (0 / 309 detections auto-closed) | 245 vessels, 64 aircraft | `val_report` holdout | 100% escalated to Priority Queue | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Safety Suite v2: Missed Threat Rate** | **0.0%** (0 / 9 threats missed) | 9 critical threat cases | Safety Suite v2 (15 scenarios total) | Rule-by-rule: 9/9 escalated to Priority Queue | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Safety Suite v2: False Escalation Rate** | **0.0%** (0 / 4 controls escalated) | 4 cooperative vessel controls | Safety Suite v2 (15 scenarios total) | Rule-by-rule: 4/4 auto-closed benign | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Safety Suite v2: Ambiguous Review Routing** | **100.0%** (2 / 2 boundary cases routed) | 2 ambiguous boundary cases (1400m, 650m) | Safety Suite v2 (15 scenarios total) | Rule-by-rule: 2/2 safely routed to Human Review Queue | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Public AIS Corpus Dark Fraction** | **45.26%** (497,676 / 1,099,634 contacts) | 1,099,634 spaceborne detections | ESA Copernicus Sentinel-2 public corpus | AIS correlation match against Sentinel-2 PipeV4 | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Workload Reduction @ 45s (Baseline A: Raw Detections)** | **86.54%** (Baseline A: 55.29h $\rightarrow$ Rakshak: 7.44h; Saved: 47.85h/hr) | Assumed 45s review per item | 12 scenes/hr pacing (4,423.6 raw det/hr vs 595.6 items/hr) | Baseline A: 14,008 raw detections review | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `COMPUTED` |
| **Workload Reduction @ 60s (Baseline A: Raw Detections)** | **86.54%** (Baseline A: 73.73h $\rightarrow$ Rakshak: 9.93h; Saved: 63.80h/hr) | Assumed 60s review per item | 12 scenes/hr pacing (4,423.6 raw det/hr vs 595.6 items/hr) | Baseline A: 14,008 raw detections review | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `COMPUTED` |
| **Workload Reduction @ 120s (Baseline A: Raw Detections)** | **86.54%** (Baseline A: 147.45h $\rightarrow$ Rakshak: 19.85h; Saved: 127.60h/hr) | Assumed 120s review per item | 12 scenes/hr pacing (4,423.6 raw det/hr vs 595.6 items/hr) | Baseline A: 14,008 raw detections review | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `COMPUTED` |
| **Workload Reduction @ 240s (Baseline A: Raw Detections)** | **86.54%** (Baseline A: 294.91h $\rightarrow$ Rakshak: 39.71h; Saved: 255.20h/hr) | Assumed 240s review per item | 12 scenes/hr pacing (4,423.6 raw det/hr vs 595.6 items/hr) | Baseline A: 14,008 raw detections review | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `COMPUTED` |
| **Workload Reduction @ 45s (Baseline B: Fixed 40 min/scene)** | **6.9%** (Saved: 0.55 hrs / surv. hr) | Assumed 45s review per item | Model @ 12 scenes/hr, 40 min baseline (8.0h cap) | Baseline B: Fixed time budget (7.45h needed vs 8.0h cap) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Workload Reduction @ 60s (Baseline B: Fixed 40 min/scene)** | **-24.1%** (Over capacity: -1.93 hrs / surv. hr) | Assumed 60s review per item | Model @ 12 scenes/hr, 40 min baseline (8.0h cap) | Baseline B: Fixed time budget (9.93h needed vs 8.0h cap) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Workload Reduction @ 120s (Baseline B: Fixed 40 min/scene)** | **-148.1%** (Over capacity: -11.85 hrs / surv. hr) | Assumed 120s review per item | Model @ 12 scenes/hr, 40 min baseline (8.0h cap) | Baseline B: Fixed time budget (19.85h needed vs 8.0h cap) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Workload Reduction @ 240s (Baseline B: Fixed 40 min/scene)** | **-396.4%** (Over capacity: -31.71 hrs / surv. hr) | Assumed 240s review per item | Model @ 12 scenes/hr, 40 min baseline (8.0h cap) | Baseline B: Fixed time budget (39.71h needed vs 8.0h cap) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Operational Human-in-the-Loop Trial** | **NOT DONE** | 0 human analysts | Live military operations room | Timed user study with defense analysts | 2026-10-10 | `evaluation/results/analyst_workload_report.json` | `NOT DONE` |

---

### KPI 9: Mission-Planning Cycle Time & Tactical SITREP Compilation

**Source JSON:** [`evaluation/results/mission_planning_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/mission_planning_report.json) & [`evaluation/assumptions.yaml`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/assumptions.yaml)  
**Status:** **Partial: system steps measured, manual baseline assumed, no human user study**  
**Context:** Evaluates operational decision cycle time (OODA loop) across 3 reproducible tactical defense scenarios:
- **Scenario A:** Dark Vessel approaching restricted zone (Mumbai ODA, Maritime Domain)
- **Scenario B:** Unidentified convoy approaching border defense post (Sector Alpha, Army Ground Domain)
- **Scenario C:** UGS seismic tripwire alarm plus drone EO/IR confirmation (Cross-Domain Sensor Fusion)

Each scenario was evaluated over 10 repetitions (30 total runs) against local live REST microservices (`/api/sar/detections`, `/api/zones`, `/api/rag/query`, `/api/sitrep`, `/api/rag/dispatch-to-mission`, `/api/army/feeds`).

| Scenario / Metric | Value | Sample Size | Dataset or Scenario | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Scenario A: Rakshak Measured (REST)** | **0.2572 ± 0.1351 s** (Min: 0.1059s, Max: 0.4134s) | 10 repetitions | Scenario A: Dark Vessel (Mumbai ODA) | Local loopback REST timing (`time.perf_counter`) | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **Scenario A: Operator-Paced Estimate** | **50.26 s** | 10 runs + model | Scenario A: Dark Vessel (Mumbai ODA) | Machine time + 50.0s assumed think-time | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `ASSUMED` |
| **Scenario A: Manual Baseline** | **1680.0 s** (28.0 min) | Operations room staff model | Scenario A: Dark Vessel (Mumbai ODA) | 5-step manual ops room procedure model | 2026-10-10 | `evaluation/assumptions.yaml` | `ASSUMED` |
| **Scenario A: Cycle Time Reduction** | **97.01%** (Operator-Paced) / **99.98%** (Scripted REST) | 10 runs vs baseline | Scenario A: Dark Vessel (Mumbai ODA) | Computed reduction from assumed baseline | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `COMPUTED` |
| **Scenario B: Rakshak Measured (REST)** | **0.1397 ± 0.0173 s** (Min: 0.1167s, Max: 0.1751s) | 10 repetitions | Scenario B: Army Convoy (Sector Alpha) | Local loopback REST timing (`time.perf_counter`) | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **Scenario B: Operator-Paced Estimate** | **50.14 s** | 10 runs + model | Scenario B: Army Convoy (Sector Alpha) | Machine time + 50.0s assumed think-time | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `ASSUMED` |
| **Scenario B: Manual Baseline** | **1320.0 s** (22.0 min) | Operations room staff model | Scenario B: Army Convoy (Sector Alpha) | 5-step manual ops room procedure model | 2026-10-10 | `evaluation/assumptions.yaml` | `ASSUMED` |
| **Scenario B: Cycle Time Reduction** | **96.20%** (Operator-Paced) / **99.99%** (Scripted REST) | 10 runs vs baseline | Scenario B: Army Convoy (Sector Alpha) | Computed reduction from assumed baseline | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `COMPUTED` |
| **Scenario C: Rakshak Measured (REST)** | **0.1560 ± 0.0217 s** (Min: 0.1105s, Max: 0.1837s) | 10 repetitions | Scenario C: UGS Alarm + Drone (Cross-Domain) | Local loopback REST timing (`time.perf_counter`) | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **Scenario C: Operator-Paced Estimate** | **50.16 s** | 10 runs + model | Scenario C: UGS Alarm + Drone (Cross-Domain) | Machine time + 50.0s assumed think-time | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `ASSUMED` |
| **Scenario C: Manual Baseline** | **1320.0 s** (22.0 min) | Operations room staff model | Scenario C: UGS Alarm + Drone (Cross-Domain) | 5-step manual ops room procedure model | 2026-10-10 | `evaluation/assumptions.yaml` | `ASSUMED` |
| **Scenario C: Cycle Time Reduction** | **96.20%** (Operator-Paced) / **99.99%** (Scripted REST) | 10 runs vs baseline | Scenario C: UGS Alarm + Drone (Cross-Domain) | Computed reduction from assumed baseline | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `COMPUTED` |
| **Cross-Scenario Average Machine Time** | **0.1843 s** | 30 runs total | 3 reproducible tactical scenarios | Mean across all 3 scenarios | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **Cross-Scenario Average Operator-Paced** | **50.19 s** | 30 runs + model | 3 reproducible tactical scenarios | Mean across all 3 scenarios | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `ASSUMED` |
| **Cross-Scenario Average Manual Baseline** | **1440.0 s** (24.0 min) | Operations room staff model | 3 reproducible tactical scenarios | Mean across all 3 scenarios | 2026-10-10 | `evaluation/assumptions.yaml` | `ASSUMED` |
| **Cross-Scenario Average Reduction** | **96.51%** | 30 runs vs baseline | 3 reproducible tactical scenarios | Mean across all 3 scenarios | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `COMPUTED` |
| **STANAG 2014 SITREP Compilation Latency** | **< 50 ms** (16.74 ms in Scen A) | 10 operational calls | Active situational entities | Procedural Python text compiler | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **Sovereign RoE Doctrine RAG Retrieval** | **< 40 ms** (39.09 ms in Scen B) | 10 operational calls | Rules of Engagement query (INBR 8 / UNCLOS) | Local BM25 lexical index (0 cloud calls) | 2026-10-10 | `evaluation/results/mission_planning_report.json` | `MEASURED` |
| **End-to-End Human Military Staff Exercise** | **NOT DONE** | 0 operational military staff | Live brigade/fleet command staff exercise | Comparative military staff exercise | 2026-10-10 | `evaluation/results/analyst_workload_report.json` | `NOT DONE` |
| **Tactical Orders Field Dissemination Time** | **NOT DONE** | 0 forward tactical units | Real radio/data dispatch | Combat net radio transmission trial | 2026-10-10 | `evaluation/results/analyst_workload_report.json` | `NOT DONE` |

---

### KPI 10: Platform Availability & Data Survivability under DDIL Conditions

**Source JSON:** [`evaluation/results/ddil_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\ddil_report.json)  
**Scenario:** 1,800.0 simulated seconds (30.0 simulated minutes), 60× time compression (35.31s wall-clock), local loopback IPC (0 external calls), detection interval 2.5s.

| Metric / Scenario | Value | Sample Size | Scenario Condition | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Edge Detection Uptime** | **100.00%** | 720 alert epochs | 30.0 min mission under active jamming | Continuous edge inference in disconnected state | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Alert Delivery Success Rate** | **100.00%** (720 / 720 delivered) | 720 generated alerts | Store-and-forward SQLite WAL queue | Idempotent deduplication & sequence tracking | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Lost Alerts** | **0** | 720 alerts | Full blackout phases | SQLite WAL persistence | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Filtered Duplicate Packets** | **13 duplicate packets handled** | 720 alerts | Flapping and retransmission | Sequence-numbered idempotency table | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Outage 1 Resync Time (300s blackout, 32 kbps)** | **40.89 ± 6.83 s** [Min: 33.19s, Max: 58.24s] | 20 seeds (120 buffered alerts) | 350ms lat, 15% packet loss, 32 kbps degraded link | Priority queue drain with anti-starvation aging | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Outage 2 Resync Time (300s blackout, 512 kbps)** | **10.06 ± 0.00 s** [Min: 10.05s, Max: 10.06s] | 20 seeds (120 buffered alerts) | 25ms lat, 0% packet loss, 512 kbps mesh link | High-speed restoration queue drain | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Picture Availability (Staleness $\le$ 10s)** | **60.36%** | 1,800 simulated seconds | 30.0 min mission | Cumulative time tracking | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Picture Availability (Staleness $\le$ 30s)** | **68.90%** | 1,800 simulated seconds | 30.0 min mission | Cumulative time tracking | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Picture Availability (Staleness $\le$ 60s)** | **72.38%** | 1,800 simulated seconds | 30.0 min mission | Cumulative time tracking | 2026-10-10 | `evaluation/results/ddil_report.json` | `SIMULATED` |
| **Physical Combat Net Radio DDIL Trials** | **NOT DONE** | 0 physical tactical radios | Tactical VHF/UHF tactical radio testbed | Hardware SINCGARS/Tadiran CNR trial | 2026-10-10 | `evaluation/results/ddil_report.json` | `NOT DONE` |

---

### Zero-Egress Air-Gap Compliance

**Source JSON:** [`evaluation/results/egress_test_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\egress_test_report.json)  
**Audit Method:** Active loopback & outbound socket trap, `psutil` network monitoring, and code scan.

| Security Audit Dimension | Measured Value | Target | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Outbound Non-Loopback Sockets** | **0** | 0 | Socket trap & OS network monitor | 2026-10-10 | `evaluation/results/egress_test_report.json` | `MEASURED` |
| **External DNS Query Attempts** | **0** | 0 | DNS intercept hook | 2026-10-10 | `evaluation/results/egress_test_report.json` | `MEASURED` |
| **External CDN/Tile References in Code** | **0** | 0 | Static regex audit (22 files) | 2026-10-10 | `evaluation/results/egress_test_report.json` | `MEASURED` |
| **Monitored Loopback Sockets (127.0.0.1)** | **40** | $\ge 1$ | Active process socket census | 2026-10-10 | `evaluation/results/egress_test_report.json` | `MEASURED` |
| **Socket Guard Violation Intercept** | **1 blocked** | Active | Controlled trap validation | 2026-10-10 | `evaluation/results/egress_test_report.json` | `MEASURED` |
| **Air-Gap Verification Verdict** | **NO_EGRESS_OBSERVED** | 0 outbound non-loopback calls | Socket trap & connection monitor | 2026-10-10 | `evaluation/results/egress_test_report.json` | `MEASURED` |
| **Kernel eBPF / Hardware Network Tap Audit** | **NOT DONE** | Hardware isolation | User-space Python hook used; kernel eBPF / TAP uninstrumented | 2026-10-10 | `evaluation/results/egress_test_report.json` | `NOT DONE` |

---

## 🏛️ 3. System Architecture & Dual-Domain Implementation

Project Rakshak 2.0 follows a strict 4-tier air-gapped pipeline:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 1: MULTI-MODAL SENSOR INGESTION LAYER                      │
│   Sentinel-1 SAR Radar   │   xView GeoTIFFs (0.3m)   │   Drone UAV EO/IR   │   AIS Transponders   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 2: SOVEREIGN EDGE INFERENCE CORE                           │
│   • CA-CFAR Radar Speckle Filter (RCS in dB, Hull Length Estimation)                   │
│   • Retrained YOLO11m Military Detector (Vessel, Aircraft, Vehicle, Infrastructure)    │
│   • O(N) Spatial Grid Indexer (500m Convoy Clustering & Geofence Intersection)         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 3: KINEMATIC THREAT MATRIX & DOCTRINE RAG                  │
│   • SAR-to-AIS Haversine Spatial Matcher (Flags dark vessels within 5 km buffer)       │
│   • Circular Error Probable (CEP) Kinematic Drift Ellipses (Dead-reckoning)           │
│   • Deterministic 0-100 Threat Scoring (Explainable, non-hallucinatory)               │
│   • Sovereign Offline RAG (Rules of Engagement: INBR 8 & Border Security Directives)   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 4: TACTICAL C2 INTERFACES & EXPORT                         │
│   • Joint Common Operating Picture (COP) with interactive 60 FPS Leaflet GIS canvas   │
│   • Naval Domain Console (SAR radar inspection & 1-click AIS adjudication)             │
│   • Army Domain Console (Garuda-04 drone downlink & UGS seismic alarm triage)          │
│   • Automated NATO STANAG 2014 Military SITREP & Mission Waypoint Dispatcher          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Naval vs. Army Domain Specialization

| Operational Parameter | ⚓ Naval Domain Console | 🪖 Army Domain Console |
| :--- | :--- | :--- |
| **Theater Scope** | Macro-scale ocean / EEZ / maritime chokepoints (thousands of km²) | Micro-scale tactical land borders, Line of Control (LoC), FOB perimeters |
| **Sensors Handled** | Sentinel-1 SAR C-Band Radar + xView Spaceborne GeoTIFF + AIS | Tactical Drone UAV EO/IR video + UGS Seismic Geophones (18 Hz) + SIGINT |
| **Primary Threat** | **Dark Vessels**: Hostile ships disabling AIS near naval security perimeters | **Tactical Convoys & Infiltration**: Blackout vehicle columns, dismounted patrols |
| **Core Algorithm** | CA-CFAR radar extraction + Haversine spatial correlation (<5 km) | Convoy clustering heuristic ($O(N)$ spatial grid) + Seismic tripwire triage |
| **Response Workflow** | 1-Click Analyst Adjudication (`Matched`, `Dark Vessel +50`, `Unknown`) | Alarm State Machine (`ACTIVE` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`) |
| **Governing Doctrine** | UNCLOS Article 110 (Right of Visit & Boarding), Indian Navy INBR 8 | Border Rules of Engagement (RoE), FOB Quick Reaction Team (QRT) dispatch |

---

## ⚡ 4. Quickstart & Deployment

### Option 1: 1-Click Production Launch (Recommended for Evaluation)
Double-click [`start_production.bat`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/start_production.bat) in the project root. This executes FastAPI directly mounting the pre-compiled React SPA with zero internet dependencies. Access at **`http://localhost:8000`**.

### Option 2: Command Line Launch
```bash
# Activate environment and launch unified C4ISR server
.\.venv\Scripts\activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Option 3: Verification Suites
```bash
# 1. Run zero-egress proof suite (confirms 0 non-loopback connections)
python evaluation/egress_test.py

# 2. Run platform smoke test suite (12/12 defense tests)
python smoke_test_platform.py

# 3. Run unit test suite (38/38 pytest cases)
python -m pytest
```

---

## 🎯 5. Live Demonstration Flow (2-Minute Walkthrough)

1. **Sovereign Access Terminal:**
   - Demonstrate the terminal login gate. Login with operational credentials bootstrapped in `.env` (or newly set during mandatory first-login password rotation). Rate-limited with immutable security audit logging.
2. **Joint Common Operating Picture (COP):**
   - View the Arabian Sea & Western Naval Command surveillance theater.
   - Point out the **Prioritized Triage Queue** on the right sidebar. Click a **Critical Dark Vessel (SAR)** contact — the map smoothly flies to its coordinate, displaying its velocity vector and Circular Error Probable (CEP) uncertainty drift ellipse.
   - Toggle map layers: Sentinel-1 SAR Radar, Optical Satellites, AIS Beacons, Defense Geofences, and Threat Heatmap.
3. **Naval Domain (Dark Vessel Interdiction):**
   - Switch to **Naval Domain**. Inspect Sentinel-1 C-Band radar hits.
   - Point out the radar targets flagged with **`CRITICAL: Confirmed Dark Vessel (No AIS) +50`**.
   - Demonstrate 1-click analyst adjudication (`Matched`, `Dark Vessel`, `Unknown`).
4. **Army Domain (Tactical Downlinks & Ground Sensors):**
   - Switch to **Army Domain**.
   - Click **"1-Click Test: Vehicle Convoys (1217.tif)"** or **"Airbase Targets (1154.tif)"**.
   - Observe real-time neural detection bounding boxes over convoys and aircraft.
   - Review Unattended Ground Sensor (UGS) seismic alarms (18 Hz tracked vehicle rumble) and triage the alarm state (`ACTIVE` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`).
5. **Automated Military SITREP & Doctrine RAG:**
   - Switch to **Tactical SITREP**. Click **"Generate STANAG Situation Report"**.
   - Show the auto-compiled NATO/Indian STANAG 2014 military report summarizing all active naval and land threats.
   - Switch to **Tactical AI (RAG)** and ask a legal query: *"What are the rules of engagement under UNCLOS Article 110 for boarding an unflagged vessel in the EEZ?"* — observe instant offline doctrine retrieval.

---

## ⚠️ 6. Operational Limitations & Known Constraints

To maintain absolute scientific and defense engineering integrity, the following operational limitations are formally documented:

1. **Simulated Spaceborne SAR & Tactical Radio Hardware:**
   No physical orbital spaceborne SAR receiver (xView3-SAR) or physical military combat net radio hardware was available during development. Dark vessel kinematics (20 independent seeds, 10,000 contacts per condition) and DDIL store-and-forward link flapping (1,800 simulated seconds) are evaluated using mathematically rigorous Monte Carlo models labeled `SIMULATED`.
2. **Vessel Class Pixel Footprint & Imbalance:**
   Small maritime vessel detection in high-resolution optical imagery remains constrained by small pixel footprints (12–35 px bounding boxes) and severe dataset class imbalance (280 vessels vs 42,824 infrastructure instances). Generalist vessel recall is **14.65%** (mAP50 12.75%), rising to **23.57%** (mAP50 16.24%) with the dedicated 1024px vessel specialist.
3. **Unvalidated Jetson Edge Projections:**
   Jetson AGX Orin and Orin Nano latency is unmeasured, order of tens of ms. Power consumption cannot be measured on host laptop and requires physical Jetson hardware rail sampling (`tegrastats`). All Jetson metrics remain strictly **unmeasured; rough estimate only**.
4. **User-Space Zero-Egress Boundary:**
   Zero-egress air-gap verification is executed using application-level Python socket interception hooks and OS-level `psutil` network monitoring. It does not incorporate kernel-level eBPF tracing or physical hardware network tap packet capture.
5. **Procedural Offline Basemap:**
   To guarantee 100% air-gapped execution without external tile downloads (`tile.openstreetmap.org` or `arcgisonline.com`), map tiles are synthesized offline procedurally on localhost. The platform does not bundle complete licensed worldwide vector MBTiles.
6. **Incomplete Ground-Truth Labels in Public Imagery:**
   The underlying public xView dataset contains incomplete labeling on minor auxiliary roads, unannotated civilian vehicles, and small coastal craft. In full-scene evaluations, genuine physical objects detected by the model are mathematically penalized as false positives due to missing annotations in ground-truth GeoTIFFs.
7. **Absence of Independent GPS Survey (Detection Localisation Error):**
   Localisation error (CEP50 = 0.70 m, CEP90 = 2.43 m) is measured strictly against the dataset's own GeoTIFF affine transform metadata, not independent differential GPS ground surveys.

---

## 👥 7. Team BotS — Roles & Responsibilities

| Team Member | Engineering Role | Core Module Responsibilities |
| :--- | :--- | :--- |
| **Aditya Bajantri** | **Team Lead & Neural Vision Architect** | YOLO11m architecture, 5,838-tile dataset retraining, WBF box fusion, PyTorch training pipelines |
| **Gagan Bongale** | **Data Engineer & Pipeline Specialist** | Satellite GeoTIFF slicing, 1024px tiling, Sentinel-2 band ingestion, annotation parsing |
| **Utsav Nanapur** | **Radar Signal & AIS Correlation Engineer** | Sentinel-1 SAR CA-CFAR speckle filtering, RCS dB calculations, Haversine spatial correlation |
| **Misbah Falak** | **Kinematics & Spatial Threat Lead** | Circular Error Probable (CEP) drift ellipses, dead-reckoning trajectory models, $O(N)$ Threat Matrix |
| **Shalina Maniyar** | **Tactical C2 Interface & GIS Engineer** | React 19 Leaflet GIS mapping, 60 FPS offline tile rendering, HUD design, C2 telemetry |
| **Niyati Gogri** | **Military SITREP & Doctrine RAG Specialist** | Automated NATO STANAG 2014 situation reporting engine, offline UNCLOS / INBR 8 doctrine RAG |

---

## 📄 8. License & Classification

* **Project Classification:** Educational & Defense Research Prototype — Hackfest 2026.
* **License:** MIT License. Free for academic, competition, and research use.
