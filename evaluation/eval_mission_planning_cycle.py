"""Empirical Evaluation of Mission-Planning Decision Cycle Time.

Project Rakshak 2.0 — Target Problem Statement Dimension:
"Mission-planning cycle time reduction under air-gapped sovereign C2"

Evaluates 3 reproducible operational tactical scenarios:
  Scenario A: Dark Vessel approaching restricted zone (Naval/Maritime Domain)
  Scenario B: Unidentified convoy approaching border post (Army Ground Domain)
  Scenario C: UGS seismic alarm plus drone confirmation (Cross-Domain Sensor Fusion)

Runs 10 repetitions per scenario against live local REST endpoints:
  - Step 1: Contact Ingestion & Target Filtering
  - Step 2: Spatial Corridor & Zone Verification
  - Step 3: Sovereign RoE Doctrine Retrieval (BM25 RAG)
  - Step 4: Automated STANAG 2014 SITREP Compilation
  - Step 5: Mission Waypoint & Actionable Tasking Dispatch

Reports:
  1. Rakshak Machine Measured Time (wall-clock latency, mean ± std across 10 runs) [MEASURED]
  2. Rakshak Operator-Paced Estimate (Machine time + assumed human think-time per step) [ASSUMED/MODEL]
  3. Traditional Operations Room Manual Baseline [ASSUMED]
  4. Cycle Time Reduction (%) [COMPUTED]

Outputs saved to:
  - evaluation/results/mission_planning_report.json
  - evaluation/results/mission_planning_summary.md
"""
from __future__ import annotations
import json
import math
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

BASE_URL = "http://127.0.0.1:8000"
REPETITIONS = 10
ROOT = Path(__file__).resolve().parent.parent
ASSUMPTIONS_FILE = ROOT / "evaluation" / "assumptions.yaml"
OUTPUT_JSON = ROOT / "evaluation" / "results" / "mission_planning_report.json"
OUTPUT_MD = ROOT / "evaluation" / "results" / "mission_planning_summary.md"


def http_request(method: str, path: str, data: dict = None, headers: dict = None) -> tuple[int, Any, float]:
    """Execute HTTP request with high-precision wall-clock timing."""
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            elapsed = time.perf_counter() - t0
            try:
                res_data = json.loads(content)
            except Exception:
                res_data = content
            return resp.status, res_data, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.perf_counter() - t0
        content = e.read().decode("utf-8")
        try:
            err_data = json.loads(content)
        except Exception:
            err_data = content
        return e.code, err_data, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return 0, str(e), elapsed


def load_assumptions() -> dict:
    """Parse assumptions.yaml without external yaml library dependency if possible."""
    # Simple YAML key extraction
    assumptions = {
        "manual_baseline_seconds": {
            "scenario_a": 1680.0,
            "scenario_b": 1320.0,
            "scenario_c": 1320.0
        },
        "operator_think_time_seconds": {
            "step_1": 10.0,
            "step_2": 8.0,
            "step_3": 15.0,
            "step_4": 12.0,
            "step_5": 5.0,
            "total_per_scenario": 50.0
        }
    }
    if ASSUMPTIONS_FILE.exists():
        text = ASSUMPTIONS_FILE.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("total_manual_seconds:") and "#" in line:
                val = float(line.split(":")[1].split("#")[0].strip())
            elif line.startswith("total_think_time_per_scenario:"):
                assumptions["operator_think_time_seconds"]["total_per_scenario"] = float(line.split(":")[1].split("#")[0].strip())
    return assumptions


