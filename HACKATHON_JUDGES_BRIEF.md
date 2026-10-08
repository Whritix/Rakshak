# PROJECT RAKSHAK 2.0: SOVEREIGN MULTIMODAL GEOSPATIAL THREAT INTELLIGENCE
## Official Technical Briefing, Architecture Justification & Hackathon Defense Guide

---

### EXECUTIVE SUMMARY
* **Project Name**: Project Rakshak 2.0 (रक्षक)
* **Domain**: Domain 1A — Sovereign Multimodal Geospatial Threat Intelligence & Joint C4ISR
* **Target Users**: Maritime Ops Centers (Indian Navy / Coast Guard), Forward Operating Bases (Indian Army), and Field Tactical Analysts.
* **Core Value Proposition**: A 100% sovereign, air-gapped, edge-deployable intelligence platform that fuses high-resolution satellite Earth observation (EO), Synthetic Aperture Radar (SAR), UAV drone full-motion video (FMV), unattended ground sensors (UGS), and SIGINT intercepts into an automated Common Operational Picture (COP). It autonomously scores, geofences, and flags tactical threats in sub-second latency with zero dependence on foreign cloud infrastructure.

---

## 1. THE PROBLEM & OPERATIONAL CHALLENGE

### The Tactical Reality
Modern military analysts face **data saturation with actionable starvation**:
1. **Massive Raster Dimensions vs. Tiny Targets**: A single military satellite pass or high-res commercial optical raster (e.g. Maxar/Planet/Sentinel) can be 20,000 × 20,000 pixels (>500 MB). Targets (vessels, missile launchers, camouflage infrastructure) occupy only 15 × 15 pixels. Standard deep learning detectors downsample the entire image to 640×640, completely erasing critical targets.
2. **Dark Vessels & AIS Spoofing**: Adversary warships, illegal fishing fleets, and covert surveillance vessels deliberately switch off their AIS (Automatic Identification System) transponders or broadcast spoofed MMSI identities in critical chokepoints (e.g., Strait of Malacca, Mumbai ODA).
3. **Bandwidth Constrained / Air-Gapped Forward Edges**: Warships at sea and forward army battalions in Ladakh or the Northeast operate in **Denied, Disrupted, Intermittent, and Limited (DDIL)** environments under strict EMCON (Emission Control). Cloud-dependent systems (OpenAI, AWS, Google Cloud) fail instantly in combat.
4. **Multi-Domain Silos**: Maritime data stays with Naval HQ; drone feeds stay with local Army units; radar stays with coastal radar chains. There is no unified, zero-latency sensor-to-shooter fusion.

### The Rakshak 2.0 Solution
* **Sub-Pixel Tiling Engine**: Slices high-resolution satellite GeoTIFFs into overlapping 1024×1024 windows, preserving raw optical resolution.
* **SAR Radar & Optical Cross-Correlation**: Correlates radar RCS ($\sigma_0$) returns with AIS logs to instantly isolate "Dark Vessels".
* **Automated Threat Assessment**: An $O(N)$ spatial grid engine scores clustering, convoy formations, and restricted zone breaches.
* **Sovereign & Edge-Ready**: Runs on local hardware down to an NVIDIA Jetson Orin Nano (15W power envelope) with local SQLite WAL storage and zero external internet requirements.

---

## 2. FULL TECH STACK & ARCHITECTURAL JUSTIFICATIONS ("THE WHY")

When presenting to judges, **do not just list technologies—explain the strategic defense rationale** behind every engineering decision.

