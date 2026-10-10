# Project Rakshak 2.0: Empirical Edge SWaP-C & Multi-Format Benchmark Summary

- **Timestamp UTC**: 2026-10-10T14:05:00.488367+00:00
- **Host Hardware**: NVIDIA GeForce RTX 4060 Laptop GPU (CUDA 12.8)
- **Evaluated Tile Resolution**: 1024×1024 px static shape
- **Holdout Validation Scope**: All 540 `val_report` tiles (66,521 ground-truth instances)
- **Vessel Specialist Scope**: 5 scenes / 21 tiles / 280 vessels (0 training scene overlap verified)

---

## 1. Latency Configuration, Thermal Spread & Power Telemetry

| Configuration / State | Base Mean Latency | Spread (3 Repeats) | Operating Clocks | GPU Thermals | Net Board Power |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **High-Performance Boost (AC Plugged-in)** | **17.39 ms** (P50: 16.7 ms) | **17.47 ± 0.14 ms** | 2,610 – 2,625 MHz | 63°C – 82°C | **+29.42 ± 0.20 W** (gross 43.1 W) |
| **Unboosted / Power-Throttled State** | **35.74 ms** (P50: 34.5 ms) | ~34.5 – 37.9 ms | ~1,100 – 1,300 MHz | 60°C | +29.77 ± 0.29 W (gross 43.4 W) |

*Power Comparison (3 Repeats @ 12.5 Hz)*:
- Measured Idle Baseline: **12.64 W**
- PyTorch FP16 (`.half()`): **43.07 ± 0.20 W** gross (+29.42 W net)
- PyTorch FP16 (AMP): **43.42 ± 0.29 W** gross (+29.77 W net)
- Delta: **+0.35 W** (negligible; no significant power difference between .half() and AMP; thermal-saturation figures dropped).

---

## 2. Multi-Format Accuracy on ALL 540 `val_report` Tiles (66,521 Targets)

| Target Class | Ground Truth Instances | PyTorch FP32 mAP@50 | PyTorch FP16 mAP@50 | ONNX Runtime mAP@50 | Accuracy Delta (FP16 vs FP32) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Vessel** | **280** | **12.38%** (P: 36.1%, R: 14.3%) | **12.75%** (P: 36.3%, R: 14.7%) | **12.49%** (P: 36.3%, R: 14.2%) | +0.37% (No loss) |
| **Aircraft** | **45** | **89.77%** (P: 57.9%, R: 86.7%) | **89.85%** (P: 57.9%, R: 86.7%) | **89.32%** (P: 60.1%, R: 86.7%) | +0.08% (Preserved) |
| **Vehicle** | **23,372** | **46.89%** (P: 60.0%, R: 52.5%) | **46.83%** (P: 59.1%, R: 52.6%) | **46.04%** (P: 60.8%, R: 51.3%) | -0.06% (Parity) |
| **Infrastructure** | **42,824** | **44.45%** (P: 62.1%, R: 38.6%) | **44.41%** (P: 61.8%, R: 38.8%) | **43.37%** (P: 61.6%, R: 37.0%) | -0.04% (Parity) |
| **OVERALL (All Classes)** | **66,521** | **48.37%** (P: 54.0%, R: 48.0%) | **48.46%** (P: 53.8%, R: 48.2%) | **47.80%** (P: 54.7%, R: 47.3%) | **+0.09% (Zero Drop)** |

*ONNX Runtime CUDA Provider Status*: **NOT DONE (CUDA 13/12 MISMATCH, AIR-GAPPED)**. CPUExecutionProvider reported as CPU baseline.

---

## 3. Vessel Specialist vs Generalist on Maritime Partition

- **Dataset Scope**: **5 scenes / 21 tiles / 280 vessels** (0 training scene overlap verified).
- **Primary Generalist (YOLO11m)**: 12.07% mAP@50 (Precision: 23.40%, Recall: 20.36%)
- **Vessel Specialist (YOLO11n)**: **16.24% mAP@50** (Precision: 35.15%, Recall: 23.57%) — **+34.5% relative gain**.

---

## 4. Theoretical Jetson Edge Projections (Wide Range, UNVALIDATED)

- **Accumulate Mode**: **FP16 Tensor Core arithmetic with FP32 accumulation**.
- **Assumed TensorRT Speedup Factor**: **1.3× to 2.0×** over raw PyTorch execution.
- **TFLOPs Specifications & Sources**:
  - Host Laptop RTX 4060: 58.2 Dense FP16 TFLOPs (NVIDIA Ada Lovelace Whitepaper & AD107 device attributes), 256.0 GB/s.
  - Jetson AGX Orin 64GB: 42.6 Dense FP16 TFLOPs (NVIDIA Jetson AGX Orin Series Data Sheet Table 1), 204.8 GB/s.
  - Jetson Orin Nano 8GB: 10.24 Dense FP16 TFLOPs (NVIDIA Jetson Orin Nano Series Data Sheet Table 1), 68.0 GB/s.

| Target Platform | Status / Provenance | Wide Latency Range (ms) | Wide Throughput Range (FPS) | Measured Power | TensorRT Acceleration Bound Formula |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **NVIDIA Jetson AGX Orin (64GB)** | `UNVALIDATED` | **[10.8 ms – 23.8 ms]** | **[42.0 – 92.6 FPS]** | *not estimated* (target envelope &le;60W) | Lower bound: `10.8 ms` (21.7ms / 2.0x TRT)<br>Upper bound: `23.8 ms` (17.39ms * 58.2 / 42.6 unaccel) |
| **NVIDIA Jetson Orin Nano (8GB)** | `UNVALIDATED` | **[32.8 ms – 98.8 ms]** | **[10.1 – 30.5 FPS]** | *not estimated* (target envelope &le;15W) | Lower bound: `32.8 ms` (65.5ms / 2.0x TRT)<br>Upper bound: `98.8 ms` (17.39ms * 58.2 / 10.24 unaccel) |

---