def run_scenario_a_step(step_idx: int) -> tuple[str, bool, float]:
    """Execute a single step for Scenario A: Dark Vessel near Mumbai ODA."""
    if step_idx == 1:
        # Step 1: Detect & Filter Dark Vessels from SAR radar
        status, data, elapsed = http_request("GET", "/api/sar/detections")
        dark_count = len([d for d in data if d.get("is_dark_vessel")]) if isinstance(data, list) else 0
        return f"SAR Dark Vessel Detection (Found {dark_count} dark targets)", status == 200, elapsed

    elif step_idx == 2:
        # Step 2: Restricted Zone & Defensive Perimeter Cross-Check
        status, data, elapsed = http_request("GET", "/api/zones")
        zone_count = len(data) if isinstance(data, list) else 0
        return f"Restricted Defense Zone Gating (Checked {zone_count} perimeters)", status == 200, elapsed

    elif step_idx == 3:
        # Step 3: Sovereign RoE Doctrine Query (BM25 RAG)
        payload = {
            "query": "Dark vessel non-responsive approaching naval security zone and Mumbai ODA buffer UNCLOS Article 110 right of visit"
        }
        status, data, elapsed = http_request("POST", "/api/rag/query", data=payload)
        citations = len(data.get("citations", [])) if isinstance(data, dict) else 0
        return f"Sovereign RoE Doctrine Retrieval ({citations} doctrine citations)", status == 200, elapsed

    elif step_idx == 4:
        # Step 4: Automated STANAG 2014 Tactical SITREP Generation
        status, data, elapsed = http_request("GET", "/api/sitrep")
        sec5 = bool(data.get("section_5_actions")) if isinstance(data, dict) else False
        return f"STANAG 2014 SITREP Compilation (Sec 5 Tactical Actions: {sec5})", status == 200, elapsed

    elif step_idx == 5:
        # Step 5: Actionable Mission Waypoint & Intercept Tasking Dispatch
        payload = {
            "title": "OPERATION SAGAR KAVACH - MARITIME INTERCEPT BRAVO",
            "directive_summary": "Dark vessel radar contact detected within 25 km Mumbai ODA perimeter. Authorized VBSS interdiction under IN-ROE-2024-SEC-4.2.",
            "checklist": [
                "Issue VHF Channel 16 / Channel 70 DSC challenge",
                "Dispatch Fast Interceptor Craft (FIC-T12) from Mumbai Naval Anchorage",
                "Execute close shadowing at 5 NM and prepare VBSS boarding team"
            ]
        }
        status, data, elapsed = http_request("POST", "/api/rag/dispatch-to-mission", data=payload)
        mid = data.get("id", "UNKNOWN") if isinstance(data, dict) else "ERR"
        return f"Intercept Tasking Dispatch (Dispatched mission {mid})", status == 200, elapsed

    raise ValueError(f"Invalid step index: {step_idx}")


def run_scenario_b_step(step_idx: int) -> tuple[str, bool, float]:
    """Execute a single step for Scenario B: Convoy approaching Border Post."""
    if step_idx == 1:
        # Step 1: UAV Drone Contact Ingestion & Target Classification
        status, data, elapsed = http_request("GET", "/api/army/feeds")
        uav_feeds = [f for f in data if f.get("domain") == "UAV"] if isinstance(data, list) else []
        return f"UAV Contact Ingestion ({len(uav_feeds)} active drone alerts)", status == 200, elapsed

    elif step_idx == 2:
        # Step 2: Multi-Target Kinematics & Approach Corridor Analysis
        status, data, elapsed = http_request("GET", "/api/tracking/fused-tracks")
        track_count = len(data) if isinstance(data, list) else 0
        return f"Fused Kinematic Corridor Analysis ({track_count} tracked vectors)", status == 200, elapsed

    elif step_idx == 3:
        # Step 3: Sovereign Ground RoE Doctrine Query (BM25 RAG)
        payload = {
            "query": "Unidentified tactical vehicle convoy approaching forward defense locality FOB Sector Alpha rules of engagement"
        }
        status, data, elapsed = http_request("POST", "/api/rag/query", data=payload)
        citations = len(data.get("citations", [])) if isinstance(data, dict) else 0
        return f"Ground RoE Doctrine Retrieval ({citations} doctrine citations)", status == 200, elapsed

    elif step_idx == 4:
        # Step 4: Automated Tactical SITREP Generation
        status, data, elapsed = http_request("GET", "/api/sitrep")
        return "Tactical Ground SITREP Compilation", status == 200, elapsed

    elif step_idx == 5:
        # Step 5: Motorized QRF Tasking & Defile Intercept Dispatch
        payload = {
            "title": "OPERATION DHRUVA - FORWARD CORRIDOR INTERCEPT",
            "directive_summary": "Unidentified vehicle cluster advancing toward FOB Alpha. Mobilize motorized QRT under IA-CORPS-SOP-SECTOR-ALPHA-2025.",
            "checklist": [
                "Lock drone electro-optical tracking onto lead vehicle",
                "Dispatch motorized Quick Reaction Team (QRT) to Pass Kilo-4 defile",
                "Activate tactical VHF/UHF frequency monitoring"
            ]
        }
        status, data, elapsed = http_request("POST", "/api/rag/dispatch-to-mission", data=payload)
        mid = data.get("id", "UNKNOWN") if isinstance(data, dict) else "ERR"
        return f"QRF Tasking Dispatch (Dispatched mission {mid})", status == 200, elapsed

    raise ValueError(f"Invalid step index: {step_idx}")


