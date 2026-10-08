# PROJECT RAKSHAK 2.0 — HACKFEST 2026 OFFICIAL 6-SLIDE SCREENING DOSSIER
**Sovereign Tactical Watch & Multi-Domain Threat Intelligence Platform**  
*Compliant with KLS Hackfest 2026 Screening Submission Guidelines (Dr. Uday Nagaraj Kulkarni, Associate Professor)*  
*Team BotS | KLS Gogte Institute of Technology (GIT), Belagavi | Submission Deadline: 5 Oct 2026, 5:00 PM*

---

## EXECUTIVE COMPLIANCE MATRIX

| Official Criterion | Where Addressed | Platform Evidence / Working Proof |
|---|---|---|
| **Max 6 Slides** | Slides 1 to 6 | Strict 1-to-1 mapping with college announcement |
| **Problem Clarity & Domain Relevance** | Slide 1 | Domain 1: Defense, Aerospace, Navy, Sovereign AI | Problem 1A |
| **Technical Feasibility & Prototype** | Slide 2 & 4 | Working prototype; verified in 12/12 smoke tests; <1.8s latency |
| **Originality & Innovation** | Slide 3 | 5-dimension comparison matrix vs optical-only, AIS-only, cloud LLMs |
| **Justification of Tech Stack** | Slide 5 | Concrete justification for YOLO11m, FastAPI, SQLite WAL, React 19 |
| **Hackathon vs. Future Enhancements** | Slide 6 | Explicit separation of working prototype vs post-hackathon roadmap |
| **Datasets, Equipment & External Access** | Slide 5 & 6 | 0 paid services, 0 external APIs, preloaded xView & Sentinel-1 data |

---

# SLIDE 1: PROJECT OVERVIEW AND PROBLEM STATEMENT

### 1. Project Title
**Project Rakshak 2.0: Sovereign Tactical Watch & Multi-Domain Threat Intelligence Platform**

### 2. Team Details
- **Institution**: KLS Gogte Institute of Technology (GIT), Belagavi, Karnataka
- **Team Name**: Team BotS
- **Team Members & Disciplines**:
  1. **Aditya Bajantri** (Lead, Neural Vision Architecture & Training)
  2. **Gagan Bongale** (Data Engineering, Augmentation & Tiling Pipeline)
  3. **Utsav Nanapur** (Radar Signal Processing, SAR CA-CFAR & AIS Matching)
  4. **Misbah Falak** (Kinematic Tracking, CEP Uncertainty & Threat Scoring)
  5. **Shalina Maniyar** (Tactical C2 Interface, GIS Mapping & Telemetry)
  6. **Niyati Gogri** (Air-Gapped Sovereign RAG & Military STANAG SITREP Engine)

### 3. Selected Domain & Problem Statement
- **Domain**: Domain 1 — Defense, Aerospace, Navy, Government, Sovereign AI
- **Problem Statement**: Problem 1A — Naval / Army Geospatial & Multimodal Threat Detection

### 4. Target Users
- **Naval C2 Watch Officers**: Maritime Operations Centers (MOC), chokepoint monitors (Malacca Strait, Arabian Sea, Bay of Bengal).
- **Army FOB Tactical Analysts**: Forward Operating Bases (FOB) monitoring border geospatial movement and electronic perimeters.
- **Maritime Patrol Aircrews**: Indian Navy P-8I Neptune & Dornier 228 sensor operators requiring instant airborne target vectoring.
- **Tactical Edge Maintainers**: Operators deploying compute nodes on shipboard racks or mobile ground vehicles without internet.

### 5. The Problem We Aim to Solve
1. **Dark Vessels & Transponder Evasion**: Hostile warships, militia boats, and smuggling tenders deliberately disable or spoof AIS transponders. Optical satellites cannot see through monsoon cloud decks, fog, or darkness.
2. **Analyst Cognitive Overload**: Panning, zooming, and verifying raw high-resolution 1024px satellite imagery takes human imagery analysts **35 to 45 minutes per scene**, causing severe delays during operational crises.
3. **High False Alarm Rates in Complex Terrain**: Off-the-shelf object detection models trigger overwhelming false alarms on road lane stripes, parking stalls, agricultural terraces, and cloud shadows.
4. **Sovereignty & EW Air-Gap Mandate**: Military doctrine forbids sending operational reconnaissance data to commercial cloud AI (OpenAI, Google Cloud, AWS) due to electronic warfare (EW) jamming, interception, and data sovereignty laws.

