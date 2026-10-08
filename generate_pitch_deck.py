"""
Project Rakshak 2.0 - Official Pitch Deck Generator for KLETECH Hackfest 2026
Strictly complies with the 6-slide screening round presentation format:
1. Project Overview and Problem Statement
2. Proposed Solution and Objectives
3. Innovation and Existing Alternatives
4. System Architecture and Workflow
5. Technology Stack and Implementation Plan
6. Expected Outcomes and Demo Plan
"""

import sys
from pathlib import Path
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent

# Theme Colors (Dark Military Tactical C4ISR Theme)
BG_COLOR = RGBColor(8, 18, 28)          # Deep Tactical Navy #08121c
CARD_BG = RGBColor(14, 31, 46)          # Panel Card #0e1f2e
CARD_BORDER = RGBColor(30, 61, 84)      # Card Border #1e3d54
ACCENT_CYAN = RGBColor(80, 215, 199)    # Tactical Cyan #50d7c7
ACCENT_GREEN = RGBColor(74, 222, 128)   # Radar Green #4ade80
ACCENT_AMBER = RGBColor(251, 191, 36)   # Warning Amber #fbbf24
ACCENT_RED = RGBColor(248, 113, 113)    # Critical Alert #f87171
TEXT_WHITE = RGBColor(255, 255, 255)    # Headers #ffffff
TEXT_LIGHT = RGBColor(203, 213, 225)    # Body text #cbd5e1
TEXT_MUTED = RGBColor(148, 163, 184)    # Muted text #94a3b8
TABLE_HEADER_BG = RGBColor(18, 48, 68)  # Table header
TABLE_ROW_ALT = RGBColor(10, 24, 36)    # Table row alternate

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_header(slide, slide_num, title, subtitle):
    # Top Category Tag
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = f"KLETECH HACKFEST 2026  //  SCREENING ROUND IDEA PRESENTATION  |  SLIDE {slide_num} OF 6"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.font.name = "Calibri"

    # Main Title
    txBox2 = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.55))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = title
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE
    p2.font.name = "Calibri"

    # Subtitle
    if subtitle:
        p2_sub = tf2.add_paragraph()
        p2_sub.text = subtitle
        p2_sub.font.size = Pt(11)
        p2_sub.font.color.rgb = TEXT_MUTED
        p2_sub.font.name = "Calibri"

def add_card(slide, left, top, width, height, title, content_items, accent_color=ACCENT_CYAN):
    # Background Box
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD_BG
    shape.line.color.rgb = CARD_BORDER
    shape.line.width = Pt(1)

    # Accent top border
    accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.06))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = accent_color
    accent_bar.line.fill.background()

    # Content Box
    txBox = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), height - Inches(0.25))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    if title:
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = accent_color
        p.font.name = "Calibri"
        p.space_after = Pt(6)

    for idx, item in enumerate(content_items):
        p = tf.add_paragraph()
        if isinstance(item, tuple):
            lead, body = item
            run1 = p.add_run()
            run1.text = lead + ": "
            run1.font.bold = True
            run1.font.color.rgb = TEXT_WHITE
            run1.font.size = Pt(10.5)
            run1.font.name = "Calibri"

            run2 = p.add_run()
            run2.text = body
            run2.font.bold = False
            run2.font.color.rgb = TEXT_LIGHT
            run2.font.size = Pt(10.5)
            run2.font.name = "Calibri"
        else:
            run = p.add_run()
            run.text = item
            run.font.size = Pt(10.5)
            run.font.color.rgb = TEXT_LIGHT
            run.font.name = "Calibri"
        p.space_after = Pt(5)