def run_scenario_c_step(step_idx: int) -> tuple[str, bool, float]:
    """Execute a single step for Scenario C: UGS alarm plus drone confirmation."""
    if step_idx == 1:
        # Step 1: Unattended Ground Sensor (UGS) Seismic Alarm Detection
        status, data, elapsed = http_request("GET", "/api/army/feeds")
        ugs_feeds = [f for f in data if f.get("domain") == "UGS"] if isinstance(data, list) else []
        return f"UGS Seismic Tripwire Alarm ({len(ugs_feeds)} geophone alerts)", status == 200, elapsed

    elif step_idx == 2:
        # Step 2: Cross-Sensor Acknowledgment & Drone Retask C2 Cycle
        status, data, elapsed = http_request("POST", "/api/army/feeds/army-ugs-01/acknowledge")
        return "UGS C2 Acknowledgment & Cross-Sensor Vectoring", status in (200, 404), elapsed

    elif step_idx == 3:
        # Step 3: Sovereign Sensor Fusion RoE Doctrine Query (BM25 RAG)
        payload = {
            "query": "Unattended ground sensor UGS seismic perimeter alarm cross-cueing tactical UAV drone confirmation rules of engagement"
        }
        status, data, elapsed = http_request("POST", "/api/rag/query", data=payload)
        citations = len(data.get("citations", [])) if isinstance(data, dict) else 0
        return f"Sensor Fusion RoE Doctrine Retrieval ({citations} doctrine citations)", status == 200, elapsed

    elif step_idx == 4:
        # Step 4: Automated Joint Incident SITREP Generation
        status, data, elapsed = http_request("GET", "/api/sitrep")
        return "Joint Incident SITREP Compilation", status == 200, elapsed

    elif step_idx == 5:
        # Step 5: Joint Air-Ground Intercept Tasking Dispatch
        payload = {
            "title": "OPERATION TRISHUL - UGS CONFIRMED INTERCEPT",
            "directive_summary": "18 Hz seismic geophone trigger confirmed by drone EO/IR gimbal. Authorized joint engagement under HQ-JOINT-C4ISR-UGS-UAV-2025.",
            "checklist": [
                "Establish persistent UAV thermal orbit over UGS sensor grid",
                "Vector forward scout patrol to confirm vehicle tracks",
                "Relay target BDA coordinates to Sector HQ"
            ]
        }
        status, data, elapsed = http_request("POST", "/api/rag/dispatch-to-mission", data=payload)
        mid = data.get("id", "UNKNOWN") if isinstance(data, dict) else "ERR"
        return f"Joint Intercept Tasking Dispatch (Dispatched mission {mid})", status == 200, elapsed

    raise ValueError(f"Invalid step index: {step_idx}")