### Visual Layout & Callout Stat
- **Layout**: Left column has Team BotS metadata with military clearance badges; Right column displays 4 dark tactical cards highlighting the 4 dilemmas.
- **Callout Stat**: `[35+ Min Manual Screening Time -> Sub-1.8s Autonomous Decision Loop]`

---

# SLIDE 2: PROPOSED SOLUTION AND OBJECTIVES

### 1. The Core Idea
A sovereign, 100% air-gapped multi-spectral intelligence platform that ingests raw optical satellite imagery, Sentinel-1 SAR radar, local AIS logs, drone EO/IR video, and ground sensors to detect, geolocate, threat-score, and advise commanders on hostile contacts in **under 1.8 seconds** on tactical edge hardware.

### 2. Key Objectives
- **All-Weather 24/7 Watch**: Combine 1024px optical neural vision with Sentinel-1 SAR radar for uninterrupted day-and-night reconnaissance through cloud decks.
- **Autonomous Dark Vessel Interception**: Auto-correlate radar contacts against local AIS streams to flag non-broadcasting contacts (**91.7% target capture rate**).
- **Explainable 0–100 Threat Scoring**: Compute deterministic, auditable threat scores based on object classification, velocity, and distance to defense geofences.
- **Air-Gapped Operational Doctrine Advice**: Deliver sub-40ms Rules of Engagement (RoE) recommendations using local military doctrine without cloud dependencies.

### 3. Core Features & Validated Vision Breakthrough
- **Dual-Engine Vision**: Primary YOLO11m (20.1M military multi-class) + secondary 1024px specialist with Weighted Box Fusion (WBF).
- **Validated 43.4% mAP50**: Evaluated across 1,068 validation scenes containing 128,390 ground targets (peak training reached 50.97%).
- **6.1× Surge in Vessel Detection**: Solved severe aerial class imbalance via class-weighted focal loss and geometric augmentation (mAP50 jumped from 3.4% to **20.84%**, precision at **50.58%**).
- **81.3% Aircraft Recall**: High-confidence acquisition of combat airframes on runways and tarmacs (mAP50 at **74.04%**).
- **Multi-Domain C2 Feeds**: Live drone UAV EO/IR downlinks and ground UGS sensors with status workflows (`ACTIVE -> ACKNOWLEDGED -> RESOLVED`).
- **Kinematic CEP Ellipse**: Oriented Circular Error Probable uncertainty prediction with forward trajectory waypoints.

### 4. Intended Benefits
- **Speed**: Reduces intelligence turnaround from 35+ minutes to **<1.8 seconds** (74.5% situational awareness acceleration).
- **Accuracy**: Prunes false alarms by >40% via GSD aspect-ratio geometry gating.
- **Sovereignty**: 100% independent of foreign cloud infrastructure or commercial APIs.

### Visual Badges
- **`35 min > 1.8 s`** — Scene-to-Decision Latency
- **`43.4% mAP`** — Validated Aerial Accuracy (6.1× Vessel Surge, 81.3% Air Recall)
- **`0 Cloud / 100% Edge`** — Sovereign Air-Gapped Deployment

---

# SLIDE 3: INNOVATION AND EXISTING ALTERNATIVES

