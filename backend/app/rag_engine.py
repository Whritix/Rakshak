"""Sovereign Air-Gapped RAG (Retrieval-Augmented Generation) Engine for Project Rakshak 2.0.

Provides cryptographic military doctrine retrieval, Rules of Engagement (RoE) advisory,
and contextual intelligence synthesis without any external cloud API dependencies.
Optimized for rapid, human-readable tactical decision making.
"""
from __future__ import annotations
import math
import re
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from backend.app.db import get_db

ROOT = Path(__file__).resolve().parents[2]

# Standard Defense Knowledge Base Seed Documents
INITIAL_DOCTRINE_CORPUS = [
    {
        'id': 'DOC-ROE-01',
        'category': 'NAVAL_ROE',
        'title': 'Indian Navy Rules of Engagement: Dark Vessel Interdiction in EEZ & Territorial Waters',
        'references_code': 'IN-ROE-2024-SEC-4.2',
        'classification': 'SECRET // RESTRICTED ROE',
        'tags': json.dumps(['dark vessel', 'ais', 'interdiction', 'maritime', 'vhf 16', 'eez', 'boarding', 'vbss']),
        'content': (
            "1. IDENTIFICATION & CHALLENGE: Any surface vessel detected via SAR radar or optical sensors with disabled, "
            "spoofed, or non-transmitting AIS transponders within the Indian Exclusive Economic Zone (EEZ) or security buffer "
            "must be challenged on International Maritime VHF Channel 16 (156.800 MHz) and Channel 70 DSC. "
            "2. INTERCEPTION DISPATCH: If the contact fails to respond within 10 minutes or alters course away from designated "
            "sea lanes toward restricted military perimeters, the Command Duty Officer is authorized to dispatch Fast Interceptor Craft (FIC) "
            "or Immediate Support Vessels (ISV) from the nearest naval operational station. "
            "3. BOARDING & VBSS: Visit, Board, Search, and Seizure (VBSS) operations are authorized under Section 4.2 once contact is "
            "shadowed within 5 nautical miles. Warning shots across the bow require authorization from Flag Officer Commanding (FOC)."
        )
    },
    {
        'id': 'DOC-ROE-02',
        'category': 'MARITIME_LAW',
        'title': 'Maritime Zones of India Act 1976 & UNCLOS Article 111 (Right of Hot Pursuit)',
        'references_code': 'MZI-ACT-1976 / UNCLOS-ART-111',
        'classification': 'UNCLASSIFIED // LEGAL DOCTRINE',
        'tags': json.dumps(['unclos', 'hot pursuit', 'legal', 'territorial waters', 'eez', 'jurisdiction', 'smuggling', 'piracy', 'article 111', 'third state']),
        'content': (
            "1. COMMENCEMENT OF HOT PURSUIT: Under UNCLOS Article 111 and Section 4 of the Maritime Zones of India Act 1976, hot pursuit of a "
            "foreign vessel may be undertaken when the competent authorities of the coastal State have good reason to believe that the "
            "vessel has violated laws and regulations of the State. The pursuit must commence when the foreign ship or one of its boats is "
            "within the internal waters, territorial sea (12 NM), or contiguous zone (24 NM) of the pursuing State. "
            "2. CONTINUITY REQUIREMENT: Pursuit must be continuous and uninterrupted by military ships or aircraft. Tactical handover "
            "between naval warships, coast guard cutters, and maritime patrol aircraft (Dornier-228 / P-8I) is legally certified as continuous. "
            "3. CESSATION: The right of hot pursuit strictly ceases as soon as the ship pursued enters the territorial sea of its own State "
            "or of a third sovereign State. Progressive proportionate force to compel stopping and boarding is authorized if orders to halt are defied."
        )
    },
    {
        'id': 'DOC-ROE-03',
        'category': 'ZONAL_SOP',
        'title': 'Critical Offshore Asset Defense SOP: Mumbai Offshore Development Area (ODA)',
        'references_code': 'HQWNC-ODA-DEF-SOP-REV3',
        'classification': 'SECRET // CRITICAL INFRASTRUCTURE',
        'tags': json.dumps(['mumbai oda', 'offshore', 'oil rig', 'platform', 'exclusion', 'buffer', 'western naval command', 'bombay high', 'pipelines']),
        'content': (
            "1. EXCLUSION ZONE: A mandatory 25 km defensive buffer is declared around all critical offshore hydrocarbon platforms "
            "and subsea pipeline manifolds in the Mumbai Offshore Development Area (ODA). "
            "2. ZERO TOLERANCE FOR UNIDENTIFIED TRAFFIC: Commercial vessels are restricted to designated shipping corridors. "
            "Any vessel loitering, anchoring without clearance, or operating with dark AIS inside the 25 km perimeter triggers an "
            "immediate +30 Threat Score escalation. "
            "3. IMMEDIATE ESCALATION: Scramble armed offshore patrol vessel (OPV) and notify INS Shikra naval air station for "
            "Chetak / MH-60R helicopter airborne reconnaissance. Naval boarding teams are placed on 15-minute standby."
        )
    },
    {
        'id': 'DOC-ROE-04',
        'category': 'ZONAL_SOP',
        'title': 'Strategic Maritime Chokepoint Watch: Malacca Strait / Nicobar 6-Degree Channel',
        'references_code': 'ANC-MARITIME-CHOKEPOINT-DIR-08',
        'classification': 'SECRET // CHOKEPOINT SURVEILLANCE',
        'tags': json.dumps(['malacca', 'nicobar', 'chokepoint', 'submarines', 'andaman', 'anc', 'p8i', 'transit', '6-degree', 'agi']),
        'content': (
            "1. CHOKEPOINT STRATEGY: The 6-Degree Channel south of Great Nicobar is India's primary maritime monitoring choke "
            "into the Malacca Strait. Over 60,000 vessels transit annually. "
            "2. TARGET PROFILE CRITERIA: Adversary auxiliary intelligence ships (AGI), acoustic research vessels, and sub-surface "
            "escort tenders must be continuously correlated against Lloyd's Register and AIS registries. "
            "3. RESPONSE DIRECTIVE: Any dark SAR contact exceeding 60 meters length must be tasked for high-resolution P-8I Neptune "
            "maritime patrol radar scan and acoustic sonobuoy deployment. Contact data is piped to Andaman and Nicobar Command (ANC) Joint Ops."
        )
    },
    {
        'id': 'DOC-ROE-05',
        'category': 'ARMY_DOCTRINE',
        'title': 'Indian Army Border Defense Interdiction SOP: Forward Defense Sector Alpha',
        'references_code': 'IA-CORPS-SOP-SECTOR-ALPHA-2025',
        'classification': 'CONFIDENTIAL // TACTICAL GROUND ROE',
        'tags': json.dumps(['army', 'convoy', 'sector alpha', 'border', 'fob', 'vehicles', 'interdiction', 'qrt', 'defile', 'kilo-4']),
        'content': (
            "1. TACTICAL BUFFER: A 12 km restricted border defense zone is active around Forward Operating Base (FOB) Alpha (32.55N, 74.80E). "
            "2. CONVOY THREAT CRITERIA: Detection of 2 or more tactical vehicles moving in cluster formation within 500 meters along "
            "unauthorized secondary tracks initiates Level-2 Combat Alert (+20 Convoy Threat Penalty). "
            "3. RESPONSE PROTOCOL: (a) Lock drone electro-optical tracking on lead vehicle; (b) Dispatch motorized Quick Reaction Team (QRT) "
            "to forward choke defile; (c) Jam tactical VHF/UHF command frequencies if unauthorized convoy approaches within 4 km of perimeter."
        )
    },
    {
        'id': 'DOC-ROE-06',
        'category': 'SIGINT_HISTORICAL',
        'title': 'Historical Signals Intelligence Dossier: Pass Kilo-4 Infiltration & Logistics Intercepts',
        'references_code': 'SIGINT-INTERCEPT-ALPHA-KILO4',
        'classification': 'SECRET // SIGINT ARCHIVE',
        'tags': json.dumps(['sigint', 'kilo-4', 'pass kilo', 'intercept', 'radio', 'weapons', 'border axis', 'convoy', '433.85', 'garuda']),
        'content': (
            "1. INTERCEPT ARCHIVE SUMMARY: Historical surveillance of Border Sector Alpha indicates adversary logistic cell "
            "'GARUDA-01' operates clandestine vehicle movements along mountain axis Pass Kilo-4 during new moon phases. "
            "2. SIGNAL CHARACTERISTICS: Intercepted burst transmissions on 433.85 MHz with signal strength >0.90 correlate with "
            "unmarked light utility trucks and all-terrain fuel bowsers. "
            "3. HISTORICAL PRECEDENT: Three previous night convoys observed at coordinates 32.55, 74.80 resulted in illicit weapons "
            "caches recovered by forward patrol units. Any RF detection on 433.85 MHz triggers immediate thermal drone cross-cueing."
        )
    },
    {
        'id': 'DOC-ROE-07',
        'category': 'UAV_TACTICAL',
        'title': 'Tactical UAV EO/IR Surveillance & Precision Target Verification SOP',
        'references_code': 'IAF-IA-UAV-SOP-2025-V2',
        'classification': 'CONFIDENTIAL // AIR RECON DOCTRINE',
        'tags': json.dumps(['uav', 'drone', 'precision', 'false positive', 'over-detection', 'aspect ratio', 'confidence', 'targeting', 'aerial']),
        'content': (
            "1. TARGET VERIFICATION CRITERIA: All tactical contacts identified via aerial drone optical/thermal sensors must satisfy "
            "physical geometry gating (vehicle aspect ratio <= 4.5, dimensions 10-110px at standard GSD) to prevent over-detection and "
            "false alarms from terrain shadows, painted road markings, and curbs. "
            "2. CONFIDENCE THRESHOLD GATING: Surveillance sweeps operate at 45% confidence floor to filter ground clutter. Kinetic "
            "targeting or artillery fire missions require >=65% verified confidence and multi-sensor correlation (optical + radar/SIGINT). "
            "3. PERSISTENCE REQUIREMENT: In dynamic video feeds, ground targets must maintain tracking lock across >=3 consecutive frames "
            "(temporal tracking consensus) before raising automated critical alerts."
        )
    },
    {
        'id': 'DOC-ROE-08',
        'category': 'AIRBASE_DEFENSE',
        'title': 'Military Airfield & FOB Air Defense Perimeter Security Directive',
        'references_code': 'HQ-IAF-BASE-DEF-SEC9',
        'classification': 'SECRET // AIR DEFENSE SOP',
        'tags': json.dumps(['airbase', 'airfield', 'fob', 'aircraft', 'runway', 'hangar', 'exclusion', 'jamming', 'drone']),
        'content': (
            "1. AIRSPACE GEOFENCE: A 15 km Vital Area (VA) / Vital Point (VP) air defense exclusion zone surrounds military airfields and forward bases. "
            "2. LOW-ALTITUDE UAV INTERCEPTION: Any unidentified unmanned aerial contact below 1,000 meters AGL is classified as hostile intent. "
            "Soft-kill RF counter-UAS directional jamming is authorized immediately. "
            "3. COMBAT AIRCRAFT DISPERSAL: When hostile aerial contacts breach the 10 km inner buffer, all alert fighters are scrambled "
            "or relocated to hardened aircraft shelters (HAS)."
        )
    }
]