| Layer | Technology Chosen | Alternatives Considered | Strategic Justification ("Why Chosen?") |
| :--- | :--- | :--- | :--- |
| **AI / Object Detection** | **YOLOv11 Nano (Custom Trained)** | Faster R-CNN, Deformable DETR, SAM, YOLOv8x | **Edge Efficiency & Frame Rate**: At just **5.5 MB** per weights file, YOLOv11n delivers **11+ FPS on standard CPU** and **80+ FPS on edge TensorRT/Jetson**. Heavy transformer models (DETR/SAM) require 24GB VRAM enterprise GPUs and introduce multi-second latencies incompatible with real-time drone downlinks. |
| **Geospatial & Rasters** | **Rasterio + GDAL + OpenCV** | PIL only, Pure Python TIFF readers | **Coordinate Integrity**: Reads raw GeoTIFF metadata, extracting affine transformations, bounding boxes, and ground sample distance (GSD). Maps pixel bounding boxes $(x, y, w, h)$ directly into real-world geographic coordinates $(\text{Lat}, \text{Lon})$ in WGS84 ($\text{EPSG}:4326$). |
| **Spatial Threat Index** | **$O(N)$ Spatial Grid Hash Index** | $O(N^2)$ Pairwise Euclidean Distance Matrix | **Scalability under Saturation**: When analyzing a 25MB satellite scene containing 2,778 targets, an $O(N^2)$ pairwise loop requires $>7.7\text{ million}$ calculations (~35 seconds). Our spatial grid cell hash (~500m buckets) drops clustering time to **0.08 seconds (400x speedup)**, keeping the UI instantly responsive. |
| **Database** | **SQLite 3 in WAL Mode** | PostgreSQL, MongoDB, Redis | **Air-Gapped Ruggedness**: Defense edge nodes cannot afford database daemon crashes, port conflicts, or network latency. SQLite is an in-process, zero-configuration engine stored in a single atomic file (`rakshak.db`). In **WAL (Write-Ahead Logging)** mode, reads and writes never block each other, delivering sub-millisecond query performance on tactical laptops. |
| **Backend Framework** | **Python 3.11 + FastAPI + Uvicorn** | Flask, Django, Node.js Express | **High-Throughput Async Streaming**: FastAPI natively handles asynchronous multipart binary streaming for large satellite GeoTIFF uploads. It provides strict schema validation via Pydantic and self-documenting OpenAPI specs. |
| **Frontend Tactical UI** | **React 19 + TypeScript + Vite + Tailwind** | Angular, Next.js, Plain HTML/JS | **Zero-Lag Tactical C2 Dashboard**: Vite provides sub-second hot reloading and instant bundle compilation. TypeScript guarantees runtime type-safety across sensor payloads. The military-grade dark HUD theme minimizes eye strain in dark naval command centers. |
| **Map Engine** | **Leaflet + React-Leaflet** | Mapbox GL, Google Maps JS API | **Sovereign Air-Gap Compliance**: Mapbox and Google Maps require active internet access, API billing keys, and telemetry reporting to foreign servers. Leaflet supports local offline map tiles and in-memory GeoJSON overlays with smooth Leaflet `flyTo` camera transitions. |
| **Edge Hardware Target** | **ONNX Runtime / TensorRT Export** | Cloud REST APIs | **Direct Tactical Portability**: 1-click export converts PyTorch models into optimized ONNX graph weights for zero-overhead execution on **NVIDIA Jetson Orin Nano / Xavier NX** on board tactical UAVs. |

---

## 3. SYSTEM ARCHITECTURE & DATA FLOW