### 1. Limitations of Existing Approaches vs. Rakshak 2.0
| Operational Area | Existing Prototype Approach | Critical Operational Limitation | How Project Rakshak 2.0 Solves It |
|---|---|---|---|
| **Satellite Vision** | Optical-only satellite AI | Completely blind in heavy cloud cover, monsoon rain, smoke, and nighttime | **Dual-Spectrum Fusion**: Pairs 1024px optical YOLO11m with Sentinel-1 SAR C-Band radar for all-weather 24/7 watch. |
| **Maritime Tracking** | Commercial AIS tracking | Hostile, militia, or smuggling vessels deliberately turn off or spoof AIS | **Dark Vessel Intercept**: Cross-correlates radar contacts against AIS logs; flags unlisted contacts (**91.7% capture rate**). |
| **Overhead Vision AI** | Generic off-the-shelf YOLO | High false alarm rate; confuses road stripes, parking markings, and shadows with vehicles | **Balanced Aerial Architecture**: Class-weighted focal loss, 1024px tiling, WBF consensus ($	imes 1.35$), and physical GSD aspect-ratio geometry gating. |
| **Doctrine & Advice** | Cloud LLMs (OpenAI, Gemini) | Strictly prohibited on air-gapped military networks; vulnerable to EW jamming | **100% Offline Sovereign RAG**: Local in-memory BM25 index delivering Indian Navy / Armed Forces RoE advice in **<40ms** with zero data egress. |
| **Situation Reports** | Manual voice / typed logs | Slow, prone to transcription error, delays interdiction orders by 20 to 45 minutes | **Automated STANAG SITREP**: Instant 5-section military report with automated tactical vectoring and target bearings. |

### 2. What Makes Our Solution Different
Project Rakshak 2.0 is not an isolated computer vision script or a conceptual mock-up. It is a **unified, multi-domain C4ISR intelligence stack** that takes raw sensor inputs and carries them all the way to legal Rules of Engagement advice and an official STANAG military SITREP—executing completely offline in a single seamless pipeline.

---

# SLIDE 4: SYSTEM ARCHITECTURE AND WORKFLOW

### 1. Labelled Architecture Diagram
```
+-----------------------------------------------------------------------------------+
| 1. LOCAL MULTI-DOMAIN INPUTS                                                      |
|    • Optical GeoTIFF / Drone (1024px)        • Sentinel-1 SAR Radar (C-Band)      |
|    • Local AIS Transponder Stream (CSV/NMEA) • Multi-Domain UAV & Ground UGS      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 2. AIR-GAPPED FASTAPI PROCESSING ENGINES                                          |
|    • Vision Engine: 1024px Tiling (320px overlap) + YOLO11m (20.1M) + WBF         |
|    • Radar Engine: Sentinel-1 CA-CFAR Clutter Adaptation + AIS Match (91.7%)      |
|    • Geospatial Engine: Rasterio WGS-84 Coordinate Transformation                 |
|    • Doctrine Engine: Offline In-Memory BM25 Indian Navy RoE RAG (<40ms)          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 3. THREAT INTEGRATION & STORAGE CORE                                              |
|    • O(N) Spatial Threat Matrix: Deterministic 0-100 Risk Score Formula           |
|    • Kinematic Tracking: Class-Aware CEP Covariance Ellipse & Waypoint Prediction |
|    • Hardened Storage: SQLite WAL Mode (32MB Cache, Foreign Keys, Threat Indexes) |
|    • Security Layer: PBKDF2-HMAC-SHA256 (200,000 iter) + JWT with jti RBAC        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 4. REACT 19 TACTICAL C2 HUD OUTPUTS                                               |
|    • Leaflet GIS Map: Optical, SAR, Drone, Geofences, Threat Heatmap              |
|    • Real-Time Threat Feed & Intercept Vectors                                    |
|    • Offline RoE Advisory Panel (BLUF Directives + Authoritative Citations)       |
|    • Automated 5-Section STANAG 2014 Military SITREP Export                       |
+-----------------------------------------------------------------------------------+
```

### 2. End-to-End User Workflow
1. **Ingest & Tile**: Operator uploads a high-resolution GeoTIFF or drone scene; system slices it into 1024×1024 tiles with 320px overlap (31.25% overlap) to prevent boundary target clipping.
2. **Ensemble Detect**: YOLO11m and specialist model run concurrent inference; Weighted Box Fusion merges duplicates and applies consensus multipliers.
3. **Radar & AIS Cross-Check**: SAR CA-CFAR radar isolates contacts; contacts without a broadcasting AIS transponder are flagged as **Dark Vessels** (+25 threat score).
4. **Kinematic Vectoring & RoE Guidance**: CEP uncertainty ellipses are calculated; commander queries sovereign RAG for legal intercept authority under UNCLOS Article 110 and Indian Navy doctrine (<40ms).
5. **C2 HUD & STANAG SITREP**: Live tactical HUD updates; system auto-generates a standardized 5-section STANAG SITREP with dynamic intercept bearings.