def build_presentation(output_path: str):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: Project Overview & Problem Statement
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1)
    add_header(slide1, 1, "Project Overview & Problem Statement", "Project Title, Team Details, Selected Domain, Target Users & The Problem Statement")

    # Left Column: Project Identity & Target Users
    add_card(slide1, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4), "PROJECT RAKSHAK 2.0 (रक्षक) — IDENTITY", [
        ("Project Title", "Project Rakshak 2.0: Sovereign Multimodal Geospatial Threat Intelligence & Joint C4ISR System"),
        ("Team Name", "BotS (KLE Technological University, Hubballi)"),
        ("Team Members", "Aditya Bajantri • Gagan Bongale • Utsav Nanapur • Misbah Falak • Shalina Maniyar • Niyati Gogri"),
        ("Selected Domain", "Domain 1A — Sovereign Defense, Geospatial Intelligence & Joint C4ISR"),
        ("Target End-Users", "Maritime Ops Centers (Indian Navy / Coast Guard), Forward Operating Bases (Indian Army), Tactical UAV Recon Analysts"),
        ("Operational Posture", "100% Air-Gapped, Zero External Cloud/API Callouts, Field-Edge Deployable (EMCON Alpha)"),
        ("Core Mission", "Deliver automated, sub-second threat detection, dark vessel interdiction, and Rules of Engagement (RoE) advisory to combat commanders in bandwidth-denied environments.")
    ], ACCENT_CYAN)

    # Right Column: The Problem Statement (The 4 Critical Operational Bottlenecks)
    add_card(slide1, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.4), "THE OPERATIONAL PROBLEM (INFORMATION SATURATION vs STARVATION)", [
        ("1. Gigapixel Rasters vs Tiny Targets", "Military satellite & UAV rasters exceed 20,000×20,000 pixels (>500MB). Tactical targets (tanks, vessels, launchers) occupy only 15×15 pixels. Standard AI downsamples to 640×640, completely erasing critical targets."),
        ("2. Maritime 'Dark Vessels' & AIS Spoofing", "Adversary intelligence ships and illegal vessels routinely disable AIS transponders or spoof MMSI identities in critical chokepoints (Malacca Strait, Mumbai ODA buffer), blinding optical radars."),
        ("3. Multi-Domain Sensor Silos", "Naval radar, satellite passes, Army drone video downlinks (FMV), and unattended ground sensors operate in isolated stovepipes. Zero-latency sensor-to-shooter coordination is absent."),
        ("4. Cloud Vulnerability at Forward Edges", "Commercial cloud AI tools (AWS, Azure, OpenAI) are completely unusable on frontline warships and forward combat posts due to strict EMCON radio silence, active electronic jamming, and data sovereignty laws.")
    ], ACCENT_AMBER)

    # =========================================================================
    # SLIDE 2: Proposed Solution & Objectives
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, 2, "Proposed Solution & Key Objectives", "Core Concept, Tactical Objectives, Core Architectural Features & Strategic Operational Benefits")

    # Card 1: Core Solution Concept
    add_card(slide2, Inches(0.8), Inches(1.5), Inches(3.7), Inches(5.4), "CORE SOLUTION CONCEPT", [
        ("Sovereign Joint COP", "A self-contained, air-gapped Joint Common Operating Picture (COP) ingesting satellite Earth observation (EO), SAR radar, UAV drone downlinks, and AIS logs onto a single unified tactical HUD."),
        ("On-Premise Neural Engine", "Runs dual-engine computer vision (YOLO11m Medium 20.1M params + Vessel Specialist) with 1024×1024 sub-pixel sliding window tiling and Weighted Box Fusion (WBF)."),
        ("Real-World Georeferencing", "Direct affine coordinate transformation via Rasterio/GDAL, mapping image pixels directly to real-world WGS-84 (EPSG:4326) Latitude/Longitude."),
        ("Air-Gapped Sovereign RAG", "Built-in cryptographic retrieval engine delivering instant military doctrine, UNCLOS law, and Rules of Engagement (RoE) checklists in <40ms with zero cloud calls.")
    ], ACCENT_CYAN)

    # Card 2: Key Tactical Objectives
    add_card(slide2, Inches(4.8), Inches(1.5), Inches(3.7), Inches(5.4), "KEY TACTICAL OBJECTIVES", [
        ("Objective 1: Sub-Pixel Accuracy", "Detect small military targets (<20px) across massive satellite scenes without downsampling loss, achieving >43% mAP@50 and >44% recall."),
        ("Objective 2: Dark Vessel Intercept", "All-weather SAR radar backscatter (CFAR) cross-correlated with local AIS databases to detect and isolate unflagged dark vessels."),
        ("Objective 3: O(N) Threat Geofencing", "Sub-second spatial grid cell hashing (~500m buckets) to flag convoy formations (+20) and restricted zone breaches (+30) in <80ms."),
        ("Objective 4: Frontline Portability", "Full edge deployment capability on standard tactical laptops and low-power NVIDIA Jetson hardware (15W power envelope).")
    ], ACCENT_GREEN)

    # Card 3: Intended Operational Benefits
    add_card(slide2, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.4), "INTENDED BENEFITS & IMPACT", [
        ("Sensor-to-Shooter Acceleration", "Shrinks tactical threat verification and response time from 45+ minutes of manual image scanning down to under 3 seconds."),
        ("Zero False-Alarm Clutter", "Physical sanity bounding-box filters (aspect ratio <= 4.5:1, vehicle dimensions 10-110px) eliminate 85% of terrain shadows and painted line false positives."),
        ("100% Data Sovereignty", "All intelligence, coordinates, and doctrine remain strictly on the local machine with zero data leakage to foreign servers or commercial APIs."),
        ("Interoperable Joint Action", "1-click dispatch transfers RAG tactical directives directly into the Mission Planner with sequenced operational checklists.")
    ], ACCENT_CYAN)

    # =========================================================================
    # SLIDE 3: Innovation & Existing Alternatives
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, 3, "Innovation & Existing Alternatives", "Comparative Analysis: Conventional Defense Approaches vs Baseline Vision vs Project Rakshak 2.0")

    # Add Comparative Table
    rows = 6
    cols = 4
    left = Inches(0.8)
    top = Inches(1.5)
    width = Inches(11.7)
    height = Inches(4.1)

    table_shape = slide3.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(3.0)
    table.columns[2].width = Inches(3.0)
    table.columns[3].width = Inches(3.5)

    headers = ["Capability Dimension", "Conventional Military C2 (Legacy)", "Standard Vision Models (YOLOv8/v11 Base)", "Project Rakshak 2.0 (Our Innovation)"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = ACCENT_CYAN if col_idx == 3 else TEXT_WHITE
        p.font.name = "Calibri"

    matrix_data = [
        ("Gigapixel Image Processing", "Manual human photo-interpreter review; multi-hour latency.", "Resizes whole image to 640×640, completely erasing targets <20px.", "1024×1024 overlapping slicing + Weighted Box Fusion (WBF). Zero target clipping."),
        ("Dark Vessel Interdiction", "Relies entirely on cooperative AIS transponders; easily spoofed.", "Optical-only detection; completely blinded by night, clouds, and haze.", "Sentinel-1 SAR Radar CFAR backscatter cross-correlated against AIS logs. Flags non-broadcasting contacts."),
        ("Spatial Threat Scoring", "Manual threat plotting on tactical charts; prone to operator lag.", "Returns unconstrained raw bounding boxes without tactical context.", "Sub-second O(N) spatial grid hashing. Autonomous convoy (+20) and geofence (+30) scoring in 80ms."),
        ("Network & Infrastructure", "Heavy centralized cloud server dependencies; vulnerable to jamming.", "Requires external REST APIs and continuous cloud connectivity.", "100% Air-Gapped Sovereign Edge runtime. Operates under strict EMCON radio silence."),
        ("Tactical Doctrine & RoE", "Physical printed doctrine binders or cloud LLMs (security leak).", "No doctrine or operational decision support capability.", "Sovereign Air-Gapped RAG Advisor: 8 indexed military doctrines with verified citations in <40ms.")
    ]

    for row_idx, data in enumerate(matrix_data, start=1):
        for col_idx, text in enumerate(data):
            cell = table.cell(row_idx, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.font.size = Pt(10)
            p.font.name = "Calibri"
            if col_idx == 0:
                p.font.bold = True
                p.font.color.rgb = TEXT_WHITE
            elif col_idx == 3:
                p.font.bold = True
                p.font.color.rgb = ACCENT_GREEN
            else:
                p.font.color.rgb = TEXT_LIGHT

    # Bottom Innovation Summary Banner
    add_card(slide3, Inches(0.8), Inches(5.8), Inches(11.7), Inches(1.1), "KEY INNOVATION SUMMARY", [
        ("The Strategic Edge", "Project Rakshak combines sub-pixel neural vision, SAR-AIS cross-cueing, O(N) spatial threat math, and sovereign RAG into an integrated, zero-cloud edge package that operates seamlessly in frontline combat conditions.")
    ], ACCENT_CYAN)

    # =========================================================================
    # SLIDE 4: System Architecture & Workflow
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, 4, "System Architecture & Operational Workflow", "Labelled Multi-Tier Architecture Diagram, Real-Time Data Flow & Frontline Operator Workflow")

    # Tier 1: Ingestion
    add_card(slide4, Inches(0.8), Inches(1.5), Inches(2.7), Inches(4.0), "TIER 1: SENSOR INGESTION", [
        ("Satellite EO Rasters", "GeoTIFF (Sentinel-2, xView) up to 20K×20K pixels."),
        ("SAR Radar Streams", "Sentinel-1 / RISAT synthetic aperture radar backscatter."),
        ("Tactical Drone Downlinks", "RTSP / MP4 high-resolution aerial full-motion video."),
        ("Maritime AIS & Signals", "AIS transponder feeds + 433.85 MHz SIGINT intercepts.")
    ], ACCENT_CYAN)

    # Tier 2: Processing & Vision
    add_card(slide4, Inches(3.8), Inches(1.5), Inches(2.7), Inches(4.0), "TIER 2: NEURAL VISION", [
        ("Sub-Pixel Slicer", "1024×1024 tiles with 31% overlap (zero seam clipping)."),
        ("Dual-Engine Detector", "YOLO11m Medium (20.1M params) + Vessel Specialist."),
        ("Weighted Box Fusion", "Consolidates overlapping multi-tile boxes (IoU 0.35)."),
        ("Physical Sanity Gating", "Filters impossible dimensions (aspect ratio <= 4.5:1).")
    ], ACCENT_GREEN)

    # Tier 3: Fusion & Analytics
    add_card(slide4, Inches(6.8), Inches(1.5), Inches(2.7), Inches(4.0), "TIER 3: SPATIAL THREAT", [
        ("WGS-84 Georeferencer", "Affine transform mapping pixel (x,y) to real Lat/Lon."),
        ("SAR-AIS Correlator", "Cross-checks radar vs 1.2km AIS to flag dark vessels."),
        ("O(N) Spatial Grid Hash", "Computes convoy formations and geofences in 80ms."),
        ("Threat Scoring Matrix", "Transparent 0-100 scoring based on RoE infractions.")
    ], ACCENT_AMBER)

    # Tier 4: Tactical C2 & RAG
    add_card(slide4, Inches(9.8), Inches(1.5), Inches(2.7), Inches(4.0), "TIER 4: TACTICAL C2 & RAG", [
        ("Sovereign RAG Engine", "Air-gapped lexical + semantic doctrine matcher."),
        ("Executive BLUF Synthesis", "Instant human-readable SITREP generation (<40ms)."),
        ("Military Leaflet HUD", "Air-gapped geospatial COP with tactical heatmaps."),
        ("Mission Planner Dispatch", "1-click handover from RoE directive to action plan.")
    ], ACCENT_CYAN)

    # Bottom Workflow Box
    add_card(slide4, Inches(0.8), Inches(5.7), Inches(11.7), Inches(1.2), "FRONTLINE OPERATOR WORKFLOW (STEP-BY-STEP)", [
        ("Step 1 -> Step 2 -> Step 3 -> Step 4", "Operator loads satellite pass or drone feed -> System executes sub-pixel detection & SAR-AIS correlation -> O(N) threat engine flags high-risk contacts & geofence breaches -> Sovereign RAG generates authorized RoE directive & dispatches action checklist to Mission Planner in <3 seconds.")
    ], ACCENT_GREEN)

    # =========================================================================
    # SLIDE 5: Technology Stack & Implementation Plan
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, 5, "Technology Stack & Implementation Plan", "Strategic Technology Choices ('The Why'), Team Responsibilities & Hackathon Development Roadmap")

    # Left: Technology Justification Card
    add_card(slide5, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.4), "CHOSEN TECHNOLOGIES & STRATEGIC JUSTIFICATIONS ('THE WHY')", [
        ("AI / Object Detection", "YOLO11m (Medium) Custom Trained: 20.1M parameters deliver +78.9% recall boost over nano models, running at 45+ FPS with FP16 Tensor Cores on edge GPUs."),
        ("Geospatial & Coordinate Mapping", "Rasterio + GDAL + OpenCV: Reads embedded GeoTIFF affine transform matrices to project bounding box pixels directly into real-world WGS-84 coordinates."),
        ("Threat Analysis Engine", "O(N) Spatial Hash Grid (Python 3.11): Replaces slow O(N^2) pairwise distance loops, computing clustering across 2,500+ targets in 80ms (400x speedup)."),
        ("Database Architecture", "SQLite 3 in WAL Mode: Zero daemon overhead, immune to network crashes, sub-millisecond atomic reads/writes, 100% self-contained in a single atomic file."),
        ("Backend Framework", "FastAPI + Uvicorn: High-throughput async multipart streaming for gigabyte GeoTIFFs with strict Pydantic type safety and self-documenting OpenAPI specs."),
        ("Tactical User Interface", "React 19 + TypeScript + Vite + Leaflet: Instant hot-reloading, zero-latency dark HUD theme, offline tile caching with zero telemetry callouts.")
    ], ACCENT_CYAN)

    # Right Top: Team Responsibilities
    add_card(slide5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(2.55), "TEAM BotS RESPONSIBILITIES & WORK ALLOCATION", [
        ("AI & Neural Vision Leads", "Aditya Bajantri & Gagan Bongale: YOLO11m training, multi-tile sliding window slicer, WBF tuning, and physical geometry sanity filters."),
        ("Geospatial & Backend Leads", "Utsav Nanapur & Misbah Falak: FastAPI architecture, Rasterio coordinate mapping, SAR CFAR radar detector, and SQLite WAL database."),
        ("Tactical UI & Systems Leads", "Shalina Maniyar & Niyati Gogri: React 19 Leaflet geospatial dashboard, military dark HUD, Sovereign RAG doctrine integration, and testing.")
    ], ACCENT_GREEN)

    # Right Bottom: Hackathon Implementation Plan (Timeline)
    add_card(slide5, Inches(6.8), Inches(4.35), Inches(5.7), Inches(2.55), "HACKATHON IMPLEMENTATION ROADMAP (HOURS 0-36)", [
        ("Phase 1: Ingestion & Baseline (0-8h)", "Setup GeoTIFF sliding window tiling pipeline, integrate baseline YOLO model, verify local SQLite database schema."),
        ("Phase 2: Dual-Engine & Fusion (8-20h)", "Implement YOLO11m + Vessel specialist ensemble, build SAR CFAR radar detector, write O(N) spatial threat clustering engine."),
        ("Phase 3: Tactical HUD & RAG (20-28h)", "Construct React 19 Leaflet COP, design military dark HUD, implement Sovereign RAG with 8 indexed defense doctrines."),
        ("Phase 4: Stress-Testing & Demo (28-36h)", "Conduct gigapixel image stress tests, verify sub-second latencies on edge GPU, rehearse live multi-domain defense demo.")
    ], ACCENT_AMBER)

    # =========================================================================
    # SLIDE 6: Expected Outcomes & Demo Plan
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, 6, "Expected Outcomes, Demo Plan & Success Metrics", "Planned Deliverables, Interactive Live Demo Flow, Measures of Success & Risk Mitigation")

    # Card 1: Planned Working Deliverables
    add_card(slide6, Inches(0.8), Inches(1.5), Inches(3.7), Inches(5.4), "PLANNED DELIVERABLES (WORKING PROTOTYPE)", [
        ("1. Joint Tactical C2 Dashboard", "Fully functional browser-based COP displaying fused optical satellite, SAR radar, and drone reconnaissance feeds."),
        ("2. Sub-Pixel Detection Pipeline", "Real-time sliding window analysis of multi-gigabyte satellite scenes detecting small vehicles and aircraft in <1.8s."),
        ("3. SAR Dark Vessel Interceptor", "Automated radar backscatter clustering cross-referenced with AIS transponders to flag uncooperative vessels."),
        ("4. Sovereign Air-Gapped RAG", "Instant, offline military doctrine advisor synthesizing executive BLUF briefings and RoE checklists in <40ms."),
        ("MVP vs Future Scope", "• Hackathon MVP: Fully working air-gapped prototype with optical, SAR, threat math, and RAG.\n• Future Enhancements: Hardware integration with Indian NavIC receiver & drone gimbal autopilot.")
    ], ACCENT_CYAN)

    # Card 2: Interactive Live Demo Plan
    add_card(slide6, Inches(4.8), Inches(1.5), Inches(3.7), Inches(5.4), "INTERACTIVE LIVE DEMO PLAN", [
        ("Act 1: Massive Satellite Ingestion", "Upload a 3,000×3,000px military satellite scene -> Rakshak slices tiles, runs YOLO11m, and detects dispersed tactical convoys in 1.4s."),
        ("Act 2: SAR Dark Vessel Isolation", "Switch to SAR radar view -> system evaluates radar cross-section (RCS) against sea clutter, detects dark vessel in Mumbai ODA buffer, triggers Threat Score 88."),
        ("Act 3: Sovereign RAG & RoE Advisory", "Operator opens 'Tactical AI (RAG)' -> queries authorized RoE for Mumbai ODA -> receives instant human-readable BLUF summary and legal citations in 36ms."),
        ("Act 4: 1-Click Mission Dispatch", "Operator clicks 'Dispatch Directive to Mission Planner' -> system automatically generates operational tasks with assigned tactical units.")
    ], ACCENT_GREEN)

    # Card 3: Success Metrics & Risk Mitigation
    add_card(slide6, Inches(8.8), Inches(1.5), Inches(3.7), Inches(5.4), "SUCCESS METRICS & RISK MITIGATION", [
        ("Key Measures of Success", "• Detection Accuracy: 43.3% mAP@50 and 44.0% Recall (+78.9% gain over baseline).\n• Inference Latency: <1.8s for multi-tile satellite raster analysis.\n• Threat Calculation: <80ms for 2,500+ contacts.\n• Zero Cloud Leakage: 100% air-gapped execution."),
        ("Required Datasets & Tools", "• Pre-cached xView defense dataset & Sentinel GeoTIFFs.\n• Local SQLite database & Python/React stack.\n• ZERO paid external APIs; zero internet required."),
        ("Key Risks & Mitigations", "• GPU Memory Overflow: Mitigated via sequential 1024px streaming crop with FP16 AMP.\n• Air-Gap Network Denied: All models, weights (161MB), and map tiles pre-cached locally on disk.")
    ], ACCENT_AMBER)

    prs.save(output_path)
    print(f"Successfully generated presentation at: {output_path}")

if __name__ == "__main__":
    out_file = ROOT / "Project_Rakshak_KLETECH_Hackfest_2026.pptx"
    build_presentation(str(out_file))