```
                          ┌────────────────────────────────────────────────────────┐
                          │                MULTIMODAL SENSOR INPUTS                │
                          └────────────────────────────────────────────────────────┘
                                 │                   │                   │
                     High-Res Optical GeoTIFF    Tactical UAV      SAR Radar / AIS
                     (Sentinel-2 / xView EO)    Downlink (FMV)      Logs / UGS Feeds
                                 │                   │                   │
                                 ▼                   ▼                   ▼
                          ┌────────────────────────────────────────────────────────┐
                          │               INGESTION & PREPROCESSING                │
                          ├────────────────────────────────────────────────────────┤
                          │ • GDAL / Rasterio Coordinate Mapping (EPSG:4326)       │
                          │ • Overlapping 1024x1024 Window Slicing Engine          │
                          │ • Dynamic Preview & Aspect-Ratio Normalization         │
                          └────────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
                          ┌────────────────────────────────────────────────────────┐
                          │               DEEP LEARNING INFERENCE                  │
                          ├────────────────────────────────────────────────────────┤
                          │ • Multiclass Tactical Model (Vehicles/Aircraft/Infra)  │
                          │ • High-Precision Maritime Vessel Model                 │
                          │ • CFAR SAR Dark Vessel Thresholding Engine             │
                          │ • Global Non-Maximum Suppression (IoU Deduplication)   │
                          └────────────────────────────────────────────────────────┘
                                                     │
                                                     ▼
                          ┌────────────────────────────────────────────────────────┐
                          │            AUTOMATED THREAT ENGINE & C2                │
                          ├────────────────────────────────────────────────────────┤
                          │ • O(N) Spatial Grid Index (Convoy/Cluster Detection)   │
                          │ • Restricted Zone Geofencing (Malacca, Mumbai ODA, FOB)│
                          │ • AIS Transponder Discrepancy & Spoofing Penalties     │
                          │ • Composite Threat Score (0 - 100) -> HIGH/MED/LOW     │
                          └────────────────────────────────────────────────────────┘
                                 │                                   │
                                 ▼                                   ▼
             ┌─────────────────────────────────────┐   ┌───────────────────────────┐
             │       LOCAL SOVEREIGN STORAGE       │   │  EDGE HARDWARE EXPORT     │
             │   SQLite 3 in WAL Mode (Single File)│   │  ONNX / TensorRT / Jetson │
             └─────────────────────────────────────┘   └───────────────────────────┘
                                 │
                                 ▼
             ┌─────────────────────────────────────────────────────────────────────┐
             │               TACTICAL COMMAND & CONTROL (C2) DASHBOARD             │
             ├─────────────────────────────────────────────────────────────────────┤
             │ • Joint Operational Picture: Dual Domain (Naval vs Army Modes)      │
             │ • Smooth Animated Geonavigation (Leaflet flyTo Zone Coordinates)   │
             │ • Multi-Class Visual Filters: Vehicles, Aircraft, Infra, Vessels    │
             │ • Military DTG STANAG Timestamps (e.g. 301108Z SEP 2026)           │
             └─────────────────────────────────────────────────────────────────────┘
```

---

## 4. CORE INNOVATIONS & KEY FEATURES

### 1. High-Resolution Sub-Pixel Window Tiling
* **The Problem**: Directly feeding a 5,000 × 5,000 satellite GeoTIFF into a neural network shrinks boats and trucks into sub-pixel blur.
* **Our Solution**: Rakshak's tiling engine cuts the image into overlapping 1024×1024 tiles with a 20% stride overlap. It runs inference on each tile in parallel, offsets the bounding boxes back to global image coordinates, and applies global Non-Maximum Suppression (NMS) to eliminate duplicate detections across boundaries.

### 2. $O(N)$ Spatial Grid Threat Engine
* **Cluster & Convoy Detection**: Automatically groups military vehicles or naval vessels moving within 500 meters of each other into tactical convoys (+20 threat penalty).
* **Restricted Zone Geofencing**: Computes real-world Haversine distance against strategic restricted defense zones (e.g., *Strait of Malacca / Nicobar Entry Watch*, *INS Kadamba Naval Base*, *Mumbai Offshore Development Area*). Any unauthorized target inside the perimeter triggers an immediate +30 threat penalty.
* **Performance**: Replaced a quadratic $O(N^2)$ distance matrix with an $O(N)$ spatial grid hash, allowing **2,778 simultaneous targets** to be evaluated in just **80 milliseconds**.

### 3. Dark Vessel & AIS Spoofing Isolation
* Correlates Synthetic Aperture Radar (SAR) CFAR radar detections with transponder broadcasts.
* If a strong Radar Cross Section (RCS $\sigma_0$) metallic reflection exists on ocean waters with **no matching AIS signal**, Rakshak flags it as a **Dark Vessel (Threat: HIGH, Score: 85+)**, alerting naval commanders to potential contraband smuggling or adversary submarine tender activity.

### 4. Dual-Domain Joint Operational C2 Console
* **Naval Domain View**: Displays coastal anchorage guards, chokepoint watches, maritime vessel overlays, AIS transponder statuses, and SAR radar contacts.
* **Army Domain View**: Dedicated tactical UAV downlink dropzone, multiclass target classification (*Vehicles, Aircraft, Infrastructure, Vessels*), target class toggles, and Unattended Ground Sensor (UGS) / SIGINT text intercept feeds.

### 5. Military Standard DTG (Date-Time Group)
* Adheres to Indian Armed Forces and STANAG military conventions: `301108Z SEP 2026`
  * `30` = Day of the month
  * `1108` = Time in 24-hour military format (11:08 AM)
  * `Z` = Zulu Time (Universal Coordinated Time / UTC)
  * `SEP 2026` = Month and Year

---

## 5. HACKATHON PRESENTATION & PITCH SCRIPT FOR JUDGES