def init_rag_knowledge_base():
    """Ensure database table exists and seed standard defense doctrine."""
    with get_db() as c:
        c.execute('''
        CREATE TABLE IF NOT EXISTS rag_knowledge_base(
            id TEXT PRIMARY KEY,
            category TEXT,
            title TEXT,
            content TEXT,
            references_code TEXT,
            classification TEXT DEFAULT 'SECRET',
            tags TEXT,
            created_at TEXT
        )''')
        
        now_iso = datetime.now(timezone.utc).isoformat()
        rows = [
            (
                d['id'], d['category'], d['title'], d['content'],
                d['references_code'], d['classification'], d['tags'], now_iso
            )
            for d in INITIAL_DOCTRINE_CORPUS
        ]
        c.executemany(
            '''INSERT OR REPLACE INTO rag_knowledge_base 
               (id, category, title, content, references_code, classification, tags, created_at) 
               VALUES (?,?,?,?,?,?,?,?)''',
            rows
        )
        c.commit()

def tokenize(text: str) -> List[str]:
    """Extract normalized alphanumeric word stems for local lexical retrieval."""
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return [w for w in clean.split() if len(w) > 2]

def search_knowledge_base(query: str, top_k: int = 3, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Hybrid lexical + bigram phrase-match scoring across local air-gapped doctrine chunks.

    Scoring weights:
      - Unigram title match:          +3.5 per token
      - Tag keyword match:            +4.5 per token
      - Unigram content match:        +1.0 per token
      - Bigram phrase in content:     +2.0 per phrase (consecutive word pair)
      - Bigram phrase in title:       +3.5 per phrase
      - BM25-style length normalise:  / sqrt(doc_len + 1)
    """
    init_rag_knowledge_base()
    q_tokens = set(tokenize(query))
    if not q_tokens:
        return []

    with get_db() as c:
        if category:
            rows = c.execute('SELECT * FROM rag_knowledge_base WHERE category = ?', (category,)).fetchall()
        else:
            rows = c.execute('SELECT * FROM rag_knowledge_base').fetchall()

    q_lower = query.lower()
    q_words = q_lower.split()

    results = []
    for r in rows:
        item = dict(r)
        title_tokens   = set(tokenize(item['title']))
        content_tokens = set(tokenize(item['content']))
        tags_list      = json.loads(item['tags'] or '[]')
        tags           = set(tags_list)

        title_overlap   = len(q_tokens.intersection(title_tokens))
        tag_overlap     = sum(1 for q in q_tokens if any(q in t for t in tags))
        content_overlap = len(q_tokens.intersection(content_tokens))

        # Bigram phrase-match bonus
        content_lower = item['content'].lower()
        title_lower   = item['title'].lower()
        phrase_bonus  = 0.0
        for i in range(len(q_words) - 1):
            bigram = q_words[i] + ' ' + q_words[i + 1]
            if bigram in content_lower:
                phrase_bonus += 2.0
            if bigram in title_lower:
                phrase_bonus += 3.5

        score = (title_overlap * 3.5) + (tag_overlap * 4.5) + (content_overlap * 1.0) + phrase_bonus
        doc_len = len(content_tokens) + 1
        normalized_score = score / math.sqrt(doc_len)

        if score > 0:
            results.append({
                'id': item['id'],
                'category': item['category'],
                'title': item['title'],
                'references_code': item['references_code'],
                'classification': item['classification'],
                'content': item['content'],
                'tags': tags_list,
                'relevance_score': round(float(normalized_score), 4)
            })

    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return results[:top_k]

def run_air_gapped_rag_advisor(query: str, operator: Optional[dict] = None) -> Dict[str, Any]:
    """Executes full RAG loop: Retrieves doctrine + fuses live situational context -> Generates tactical directive."""
    start_time = time.perf_counter()
    init_rag_knowledge_base()
    
    # 1. RETRIEVE: Get top relevant doctrine / RoE documents
    docs = search_knowledge_base(query, top_k=2)
    if not docs:
        docs = search_knowledge_base('dark vessel roe interdiction', top_k=2)

    primary_doc = docs[0] if docs else None
    sec_doc = docs[1] if len(docs) > 1 else None

    # 2. CONTEXT FUSION: Retrieve live situational picture from SQLite
    with get_db() as c:
        dark_vessels = c.execute('SELECT * FROM sar_detections WHERE is_dark_vessel = 1 LIMIT 3').fetchall()
        recent_zones = c.execute('SELECT * FROM zones LIMIT 4').fetchall()
        high_threats = c.execute('SELECT * FROM detections WHERE threat_score >= 60 LIMIT 3').fetchall()
        army_alerts = c.execute('SELECT * FROM army_feeds WHERE status = "ACTIVE" LIMIT 2').fetchall()

    dark_vessel_list = [dict(d) for d in dark_vessels]
    zone_list = [dict(z) for z in recent_zones]
    threat_list = [dict(t) for t in high_threats]
    army_list = [dict(a) for a in army_alerts]

    # 3. DOMAIN & TOPIC INTELLIGENCE SYNTHESIS
    q_lower = query.lower()

    # Topic Matchers
    is_hot_pursuit = any(k in q_lower for k in ['hot pursuit', 'unclos', 'article 111', 'mzi', 'legal', 'jurisdiction', 'third state', 'law'])
    is_mumbai_oda = any(k in q_lower for k in ['mumbai', 'oda', 'offshore', 'oil rig', 'platform', 'bombay high', 'pipeline', 'hydrocarbon'])
    is_malacca = any(k in q_lower for k in ['malacca', 'nicobar', '6-degree', 'chokepoint', 'anc', 'andaman', 'p8i', 'agi'])
    is_army_convoy = any(k in q_lower for k in ['convoy', 'sector alpha', 'fob', 'vehicle', 'qrt', 'defile', 'alpha'])
    is_sigint = any(k in q_lower for k in ['433', 'sigint', 'kilo-4', 'pass kilo', 'burst', 'garuda', 'intercept', 'radio'])
    is_uav_precision = any(k in q_lower for k in ['uav', 'drone', 'precision', 'false positive', 'over-detection', 'false alarm', 'verification', 'optical', 'recall'])

    # Format live target coordinates cleanly
    if dark_vessel_list:
        v0 = dark_vessel_list[0]
        vessel_str = f"SAR Dark Contact {v0['id']} ({v0['lat']:.2f} deg N, {v0['lon']:.2f} deg E) | RCS {v0.get('rcs_sigma0_db', -8.0)} dB"
    else:
        vessel_str = "Strategic Maritime Perimeter (Western Naval Command Sector)"

    # Synthesize tailored intelligence based on the exact query
    if is_hot_pursuit:
        directive_type = "LEGAL JURISDICTION & HOT PURSUIT DIRECTIVE"
        bluf = (
            "Under UNCLOS Article 111 and Section 4 of the Maritime Zones of India Act (1976), Indian naval and coast guard assets "
            "possess full sovereign authority to initiate and sustain hot pursuit against foreign vessels suspected of violating national laws. "
            "Pursuit must commence within internal waters, territorial sea (12 NM), or the contiguous zone (24 NM), must remain continuous "
            "via unbroken air/sea handover, and strictly terminates upon the vessel entering foreign territorial waters."
        )
        target_focus = "Suspect Foreign Vessel Defying Halt Orders"
        threat_tier = "LEGAL MANDATE // ACTIVE INTERDICTION"
        geofence_status = "Indian Territorial Sea (12 NM) / Contiguous Zone (24 NM)"
        sensor_correlation = "Continuous Radar Track & Visual Air-Sea Handover Log"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (0-5 MIN)",
                "action": "Broadcast formal lawful halt order over VHF Channel 16 citing UNCLOS Article 111 and Maritime Zones of India Act 1976.",
                "responsible": "Command Duty Officer / Tactical Watch"
            },
            {
                "step": 2,
                "priority": "TACTICAL LOGGING",
                "action": "Record precise GPS coordinates, timestamp, and radar tracking lock at the exact moment pursuit commences to establish legal continuity.",
                "responsible": "Navigation & Tactical Plotting Officer"
            },
            {
                "step": 3,
                "priority": "AIR HANDOVER",
                "action": "Dispatch maritime patrol aircraft (Dornier-228 / P-8I Neptune) to ensure continuous, unbroken tracking if surface vessels encounter range limits.",
                "responsible": "Air Operations Controller / INS Hansa"
            },
            {
                "step": 4,
                "priority": "INTERCEPTION & VBSS",
                "action": "Execute armed Visit, Board, Search, and Seizure (VBSS) once vessel is shadowed within 5 NM outside foreign territorial waters.",
                "responsible": "Naval Boarding Party Commander"
            }
        ]
        escalation_boundaries = [
            "Entering Foreign Waters: Hot pursuit MUST immediately cease the moment the suspect vessel crosses into the 12 NM territorial sea of its flag state or any third sovereign nation.",
            "Disabling Fire: Disabling fire directed at steering/propulsion requires authorization from Flag Officer Commanding (FOC) after formal audio/visual warning shots have failed."
        ]

    elif is_mumbai_oda:
        directive_type = "MUMBAI ODA CRITICAL ASSET DEFENSE DIRECTIVE"
        bluf = (
            "A mandatory 25 km defensive buffer is active around all hydrocarbon platforms and subsea pipeline networks in the Mumbai "
            "Offshore Development Area (ODA). Operating with dark (disabled) AIS within this perimeter constitutes an immediate Level-3 "
            "security breach, triggering a +30 Threat Score escalation, Fast Interceptor Craft (FIC) scramble, and naval helicopter reconnaissance."
        )
        target_focus = vessel_str
        threat_tier = "CRITICAL // OFFSHORE BUFFER BREACH"
        geofence_status = "Mumbai Offshore Development Area (25 km Exclusion Zone)"
        sensor_correlation = f"SAR Satellite Radar Contact + AIS Transponder Silencing ({len(dark_vessel_list)} dark contacts monitored)"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (0-5 MIN)",
                "action": "Challenge contact immediately on International Maritime VHF Channel 16 (156.800 MHz) and DSC Channel 70 demanding vessel manifest and identity.",
                "responsible": "Western Naval Command Joint Watch"
            },
            {
                "step": 2,
                "priority": "INTERCEPT SCRAMBLE",
                "action": "Dispatch Fast Interceptor Craft (FIC) or Immediate Support Vessel (ISV) from nearest naval base to shadow and intercept target.",
                "responsible": "Naval Base Operations Officer"
            },
            {
                "step": 3,
                "priority": "AERIAL RECON",
                "action": "Task INS Shikra naval air station to scramble armed Chetak or MH-60R helicopter for low-altitude optical and thermal identification.",
                "responsible": "Naval Air Squadron Duty Officer"
            },
            {
                "step": 4,
                "priority": "TACTICAL BOARDING",
                "action": "If target fails to respond within 10 minutes or loiters near platforms, deploy armed VBSS boarding party to inspect cargo and verify crew credentials.",
                "responsible": "Boarding Team Officer (VBSS)"
            }
        ]
        escalation_boundaries = [
            "Platform Proximity (<5 km): Any dark vessel approaching within 5 km of an offshore production platform is treated as hostile intent; armed interdiction authorized.",
            "Warning Shots: Warning shots across the bow require authorization from Flag Officer Commanding (FOC) Western Naval Command."
        ]

    elif is_malacca:
        directive_type = "STRATEGIC MARITIME CHOKEPOINT SURVEILLANCE DIRECTIVE"
        bluf = (
            "The 6-Degree Channel south of Great Nicobar is India's premier strategic monitoring gate into the Malacca Strait. "
            "Doctrine mandates 100% correlation of all vessels against Lloyd's Register. Any unflagged or dark contact exceeding 60 meters length "
            "or loitering near submarine transit routes must be immediately targeted with high-resolution P-8I Neptune radar scans and acoustic sonobuoy tracking."
        )
        target_focus = "Malacca Strait Approach / Nicobar 6-Degree Channel"
        threat_tier = "HIGH // CHOKEPOINT VULNERABILITY WATCH"
        geofence_status = "Andaman & Nicobar Command (ANC) Sovereign Maritime Corridor"
        sensor_correlation = "High-Resolution SAR Radar & Acoustic Surveillance Array"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (0-5 MIN)",
                "action": "Correlate radar return against regional AIS feeds, Lloyd's Register of Ships, and regional white-shipping agreements.",
                "responsible": "ANC Joint Operations Center (JOC Port Blair)"
            },
            {
                "step": 2,
                "priority": "RADAR SWEEP",
                "action": "Task P-8I Neptune maritime patrol aircraft for AN/APY-10 multi-mode synthetic aperture radar sweep and optical verification.",
                "responsible": "Air Operations Controller / INS Baaz"
            },
            {
                "step": 3,
                "priority": "ASW SCREENING",
                "action": "Deploy active/passive directional sonobuoys if target profile matches auxiliary intelligence ship (AGI) or sub-surface escort tender.",
                "responsible": "Airborne Tactical Officer (P-8I)"
            },
            {
                "step": 4,
                "priority": "SURFACE SHADOW",
                "action": "Task forward-deployed Offshore Patrol Vessel (OPV) or Corvette to establish continuous radar shadow along international transit boundary.",
                "responsible": "Naval Task Group Commander"
            }
        ]
        escalation_boundaries = [
            "International Transit Passage: Vessels navigating within the recognized transit passage lane cannot be impeded unless hostile actions or illegal surveys are confirmed.",
            "Sonobuoy Deployment: Authorized inside Indian territorial waters and EEZ; coordinated through Andaman & Nicobar Command."
        ]

    elif is_sigint:
        directive_type = "SIGNALS INTELLIGENCE & CLANDESTINE INTERCEPT DIRECTIVE"
        bluf = (
            "RF burst transmissions on 433.85 MHz with signal strength >0.90 correlate with adversary logistic cell 'GARUDA-01' "
            "operating clandestine supply operations along mountain axis Pass Kilo-4. SOP mandates immediate sensor cross-cueing: "
            "UAV thermal electro-optical sensors must instantly slew to coordinates (32.55°N, 74.80°E) to confirm vehicle signatures."
        )
        target_focus = "Pass Kilo-4 Mountain Axis (32.55°N, 74.80°E)"
        threat_tier = "HIGH // CLANDESTINE INFILTRATION ALERT"
        geofence_status = "Forward Defense Sector Alpha (12 km Tactical Buffer)"
        sensor_correlation = "SIGINT RF 433.85 MHz Emitter Triangulation + UAV Thermal Cross-Cue"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (0-5 MIN)",
                "action": "Slew high-altitude UAV gimbal sensors directly to the RF triangulation coordinates; engage FLIR thermal imaging.",
                "responsible": "Tactical UAV Flight Controller"
            },
            {
                "step": 2,
                "priority": "RF ANALYSIS",
                "action": "Capture and log RF waterfall spectrum on 433.85 MHz; extract packet modulation and burst frequency headers.",
                "responsible": "SIGINT Intercept Section Head"
            },
            {
                "step": 3,
                "priority": "GROUND AMBUSH",
                "action": "Alert forward infantry patrol elements along Pass Kilo-4 defile to block designated adversary egress routes.",
                "responsible": "Sector Alpha Battalion Commander"
            },
            {
                "step": 4,
                "priority": "CACHE RECOVERY",
                "action": "Dispatch combat engineer detachment with mine/metal detectors to search historical weapons cache coordinates.",
                "responsible": "Field Security Detachment Commander"
            }
        ]
        escalation_boundaries = [
            "Armed Confrontation: Hostile elements actively transporting weapons caches within restricted border buffer are subject to immediate detention or armed engagement under RoE Section 3.",
            "Electronic Jamming: Directional spot-jamming on 433.85 MHz authorized immediately to sever adversary command links."
        ]

    elif is_uav_precision:
        directive_type = "TACTICAL UAV AIRBORNE RECONNAISSANCE & VERIFICATION DIRECTIVE"
        bluf = (
            "High-altitude UAV reconnaissance requires strict physical geometry gating and multi-stage filtering to eliminate "
            "over-detection caused by terrain shadows, painted lines, and road curbs. Operational doctrine mandates aspect ratio limits (<=4.5:1), "
            "a 45% confidence floor for surveillance sweeps, and 3-frame temporal consensus before queuing automated military strike alerts."
        )
        target_focus = "Tactical Ground Target Callset (Vehicles, Aircraft, Defense Infrastructure)"
        threat_tier = "PRECISION GATING // OPERATIONAL PROTOCOL"
        geofence_status = "Tactical Reconnaissance Area of Interest (AOI)"
        sensor_correlation = "Multi-Class Neural Detector + Weighted Box Fusion (IoU 0.35) + Physical Sanity Filter"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (CALIBRATION)",
                "action": "Set UI confidence threshold to 45% (Tactical Clean) to suppress background terrain clutter while preserving tactical vehicle signatures.",
                "responsible": "Drone Sensor Operator / Image Analyst"
            },
            {
                "step": 2,
                "priority": "GEOMETRY GATING",
                "action": "Verify bounding boxes against physical dimensions: reject vehicle aspect ratios >4.5 (road lines/fences) and dimensions outside 10-110px.",
                "responsible": "Project Rakshak Vision Pipeline"
            },
            {
                "step": 3,
                "priority": "TEMPORAL TRACKING",
                "action": "Require target persistence across minimum 3 consecutive video frames via Kalman/ByteTrack filter before triggering priority alerts.",
                "responsible": "Automated C4ISR Tracking Subsystem"
            },
            {
                "step": 4,
                "priority": "FIRE MISSION QUEUING",
                "action": "For kinetic strike or artillery handover, require verified target confidence >=65% and secondary sensor correlation (optical + radar/SIGINT).",
                "responsible": "Tactical Fire Direction Officer"
            }
        ]
        escalation_boundaries = [
            "Low-Confidence (<45%) Target Engagement: Strictly prohibited for automated kinetic weapons release without human operator visual confirmation.",
            "Civilian Clutter Buffer: Targets within 200 meters of non-combatant residential structures require dual-officer visual verification."
        ]

    elif is_army_convoy:
        directive_type = "GROUND INTERDICTION & BORDER DEFENSE DIRECTIVE"
        bluf = (
            "A 12 km tactical buffer is active around Forward Operating Base (FOB) Alpha (32.55°N, 74.80°E). Detection of 2 or more "
            "tactical vehicles moving in cluster formation within 500 meters along unauthorized secondary tracks initiates a Level-2 "
            "Combat Alert (+20 Threat Score), authorizing UAV continuous thermal lock, motorized QRT dispatch, and defile interdiction."
        )
        target_focus = "Hostile Vehicle Convoy near FOB Alpha (32.55°N, 74.80°E)"
        threat_tier = "HIGH // TACTICAL CONVOY INTERDICTION"
        geofence_status = "Forward Operating Base Alpha (12 km Tactical Buffer)"
        sensor_correlation = f"UAV EO/IR Downlink + Ground Sensor Tripwire ({len(army_list)} active military contacts)"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (0-5 MIN)",
                "action": "Lock high-altitude UAV gimbal in continuous electro-optical and FLIR thermal tracking on the lead convoy vehicle.",
                "responsible": "Tactical UAV Pilot / Sensor Operator"
            },
            {
                "step": 2,
                "priority": "QRT DISPATCH",
                "action": "Scramble motorized Quick Reaction Team (QRT) with armored personnel carriers (APCs) to establish blocking position at Defile Kilo-4.",
                "responsible": "FOB Alpha Quick Reaction Team Commander"
            },
            {
                "step": 3,
                "priority": "C4ISR CROSS-CUE",
                "action": "Cross-verify vehicle movement against the SIGINT intercept database and border outpost sensor tripwires.",
                "responsible": "Battalion Intelligence Officer (S2)"
            },
            {
                "step": 4,
                "priority": "TACTICAL EW",
                "action": "If convoy breaches the 4 km inner perimeter, initiate tactical directional RF jamming on adversary VHF/UHF command frequencies.",
                "responsible": "Electronic Warfare Detachment Leader"
            }
        ]
        escalation_boundaries = [
            "Crossing Line of Control / Zero Line: Immediate kinetic engagement authorized under Forward Combat Rules of Engagement.",
            "Vehicle Disabling: Road-spike deployment and engine-block disabling fire authorized at designated defile chokepoints."
        ]

    else:
        # Default Maritime Naval RoE
        directive_type = "MARITIME AIR-SEA INTERDICTION DIRECTIVE"
        bluf = (
            f"Under Indian Navy Rules of Engagement (IN-ROE-2024-SEC-4.2), any surface vessel operating with disabled, spoofed, or non-transmitting "
            f"AIS transponders inside the Indian EEZ or security buffer must be immediately challenged on VHF Channel 16 and Channel 70 DSC. "
            f"Failure to respond within 10 minutes authorizes Fast Interceptor Craft (FIC) dispatch and aerial maritime patrol reconnaissance."
        )
        target_focus = vessel_str
        threat_tier = "HIGH // DARK AIS CONTACT IN SECURITY ZONE"
        geofence_status = f"{zone_list[0]['name'] if zone_list else 'Sovereign Coastal Zone'} (Active Defensive Buffer)"
        sensor_correlation = f"SAR Satellite Radar Contact + AIS Transponder Silencing ({len(dark_vessel_list)} dark contacts monitored)"
        action_plan = [
            {
                "step": 1,
                "priority": "IMMEDIATE (0-5 MIN)",
                "action": "Challenge contact immediately on International Maritime VHF Channel 16 (156.800 MHz) & DSC Channel 70 demanding vessel manifest and identity.",
                "responsible": "Command Duty Officer / Naval Watch"
            },
            {
                "step": 2,
                "priority": "INTERCEPT SCRAMBLE",
                "action": "Scramble Fast Interceptor Craft (FIC) or Immediate Support Vessel (ISV) from nearest naval base to shadow and intercept target.",
                "responsible": "Naval Base Operations Officer"
            },
            {
                "step": 3,
                "priority": "AERIAL PATROL",
                "action": "Authorize visual surveillance fly-by from maritime patrol aircraft (Dornier-228 / P-8I Neptune).",
                "responsible": "Air Operations Controller / INS Hansa"
            },
            {
                "step": 4,
                "priority": "TACTICAL VBSS",
                "action": "Prepare armed Visit, Board, Search and Seizure (VBSS) boarding party if target fails to respond within 10 minutes or alters course suspiciously.",
                "responsible": "Naval Boarding Party Commander"
            }
        ]
        escalation_boundaries = [
            "Warning Shots: Warning shots across the bow strictly require prior authorization from Flag Officer Commanding (FOC).",
            "Boarding Authorization: VBSS operations authorized under Section 4.2 once contact is shadowed within 5 nautical miles and radio timeout expires."
        ]

    dtg_now = datetime.now(timezone.utc).strftime('%d%H%MZ %b %Y').upper()
    callsign = operator.get('callsign', 'SOV-COMMAND') if operator else 'SOV-COMMAND'

    # Build beautifully formatted human-readable directive text
    directive_lines = [
        f"==================================================================",
        f"  PROJECT RAKSHAK 2.0 // SOVEREIGN TACTICAL C4ISR ADVISORY",
        f"==================================================================",
        f"DIRECTIVE TYPE : {directive_type}",
        f"AUTHORITY      : {primary_doc['title'] if primary_doc else 'Standard Indian Defense Doctrine'}",
        f"REFERENCE CODE : {primary_doc['references_code'] if primary_doc else 'IN-ROE-GENERAL'}",
        f"CLASSIFICATION : {primary_doc['classification'] if primary_doc else 'SECRET // RESTRICTED ROE'}",
        f"DTG GENERATED  : {dtg_now} (Air-Gapped Sovereign Reasoning Core)",
        f"OPERATOR       : {callsign} // CLEARANCE: TOP SECRET (EYES ONLY)",
        f"------------------------------------------------------------------",
        f"",
        f"[1] BOTTOM LINE UP FRONT (BLUF):",
        f"    {bluf}",
        f"",
        f"[2] SITUATIONAL APPRAISAL & SENSOR FUSION:",
        f"    * Target Contact    : {target_focus}",
        f"    * Threat Assessment : {threat_tier}",
        f"    * Monitored Geofence: {geofence_status}",
        f"    * Sensor Correlation: {sensor_correlation}",
        f"    * Active Databases  : {len(dark_vessel_list)} SAR dark vessels, {len(zone_list)} restricted zones, {len(threat_list)} optical contacts.",
        f"",
        f"[3] RETRIEVED DEFENSE DOCTRINE CLAUSES:",
        f"    Authority: {primary_doc['title'] if primary_doc else 'Indian Defense SOP'}",
        f"    Citation : {primary_doc['references_code'] if primary_doc else 'IN-ROE-2024'}",
        f"    Content  : \"{primary_doc['content'] if primary_doc else 'Standard Military Rules of Engagement apply.'}\"",
        f"",
        f"[4] AUTHORIZED OPERATIONAL ACTION CHECKLIST:",
    ]

    for item in action_plan:
        directive_lines.append(f"    [{item['step']}] [{item['priority']}] {item['action']}")
        directive_lines.append(f"        -> Responsible: {item['responsible']}")

    directive_lines.extend([
        f"",
        f"[5] RULES OF ENGAGEMENT & ESCALATION REDLINES:",
    ])
    for esc in escalation_boundaries:
        directive_lines.append(f"    * {esc}")

    directive_lines.extend([
        f"",
        f"==================================================================",
        f"  END OF TACTICAL DIRECTIVE // TRANSMIT VIA SECURE LINK ONLY",
        f"=================================================================="
    ])

    formatted_directive = "\n".join(directive_lines)

    # Simplified list of checklist strings for backwards compatibility
    simple_checklist = [f"{item['priority']}: {item['action']}" for item in action_plan]

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    citations = []
    for d in docs:
        citations.append({
            'citation_id': d.get('references_code', 'ROE-DOC'),
            'title': d.get('title', 'Military Doctrine'),
            'jurisdiction': 'Indian EEZ & Territorial Waters' if any(k in d.get('category', '') for k in ['MARITIME', 'CHOKEPOINT', 'NAVAL']) else 'Joint Ground Defense Command',
            'classification': d.get('classification', 'SECRET'),
            'relevance_score': f"{d.get('relevance_score', 1.0):.2f}",
            'text_snippet': d.get('content', '')
        })

    return {
        'query': query,
        'directive_type': directive_type,
        'dtg': dtg_now,
        'bluf': bluf,
        'operator_callsign': callsign,
        'operator': operator or {'callsign': 'COMMANDER', 'role': 'OPERATOR'},
        'retrieved_documents': docs,
        'citations': citations,
        'target_focus': target_focus,
        'threat_tier': threat_tier,
        'situation_assessment': {
            'target_focus': target_focus,
            'threat_tier': threat_tier,
            'geofence_status': geofence_status,
            'sensor_correlation': sensor_correlation,
            'summary': bluf
        },
        'action_plan': action_plan,
        'checklist': simple_checklist,
        'escalation_boundaries': escalation_boundaries,
        'doctrine_content': primary_doc['content'] if primary_doc else '',
        'directive': formatted_directive,
        'synthesized_directive': formatted_directive,
        'latency_ms': elapsed_ms,
        'classification': primary_doc['classification'] if primary_doc else 'SECRET // TACTICAL ROE',
        'active_context': {
            'dark_vessels_monitored': len(dark_vessel_list),
            'zones_monitored': len(zone_list),
            'high_threats_active': len(threat_list)
        }
    }
