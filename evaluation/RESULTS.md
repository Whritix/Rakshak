# 🛡️ Project Rakshak 2.0 — Grounded Operational KPI Results Master (`RESULTS.md`)

> **Master Evaluation Dossier**: Every metric, number, and benchmark recorded in this file is extracted strictly from canonical JSON benchmark reports stored in [`evaluation/results/`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results).
> No metrics or thresholds have been invented or altered. Every row defines value, sample size, dataset or scenario, method, date, source JSON path, and an explicit provenance tag.

---

## 1. Per-Class Precision, Recall & mAP

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

## 2. Dark-Vessel Detection Rate

**Source JSON:** [`evaluation/results/dark_vessel_eval_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\dark_vessel_eval_report.json)  
**Dataset / Scenario:** 20 independent seeds (`seed=1` to `seed=20`), $N=500$ contacts per cell ($10,000$ contacts evaluated per sweep condition). Synthetic maritime scenario (no local xView3-SAR dataset present in repository).

| Metric / Scenario | Value | Sample Size | Dataset or Scenario | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Headline E2E Dark Vessel Capture** | **79.40 ± 2.80%** [95% CI: 78.09%, 80.71%] | 20 seeds (10,000 contacts, 3,000 dark) | Arabian Sea littoral, 2.0 km radius, ±30 min offset | CA-CFAR + AIS Dead-Reckoning temporal correlation | 2026-10-10 | `evaluation/results/dark_vessel_eval_report.json` | `SIMULATED` |
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

## 3. Sensor-to-Alert Latency

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
| **SAR CA-CFAR Radar Processing** | **1.1 s** | 25,000 radar cells | 289 km² radar coverage footprint | 2D CA-CFAR sliding window algorithm | 2026-10-10 | `backend/app/sar_engine.py` | `MEASURED` |
| **SAR-to-AIS Haversine Spatial Matching** | **85 ms** | All active AIS coastal tracks | 5 km correlation buffer | Haversine great-circle calculation | 2026-10-10 | `backend/app/sar_engine.py` | `MEASURED` |
| **Sovereign BM25 Doctrine RAG Query** | **< 40 ms** | 12 sovereign military doctrine documents | Rules of Engagement query (INBR 8 / UNCLOS) | Local BM25 lexical index (0 network calls) | 2026-10-10 | `backend/app/rag_engine.py` | `MEASURED` |
| **STANAG 2014 SITREP Compilation** | **< 50 ms** | Active threat entities | Military SITREP generation | In-memory procedural STANAG compiler | 2026-10-10 | `backend/app/sitrep_generator.py` | `MEASURED` |
| **End-to-End Decision Pipeline Target** | **< 1.8 s** | Target envelope | Full scene ingestion to alert dispatch | Complete multi-modal pipeline | 2026-10-10 | `backend/app/kpi_service.py` | `PROJECTED` |
| **Complete Scene Ingestion (Multi-Tile Triage)** | **NOT DONE** (Empirical multi-scene latency distribution unlogged in JSON) | 0 logged full scenes in JSON | 38 validation scenes | Sliced SAHI tile orchestration | 2026-10-10 | `evaluation/results/` | `NOT DONE` |

---

## 4. False Alarms & Threat Alert Rates

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

## 5. Track Continuity & ID-Switch Rate

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
| **Chokepoint: JPDA ID Switches** | **2** | 50 seeds (205 GT points) | 5 vessels, dense clutter $\lambda_c=10^{-4}$ | JPDA (Mutual exclusion) | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: JPDA MOTA / MOTP** | MOTA: **71.22%**, MOTP: **12.62 m** | 50 seeds (205 GT points) | High-density chokepoint | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: JPDA Track Continuity** | **88.29%** (vs Hungarian 82.44%, NN 80.00%) | 50 seeds (205 GT points) | High-density chokepoint | JPDA | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Chokepoint: Hungarian ID Switches** | **0** (MOTA: **51.22%**, Continuity: **82.44%**) | 50 seeds (205 GT points) | High-density chokepoint | Hungarian + Mahalanobis Gate | 2026-10-10 | `evaluation/results/tracking_report.json` | `SIMULATED` |
| **Field Radar Multi-Target Track Trials** | **NOT DONE** | 0 physical tracks | Physical coastal radar tracking | Hardware radar tracker deployment | 2026-10-10 | `evaluation/results/tracking_report.json` | `NOT DONE` |

---

## 6. Geolocation Precision & Circular Error Probable (CEP)

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

## 7. Edge Throughput, Model Size & Power (SWaP-C)

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
| **Jetson AGX Orin 64GB Latency Range** | **[10.8 ms – 23.8 ms]** | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Roofline scaling from 42.6 TFLOPs | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED` |
| **Jetson AGX Orin 64GB Throughput Range** | **[42.0 – 92.6 FPS]** | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Roofline scaling from 42.6 TFLOPs | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED` |
| **Jetson AGX Orin 64GB Measured Power** | *not estimated* (target envelope &le;60W) | 0 physical measurements | Physical Jetson not present on host | Physical `tegrastats` hardware rail sampling | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `NOT DONE` |
| **Jetson Orin Nano 8GB Latency Range** | **[32.8 ms – 98.8 ms]** | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Roofline scaling from 10.24 TFLOPs | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED` |
| **Jetson Orin Nano 8GB Throughput Range** | **[10.1 – 30.5 FPS]** | Roofline interval | Theoretical interval (1.3×–2.0× TRT) | Roofline scaling from 10.24 TFLOPs | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `PROJECTED` |
| **Jetson Orin Nano 8GB Measured Power** | *not estimated* (target envelope &le;15W) | 0 physical measurements | Physical Jetson not present on host | Physical `tegrastats` hardware rail sampling | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `NOT DONE` |
| **Archived Single-Point Estimates** | **19.4 ms, 38.2 ms, 28 W, 12 W** | 4 historical metrics | Superseded early estimates | Formally archived (unvalidated single points) | 2026-10-10 | `evaluation/results/edge_bench_report.json` | `SUPERSEDED_ARCHIVED` |

---

## 8. Analyst Workload Reduction

**Source JSON:** [`evaluation/results/analyst_workload_report.json`](file:///c:/Users/awhri\OneDrive\Desktop\DEF\evaluation\results\analyst_workload_report.json)  
**Partition:** Strictly held-out `val_report` (38 scenes, 32.12 km², 2,379 consolidated entities).

| Metric / Scenario | Value | Sample Size | Dataset or Scenario | Method / Model | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Real Auto-Close Rate (`val_report`)** | **20.72%** (493 / 2,379 entities) | 2,379 consolidated entities | 38 holdout scenes | Spatial clustering & rule-based auto-closure | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Scene-Level Bootstrap 95% CI** | **[19.68%, 20.21%]** | 1,000 bootstrap resamples | 38 distinct scenes | Cluster bootstrap across scenes | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Vehicle Auto-Close Fraction** | **42.83%** (493 / 1,151 entities) | 1,151 vehicle entities | `val_report` holdout | Isolated civilian vehicles auto-closed | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Infrastructure Auto-Close Fraction** | **0.00%** (0 / 984 entities auto-closed) | 984 infrastructure entities | `val_report` holdout | 100% routed to Human Review Queue | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Vessel & Aircraft Auto-Close Fraction** | **0.00%** (0 / 309 detections auto-closed) | 245 vessels, 64 aircraft | `val_report` holdout | 100% escalated to Priority Queue | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Missed Threat Rate** | **0.0%** (0 / 6 threats missed) | 6 adversarial threat cases | Safety Suite v2 adversarial tests | Gating & threat escalation policy | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **False Escalation Rate** | **0.0%** (0 / 4 controls escalated) | 4 cooperative vessel controls | Safety Suite v2 control tests | AIS correlation verification | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Public AIS Corpus Dark Fraction** | **45.26%** | 1,099,634 spaceborne detections | ESA Copernicus Sentinel-2 public corpus | AIS correlation match against Sentinel-2 | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `MEASURED` |
| **Workload Reduction @ 45s Glance** | **6.9%** (Saved: 0.55 hrs / surv. hr) | Assumed 45s review per item | Model @ 12 scenes/hr, 40 min baseline | Unified time model (751.3 entities/hr) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Workload Reduction @ 60s Rapid** | **-24.1%** (Saved: -1.93 hrs / surv. hr) | Assumed 60s review per item | Model @ 12 scenes/hr, 40 min baseline | Unified time model (595.6 review items/hr) | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Workload Reduction @ 120s Standard** | **-148.1%** (Saved: -11.85 hrs / surv. hr) | Assumed 120s review per item | Model @ 12 scenes/hr, 40 min baseline | Unified time model | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Workload Reduction @ 240s Forensic** | **-396.4%** (Saved: -31.71 hrs / surv. hr) | Assumed 240s review per item | Model @ 12 scenes/hr, 40 min baseline | Unified time model | 2026-10-09 | `evaluation/results/analyst_workload_report.json` | `ASSUMED` |
| **Operational Human-in-the-Loop Trial** | **NOT DONE** | 0 human analysts | Live military operations room | Timed user study with defense analysts | 2026-10-10 | `evaluation/results/analyst_workload_report.json` | `NOT DONE` |

---

## 9. Mission-Planning Cycle Time

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

## 10. Availability Under DDIL Conditions

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

## 11. Zero-Egress & Air-Gap Compliance

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

## 12. Multi-Temporal Satellite Change Detection

**Source JSON:** [`evaluation/results/change_detection_report.json`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/change_detection_report.json) & [`evaluation/results/change_detection_summary.md`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/evaluation/results/change_detection_summary.md)  
**Dataset / Scenario:** 20 seeded synthetic bi-temporal pairs (`seed=1` to `seed=20`) constructed from 100% held-out `val_report` partition (540 tiles). Each synthetic pair contains exactly 3 ground-truth object edits (1 NEW, 1 REMOVED, 1 MOVED) = 60 total edits across 20 pairs (+1 structural revetment per pair). Injected misalignments 0.0 to 8.0 px; class-aware Hungarian bipartite matching with stationary distance $\le 28$ px and movement distance $\le 120$ px; secondary radiometric normalisation with channel gain & bias calibration.

| Metric / Tactical Scenario | Value | Sample Size | Scenario Condition | Method | Date | Source JSON Path | Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Headline Change Precision (Raw)** | **31.17 ± 30.86%** (0.3117) [Pooled: **23.76%** (0.2376)] | 20 seeds (60 ground-truth edits, 3 edits/pair) | `val_report` holdout | YOLO11m + Class-Aware Hungarian Matcher | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Headline Change Recall (Raw)** | **40.00 ± 24.95%** (0.4000) [Pooled: **40.00%** (0.4000)] | 20 seeds (60 ground-truth edits, 3 edits/pair) | `val_report` holdout | YOLO11m + Class-Aware Hungarian Matcher | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Headline Change F1 Score (Raw)** | **0.3005 ± 0.2142** (0.3005) [Pooled: **0.2981**] | 20 seeds (60 ground-truth edits, 3 edits/pair) | `val_report` holdout | Harmonic mean of change precision & recall | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Stability-Filtered Change Precision** | **32.50 ± 45.48%** (0.3250) [Pooled: **87.50%** (0.8750)] | 20 seeds (60 ground-truth edits, 3 edits/pair) | `val_report` holdout | Conf $\ge 0.40$, Ghost check $< 0.15$ within 28px | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Stability-Filtered Change Recall** | **11.67 ± 15.90%** (0.1167) [Pooled: **11.67%** (0.1167)] | 20 seeds (60 ground-truth edits, 3 edits/pair) | `val_report` holdout | Conf $\ge 0.40$, Ghost check $< 0.15$ within 28px | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Stability-Filtered Change F1 Score** | **0.1700 ± 0.2326** (0.1700) [Pooled: **0.2059**] | 20 seeds (60 ground-truth edits, 3 edits/pair) | `val_report` holdout | Conf $\ge 0.40$, Ghost check $< 0.15$ within 28px | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Aircraft Change Precision** | **75.00%** (0.7500) | 16 GT aircraft edits | 10 aircraft holdout tiles | YOLO11m + Class-Aware Matching | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Aircraft Change Recall** | **37.50%** (0.3750) | 16 GT aircraft edits | 10 aircraft holdout tiles | YOLO11m + Class-Aware Matching | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Aircraft Change F1 Score** | **0.5000 ± 0.3333** (0.5000) | 16 GT aircraft edits | 10 aircraft holdout tiles | Class-specific F1 | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Vehicle Change Precision** | **21.95%** (0.2195) | 44 GT vehicle edits | 10 vehicle holdout tiles | YOLO11m + Class-Aware Matching | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Vehicle Change Recall** | **40.91%** (0.4091) | 44 GT vehicle edits | 10 vehicle holdout tiles | YOLO11m + Class-Aware Matching | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Vehicle Change F1 Score** | **0.2857 ± 0.1789** (0.2857) | 44 GT vehicle edits | 10 vehicle holdout tiles | Class-specific F1 | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **NEW Objects Precision** | **20.51%** (0.2051) | 20 GT additions | `val_report` holdout | Unmatched post-scene neural detections | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **NEW Objects Recall** | **40.00%** (0.4000) | 20 GT additions | `val_report` holdout | Unmatched post-scene neural detections | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **NEW Objects F1 Score** | **0.2712** | 20 GT additions | `val_report` holdout | Harmonic mean | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **REMOVED Objects Precision** | **19.15%** (0.1915) | 20 GT removals | `val_report` holdout | Inpainted post-scene missing detections | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **REMOVED Objects Recall** | **45.00%** (0.4500) | 20 GT removals | `val_report` holdout | Inpainted post-scene missing detections | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **REMOVED Objects F1 Score** | **0.2687** | 20 GT removals | `val_report` holdout | Harmonic mean | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **MOVED Objects Precision** | **46.67%** (0.4667) | 20 GT relocations | `val_report` holdout | Spatial relocation (18 < d $\le$ 120 px) | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **MOVED Objects Recall** | **35.00%** (0.3500) | 20 GT relocations | `val_report` holdout | Spatial relocation (18 < d $\le$ 120 px) | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **MOVED Objects F1 Score** | **0.4000** | 20 GT relocations | `val_report` holdout | Harmonic mean | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Mean Co-Registration Error (0-8 px shift)** | **0.1887 ± 0.1350 px** | 20 seeds (shifts 0.0 to 8.0 px) | Sub-pixel co-registration | ORB (2500 kp) + RANSAC & Phase Correlation | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Registration Error @ 0.0 px Shift** | **0.0017 ± 0.0010 px** (Max: **0.0034 px**) | 8 trials | Stationary baseline | ORB + RANSAC Affine | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Registration Error @ 2.0 px Shift** | **0.0807 ± 0.0443 px** (Max: **0.1650 px**) | 8 trials | 2.0 px radial offset | ORB + RANSAC Affine | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Registration Error @ 4.0 px Shift** | **0.1037 ± 0.0825 px** (Max: **0.3097 px**) | 8 trials | 4.0 px radial offset | ORB + RANSAC Affine | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Registration Error @ 6.0 px Shift** | **0.1270 ± 0.1538 px** (Max: **0.4494 px**) | 8 trials | 6.0 px radial offset | ORB + RANSAC Affine | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Registration Error @ 8.0 px Shift** | **0.1086 ± 0.0537 px** (Max: **0.2322 px**) | 8 trials | 8.0 px radial offset | ORB + RANSAC Affine | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Structural Anomaly Capture Rate** | **70.00%** (0.7000) | 20 injected structural revetments | Secondary pixel diff signal | Radiometric gain/bias normalization & morphological filtering | 2026-10-10 | `evaluation/results/change_detection_report.json` | `SIMULATED` |
| **Real-World Bi-Temporal Satellite Sea/Land Trials** | **NOT DONE** | 0 multi-pass satellite overflights | Operational satellite constellation passes | Requires multi-day satellite tasking | 2026-10-10 | `evaluation/results/change_detection_report.json` | `NOT DONE` |

### False-Positive Root Cause Breakdown (77 Total Raw FPs)

| Root Cause Category | Count | Percentage | Physical / Algorithmic Mechanism | Mitigation |
| :--- | :---: | :---: | :--- | :--- |
| **(a) Detector flicker on unchanged objects** | **49** | **63.64%** | Unedited ground-truth objects present in both scenes hovering near 0.25 threshold in one scene but missed in partner scene | Pruned by partner-scene ghost filter ($< 0.15$ within 28px) |
| **(b) Inpainting boundary artifacts** | **24** | **31.17%** | Telea inpainting on natural structured terrain leaves high-frequency texture steps that trigger false detections | Pruned by confidence elevation ($\ge 0.40$) |
| **(c) Mis-registration / texture noise** | **4** | **5.19%** | Residual sub-pixel displacement noise and unassociated background clutter | Controlled by ORB+RANSAC sub-pixel co-registration |
| **Total Baseline False Positives** | **77** | **100.00%** | Combined false alarms before stability filtration | Reduced to **1 FP** (98.7% reduction) under stability filter |

---

## 13. Problem Statement Mapping & Milestone Grounding

| Dimension | Implemented Status | Completion Rate |
| :--- | :--- | :--- |
| **Completed (Measured)** | 6 of 13 primary dimensions | **46.2%** |
| **Completed (Simulated)** | 5 of 14 target dimensions | **35.7%** |
| **Partially Completed** | 2 of 13 primary dimensions (SWaP-C & Mission Planning) | **15.4%** |
| **Unmeasured / Field Exercise** | 1 of 13 primary dimensions (GPS CEP field survey) | **7.7%** |