Use this exact structure when presenting to hackathon evaluators.

### Phase 1: The 60-Second Hook
> *"Respected Judges, during a maritime crisis in the Indian Ocean or a border escalation in high-altitude terrain, military commanders do not lack raw sensor data—they are drowning in it. A single satellite pass contains 400 million pixels, while forward UAVs stream uncompressed video every second.
> 
> Current military consoles either rely on slow manual analyst tagging or depend on cloud connections that are instantly severed in electronic warfare. 
> 
> We built **Project Rakshak 2.0**: a 100% sovereign, air-gapped, multimodal geospatial intelligence console. It runs locally on shipboard servers and tactical edge hardware, automatically fusing satellite GeoTIFFs, UAV downlinks, SAR radar, and ground sensors into an instant Common Operational Picture with sub-second threat scoring."*

---

### Phase 2: The 3-Minute Live Demo Flow

1. **Demonstrate Sovereign Readiness**:
   * Point out the live telemetry banner: `AIR-GAPPED // LOCAL HOST` and the military DTG timestamp (`301108Z SEP 2026`).
   * Show that the system runs completely offline with local SQLite in WAL mode—no foreign API calls.
2. **Demonstrate 1-Click Large Satellite Inference**:
   * Click **"Load Convoy (1217.tif)"**.
   * Show the tiling engine processing a **25 MB satellite GeoTIFF** with **2,778 real detected targets** in just **10 seconds**.
   * Zoom into the raster overlay: show how bounding boxes accurately track micro-scale vehicles and military infrastructure.
3. **Demonstrate Visual Filtering**:
   * Click **`[🟡 Vehicles Only]`** ➔ The clutter vanishes, isolating troop convoys.
   * Click **`[🟣 Infrastructure Only]`** ➔ Displays hardened defense shelters and runways.
   * Toggle **`[🏷️ Labels: OFF]`** to show clean tactical outlines, then back **`[ON]`**.
4. **Demonstrate Interactive Geonavigation**:
   * Under Restricted Zones, click **"Strait of Malacca / Nicobar Entry Watch"**.
   * Watch the map execute a smooth, animated `flyTo` camera glide directly to `6.85° N, 93.80° E`, displaying the glowing pulsing 30 km defense buffer.
5. **Demonstrate Multimodal Army UAV Downlink**:
   * Switch to the **Army Domain** tab.
   * Double-tap or drag-and-drop a tactical drone image into the downlink dropzone.
   * Show immediate inference: targets highlighted, confidence scores generated, and threat score updated in **88 milliseconds**.
6. **Demonstrate Edge Export for Field Deployment**:
   * Click **"Export to Edge (ONNX)"**.
   * Show the toast notification confirming the model was serialized into an ONNX execution graph ready for deployment on an **NVIDIA Jetson Orin Nano** at a forward operating base.

---

### Phase 3: Winning Answers to Anticipated Judge Questions

#### Q1: "Why did you use SQLite instead of a modern database like PostgreSQL or MongoDB?"
> **Answer**: *"In a commercial cloud app, Postgres or MongoDB makes sense. But Project Rakshak is designed for **air-gapped combat environments**—inside a naval frigate's combat operations room or a forward army bunker. Running a separate database server daemon introduces network overhead, memory overhead, port conflicts, and failure modes if the daemon crashes. 
> SQLite is an in-process, zero-configuration engine compiled directly into the application. By enabling **WAL (Write-Ahead Logging)** mode, reads and writes occur concurrently with sub-millisecond latency. Furthermore, the entire mission database is stored in a single ruggedized file (`rakshak.db`), allowing commanders to physically extract the mission state on an encrypted USB drive in seconds."*

#### Q2: "Why YOLOv11 and not a heavier Vision Transformer or Segment Anything (SAM)?"
> **Answer**: *"Vision Transformers and Foundation Models (like SAM or CLIP) have astronomical parameter sizes (300M+ parameters) requiring high-end data center GPUs (A100/H100) consuming 400W of power. 
> In contrast, our custom-trained YOLOv11 Nano model weighs only **5.5 MB**, achieves **11+ FPS on a standard CPU**, and runs at **80+ FPS on a 15W NVIDIA Jetson Orin Nano**. On tactical UAVs and field edge stations where power and compute are strictly budgeted, YOLOv11 delivers the ideal balance of sub-pixel accuracy and real-time inference speed."*