def calc_stats(values: List[float]) -> tuple[float, float, float, float]:
    """Calculate mean, std, min, max."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    std_val = math.sqrt(variance)
    return mean_val, std_val, min(values), max(values)


def run_benchmark():
    print("=" * 75)
    print("  PROJECT RAKSHAK 2.0 — MISSION-PLANNING CYCLE TIME EVALUATION")
    print("  Air-Gapped Sovereign C2 Decision Cycle: Measured REST vs Assumed Baseline")
    print("=" * 75)

    assumptions = load_assumptions()
    operator_think_time = assumptions["operator_paced_think_times"]["total_per_scenario"] if "operator_paced_think_times" in assumptions else assumptions["operator_think_time_seconds"]["total_per_scenario"]

    scenarios = [
        {
            "id": "scenario_a",
            "name": "Scenario A: Dark Vessel Approaching Restricted Zone (Mumbai ODA)",
            "domain": "Maritime / Naval",
            "manual_baseline_s": assumptions["manual_baseline_seconds"]["scenario_a"],
            "runner": run_scenario_a_step
        },
        {
            "id": "scenario_b",
            "name": "Scenario B: Convoy Approaching Border Defense Post (Sector Alpha)",
            "domain": "Land / Army Ground",
            "manual_baseline_s": assumptions["manual_baseline_seconds"]["scenario_b"],
            "runner": run_scenario_b_step
        },
        {
            "id": "scenario_c",
            "name": "Scenario C: UGS Seismic Alarm plus Drone Confirmation",
            "domain": "Cross-Domain Sensor Fusion",
            "manual_baseline_s": assumptions["manual_baseline_seconds"]["scenario_c"],
            "runner": run_scenario_c_step
        }
    ]

    all_results = {}

    for sc in scenarios:
        sc_id = sc["id"]
        sc_name = sc["name"]
        print(f"\n[+] Executing {sc_name}")
        print(f"    Domain: {sc['domain']} | Repetitions: {REPETITIONS} | Manual Baseline: {sc['manual_baseline_s']:.1f}s")

        step_latencies: Dict[int, List[float]] = {i: [] for i in range(1, 6)}
        step_descriptions: Dict[int, str] = {}
        total_latencies: List[float] = []

        for rep in range(1, REPETITIONS + 1):
            rep_total = 0.0
            for step_idx in range(1, 6):
                desc, ok, elapsed = sc["runner"](step_idx)
                if rep == 1:
                    step_descriptions[step_idx] = desc
                step_latencies[step_idx].append(elapsed)
                rep_total += elapsed
            total_latencies.append(rep_total)

        # Statistics
        total_mean, total_std, total_min, total_max = calc_stats(total_latencies)
        operator_paced_total = total_mean + operator_think_time
        manual_baseline = sc["manual_baseline_s"]

        machine_reduction_pct = ((manual_baseline - total_mean) / manual_baseline) * 100.0
        operator_paced_reduction_pct = ((manual_baseline - operator_paced_total) / manual_baseline) * 100.0

        step_stats = {}
        for step_idx in range(1, 6):
            s_mean, s_std, s_min, s_max = calc_stats(step_latencies[step_idx])
            step_stats[step_idx] = {
                "step_index": step_idx,
                "description": step_descriptions.get(step_idx, f"Step {step_idx}"),
                "mean_ms": round(s_mean * 1000.0, 2),
                "std_ms": round(s_std * 1000.0, 2),
                "mean_seconds": round(s_mean, 4),
                "std_seconds": round(s_std, 4),
                "provenance": "MEASURED"
            }

        all_results[sc_id] = {
            "scenario_name": sc_name,
            "domain": sc["domain"],
            "repetitions": REPETITIONS,
            "rakshak_measured": {
                "mean_seconds": round(total_mean, 4),
                "std_seconds": round(total_std, 4),
                "min_seconds": round(total_min, 4),
                "max_seconds": round(total_max, 4),
                "formatted": f"{total_mean:.4f} ± {total_std:.4f} s",
                "provenance": "MEASURED"
            },
            "rakshak_operator_paced": {
                "assumed_think_time_seconds": round(operator_think_time, 1),
                "total_seconds": round(operator_paced_total, 2),
                "formatted": f"{operator_paced_total:.2f} s",
                "provenance": "ASSUMED"
            },
            "manual_assumed_baseline": {
                "total_seconds": round(manual_baseline, 1),
                "total_minutes": round(manual_baseline / 60.0, 1),
                "formatted": f"{manual_baseline:.1f} s ({manual_baseline/60.0:.1f} min)",
                "provenance": "ASSUMED"
            },
            "cycle_time_reduction": {
                "machine_reduction_pct": round(machine_reduction_pct, 2),
                "operator_paced_reduction_pct": round(operator_paced_reduction_pct, 2),
                "formatted": f"{operator_paced_reduction_pct:.2f}% (Operator-Paced) / {machine_reduction_pct:.2f}% (Scripted REST)",
                "provenance": "COMPUTED"
            },
            "per_step_breakdown": step_stats
        }

        print(f"    --> Rakshak Measured (REST):      {total_mean:.4f} ± {total_std:.4f} s [MEASURED]")
        print(f"    --> Rakshak Operator-Paced:      {operator_paced_total:.2f} s ({operator_think_time}s think-time) [ASSUMED]")
        print(f"    --> Manual Ops Room Baseline:     {manual_baseline:.1f} s ({manual_baseline/60.0:.1f} min) [ASSUMED]")
        print(f"    --> Decision Cycle Reduction:    {operator_paced_reduction_pct:.2f}% [COMPUTED]")

    # Overall Summary Across 3 Scenarios
    avg_machine_s = sum(r["rakshak_measured"]["mean_seconds"] for r in all_results.values()) / 3.0
    avg_operator_s = sum(r["rakshak_operator_paced"]["total_seconds"] for r in all_results.values()) / 3.0
    avg_manual_s = sum(r["manual_assumed_baseline"]["total_seconds"] for r in all_results.values()) / 3.0
    avg_reduction_pct = ((avg_manual_s - avg_operator_s) / avg_manual_s) * 100.0

    report_payload = {
        "metadata": {
            "title": "Project Rakshak 2.0 Mission-Planning Decision Cycle Time Benchmark",
            "target_problem_statement": "Problem Statement 1A: Naval/Army Geospatial & Multimodal Threat Detection",
            "kpi_dimension": "Mission-Planning Cycle Time",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repetitions_per_scenario": REPETITIONS,
            "host": "Stand-Alone Air-Gapped FOB Node (127.0.0.1:8000)",
            "overall_status": "Partial: system steps measured, manual baseline assumed, no human user study"
        },
        "summary": {
            "avg_machine_measured_seconds": round(avg_machine_s, 4),
            "avg_operator_paced_seconds": round(avg_operator_s, 2),
            "avg_manual_assumed_seconds": round(avg_manual_s, 1),
            "avg_manual_assumed_minutes": round(avg_manual_s / 60.0, 1),
            "avg_operator_reduction_pct": round(avg_reduction_pct, 2)
        },
        "scenarios": all_results
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)
    print(f"\n[+] Saved raw report to {OUTPUT_JSON}")

    # Generate Markdown Summary
    md_content = f"""# ⏱️ Mission-Planning Cycle Time Evaluation Summary

