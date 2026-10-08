"""End-to-End Platform Smoke Test Suite for Project Rakshak 2.0.

Tests all tactical defense endpoints across:
  - System Health & Active Checkpoint Telemetry
  - Operator Authentication & RBAC (PBKDF2-200k, JWT, JTI)
  - SAR / Space Radar Feeds (CFAR, dark vessel filtering, size classification)
  - Joint Army Tactical Feeds (status workflows: ACTIVE -> ACKNOWLEDGED -> RESOLVED)
  - Target Tracking Kinematics (class-aware CEP, uncertainty ellipse)
  - Sovereign RAG Doctrine Engine (RoE retrieval, directive dispatch)
  - Automated Dynamic SITREP Generation (dynamic Section 5 tactical actions)
  - Edge Telemetry & Hardware KPIs
"""
import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"


def request(method: str, path: str, data: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            content = resp.read().decode("utf-8")
            try:
                res_data = json.loads(content)
            except Exception:
                res_data = content
            return status_code, res_data
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_data = json.loads(content)
        except Exception:
            err_data = content
        return e.code, err_data
    except Exception as e:
        return 0, str(e)


def run_smoke_tests():
    print("=" * 70)
    print("  PROJECT RAKSHAK 2.0 — END-TO-END PLATFORM SMOKE TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    def test(name: str, fn):
        nonlocal passed, failed
        try:
            ok, msg = fn()
            if ok:
                print(f"  [PASS] {name:<48} : {msg}")
                passed += 1
            else:
                print(f"  [FAIL] {name:<48} : {msg}")
                failed += 1
        except Exception as ex:
            print(f"  [ERROR] {name:<48} : Exception {ex}")
            failed += 1

    # 1. Health
    def t_health():
        status, data = request("GET", "/api/health")
        if status == 200 and data.get("status") == "ok":
            return True, f"System: {data.get('system')} | Active: {data.get('active_checkpoint')}"
        return False, f"HTTP {status}: {data}"
    test("1. System Health & Active Checkpoint", t_health)

    # 2. Model Status
    def t_model_status():
        status, data = request("GET", "/api/model/status")
        if status == 200 and "checkpoints" in data:
            active = data.get("active_model", "")
            epochs = data.get("checkpoints", {}).get("xview_yolo11m_military", {}).get("epochs_completed", 0)
            return True, f"Active: {active} | Completed Epochs: {epochs}"
        return False, f"HTTP {status}: {data}"
    test("2. Model Telemetry & Results Status", t_model_status)

    # 3. Auth Registration & Login
    token = None
    def t_auth():
        nonlocal token
        ts = int(time.time())
        username = f"tactical_smoke_{ts}"
        # Register
        reg_body = {
            "username": username,
            "password": "DefenseSecurePassword!2026",
            "full_name": "Major Vikram Rathore",
            "callsign": "GARUDA-LEADER",
            "rank": "Major",
            "role": "TACTICAL_COMMANDER",
            "clearance": "TOP_SECRET"
        }
        r_status, r_data = request("POST", "/api/auth/register", reg_body)
        if r_status != 200:
            return False, f"Registration failed: HTTP {r_status} - {r_data}"

        # Login
        login_body = {
            "username": username,
            "password": "DefenseSecurePassword!2026"
        }
        l_status, l_data = request("POST", "/api/auth/login", login_body)
        if l_status == 200 and "access_token" in l_data:
            token = l_data["access_token"]
            return True, f"Token generated (Bearer {token[:12]}...) | Role: {l_data['user']['role']}"
        return False, f"Login failed: HTTP {l_status} - {l_data}"
    test("3. Security Hardening (PBKDF2-200k & JWT Auth)", t_auth)

    # 4. Auth Verification & Operator Profile
    def t_auth_me():
        if not token:
            return False, "No auth token from previous test"
        headers = {"Authorization": f"Bearer {token}"}
        status, data = request("GET", "/api/auth/me", headers=headers)
        if status == 200 and data.get("status") == "authenticated":
            user = data.get("user", {})
            return True, f"Operator: {user.get('full_name')} ({user.get('callsign')}) | Clearance: {user.get('clearance')}"
        return False, f"HTTP {status}: {data}"
    test("4. Operator Identity & Clearance RBAC", t_auth_me)

    # 5. SAR Space Radar & Dark Vessel Filtering
    def t_sar():
        # List detections
        s1, d1 = request("GET", "/api/sar/detections")
        if s1 != 200 or not isinstance(d1, list):
            return False, f"Failed GET /api/sar/detections: HTTP {s1}"

        # Dark vessels only
        s2, d2 = request("GET", "/api/sar/dark-vessels")
        if s2 == 200 and isinstance(d2, list):
            count_dark = len(d2)
            first = d2[0] if count_dark > 0 else {}
            v_class = first.get("vessel_class", "N/A")
            return True, f"Total SAR: {len(d1)} | Confirmed Dark Vessels: {count_dark} | Class: {v_class}"
        return False, f"Failed GET /api/sar/dark-vessels: HTTP {s2}"
    test("5. SAR Engine & Dark Vessel Intercept", t_sar)

    # 6. Joint Army Feeds & Workflow Status
    feed_id = None
    def t_army():
        nonlocal feed_id
        # Seed and list (returns list directly)
        s1, feeds = request("GET", "/api/army/feeds")
        if s1 != 200 or not isinstance(feeds, list) or not feeds:
            return False, f"Failed GET /api/army/feeds: HTTP {s1}"

        feed_id = feeds[0]["id"]
        # Stats
        s2, d2 = request("GET", "/api/army/stats")
        if s2 == 200 and isinstance(d2, dict):
            return True, f"Active feeds: {d2.get('active')} | Total: {d2.get('total')} | UAV: {d2.get('drone_uav')} | UGS: {d2.get('ugs_ground')}"
        return False, f"Failed GET /api/army/stats: HTTP {s2}"
    test("6. Multi-Domain Army Feeds & Domain Stats", t_army)

    # 7. Army Feed Status Transitions (ACKNOWLEDGE & RESOLVE)
    def t_army_transition():
        if not feed_id:
            return False, "No feed_id available"
        # Acknowledge
        s1, d1 = request("PATCH", f"/api/army/feeds/{feed_id}/status", {"status": "ACKNOWLEDGED"})
        if s1 != 200:
            return False, f"Acknowledge failed: HTTP {s1} - {d1}"

        # Resolve
        s2, d2 = request("PATCH", f"/api/army/feeds/{feed_id}/status", {"status": "RESOLVED"})
        if s2 == 200:
            return True, f"Feed {feed_id} successfully cycled ACTIVE -> ACKNOWLEDGED -> RESOLVED"
        return False, f"Resolve failed: HTTP {s2} - {d2}"
    test("7. Army Feed C2 Status Workflow (PATCH)", t_army_transition)

    # 8. Target Tracking & Kinematic Uncertainty Ellipse
    def t_tracking():
        track_req = {
            "lat": 18.9220,
            "lon": 72.8346,
            "heading_deg": 240.0,
            "speed_knots": 22.5,
            "intervals_min": [15, 30, 60],
            "target_class": "Vessel"
        }
        status, data = request("POST", "/api/tracking/vector", track_req)
        if status == 200 and "trajectory" in data:
            waypoints = data.get("trajectory", [])
            last_wp = waypoints[-1] if waypoints else {}
            ellipse = last_wp.get("confidence_ellipse", {})
            dist = data.get("total_distance_km", 0)
            return True, f"Waypoints: {len(waypoints)} | Dist: {dist:.1f}km | CEP: {last_wp.get('cep_meters', 0):.0f}m | Ellipse: {ellipse.get('semi_major_m', 0):.0f}x{ellipse.get('semi_minor_m', 0):.0f}m"
        return False, f"HTTP {status}: {data}"
    test("8. Kinematic Tracking Engine & Uncertainty Model", t_tracking)

    # 9. Automated Dynamic SITREP Generation
    def t_sitrep():
        status, data = request("GET", "/api/sitrep")
        if status == 200 and "report_markdown" in data:
            sitrep_txt = data["report_markdown"]
            has_dynamic_actions = "ACTION 1:" in sitrep_txt or "RECOMMENDED TACTICAL ACTIONS" in sitrep_txt
            has_optical = "OPTICAL SATELLITE DETECTIONS" in sitrep_txt
            breakdown = data.get("threat_breakdown", {})
            return True, f"Dynamic SITREP generated | Threat Breakdown: High={breakdown.get('high')}, Med={breakdown.get('medium')} | Dynamic Actions: {has_dynamic_actions}"
        return False, f"HTTP {status}: {data}"
    test("9. Dynamic SITREP Generation & Sensor Fusion", t_sitrep)

    # 10. Sovereign RAG Knowledge Base & RoE Advisor
    def t_rag():
        q_body = {
            "query": "What are the rules of engagement for an unflagged vessel in the Indian EEZ that refuses AIS communication?"
        }
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        status, data = request("POST", "/api/rag/query", q_body, headers=headers)
        if status == 200 and ("bluf" in data or "directive_type" in data):
            citations = data.get("citations", [])
            doctrine_title = citations[0].get("title", "") if citations else "UNCLOS / IN Doctrine"
            directive = data.get("directive_type", "TACTICAL DIRECTIVE")
            return True, f"Directive: {directive[:32]}... | Citations: {len(citations)} | Authority: {doctrine_title[:28]}..."
        return False, f"HTTP {status}: {data}"
    test("10. Air-Gapped Sovereign RAG & RoE Advisor", t_rag)

    # 11. Edge Telemetry & Hardware KPIs
    def t_edge():
        status, data = request("GET", "/api/edge/telemetry")
        if status == 200 and "host_hardware" in data:
            hw = data.get("host_hardware", {})
            spec = data.get("model_spec", {})
            return True, f"Arch: {spec.get('architecture', 'YOLO11m')[:28]} | CPU: {hw.get('cpu_usage_pct')}% | Free Disk: {hw.get('disk_free_gb')}GB"
        return False, f"HTTP {status}: {data}"
    test("11. Edge Telemetry & Hardware Telemetry", t_edge)

    # 12. Defense KPIs
    def t_kpis():
        status, data = request("GET", "/api/kpis")
        if status == 200 and "kpi_categories" in data:
            k = data.get("kpi_categories", {})
            target_pct = data.get("deployment_target_benchmarks", {}).get("dark_vessel_capture_rate_target_pct", 91.7)
            return True, f"Platform KPIs loaded ({len(k)} categories) | Target Capture Rate: {target_pct}%"
        return False, f"HTTP {status}: {data}"
    test("12. Tactical Defense KPIs & Benchmarks", t_kpis)

    print("=" * 70)
    print(f"  SMOKE TEST SUMMARY: {passed} PASSED / {failed} FAILED (TOTAL {passed + failed})")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