#### Q3: "How does your system handle small targets in massive satellite images?"
> **Answer**: *"Standard computer vision pipelines downsample whole images to 640×640 pixels, which makes a 20-meter patrol boat or truck vanish into a single blurry pixel. 
> Rakshak implements a **Sub-Pixel Window Slicing Engine**: we slide a 1024×1024 window across the full-resolution GeoTIFF with a 20% overlap. Each tile retains 100% of its native Ground Sample Distance (GSD). We then remap the localized tile detections back to global geographic space using affine geo-transformations and perform global Non-Maximum Suppression (NMS) to eliminate edge duplicates."*

#### Q4: "Can this system be deployed on cloud servers like Render or Vercel if needed?"
> **Answer**: *"Yes. We built a production-grade multi-stage Docker container (`Dockerfile`) that packages the Node 20 frontend compiler and the Python 3.11 GDAL/PyTorch backend into a single container. It is 1-click deployable to Render or Hugging Face Spaces (which provides free 16GB RAM for heavy satellite tiling), while the React C2 frontend can be split onto Vercel's global edge network via our pre-configured `vercel.json` rewrite proxy."*

---

## 6. FUTURE SCOPE & STRATEGIC DEFENSE ROADMAP

If deployed into operational service with defense procurement agencies (e.g. iDEX, DRDO, DDP), Project Rakshak 2.0 has a clear three-tier evolution path:

```
┌────────────────────────────────────────────────────────────────────────┐
│ NEAR TERM (6 - 12 Months): Edge & Tactical Acceleration                │
├────────────────────────────────────────────────────────────────────────┤
│ • TensorRT FP16 / INT8 Quantization: 4x throughput boost on Jetson.    │
│ • Offline Vector Tile Server: Packaged MBTiles / PMTiles for complete  │
│   zero-internet offline world map rendering without tile servers.      │
│ • Rotary & Fixed-Wing UAV Video Stream (RTSP / H.264) direct decoding. │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ MEDIUM TERM (12 - 24 Months): Multimodal & Sensor Expansion           │
├────────────────────────────────────────────────────────────────────────┤
│ • On-Orbit Satellite Edge Processing: Deploying quantized YOLO models │
│   directly on ISRO / private earth observation satellites to detect   │
│   threats in space and transmit only target coordinates over Satcom.   │
│ • Advanced ATR (Automatic Target Recognition): Distinguishing specific │
│   warship classes (Destroyer vs Frigate vs Aircraft Carrier vs Trawler)│
│ • Electronic Warfare (EW) & Direction Finding (DF) triangulation logs. │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LONG TERM (24 - 36 Months): Autonomous Multi-Domain C4ISR               │
├────────────────────────────────────────────────────────────────────────┤
│ • Tri-Service Common Operational Picture (Indian Navy, Army, Air Force)│
│ • Autonomous Swarm Re-Tasking: Sensor-to-Shooter closed loop where a  │
│   satellite detection automatically re-routes a nearby patrol UAV to  │
│   verify the dark contact.                                             │
│ • Post-Quantum Cryptography (PQC) encryption for all C2 data links.   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. QUICK SPECIFICATION SHEET FOR JUDGES

| Metric | Project Rakshak 2.0 Value |
| :--- | :--- |
| **Model Size** | **5.5 MB** (`best.pt` YOLOv11n) |
| **Drone Frame Inference Latency** | **88 milliseconds** (~11.3 FPS on standard CPU) |
| **Full 25 MB Satellite GeoTIFF Speed** | **10.2 seconds** for 2,778 high-res targets |
| **Clustering Latency (2,778 targets)** | **0.08 seconds** ($O(N)$ Spatial Grid Index) |
| **Data Footprint (Code + Models)** | **~75 MB** (fully fits in standard Git repository) |
| **Operational Independence** | **100% Air-Gapped Capable** (Zero cloud lock-in) |
| **Database Engine** | **SQLite 3 (WAL mode)** with zero server dependencies |
| **Edge Hardware Compatibility** | **NVIDIA Jetson Orin Nano, Xavier NX, x86/ARM64** |
| **Standard Timestamps** | **STANAG / Indian Armed Forces DTG (Date-Time Group)** |

---
*Document prepared for Hackathon Evaluation & Defense Technology Jury Review.*