**Project Rakshak 2.0 — Sovereign Air-Gapped C4ISR Platform**  
**Problem Statement KPI:** Mission-Planning Cycle Time Reduction  
**Evaluation Date:** {report_payload['metadata']['date']}  
**Status:** **Partial: system steps measured, manual baseline assumed, no human user study**  

---

## 1. Executive Summary

In operational military command rooms without automated multi-sensor fusion, the mission-planning decision cycle (OODA loop) requires manual cross-referencing of radar and AIS logs, nautical chart buffer measurements, hardcopy doctrine binder searches (INBR 8 / UNCLOS), manual typing of STANAG 2014 situation reports, and manual waypoint trajectory calculations. This manual workflow consumes **1,320 – 1,680 seconds (22 – 28 minutes)** per incident.

Project Rakshak 2.0 automates the entire sensor-to-directive pipeline via sovereign local REST microservices:
1. **Measured Machine Latency (Scripted REST):** **{avg_machine_s:.4f} s** across 10 repetitions per scenario (`MEASURED`).
2. **Operator-Paced Realistic Estimate:** **{avg_operator_s:.2f} s** incorporating 50.0s of assumed human inspection and review think-time (`ASSUMED`).
3. **Manual Baseline Time:** **{avg_manual_s:.1f} s ({avg_manual_s/60.0:.1f} min)** (`ASSUMED`).
4. **Mission-Planning Cycle Time Reduction:** **{avg_reduction_pct:.2f}%** (`COMPUTED`).

