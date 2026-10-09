# 🛡️ Project Rakshak 2.0: Sovereign Dual-Domain C4ISR Platform

[![Defense Grade](https://img.shields.io/badge/Classification-TOP%20SECRET%20%2F%2F%20RESTRICTED-red.svg)](#)
[![Air-Gapped Compliance](https://img.shields.io/badge/EMCON-ALPHA%20(100%25%20Air--Gapped)-0f766e.svg)](#)
[![Domain](https://img.shields.io/badge/KLS%20Hackfest%202026-Problem%201A%20(Naval%2FArmy%20Threat%20Detection)-blue.svg)](#)
[![Model](https://img.shields.io/badge/AI%20Model-YOLO11m%20(43.4%25%20mAP50)-green.svg)](#)
[![Tests](https://img.shields.io/badge/Smoke%20Tests-12%2F12%20Passing-brightgreen.svg)](#)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20%2F%20Air--Gapped-blueviolet.svg)](#)

> **Sovereign Multi-Modal Geospatial Threat Intelligence & Common Operating Picture (COP) Engine**  
> *Engineered for Hackfest 2026 — Problem Statement 1A: Naval / Army Geospatial & Multimodal Threat Detection*  
> **Team BotS | KLS Gogte Institute of Technology (GIT) / KLE Technological University**

---

## 📌 Executive Summary

Modern military surveillance across India's maritime Exclusive Economic Zones (EEZ) and northern land borders suffers from three critical vulnerabilities:
1. **Dark Vessels & AIS Evasion:** Hostile warships, smuggler craft, and spy trawlers deliberately disable AIS transponders. Commercial optical satellites are blinded by night, rain, and heavy monsoon cloud cover.
2. **Analyst Cognitive Overload:** Human image analysts take **35 to 45 minutes** to manually screen a single high-resolution satellite scene, creating unacceptable operational delays during crises.
3. **Data Sovereignty & Electronic Warfare (EW):** Military doctrine forbids transmitting tactical reconnaissance feeds to commercial cloud APIs (AWS, OpenAI, Google Cloud) due to electronic jamming, interception, and strict sovereignty laws.

**Project Rakshak 2.0** solves this with an **air-gapped, edge-deployable C4ISR platform** that fuses **Spaceborne SAR Radar (Sentinel-1)**, **High-Resolution Optical Satellite Imagery (xView 0.3m)**, **Tactical Drone UAV Video (Garuda-04)**, **Unattended Ground Sensors (UGS)**, and **Marine AIS Transponders** into a unified **Common Operating Picture (COP)** with sub-1.8s decision latency.

---

## 🚀 Key Innovations & Performance Benchmarks

| Capability Metric | Legacy Approach / Baseline | Project Rakshak 2.0 | Operational Impact |
| :--- | :--- | :--- | :--- |
| **Scene Ingestion & Threat Resolution** | 35–45 minutes (Manual human triage) | **< 1.8 seconds** (Autonomous pipeline) | **99% latency reduction**; real-time vectoring |
| **All-Weather Dark Vessel Capture** | 0% at night/clouds (Optical-only) | **91.7% capture rate** (SAR-AIS correlation) | Fuses Sentinel-1 C-Band radar with AIS |
| **Vessel Detection Precision (mAP50)** | 3.4% (Generic COCO / baseline detector) | **20.84%** (Retrained on 5,838 tiles) | **6.1× surge** in small maritime vessel recall |
| **Multi-Class Detection Accuracy** | 27.7% mAP50 (Initial 1024px YOLO11n) | **43.4% mAP50** (YOLO11m military checkpoint) | 81.3% combat aircraft recall; 4-class fusion |
| **Air-Gap Sovereign Compliance** | Cloud API dependent (Vulnerable to EW) | **100% Air-Gapped (0 net bytes egress)** | SQLite WAL mode + local PyTorch runtime |
| **Edge Compute Footprint** | Cloud GPU cluster required | **28W Budget** (NVIDIA Jetson AGX Orin) | 19.4 ms latency (51.5 FPS) via TensorRT FP16 |
| **Military SITREP Generation** | 20+ minutes manual draft | **Instant 1-Click Dispatch** | Standardized NATO/Indian STANAG 2014 format |

---

## 🏛️ System Architecture

Project Rakshak 2.0 follows a strict 4-tier air-gapped pipeline:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TIER 1: MULTI-MODAL SENSOR INGESTION LAYER                      │
│   Sentinel-1 SAR Radar   │   xView GeoTIFFs (0.3m)   │   Drone UAV EO/IR   │   AIS
                                                                              Transponders│
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

---

## ⚓ Dual-Domain Implementation: Naval vs. Army

The platform provides dedicated domain consoles tailored to specific military branches while fusing them into the Joint COP:

| Operational Parameter | ⚓ Naval Domain Console | 🪖 Army Domain Console |
| :--- | :--- | :--- |
| **Theater Scope** | Macro-scale ocean / EEZ / maritime chokepoints (thousands of km²) | Micro-scale tactical land borders, Line of Control (LoC), FOB perimeters |
| **Sensors Handled** | Sentinel-1 SAR C-Band Radar + xView Spaceborne GeoTIFF + AIS | Tactical Drone UAV EO/IR video + UGS Seismic Geophones (18 Hz) + SIGINT |
| **Primary Threat** | **Dark Vessels**: Hostile ships disabling AIS near naval security perimeters | **Tactical Convoys & Infiltration**: Blackout vehicle columns, dismounted patrols |
| **Core Algorithm** | CA-CFAR radar extraction + Haversine spatial correlation (<5 km) | Convoy clustering heuristic ($O(N)$ spatial grid) + Seismic tripwire triage |
| **Response Workflow** | 1-Click Analyst Adjudication (`Matched`, `Dark Vessel +50`, `Unknown`) | Alarm State Machine (`ACTIVE` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`) |
| **Governing Doctrine** | UNCLOS Article 110 (Right of Visit & Boarding), Indian Navy INBR 8 | Border Rules of Engagement (RoE), FOB Quick Reaction Team (QRT) dispatch |

---

## 🔬 Dataset Heritage & Neural Training Lineage

The detection engine represents a multi-stage training evolution:

1. **Phase 1: Exploratory Benchmark (Harborwatch 1A MVP)**
   - Initial xView dataset audit: 601,937 labels across 847 image IDs.
   - Retained 32 high-priority India-extent validation scenes (68.1–97.4°E, 6.7–35.5°N), freeing 7.10 GiB of non-relevant imagery.
   - Initial baseline YOLO11n model scored 0.277 mAP50 on vessel classes with missed contacts in dense harbors.
2. **Phase 2: Sentinel-2 Pipe V4 Cross-Validation**
   - Ingested Sentinel-2 multispectral rasters (B02, B03, B04, B08, B11, B12) over Mumbai coastal footprints (`2026-04-28` and `2026-05-31`).
   - Benchmarked against Pipe V4 published detections and AIS correlation fields.
3. **Phase 3: Production Retraining (YOLO11m Military Multi-Class)**
   - Generated **5,838 military target tiles** (1024×1024 px with 20% overlap).
   - Applied Weighted Box Fusion (WBF) and rare-class oversampling.
   - **Trained YOLO11m across 4 consolidated defense classes:**
     - `Vessel` (Cargo, tanker, fishing, military warships)
     - `Aircraft` (Fixed-wing transport, fighter aircraft)
     - `Vehicle` (Trucks, armored combat vehicles, utility transports)
     - `Infrastructure` (Bunkers, storage facilities, hangars, towers)
   - **Achieved 43.4% mAP50 overall**, with vessel detection surging **6.1×** from 3.4% to 20.84%, and 81.3% recall on aircraft.

---

## 💻 Tech Stack & Justifications

* **Neural Vision:** `YOLO11m` + `PyTorch 2.6` — Optimal balance between parameter capacity (20.1M params) and low-latency inference on small targets; TensorRT INT8 exportable.
* **Backend API:** `FastAPI` + `Python 3.11` — Asynchronous non-blocking architecture delivering sub-millisecond REST and WebSocket performance.
* **Database:** `SQLite 3` with **Write-Ahead Logging (WAL)** — Zero-configuration, zero-daemon local persistence with ACID compliance; immune to crash corruption under air-gapped field conditions.
* **Tactical UI:** `React 19` + `TypeScript` + `Vite` + `Leaflet GIS` — Hardware-accelerated 60 FPS mapping with custom SVG reticles, zero external tile dependencies.
* **Radar & Signal Processing:** `NumPy` + `SciPy` — Pure offline mathematical implementation of Cell-Averaging Constant False Alarm Rate (CA-CFAR) and Haversine great-circle distance formulas.
* **Security & Auth:** `PBKDF2-HMAC-SHA256` (200,000 iterations) + `JWT RBAC` — Sovereign terminal security gate enforcing Commander and Analyst access levels.

---

## 🛠️ Installation & Quick Start

### Prerequisites
* Windows 10/11, Ubuntu 22.04+, or macOS
* Python 3.10, 3.11, or 3.12
* Node.js 18+ (optional; pre-built production frontend is already bundled in `frontend/dist`)

---

### Option 1: 1-Click Launch (Windows — Recommended)
Double-click the pre-configured batch scripts in the project root:
* **To start the complete system:** Double-click [`run_rakshak.bat`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/run_rakshak.bat) (starts FastAPI + Vite, launches browser).
* **To run single-command production:** Double-click [`start_production.bat`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/start_production.bat) (serves compiled UI directly from FastAPI on port 8000).
* **To shut down all services:** Double-click [`stop_rakshak.bat`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/stop_rakshak.bat).

---

### Option 2: VS Code Build Task
1. Open the project folder in VS Code.
2. Press **`Ctrl` + `Shift` + `B`**.
3. VS Code will automatically open two dedicated split terminals and launch both the backend and frontend simultaneously.

---

### Option 3: Manual Terminal Setup

```bash
# 1. Clone repository
git clone https://github.com/Whritix/Rakshak.git
cd Rakshak

# 2. Set up Python virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Unified Server (Backend + Pre-compiled Frontend)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** in any web browser.

---

### Option 4: Docker & Docker Compose

```bash
# Build and run the multi-stage Docker container
docker compose up --build
```
Access the console at **`http://localhost:8000`**.

---

## 📦 Deployment & Containerization
 
### A. Multi-Stage Docker Container (Air-Gapped Ready)
The repository includes an optimized multi-stage [`Dockerfile`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/Dockerfile) and [`docker-compose.yml`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/docker-compose.yml):
```bash
# Build and run the self-contained tactical server
docker compose up --build
```
Access the tactical console at **`http://localhost:8000`**.
 
### B. Standalone Edge Production Server
For air-gapped field workstations without Node.js or external network access, FastAPI directly mounts and serves the optimized compiled React SPA:
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Or simply double-click [`start_production.bat`](file:///c:/Users/awhri/OneDrive/Desktop/DEF/start_production.bat).
 
---

## 🎯 Live Hackathon Demonstration Flow (2-Minute Jury Walkthrough)

1. **Sovereign Access Terminal:**
   - Demonstrate the terminal login gate. Login as `analyst` (`tactical123`) or `commander` (`sovereign2026`).
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

## 🧪 Verification & Automated Testing

The codebase includes an automated defense test suite covering all operational endpoints:

```bash
# Run complete platform smoke test
python smoke_test_platform.py
```

**Test Results:**
* `[TEST 01]` Platform Health & Model Availability — **PASS**
* `[TEST 02]` KPI Accuracy & Validation Metrics — **PASS**
* `[TEST 03]` Jetson Orin Edge Benchmarks — **PASS**
* `[TEST 04]` Restricted Geofencing Zones — **PASS**
* `[TEST 05]` Optical Multi-Class Model Inference — **PASS**
* `[TEST 06]` Sentinel-1 SAR Radar Telemetry — **PASS**
* `[TEST 07]` Dark Vessel Spatial Matching (<5 km) — **PASS**
* `[TEST 08]` Army Tactical Multimodal Ingestion — **PASS**
* `[TEST 09]` Army Sensor Alarm Lifecycle State Machine — **PASS**
* `[TEST 10]` Kinematic Trajectory & CEP Drift Projection — **PASS**
* `[TEST 11]` Automated STANAG 2014 SITREP Generation — **PASS**
* `[TEST 12]` Sovereign Rules of Engagement Doctrine RAG — **PASS**
* **Final Verdict: 12 / 12 (100%) Smoke Tests Passing.**

---

## 👥 Team BotS — Roles & Responsibilities

| Team Member | Engineering Role | Core Module Responsibilities |
| :--- | :--- | :--- |
| **Aditya Bajantri** | **Team Lead & Neural Vision Architect** | YOLO11m architecture, 5,838-tile dataset retraining, WBF box fusion, PyTorch training pipelines |
| **Gagan Bongale** | **Data Engineer & Pipeline Specialist** | Satellite GeoTIFF slicing, 1024px tiling, Sentinel-2 band ingestion, annotation parsing |
| **Utsav Nanapur** | **Radar Signal & AIS Correlation Engineer** | Sentinel-1 SAR CA-CFAR speckle filtering, RCS dB calculations, Haversine spatial correlation |
| **Misbah Falak** | **Kinematics & Spatial Threat Lead** | Circular Error Probable (CEP) drift ellipses, dead-reckoning trajectory models, $O(N)$ Threat Matrix |
| **Shalina Maniyar** | **Tactical C2 Interface & GIS Engineer** | React 19 Leaflet GIS mapping, 60 FPS offline tile rendering, HUD design, C2 telemetry |
| **Niyati Gogri** | **Military SITREP & Doctrine RAG Specialist** | Automated NATO STANAG 2014 situation reporting engine, offline UNCLOS / INBR 8 doctrine RAG |

---

## 📄 License & Classification

* **Project Classification:** Educational & Defense Research Prototype — Hackfest 2026.
* **License:** MIT License. Free for academic, competition, and research use.
