"""Generate a comprehensive, beautifully styled PDF guide explaining Project Rakshak 2.0.

Written in an engaging, intuitive style accessible to a 12-year-old, while thoroughly
detailing the Problem Statement, Solutions, all 8 core platform modules (Joint COP,
Naval Domain, Army Domain, Change Detection, Tactical SITREP, Tactical AI, Mission
Planner, Edge & KPIs), what features exist, what operators can do, and the exact
technologies and algorithms used to build each one.
"""

import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' and running headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        
        # Don't draw header/footer on cover / first page
        if self._pageNumber > 1:
            # Running Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0f172a"))
            self.drawString(54, 752, "PROJECT RAKSHAK 2.0")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(160, 752, "|   AIR-GAPPED C4ISR EXPLAINER & OPERATIONAL GUIDE")
            
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.75)
            self.line(54, 744, 558, 744)

            # Running Footer
            self.line(54, 46, 558, 46)
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0284c7"))
            self.drawString(54, 32, "INDIAN ARMED FORCES C4ISR")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(200, 32, "|   100% Zero-Egress Air-Gapped Prototype   |   KLS Hackfest 2026")
            self.drawRightString(558, 32, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()


def create_explainer_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    primary_navy = colors.HexColor("#0f172a")
    accent_blue  = colors.HexColor("#0284c7")
    accent_teal  = colors.HexColor("#0d9488")
    danger_red   = colors.HexColor("#e11d48")
    warning_gold = colors.HexColor("#d97706")
    success_green= colors.HexColor("#16a34a")
    text_dark    = colors.HexColor("#1e293b")
    text_muted   = colors.HexColor("#64748b")
    bg_light     = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#e2e8f0")

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_navy,
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=accent_blue,
        alignment=TA_CENTER
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=primary_navy,
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=accent_blue,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
        spaceBefore=2,
        spaceAfter=3,
        alignment=TA_LEFT
    )

    callout_text = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=primary_navy
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.8,
        textColor=text_dark,
        leftIndent=12,
        firstLineIndent=-8,
        spaceBefore=1.5,
        spaceAfter=1.5
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=text_dark
    )

    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # COVER / HEADER BANNER
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph("PROJECT RAKSHAK 2.0", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("THE ULTIMATE DEFENSE COMMAND GUIDE (EXPLAINED FOR A 12-YEAR-OLD & EVERYONE ELSE!)", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>Naval & Army Geospatial & Multimodal Threat Detection Platform</b>", ParagraphStyle('SubSub', parent=subtitle_style, fontSize=9.5, textColor=accent_teal)))
    story.append(Spacer(1, 6))

    # Metadata Pill Box
    meta_data = [
        [
            Paragraph("<b>Security Level:</b> 100% Air-Gapped (Zero Cloud)", table_cell_style),
            Paragraph("<b>Target Domain:</b> Indian Armed Forces (Naval & Army)", table_cell_style),
            Paragraph("<b>Core Stack:</b> FastAPI + React 19 + YOLO11m", table_cell_style),
        ]
    ]
    t_meta = Table(meta_data, colWidths=[165, 175, 164])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # THE PROBLEM STATEMENT & THE RAKSHAK SOLUTION
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[THE MISSION] The Real-World Problem & How Rakshak Saves the Day", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceBefore=2, spaceAfter=6))

    story.append(Paragraph(
        "<b>Imagine this real-world defense challenge:</b> India has over <b>7,500 kilometers of coastline</b> and thousands of kilometers of high-mountain land borders. "
        "Every single day, hundreds of satellites in outer space take giant high-resolution photos of the Earth. Patrol drones buzz through the sky recording video. "
        "Space radar satellites beam pulses through thick monsoon storm clouds. Meanwhile, thousands of cargo ships, tankers, and fishing boats sail the Arabian Sea.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Danger: Hostile 'Ghost Ships' and Camouflaged Convoys!</b> "
        "Every commercial vessel is legally required to broadcast an automatic GPS radio beacon (called <b>AIS</b>) that shouts its name, speed, and position. "
        "However, hostile warships, pirates, and smugglers deliberately turn off their radio beacons. When they do this, they turn into a <b>'Dark Vessel' (a Ghost Ship)</b>! "
        "On standard port radar screens, they simply vanish. On land, enemy military convoys conceal themselves under tree lines, and adversaries attempt sabotage at remote forward bases.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Why Can't Human Officers Just Watch the Screens?</b> "
        "A single satellite pass takes pictures covering millions of square meters containing hundreds of thousands of cars, buildings, and boats. "
        "If human defense analysts had to manually click and verify all 14,000 raw objects detected in every pass, it would take <b>over 73 hours of work for every single hour of surveillance</b>! "
        "Human eyes get tired, attention drifts, and dangerous threats slip right past.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Worst Nightmare: The Enemy Jams the Internet!</b> "
        "In real combat, adversaries use electronic warfare to jam satellite links, cut undersea communication cables, and block cloud connections. "
        "If a defense platform relies on Google Cloud, Amazon AWS, or OpenAI, the entire system dies the exact second the internet cable is cut!",
        body_style
    ))

    # Solution Callout
    sol_box = [
        [
            Paragraph(
                "<b>[SOVEREIGN SOLUTION] Project Rakshak 2.0:</b><br/>"
                "Project Rakshak 2.0 is a <b>100% sovereign, air-gapped AI super-brain</b> running directly on local defense laptops and field devices. "
                "It makes <b>ZERO external internet calls</b>—no cloud APIs, no online maps, no outside servers. "
                "It fuses 5 different sensor streams (Sentinel-1 SAR radar, xView high-res optical imagery, UAV drone video, ground seismic geophones, and AIS radio), "
                "detects hidden ghost ships in <b>1.6 seconds</b>, clusters 14,000 raw objects into spatial entities to slash <b>86.5% of analyst busywork</b>, "
                "and compiles official NATO/Indian military SITREP orders in <b>less than 0.05 seconds</b>!",
                callout_text
            )
        ]
    ]
    t_sol = Table(sol_box, colWidths=[504])
    t_sol.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#e0f2fe")),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#0284c7")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_sol)
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 1: JOINT COP (COMMON OPERATING PICTURE)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 1] Joint COP (Common Operating Picture) — The Master Command Map", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "Think of the Joint COP like the giant tactical map in your favorite strategy or battle-royale video game! "
        "Instead of forcing officers to juggle ten confusing computer screens with separate lists of ships, radar dots, and drone coordinates, "
        "the Joint COP combines EVERYTHING onto one smooth, interactive 60-FPS map. Commanders see the entire Arabian Sea, "
        "naval task forces, and border sectors live on screen.",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Interactive Vector Canvas:</b> Displays India's sovereign coastline, the 200-nautical-mile Exclusive Economic Zone (EEZ) perimeter in glowing amber, and strategic naval bases (Mumbai Western Fleet, Karwar Project Seabird, Goa INS Hansa).", bullet_style))
    story.append(Paragraph("• <b>Multi-Sensor Tactical Reticles:</b> Color-coded symbols for optical satellite hits (cyan), Sentinel-1 space radar contacts (magenta), live AIS vessels (green), and drone/ground alarms (orange).", bullet_style))
    story.append(Paragraph("• <b>Prioritized Triage Queue Sidebar:</b> A ranked real-time feed on the right side listing threats from highest score (95/100) to lowest.", bullet_style))
    story.append(Paragraph("• <b>Kinematic Drift Uncertainty Ellipses:</b> Glowing geometric ovals around targets illustrating Circular Error Probable (CEP) drift bounds if radio contact is lost.", bullet_style))
    story.append(Paragraph("• <b>Three Procedural Map Themes:</b> <i>Offline Basemap</i> (muted land & ocean), <i>Dark Tactical</i> (stealth black with high-contrast coastlines), and <i>Offline Terrain</i> (elevation shading bands).", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Click any high-priority alert in the triage sidebar: The map smoothly flies directly to the target coordinate!", bullet_style))
    story.append(Paragraph("• Toggle sensor layers on/off with switches (Optical, Radar, AIS, Geofences, Threat Heatmaps, and Sovereign Coastline Overlay).", bullet_style))
    story.append(Paragraph("• Switch map styles instantly to match daylight operations or dark command-bunker lighting.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>Frontend:</b> React 19, Leaflet GIS mapping engine, dynamic SVG coordinate projections, and Lucide defense iconography.", bullet_style))
    story.append(Paragraph("• <b>Local Tile Engine:</b> A fully procedural Python tile server in <code>backend/app/tile_service.py</code> using Pillow to synthesize PNG map tiles on localhost. <i>Zero calls to OpenStreetMap or Google Maps!</i>", bullet_style))
    story.append(Paragraph("• <b>Kinematic Fusion:</b> Constant-Velocity Kalman Filter covariance matrices in local ENU frame generating real-time CEP drift ellipses.", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 2: NAVAL DOMAIN
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 2] Naval Domain — Space Detectives Hunting Ghost Ships", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "This is the ghost ship hunter! When an illegal boat or secret spy submarine tries to sneak into Indian waters, "
        "they switch off their radio beacon so ordinary maritime radars cannot see their name. But Rakshak uses space radar satellites "
        "(Sentinel-1) that shoot microwave radar beams straight through storm clouds and pitch-black darkness. "
        "When the radar bounce comes back bright, but there is NO radio beacon at that spot, Rakshak screams: <i>'Aha! Confirmed Dark Vessel!'</i>",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>High-Res Satellite Image Canvas:</b> Shows crisp aerial views of ports and open ocean with colored AI bounding boxes drawn around every vessel.", bullet_style))
    story.append(Paragraph("• <b>Sentinel-1 SAR Radar Cards:</b> Displays radar cross-section (RCS backscatter in decibels), estimated ship length in meters (e.g., 118m Frigate or 185m Tanker), and AIS match status.", bullet_style))
    story.append(Paragraph("• <b>Confidence & Class Filter Bar:</b> Buttons to toggle target types (Aircraft, Vehicles, Infrastructure, Maritime Vessels) and a threshold dropdown (from 25% raw to 80% verified).", bullet_style))
    story.append(Paragraph("• <b>Analyst Action Buttons:</b> Rapid 1-click triage buttons on each detected ship: <code>[Matched]</code>, <code>[Dark Vessel (+50 Threat)]</code>, or <code>[Unknown]</code>.", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Drag and drop ANY satellite picture or GeoTIFF (Sentinel-2, xView) into the dropzone to scan it in 1.6 seconds.", bullet_style))
    story.append(Paragraph("• Switch AI brains between the <b>Joint 4-Class Model (YOLO11m)</b> and the dedicated <b>Vessel Specialist Model (YOLO11n-1024)</b>.", bullet_style))
    story.append(Paragraph("• Manually adjudicate a contact with one click to confirm it as a threat or mark it safe.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>Computer Vision:</b> Ultralytics YOLO11m (20.1 million parameters) trained on 5,838 satellite chips, plus a specialist YOLO11n fine-tuned on high-resolution 1024px maritime tiles.", bullet_style))
    story.append(Paragraph("• <b>SAHI (Slicing Aided Hyper Inference):</b> Slices giant 3000x3000px satellite photos into overlapping 1024px tiles with Weighted Box Fusion (WBF) so tiny 12-pixel boats are never missed.", bullet_style))
    story.append(Paragraph("• <b>CA-CFAR Radar Algorithm:</b> Cell-Averaging Constant False Alarm Rate sliding-window algorithm in <code>backend/app/sar_engine.py</code> that separates metal hull returns from ocean wave sea clutter.", bullet_style))
    story.append(Paragraph("• <b>Dead-Reckoning Haversine Math:</b> Calculates great-circle distances and forward-predicts AIS vessel paths using Speed Over Ground (SOG) and Course Over Ground (COG).", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 3: ARMY DOMAIN
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 3] Army Domain — Drones, Earthquake Spies & Secret Radios", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "Guarding land borders isn't just about cameras—it's about listening and feeling! "
        "The Army Domain connects three cool gadgets together: (1) Flying drones with thermal cameras that spot vehicle convoys, "
        "(2) Mini earthquake sensors (called UGS) buried in the dirt that 'feel' the heavy rumble of tanks, and "
        "(3) Radio sniffers (SIGINT) that catch intercepted enemy radio signals.",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Interactive UAV Tactical Downlink:</b> Video/image screen showing camera feeds with 1-click test buttons for real battlefield files (<code>1217.tif</code> with convoys and <code>1154.tif</code> airbases).", bullet_style))
    story.append(Paragraph("• <b>Seismic Geophone Telemetry:</b> Vibration frequency readouts (e.g., 18 Hz harmonic rumble characteristic of heavy tracked armored vehicles).", bullet_style))
    story.append(Paragraph("• <b>Tactical SIGINT Intercept Logs:</b> Intercepted VHF messages with lines-of-bearing, signal strength percentages, and threat assessment scores.", bullet_style))
    story.append(Paragraph("• <b>C2 Alarm State Machine:</b> Badges that change color as alarms are handled: <code>ACTIVE</code> (red) -> <code>ACKNOWLEDGED</code> (amber) -> <code>RESOLVED</code> (green).", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Click <i>'1-Click Test: Vehicle Convoys'</i> or <i>'Airbase Targets'</i> to watch neural AI detect dozens of tanks and jets instantly.", bullet_style))
    story.append(Paragraph("• Acknowledge and resolve seismic alarms with one click using the live Command & Control (C2) button.", bullet_style))
    story.append(Paragraph("• Upload custom drone still images (VisDrone / VIRAT formats) for rapid automated threat triage.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>Multi-Class Neural Vision:</b> Fine-tuned YOLO11m weights detecting military trucks, small cars, and transport aircraft.", bullet_style))
    story.append(Paragraph("• <b>Digital Signal Processing:</b> Fast Fourier Transform (FFT) frequency classification modeling 18 Hz tracked vehicle seismic peaks in <code>backend/app/army_engine.py</code>.", bullet_style))
    story.append(Paragraph("• <b>RESTful C2 State Machine:</b> FastAPI PATCH endpoints with idempotent SQLite WAL database locking for zero-loss alarm updates.", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 4: CHANGE DETECTION
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 4] Change Detection — Cosmic 'Spot the Difference' from Orbit", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "Have you ever played 'Spot the Difference' in a puzzle book? Now imagine doing that with two satellite photos taken months apart from 600 kilometers in space! "
        "The satellite wobbles slightly, the sun moves, shadows shift, and trees change color. "
        "If the enemy quietly parked 4 missile launchers in an empty clearing, how do you find them? "
        "Rakshak lines up both photos perfectly down to a fraction of a single pixel, runs AI on both, and immediately highlights whatever was added, moved, or destroyed!",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Side-by-Side Dual Scene Viewer:</b> Displays the 'Before' image (Baseline pass) and 'After' image (Surveillance pass).", bullet_style))
    story.append(Paragraph("• <b>Visual Diff Mask:</b> Neon-highlighted overlay showing the exact bounding boxes of new or missing objects.", bullet_style))
    story.append(Paragraph("• <b>Registration Quality Meter:</b> Shows sub-pixel alignment accuracy (measured at <b>0.14 pixels</b> of error across 8px shifts).", bullet_style))
    story.append(Paragraph("• <b>Flicker Stability Filter:</b> An intelligent toggle that weeds out camera lighting flicker so analysts only see genuine physical changes.", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Select any of the 40 reproducible test pairs (seeds 21-60) or upload custom dual passes.", bullet_style))
    story.append(Paragraph("• Run automated computer vision co-registration with one click.", bullet_style))
    story.append(Paragraph("• Toggle the Stability Filter to boost change precision from 28% all the way to <b>80.95%</b>!", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>ORB + RANSAC Alignment:</b> Oriented FAST and Rotated BRIEF feature point detectors combined with Random Sample Consensus homography in OpenCV.", bullet_style))
    story.append(Paragraph("• <b>Hungarian Bipartite Matching:</b> The Kuhn-Munkres algorithm matches objects between both scenes based on bounding-box distance and class identity.", bullet_style))
    story.append(Paragraph("• <b>Radiometric Normalization:</b> Local histogram equalization to remove cloud shadow brightness differences without hallucinating false alarms.", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 5: TACTICAL SITREP
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 5] Tactical SITREP — The 0.05-Second Military Report Writer", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "In military operations, commanders need to send formal situation reports (called a 'SITREP') to the General at headquarters. "
        "Normally, an officer has to sit at a desk with a notebook, call radar operators, count vessels, check coordinates, and type a long report. "
        "This takes <b>20 to 30 minutes</b>! In war, 30 minutes is an eternity. "
        "Rakshak has an automated robot clerk that pulls all live threats from radar, drones, and satellites, "
        "organizes them into standard NATO/Indian military format, and compiles the entire document in <b>0.016 seconds (less than a single blink!)</b>.",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Standard STANAG 2014 Format:</b> Official military briefing structure with DTG (Date-Time-Group), Section 1 (Situation & Enemy Forces), Section 2 (Friendly Forces), Section 3 (Air/Naval Threat Breakdown), Section 4 (Priority Action Matrix), and Section 5 (Commander's Assessment).", bullet_style))
    story.append(Paragraph("• <b>Live Threat Census:</b> Exact breakdown of active threats (e.g., 7 HIGH, 1 MEDIUM, 0 LOW).", bullet_style))
    story.append(Paragraph("• <b>Pre-Compiled Recommended Actions:</b> Automatically suggested tactical orders (e.g., <i>'Dispatch Fast Attack Craft to Sector Alpha'</i> or <i>'Raise Alert Level to ORANGE'</i>).", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Click <i>'Generate STANAG Situation Report'</i> to refresh the briefing instantly with real-time field data.", bullet_style))
    story.append(Paragraph("• Click <i>'Copy Briefing'</i> to copy the full markdown text to your clipboard for radio dispatch.", bullet_style))
    story.append(Paragraph("• Click <i>'Export SITREP (.md)'</i> to download a clean, dated markdown file.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>Procedural Template Compiler:</b> Implemented in <code>backend/app/sitrep_generator.py</code>, pulling live relational data from SQLite WAL in microseconds.", bullet_style))
    story.append(Paragraph("• <b>Military Standards:</b> Strictly modeled after NATO STANAG 2014 and Indian Armed Forces Joint Doctrine guidelines.", bullet_style))
    story.append(Paragraph("• <b>Zero-Cloud Guarantee:</b> 100% deterministic local Python execution without any generative LLM hallucinations or delay.", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 6: TACTICAL AI (DOCTRINE RAG)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 6] Tactical AI (Doctrine RAG) — The Sovereign Military Lawyer in a Box", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "Can a navy warship just shoot at any suspicious boat in the ocean? <i>No way!</i> "
        "There are very strict international laws and military rules of engagement (RoE). "
        "If a captain boards a ship without following the law, it could cause an international crisis. "
        "Tactical AI is like having a genius military lawyer and Admiral sitting right next to you! "
        "You ask: <i>'Can we board a ship that has no flag in our 200-mile zone?'</i> "
        "In <b>0.039 seconds</b>, it quotes the exact international treaty (UNCLOS Article 110) and tells you the exact legal steps to take, completely offline!",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Tactical Query Input Terminal:</b> Clean command prompt to type operational legal and tactical questions.", bullet_style))
    story.append(Paragraph("• <b>Tactical Action Directives:</b> Bold operational guidance (e.g., <i>'EXERCISE RIGHT OF VISIT UNDER UNCLOS ART 110'</i>).", bullet_style))
    story.append(Paragraph("• <b>Sovereign Doctrine Library Citations:</b> Displays official paragraph excerpts from UNCLOS 1982, Indian Navy Book of Reference (INBR 8), and Maritime Zones Act 1976.", bullet_style))
    story.append(Paragraph("• <b>1-Click Mission Dispatch Button:</b> A button labeled <i>'Dispatch to Mission Planner'</i> that takes the coordinates mentioned in the query and sends them straight to the flight route planner!", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Ask questions about boarding rights, hot pursuit, air defense warning zones, or rules of engagement.", bullet_style))
    story.append(Paragraph("• Inspect the verbatim doctrine paragraphs and legal authority cards.", bullet_style))
    story.append(Paragraph("• Send any investigated target coordinate directly into the flight route planner with one click.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>BM25 Lexical Retrieval Engine:</b> Okapi BM25 ranking algorithm in <code>backend/app/rag_engine.py</code> that indexes sovereign defense documents locally.", bullet_style))
    story.append(Paragraph("• <b>100% Deterministic & Hallucination-Free:</b> Unlike cloud AI models that can make things up, BM25 returns genuine legal texts verbatim in under 40 milliseconds with 0 cloud calls.", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 7: MISSION PLANNER
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 7] Mission Planner — The Safe Stealth Flight Navigator", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "Imagine Google Maps, but built for stealth fighter jets and reconnaissance drones! "
        "When pilots fly a mission, they can't just fly in a straight line. They have to avoid enemy missile zones, "
        "stay inside safe corridors, and keep track of their fuel. "
        "The Mission Planner lets commanders click waypoints on an offline map, calculates the exact flight distance and time, "
        "and warns them if their path accidentally crosses into a dangerous red zone!",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Flight Route Canvas:</b> Displays flight paths connecting waypoints with dashed bright cyan navigation lines.", bullet_style))
    story.append(Paragraph("• <b>Geofenced Danger Zones:</b> Red circular buffer zones showing enemy Surface-to-Air Missile (SAM) coverage and high-threat areas.", bullet_style))
    story.append(Paragraph("• <b>Waypoint Telemetry Table:</b> Lists each waypoint coordinate (Lat, Lon), planned altitude in feet, and leg distance in kilometers.", bullet_style))
    story.append(Paragraph("• <b>Automatic Extent Fitting:</b> Map automatically zooms to fit all waypoints and nearby coastlines cleanly on screen.", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Add custom waypoints by clicking on the map or accepting coordinates dispatched from Tactical AI.", bullet_style))
    story.append(Paragraph("• Check total mission flight time and distance (e.g., 41.7 km patrol in 11.2 minutes at cruising speed).", bullet_style))
    story.append(Paragraph("• Toggle between Offline Basemap and Dark Tactical views to review route terrain.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>Geodesic Spatial Math:</b> Haversine equations computing true nautical distances across the Earth's curvature.", bullet_style))
    story.append(Paragraph("• <b>Point-in-Polygon & Circle Collision:</b> Real-time collision detection alerting when flight legs intersect restricted danger zones.", bullet_style))
    story.append(Paragraph("• <b>Leaflet Polyline Vector Engine:</b> Hardware-accelerated 60 FPS vector path drawing in React 19.", bullet_style))
    story.append(Spacer(1, 8))

    # ─────────────────────────────────────────────────────────────────────────
    # MODULE 8: EDGE HARDWARE & KPIS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("[MODULE 8] Edge Hardware & KPIs — How Fast, Tough & Smart is the Robot?", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=2, spaceAfter=5))

    story.append(Paragraph(
        "<b>Explained for a 12-Year-Old:</b> "
        "It's easy to make a computer program fast if you have a giant room filled with supercomputers connected to the internet. "
        "But what if the AI has to fly on a tiny military drone the size of a pizza box, powered by a battery? "
        "This section proves how lightweight, power-efficient, and rock-solid Project Rakshak 2.0 really is!",
        body_style
    ))
    story.append(Paragraph("<b>What All Is There (Visual Screen Features):</b>", h2_style))
    story.append(Paragraph("• <b>Model Weight Card:</b> Shows that the YOLO11m brain is only <b>38.7 MB</b> with <b>20.1 million parameters</b>—small enough to fit on a USB thumb drive!", bullet_style))
    story.append(Paragraph("• <b>Live Hardware Power Meter:</b> Real power measurements from the host GPU (<b>43.07 Watts</b> during full inference—less power than a household light bulb!).", bullet_style))
    story.append(Paragraph("• <b>Supersonic Speed Stats:</b> Boosted GPU inference speed of <b>17.85 milliseconds per tile</b> (that is over <b>55 frames every single second!</b>).", bullet_style))
    story.append(Paragraph("• <b>Jetson Edge Scaling Rooflines:</b> Theoretical hardware projections for NVIDIA Jetson AGX Orin (10.8-23.8 ms) and Orin Nano (32.8-98.8 ms).", bullet_style))
    story.append(Paragraph("• <b>DDIL Jamming Proof Card:</b> Proof that the system survived 30 minutes of simulated electronic jamming with <b>100% uptime</b> and <b>0 lost alerts</b>.", bullet_style))

    story.append(Paragraph("<b>What You Can Do (Operator Actions):</b>", h2_style))
    story.append(Paragraph("• Inspect live GPU memory, CPU percentage, and disk capacity in real time.", bullet_style))
    story.append(Paragraph("• Audit the 10 graded Hackfest defense KPIs with complete provenance tracking.", bullet_style))
    story.append(Paragraph("• Verify zero-egress compliance: Proof that 0 bytes left the machine to outside servers.", bullet_style))

    story.append(Paragraph("<b>What Was Used to Build It (The Science & Tech):</b>", h2_style))
    story.append(Paragraph("• <b>PyTorch CUDA Event Timers:</b> Microsecond-accurate GPU execution measurement using hardware events.", bullet_style))
    story.append(Paragraph("• <b>NVIDIA Management Library (NVML):</b> Hardware board power sampling at 12.5 Hz via <code>nvidia-smi</code>.", bullet_style))
    story.append(Paragraph("• <b>Store-and-Forward SQLite WAL Outbox:</b> Anti-starvation priority queue in <code>backend/app/ddil_sync.py</code> that holds alerts in local database storage during radio silence and syncs when links restore.", bullet_style))
    story.append(Spacer(1, 10))

    # ─────────────────────────────────────────────────────────────────────────
    # MASTER COMPARISON TABLE & CONCLUSION
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())  # Dedicated, clean final spread for master matrix & conclusion

    story.append(Paragraph("[MASTER DOSSIER] Summary Matrix: All 8 Modules at a Glance", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph("A quick-reference tactical scorecard comparing every module, its core metaphor, operator capabilities, and the underlying technology:", body_style))
    story.append(Spacer(1, 6))

    table_data = [
        [
            Paragraph("<b>Module</b>", table_header_style),
            Paragraph("<b>12-Year-Old Metaphor</b>", table_header_style),
            Paragraph("<b>What You Can Do</b>", table_header_style),
            Paragraph("<b>Technology Used</b>", table_header_style),
        ],
        [
            Paragraph("<b>1. Joint COP</b>", table_cell_style),
            Paragraph("Interactive video game battle map", table_cell_style),
            Paragraph("Track threats, fly to blips, switch map styles, inspect drift circles", table_cell_style),
            Paragraph("React 19, Leaflet, local Python procedural tile generator, Kalman filters", table_cell_style),
        ],
        [
            Paragraph("<b>2. Naval Domain</b>", table_cell_style),
            Paragraph("Space detectives catching ghost ships", table_cell_style),
            Paragraph("Upload satellite images, run 1.6s scan, adjudicate dark vessels with 1 click", table_cell_style),
            Paragraph("YOLO11m/n, SAHI 1024px slicing, Sentinel-1 CA-CFAR radar math, Haversine", table_cell_style),
        ],
        [
            Paragraph("<b>3. Army Domain</b>", table_cell_style),
            Paragraph("Drones, earthquake spies & secret radios", table_cell_style),
            Paragraph("Watch drone tank detections, handle 18 Hz seismic alarms, review SIGINT", table_cell_style),
            Paragraph("YOLO11 vision, FFT vibration signal processing, FastAPI C2 state machine", table_cell_style),
        ],
        [
            Paragraph("<b>4. Change Detection</b>", table_cell_style),
            Paragraph("Cosmic 'Spot the Difference' puzzle", table_cell_style),
            Paragraph("Align 2 satellite passes, highlight new/moved objects, filter camera flicker", table_cell_style),
            Paragraph("ORB + RANSAC sub-pixel alignment, Hungarian bipartite matching, OpenCV", table_cell_style),
        ],
        [
            Paragraph("<b>5. Tactical SITREP</b>", table_cell_style),
            Paragraph("Supersonic military report writer", table_cell_style),
            Paragraph("Generate official military intelligence report in 0.016s, copy or export", table_cell_style),
            Paragraph("Procedural Python compiler, NATO STANAG 2014 standards, SQLite WAL aggregation", table_cell_style),
        ],
        [
            Paragraph("<b>6. Tactical AI</b>", table_cell_style),
            Paragraph("Military lawyer & Admiral in a box", table_cell_style),
            Paragraph("Ask complex rules of engagement questions, quote law, dispatch to planner", table_cell_style),
            Paragraph("BM25 lexical ranking engine, offline UNCLOS & INBR 8 doctrine corpus", table_cell_style),
        ],
        [
            Paragraph("<b>7. Mission Planner</b>", table_cell_style),
            Paragraph("Stealth flight navigation autopilot", table_cell_style),
            Paragraph("Plot flight waypoints, calculate flight time & fuel, detect danger zones", table_cell_style),
            Paragraph("Geodesic Haversine math, point-in-polygon geofencing, Leaflet vector routes", table_cell_style),
        ],
        [
            Paragraph("<b>8. Edge & KPIs</b>", table_cell_style),
            Paragraph("Robot fitness & speed speedometer", table_cell_style),
            Paragraph("Inspect 17.8ms latency, 43W power draw, verify 0-byte air-gap security", table_cell_style),
            Paragraph("PyTorch CUDA event timing, NVML power polling, DDIL store-and-forward outbox", table_cell_style),
        ],
    ]

    t_master = Table(table_data, colWidths=[85, 115, 150, 154])
    t_master.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_navy),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_light]),
    ]))
    story.append(t_master)
    story.append(Spacer(1, 14))

    # ─────────────────────────────────────────────────────────────────────────
    # CONCLUSION / HERO STATEMENT
    # ─────────────────────────────────────────────────────────────────────────
    conclusion_box = [
        [
            Paragraph(
                "<b>[THE BIG TAKEAWAY] A Sovereign Shield for Tomorrow's Commanders:</b><br/>"
                "Project Rakshak 2.0 proves that cutting-edge defense artificial intelligence does not need the cloud, does not need big tech servers, "
                "and does not need an internet connection. By combining smart neural vision, radar physics, signal math, and rock-solid offline engineering, "
                "Rakshak creates an unbreakable digital shield that protects our borders—no matter how rough the storm or how fierce the electronic warfare!",
                ParagraphStyle('FinalHero', parent=callout_text, fontSize=9, leading=13.5, textColor=primary_navy)
            )
        ]
    ]
    t_conc = Table(conclusion_box, colWidths=[504])
    t_conc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ecfdf5")),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#059669")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_conc)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")

    # Also copy to parent Desktop directory for immediate user access
    desktop_dest = output_path.parent.parent / output_path.name
    try:
        shutil.copy2(output_path, desktop_dest)
        print(f"PDF also copied to: {desktop_dest}")
    except Exception as e:
        print(f"Note: Could not copy to desktop: {e}")


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parents[1] / "Project_Rakshak_Explainer_Guide.pdf"
    create_explainer_pdf(out_file)