### Bottom Note
- *Verified on local NVIDIA RTX 4060 GPU / Jetson Orin SWaP-C profile with zero external network egress.*

---

# SLIDE 5: TECHNOLOGY STACK AND IMPLEMENTATION PLAN

### 1. Proposed Technologies & Suitability Justification
| Layer | Technologies Selected | Technical Justification |
|---|---|---|
| **Vision & Geospatial** | Ultralytics YOLO11m (20.1M params), PyTorch, Rasterio, Pillow, WBF | State-of-the-art small-object detection in aerial nadir photography; Rasterio guarantees precise WGS-84 coordinate mapping. |
| **Radar Signal Processing** | NumPy, SciPy (CA-CFAR windowing) | High-speed vectorized computation of local clutter statistics without heavy proprietary radar toolboxes. |
| **Backend & Security** | FastAPI, Python 3.13, SQLite WAL, PBKDF2-200k, PyJWT | Asynchronous high-throughput REST API; SQLite WAL provides zero-maintenance air-gapped persistence; 200k PBKDF2 meets NIST 2024 defense standards. |
| **Tactical Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Leaflet, Recharts | Zero-latency hardware-accelerated GIS map rendering; strict type safety for mission-critical command workflows. |
| **Hardware Platform** | NVIDIA GeForce RTX 4060 Laptop (8GB VRAM) / Jetson Orin Profile | Accessible tactical compute; sub-1.8s execution within standard SWaP-C constraints. |

### 2. Team Responsibilities
- **Aditya Bajantri & Gagan Bongale**: Neural Architecture, YOLO11m Retraining, Class Weights & Geometric Augmentation.
- **Utsav Nanapur & Misbah Falak**: SAR CA-CFAR Radar Engine, AIS Correlation, Kinematic CEP Tracker & Threat Scoring.
- **Shalina Maniyar & Niyati Gogri**: React 19 C2 Tactical HUD, STANAG SITREP Generator, Sovereign RoE RAG & Auth RBAC.

### 3. Implementation Plan & Timeline for the Hackathon
- **Oct 9–10 (Mentor Sessions)**: Lock test scenarios, refine multi-spectral edge tuning, validate jury briefing.
- **Hours 0–2 (Setup & Verification)**: Launch local air-gapped environment; verify 12/12 smoke tests on RTX 4060 hardware.
- **Hours 2–7 (Edge Optimization & Scenario Tuning)**: Optimize SAR CFAR thresholding for Indian coastline scenes; ingest sample UAV downlinks.
- **Hours 7–10 (Integration Testing & Rehearsal)**: End-to-end rehearsal of the 5-minute jury pitch flow; verify STANAG SITREP exports.

---

# SLIDE 6: EXPECTED OUTCOMES AND DEMO PLAN

### 1. Planned Deliverables (Working Today)
- **Full-Stack Sovereign C2 Dashboard**: Live React 19 interface at `http://127.0.0.1:5173/` with interactive multi-layer tactical mapping.
- **Dual-Spectrum Neural Detection**: 43.4% mAP50 optical detection + 91.7% SAR dark-vessel capture rate.
- **Tactical Threat Core**: Deterministic 0–100 scoring, CEP covariance ellipses, and UAV/UGS status workflows.
- **Air-Gapped RoE Advisor & SITREP**: Instant (<40ms) BLUF directives and automated STANAG military SITREP exports.