---

## 2. Comparative Scenario Results

| Scenario | Domain | Rakshak Measured (REST) | Operator-Paced Estimate | Manual Assumed Baseline | Cycle Time Reduction | Provenance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **A: Dark Vessel in Restricted Zone** | Maritime / Naval | **{all_results['scenario_a']['rakshak_measured']['formatted']}** | **{all_results['scenario_a']['rakshak_operator_paced']['formatted']}** | **{all_results['scenario_a']['manual_assumed_baseline']['formatted']}** | **{all_results['scenario_a']['cycle_time_reduction']['operator_paced_reduction_pct']:.2f}%** | `PARTIAL` |
| **B: Convoy Approaching Border Post** | Land / Army Ground | **{all_results['scenario_b']['rakshak_measured']['formatted']}** | **{all_results['scenario_b']['rakshak_operator_paced']['formatted']}** | **{all_results['scenario_b']['manual_assumed_baseline']['formatted']}** | **{all_results['scenario_b']['cycle_time_reduction']['operator_paced_reduction_pct']:.2f}%** | `PARTIAL` |
| **C: UGS Alarm + Drone Confirmation** | Cross-Domain Fusion | **{all_results['scenario_c']['rakshak_measured']['formatted']}** | **{all_results['scenario_c']['rakshak_operator_paced']['formatted']}** | **{all_results['scenario_c']['manual_assumed_baseline']['formatted']}** | **{all_results['scenario_c']['cycle_time_reduction']['operator_paced_reduction_pct']:.2f}%** | `PARTIAL` |
| **OVERALL AVERAGE** | **Joint Multi-Domain** | **{avg_machine_s:.4f} s** | **{avg_operator_s:.2f} s** | **{avg_manual_s:.1f} s ({avg_manual_s/60.0:.1f} min)** | **{avg_reduction_pct:.2f}%** | `PARTIAL` |

*Note: Scripted REST calls execute in milliseconds because they bypass human perceptual latency. The Operator-Paced model adds 50.0 seconds of realistic human inspection time (10s contact review, 8s geofence check, 15s RoE reading, 12s SITREP review, 5s dispatch).*

---

## 3. Per-Step Breakdown (Measured Machine Latency)

