# ⏱️ Mission-Planning Cycle Time Evaluation Summary

**Project Rakshak 2.0 — Sovereign Air-Gapped C4ISR Platform**  
**Problem Statement KPI:** Mission-Planning Cycle Time Reduction  
**Evaluation Date:** 2026-10-10  
**Status:** **Partial: system steps measured, manual baseline assumed, no human user study**  

---

## 1. Executive Summary

In operational military command rooms without automated multi-sensor fusion, the mission-planning decision cycle (OODA loop) requires manual cross-referencing of radar and AIS logs, nautical chart buffer measurements, hardcopy doctrine binder searches (INBR 8 / UNCLOS), manual typing of STANAG 2014 situation reports, and manual waypoint trajectory calculations. This manual workflow consumes **1,320 – 1,680 seconds (22 – 28 minutes)** per incident.

Project Rakshak 2.0 automates the entire sensor-to-directive pipeline via sovereign local REST microservices:
1. **Measured Machine Latency (Scripted REST):** **0.1843 s** across 10 repetitions per scenario (`MEASURED`).
2. **Operator-Paced Realistic Estimate:** **50.19 s** incorporating 50.0s of assumed human inspection and review think-time (`ASSUMED`).
3. **Manual Baseline Time:** **1440.0 s (24.0 min)** (`ASSUMED`).
4. **Mission-Planning Cycle Time Reduction:** **96.51%** (`COMPUTED`).

---

## 2. Comparative Scenario Results

| Scenario | Domain | Rakshak Measured (REST) | Operator-Paced Estimate | Manual Assumed Baseline | Cycle Time Reduction | Provenance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **A: Dark Vessel in Restricted Zone** | Maritime / Naval | **0.2572 ± 0.1351 s** | **50.26 s** | **1680.0 s (28.0 min)** | **97.01%** | `PARTIAL` |
| **B: Convoy Approaching Border Post** | Land / Army Ground | **0.1397 ± 0.0173 s** | **50.14 s** | **1320.0 s (22.0 min)** | **96.20%** | `PARTIAL` |
| **C: UGS Alarm + Drone Confirmation** | Cross-Domain Fusion | **0.1560 ± 0.0217 s** | **50.16 s** | **1320.0 s (22.0 min)** | **96.20%** | `PARTIAL` |
| **OVERALL AVERAGE** | **Joint Multi-Domain** | **0.1843 s** | **50.19 s** | **1440.0 s (24.0 min)** | **96.51%** | `PARTIAL` |

*Note: Scripted REST calls execute in milliseconds because they bypass human perceptual latency. The Operator-Paced model adds 50.0 seconds of realistic human inspection time (10s contact review, 8s geofence check, 15s RoE reading, 12s SITREP review, 5s dispatch).*

---

## 3. Per-Step Breakdown (Measured Machine Latency)

### Scenario A: Dark Vessel Approaching Restricted Zone (Mumbai ODA)
- **Step 1: Contact Ingestion & Dark Filtering:** 51.44 ± 25.80 ms (`MEASURED`)
- **Step 2: Restricted Buffer Verification:** 13.11 ± 7.84 ms (`MEASURED`)
- **Step 3: Sovereign RoE Doctrine Query:** 92.25 ± 52.29 ms (`MEASURED`)
- **Step 4: Automated STANAG 2014 SITREP:** 16.74 ± 9.88 ms (`MEASURED`)
- **Step 5: Mission Intercept Waypoint Dispatch:** 83.63 ± 52.96 ms (`MEASURED`)

### Scenario B: Convoy Approaching Border Post (Sector Alpha)
- **Step 1: UAV Drone Contact Ingestion:** 19.45 ± 10.00 ms (`MEASURED`)
- **Step 2: Fused Kinematics Analysis:** 17.35 ± 8.81 ms (`MEASURED`)
- **Step 3: Sovereign Ground RoE Retrieval:** 39.09 ± 6.86 ms (`MEASURED`)
- **Step 4: Tactical SITREP Compilation:** 22.96 ± 5.99 ms (`MEASURED`)
- **Step 5: QRF Tasking & Intercept Dispatch:** 40.83 ± 8.45 ms (`MEASURED`)

### Scenario C: UGS Seismic Alarm plus Drone Confirmation
- **Step 1: UGS Geophone Alarm Detection:** 25.20 ± 9.78 ms (`MEASURED`)
- **Step 2: Sensor C2 Acknowledgment & Cross-Cue:** 19.99 ± 6.54 ms (`MEASURED`)
- **Step 3: Sensor Fusion RoE Retrieval:** 47.47 ± 3.68 ms (`MEASURED`)
- **Step 4: Joint Tactical SITREP Compilation:** 21.29 ± 8.28 ms (`MEASURED`)
- **Step 5: Joint Intercept Tasking Dispatch:** 42.05 ± 12.27 ms (`MEASURED`)