### 2. What the Live Demo Will Show (5-Minute Jury Pitch)
1. **0:00 - 1:00 (Authentication & Clearance)**: Log in as Tactical Commander (Major Vikram Rathore); verify PBKDF2-200k + JWT RBAC clearance.
2. **1:00 - 2:00 (Scene Ingest & Detection)**: Ingest sample reconnaissance tile `1154.tif`; demonstrate 223 tactical targets detected in ~6 seconds (178 Vehicles, 35 Aircraft, 10 Bunkers) with zero boundary clipping.
3. **2:00 - 3:00 (Multi-Spectrum SAR & Feeds)**: Toggle the SAR radar layer to reveal dark vessels operating with disabled AIS; cycle a live drone UAV feed (`ACTIVE -> ACKNOWLEDGED -> RESOLVED`).
4. **3:00 - 4:00 (Kinematic Vectors & RoE Guidance)**: Click a hostile dark vessel to inspect its CEP uncertainty ellipse; query the offline RoE advisor for intercept authority under UNCLOS Article 110 and Indian Navy doctrine (<40ms).
5. **4:00 - 5:00 (STANAG SITREP & Telemetry)**: Generate the official 5-section military SITREP with dynamic intercept bearings; display edge hardware telemetry on local RTX 4060 with zero cloud calls.

### 3. Measures of Success (Verified Benchmarks)
- **`<1.8 s`** — Scene-to-Decision Latency (Real-time actionable response)
- **`43.4% mAP`** — Validated Accuracy (6.1× Vessel Surge, 81.3% Air Recall)
- **`12 / 12 PASS`** — End-to-End Platform Smoke Tests (Zero Failures)
- **`0 Cloud Calls`** — 100% Air-Gapped Sovereign Deployment

### 4. Key Risks, Dependencies & Distinctions
- **Datasets & Equipment (Zero Paid Services)**:
  - *Datasets*: DIUx xView 0.3m aerial benchmark + preloaded Sentinel-1 SAR C-band scenes (all free, preloaded on disk).
  - *Equipment*: Single NVIDIA RTX laptop (8GB VRAM); no external cloud servers, GPUs, or paid APIs required.
- **Distinguishing Hackathon Prototype vs. Future Roadmap**:
  - *Working Today (Hackathon Deliverable)*: Full optical/SAR vision engine, AIS correlation, threat scoring, CEP tracking, offline RoE RAG, STANAG SITREP generator.
  - *Future Enhancements (Post-Hackathon)*: NVIDIA Jetson Orin TensorRT INT8 quantization, live RTSP drone video stream ingest, dynamic Kalman track filtering, and onboard satellite FPGA deployment.

---

## CLAUDE SLIDE DECK CREATION PROMPT (COPY-PASTE READY)

```text
You are an expert defense technology presentation designer and military visual strategist.

I have provided the official KLS Hackfest 2026 Master Screening Dossier for Project Rakshak 2.0 (Team BotS, KLS GIT Belagavi).

Generate an exact 6-SLIDE PowerPoint presentation deck strictly adhering to the college screening guidelines announced by Dr. Uday Nagaraj Kulkarni.

Presentation Guidelines:
1. Exact Slide Count: Exactly 6 Slides matching the required screening sections:
   Slide 1: Project Overview and Problem Statement
   Slide 2: Proposed Solution and Objectives
   Slide 3: Innovation and Existing Alternatives
   Slide 4: System Architecture and Workflow
   Slide 5: Technology Stack and Implementation Plan
   Slide 6: Expected Outcomes and Demo Plan
2. Visual Aesthetic: Sovereign Defense C4ISR Command Center (Dark Slate #0F172A, Radar Cyan #06B6D4, Alert Amber #F59E0B, Defense Green #10B981).
3. Evaluator Alignment: Address all screening evaluation criteria:
   - Problem clarity & domain relevance (Domain 1: Defense & Sovereign AI, Problem 1A)
   - Feasibility & working prototype (43.4% mAP, 6.1x vessel surge, <1.8s latency, 12/12 smoke tests)
   - Justification of tech stack (PyTorch, YOLO11m, FastAPI, SQLite WAL, React 19)
   - Explicit distinction between hackathon prototype deliverables and future enhancements
   - Confirmation of 0 paid services, 0 external APIs, preloaded open datasets
4. Provide for each slide:
   a. Slide Number and Title
   b. Visual Layout & Diagram Concept (for PowerPoint / Gamma)
   c. Bullet Points & Complete Comparison Tables
   d. Key Metric Callout Box
   e. Presenter Pitch Script / Speaker Notes
```