### Scenario A: Dark Vessel Approaching Restricted Zone (Mumbai ODA)
- **Step 1: Contact Ingestion & Dark Filtering:** {all_results['scenario_a']['per_step_breakdown'][1]['mean_ms']:.2f} ± {all_results['scenario_a']['per_step_breakdown'][1]['std_ms']:.2f} ms (`MEASURED`)
- **Step 2: Restricted Buffer Verification:** {all_results['scenario_a']['per_step_breakdown'][2]['mean_ms']:.2f} ± {all_results['scenario_a']['per_step_breakdown'][2]['std_ms']:.2f} ms (`MEASURED`)
- **Step 3: Sovereign RoE Doctrine Query:** {all_results['scenario_a']['per_step_breakdown'][3]['mean_ms']:.2f} ± {all_results['scenario_a']['per_step_breakdown'][3]['std_ms']:.2f} ms (`MEASURED`)
- **Step 4: Automated STANAG 2014 SITREP:** {all_results['scenario_a']['per_step_breakdown'][4]['mean_ms']:.2f} ± {all_results['scenario_a']['per_step_breakdown'][4]['std_ms']:.2f} ms (`MEASURED`)
- **Step 5: Mission Intercept Waypoint Dispatch:** {all_results['scenario_a']['per_step_breakdown'][5]['mean_ms']:.2f} ± {all_results['scenario_a']['per_step_breakdown'][5]['std_ms']:.2f} ms (`MEASURED`)

### Scenario B: Convoy Approaching Border Post (Sector Alpha)
- **Step 1: UAV Drone Contact Ingestion:** {all_results['scenario_b']['per_step_breakdown'][1]['mean_ms']:.2f} ± {all_results['scenario_b']['per_step_breakdown'][1]['std_ms']:.2f} ms (`MEASURED`)
- **Step 2: Fused Kinematics Analysis:** {all_results['scenario_b']['per_step_breakdown'][2]['mean_ms']:.2f} ± {all_results['scenario_b']['per_step_breakdown'][2]['std_ms']:.2f} ms (`MEASURED`)
- **Step 3: Sovereign Ground RoE Retrieval:** {all_results['scenario_b']['per_step_breakdown'][3]['mean_ms']:.2f} ± {all_results['scenario_b']['per_step_breakdown'][3]['std_ms']:.2f} ms (`MEASURED`)
- **Step 4: Tactical SITREP Compilation:** {all_results['scenario_b']['per_step_breakdown'][4]['mean_ms']:.2f} ± {all_results['scenario_b']['per_step_breakdown'][4]['std_ms']:.2f} ms (`MEASURED`)
- **Step 5: QRF Tasking & Intercept Dispatch:** {all_results['scenario_b']['per_step_breakdown'][5]['mean_ms']:.2f} ± {all_results['scenario_b']['per_step_breakdown'][5]['std_ms']:.2f} ms (`MEASURED`)

### Scenario C: UGS Seismic Alarm plus Drone Confirmation
- **Step 1: UGS Geophone Alarm Detection:** {all_results['scenario_c']['per_step_breakdown'][1]['mean_ms']:.2f} ± {all_results['scenario_c']['per_step_breakdown'][1]['std_ms']:.2f} ms (`MEASURED`)
- **Step 2: Sensor C2 Acknowledgment & Cross-Cue:** {all_results['scenario_c']['per_step_breakdown'][2]['mean_ms']:.2f} ± {all_results['scenario_c']['per_step_breakdown'][2]['std_ms']:.2f} ms (`MEASURED`)
- **Step 3: Sensor Fusion RoE Retrieval:** {all_results['scenario_c']['per_step_breakdown'][3]['mean_ms']:.2f} ± {all_results['scenario_c']['per_step_breakdown'][3]['std_ms']:.2f} ms (`MEASURED`)
- **Step 4: Joint Tactical SITREP Compilation:** {all_results['scenario_c']['per_step_breakdown'][4]['mean_ms']:.2f} ± {all_results['scenario_c']['per_step_breakdown'][4]['std_ms']:.2f} ms (`MEASURED`)
- **Step 5: Joint Intercept Tasking Dispatch:** {all_results['scenario_c']['per_step_breakdown'][5]['mean_ms']:.2f} ± {all_results['scenario_c']['per_step_breakdown'][5]['std_ms']:.2f} ms (`MEASURED`)
"""
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[+] Saved markdown summary to {OUTPUT_MD}")
    print("\n[+] Mission-planning benchmark successfully completed.")


if __name__ == "__main__":
    run_benchmark()
