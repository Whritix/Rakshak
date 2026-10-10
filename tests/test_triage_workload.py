"""Test Suite for Defense Auto-Triage & Workload Reduction — Project Rakshak 2.0.

Verifies:
1. Reopen is sticky across re-runs (never re-closed by automated sweeps).
2. Zero duplicate audit rows in SQLite WAL table.
3. RBAC role restrictions on operator overrides.
4. Explainable auto-close rules per class (infrastructure, isolated transient, convoy prohibited).
5. Seeded Safety Ground-Truth Adversarial & Spoofing Test Suite:
   - Case A: AIS Position Spoofing (coordinate deviation > 1500m)
   - Case B: Vessel in Restricted Exclusion Buffer Zone (Geofence Breach)
   - Case C: Implausible Kinematics (Speed violation > physical ceiling)
   - Case D: Stale AIS Heartbeat (> 4 hours age)
   - Case E: Confirmed Dark Vessel (AIS silenced)
   - Case F: Benign Cooperative Vessel (Control)
   - Confirms Missed Threat Rate = 0.0%.
"""
import sys
import math
import unittest
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.db import get_db, init_database
from backend.app.triage_service import (
    evaluate_contact,
    verify_safety_anomalies,
    execute_triage_cycle,
    reopen_triaged_item,
    get_audit_trail,
    consolidate_detections_into_entities,
    load_triage_config,
    db_session
)


class TestTriageWorkload(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()
        cls.cfg = load_triage_config()

    def test_1_sticky_reopen_across_reruns(self):
        """Test that once an operator reopens an item, subsequent triage runs never re-close it."""
        test_id = f"test-sticky-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with db_session() as c:
            c.execute("""
                INSERT OR REPLACE INTO detections (
                    id, source, image_name, kind, confidence, threat_score, threat_level,
                    ais_status, mmsi, review_status, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (test_id, 'Radar', 'test_scene.tif', 'Vessel', 0.92, 20, 'LOW', 'matched', '419009999', 'auto_closed', now_iso))
            c.execute("""
                INSERT OR REPLACE INTO auto_triage_audit (
                    id, item_id, source_type, scene_or_source, kind, threat_score, threat_level,
                    triage_action, status, matched_identity, reason, triaged_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (uuid.uuid4().hex, test_id, 'OPTICAL_DETECTION', 'test_scene.tif', 'Vessel', 20, 'LOW', 'AUTO_CLOSED', 'CLOSED', '419009999', 'Routine cooperative vessel', now_iso))
            c.commit()

        # Operator overrides and reopens the item
        res = reopen_triaged_item(test_id, operator='CDR_VIKRAM', reason='Suspicious deck cargo spotted', operator_role='COMMANDER')
        self.assertTrue(res['success'])
        self.assertEqual(res['record']['status'], 'REOPENED')

        # Re-execute triage cycle
        cycle = execute_triage_cycle(persist_audit=True)
        self.assertEqual(cycle['status'], 'COMPLETED')

        # Verify audit status remains REOPENED
        trail = get_audit_trail(limit=100)
        matching = [t for t in trail if t['item_id'] == test_id]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]['status'], 'REOPENED', "Sticky override failed: item was re-closed by triage sweep!")

    def test_2_no_duplicate_audit_rows(self):
        """Test that multiple triage sweeps update existing records without creating duplicates."""
        test_id = f"test-dedup-{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with db_session() as c:
            c.execute("""
                INSERT OR REPLACE INTO detections (
                    id, source, image_name, kind, confidence, threat_score, threat_level,
                    ais_status, mmsi, review_status, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (test_id, 'Radar', 'test_scene.tif', 'Vessel', 0.95, 20, 'LOW', 'matched', '419008888', 'pending', now_iso))
            c.commit()

        # Run 3 consecutive triage sweeps
        execute_triage_cycle(persist_audit=True)
        execute_triage_cycle(persist_audit=True)
        execute_triage_cycle(persist_audit=True)

        with db_session() as c:
            rows = c.execute("SELECT COUNT(*) FROM auto_triage_audit WHERE item_id = ?", (test_id,)).fetchone()
            count = rows[0]

        self.assertEqual(count, 1, f"Found {count} duplicate audit rows for item_id {test_id}!")

    def test_3_rbac_role_restriction(self):
        """Test that unauthorized roles cannot override triage decisions."""
        test_id = f"test-rbac-{uuid.uuid4().hex[:8]}"
        # Unauthorized guest role should be rejected
        unauth_res = reopen_triaged_item(test_id, operator='GuestUser', reason='Unauthorized click', operator_role='GUEST')
        self.assertFalse(unauth_res['success'])
        self.assertEqual(unauth_res.get('status_code'), 403)

        # Authorized analyst role should be accepted
        auth_res = reopen_triaged_item(test_id, operator='MajRajesh', reason='Valid analyst triage', operator_role='ANALYST')
        # Even if item not in detections, role check passes (fails with 404 not 403)
        self.assertNotEqual(auth_res.get('status_code'), 403)

    def test_4_auto_close_rules_per_class(self):
        """Test class-specific explainable auto-close policies."""
        # 1. Verified known static infrastructure (with multi-temporal baseline) -> AUTO_CLOSED
        infra_eval = evaluate_contact(
            item_id="inf-001",
            threat_score=25,
            ais_status="unknown",
            kind="Infrastructure",
            contact_meta={"is_in_geofence": False, "is_convoy": False, "is_known_static": True},
            cfg=self.cfg
        )
        self.assertEqual(infra_eval['triage_action'], 'AUTO_CLOSED')
        self.assertIn("Known static baseline infrastructure", infra_eval['reason'])

        # 2. Single-pass infrastructure WITHOUT multi-pass baseline -> HUMAN_REVIEW (Class-based static assumption removed)
        infra_single_pass = evaluate_contact(
            item_id="inf-single-002",
            threat_score=25,
            ais_status="unknown",
            kind="Infrastructure",
            contact_meta={"is_in_geofence": False, "is_convoy": False, "is_known_static": False},
            cfg=self.cfg
        )
        self.assertEqual(infra_single_pass['triage_action'], 'HUMAN_REVIEW', "Single pass infrastructure without historical baseline must NOT auto-close!")

        # 3. Aircraft WITHOUT matched transponder -> HUMAN_REVIEW (Strictly barred from uncooperative auto-close)
        aircraft_eval = evaluate_contact(
            item_id="air-001",
            threat_score=20,
            ais_status="unknown",
            kind="Aircraft",
            contact_meta={"is_in_geofence": False},
            cfg=self.cfg
        )
        self.assertEqual(aircraft_eval['triage_action'], 'HUMAN_REVIEW', "Aircraft without transponder match must NOT auto-close!")

        # 4. Transient isolated low-confidence vehicle observation -> AUTO_CLOSED
        trans_eval = evaluate_contact(
            item_id="trans-001",
            threat_score=30,
            ais_status="unknown",
            kind="Vehicle",
            contact_meta={"confidence": 0.38, "is_in_geofence": False, "is_convoy": False, "reobserved_count": 1},
            cfg=self.cfg
        )
        self.assertEqual(trans_eval['triage_action'], 'AUTO_CLOSED')
        self.assertIn("Transient isolated low-confidence", trans_eval['reason'])

        # 5. Military Convoy -> STRICTLY PROHIBITED FROM AUTO-CLOSURE
        convoy_eval = evaluate_contact(
            item_id="mil-convoy-001",
            threat_score=30,
            ais_status="unknown",
            kind="Military Vehicle Convoy",
            contact_meta={"is_convoy": True},
            cfg=self.cfg
        )
        self.assertNotEqual(convoy_eval['triage_action'], 'AUTO_CLOSED')
        self.assertEqual(convoy_eval['triage_action'], 'ESCALATED_PRIORITY')

    def test_5_safety_spoofing_and_adversarial_suite(self):
        """Seeded ground-truth adversarial threat scenarios: verify 0.0% missed threat rate."""
        now_utc = datetime.now(timezone.utc)
        scenarios = [
            # Case 1: AIS Position Spoofing (Reported position deviates 12 km from radar centroid)
            {
                "case_name": "AIS Position Spoofing",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "threat-spoofer-01",
                    "threat_score": 25,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419001122",
                    "lat": 18.9100, "lon": 72.8400,
                    "ais_lat": 18.8000, "ais_lon": 72.7500, # ~15 km deviation
                    "speed_knots": 14.0,
                    "is_in_geofence": False
                }
            },
            # Case 2: Vessel Navigating Inside Restricted Exclusion Zone (Geofence Breach)
            {
                "case_name": "Vessel in Restricted Buffer Zone",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "threat-geofence-02",
                    "threat_score": 30,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419002233",
                    "lat": 14.8200, "lon": 74.1300,
                    "is_in_geofence": True,
                    "geofence_name": "INS Kadamba Naval Exclusion Zone"
                }
            },
            # Case 3: Implausible Kinematics (Cargo ship speed 58 knots)
            {
                "case_name": "Implausible Kinematics",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "threat-kinematics-03",
                    "threat_score": 25,
                    "ais_status": "matched",
                    "kind": "Merchant / Corvette",
                    "matched_identity": "419003344",
                    "lat": 19.1000, "lon": 72.5000,
                    "speed_knots": 58.5, # Impossible for commercial merchant
                    "is_in_geofence": False
                }
            },
            # Case 4: Stale AIS Heartbeat (Transmission is 7 hours old)
            {
                "case_name": "Stale AIS Heartbeat",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "threat-stale-04",
                    "threat_score": 25,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419004455",
                    "lat": 19.2000, "lon": 72.4000,
                    "heartbeat_age_hours": 7.0,
                    "is_in_geofence": False
                }
            },
            # Case 5: Confirmed Dark Vessel (No AIS transponder)
            {
                "case_name": "True Dark Vessel",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "threat-dark-05",
                    "threat_score": 25,
                    "ais_status": "unmatched",
                    "kind": "Vessel",
                    "matched_identity": None,
                    "lat": 19.3000, "lon": 72.3000,
                    "is_in_geofence": False
                }
            },
            # Case 6: Benign Cooperative Vessel (Control)
            {
                "case_name": "Benign Cooperative Vessel Control",
                "is_ground_truth_threat": False,
                "expected_action": "AUTO_CLOSED",
                "data": {
                    "item_id": "benign-control-06",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419001284",
                    "lat": 18.8450, "lon": 72.8210,
                    "ais_lat": 18.8451, "ais_lon": 72.8211, # 15m deviation (valid)
                    "speed_knots": 12.0, # Valid commercial speed
                    "heartbeat_age_hours": 0.2,
                    "is_in_geofence": False
                }
            },
            # Case 7a: Spatial Boundary 1400m (Subtle deviation <= 1500m -> HUMAN_REVIEW)
            {
                "case_name": "Spatial Boundary 1400m (Subtle Deviation)",
                "is_ground_truth_threat": False,
                "expected_action": "HUMAN_REVIEW",
                "data": {
                    "item_id": "boundary-dev-1400m",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419007711",
                    "lat": 18.8500, "lon": 72.8200,
                    "ais_lat": 18.8500 + (1400.0 / 111139.0), "ais_lon": 72.8200, # exactly 1400m
                    "speed_knots": 10.0,
                    "is_in_geofence": False
                }
            },
            # Case 7b: Spatial Boundary 1600m (Overt spoof > 1500m -> ESCALATED_PRIORITY)
            {
                "case_name": "Spatial Boundary 1600m (Overt Spoof)",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "boundary-dev-1600m",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419007722",
                    "lat": 18.8500, "lon": 72.8200,
                    "ais_lat": 18.8500 + (1600.0 / 111139.0), "ais_lon": 72.8200, # exactly 1600m
                    "speed_knots": 10.0,
                    "is_in_geofence": False
                }
            },
            # Case 8a: Stale Heartbeat Boundary 3.9h (<= 4.0h -> AUTO_CLOSED)
            {
                "case_name": "Heartbeat Boundary 3.9h (Fresh)",
                "is_ground_truth_threat": False,
                "expected_action": "AUTO_CLOSED",
                "data": {
                    "item_id": "boundary-age-39h",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419008811",
                    "lat": 18.8450, "lon": 72.8210,
                    "ais_lat": 18.8450, "ais_lon": 72.8210,
                    "speed_knots": 10.0,
                    "heartbeat_age_hours": 3.9,
                    "is_in_geofence": False
                }
            },
            # Case 8b: Stale Heartbeat Boundary 4.1h (> 4.0h -> ESCALATED_PRIORITY)
            {
                "case_name": "Heartbeat Boundary 4.1h (Stale)",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "boundary-age-41h",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419008822",
                    "lat": 18.8450, "lon": 72.8210,
                    "ais_lat": 18.8450, "ais_lon": 72.8210,
                    "speed_knots": 10.0,
                    "heartbeat_age_hours": 4.1,
                    "is_in_geofence": False
                }
            },
            # Case 9a: Commercial Speed Boundary 27.0 kts (<= 28.0 kts -> AUTO_CLOSED)
            {
                "case_name": "Speed Boundary 27.0 kts (Plausible Cargo)",
                "is_ground_truth_threat": False,
                "expected_action": "AUTO_CLOSED",
                "data": {
                    "item_id": "boundary-speed-27kts",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Merchant / Corvette",
                    "matched_identity": "419009911",
                    "lat": 18.8450, "lon": 72.8210,
                    "ais_lat": 18.8450, "ais_lon": 72.8210,
                    "speed_knots": 27.0,
                    "heartbeat_age_hours": 0.5,
                    "is_in_geofence": False
                }
            },
            # Case 9b: Commercial Speed Boundary 29.0 kts (> 28.0 kts -> ESCALATED_PRIORITY)
            {
                "case_name": "Speed Boundary 29.0 kts (Cargo Kinematic Violation)",
                "is_ground_truth_threat": True,
                "expected_action": "ESCALATED_PRIORITY",
                "data": {
                    "item_id": "boundary-speed-29kts",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Merchant / Corvette",
                    "matched_identity": "419009922",
                    "lat": 18.8450, "lon": 72.8210,
                    "ais_lat": 18.8450, "ais_lon": 72.8210,
                    "speed_knots": 29.0,
                    "heartbeat_age_hours": 0.5,
                    "is_in_geofence": False
                }
            },
            # Case 10: AIS-SAR Time Offset with Dead-Reckoning (15 min at 15 kts along heading 45 deg)
            # Distance traveled = 15 * 0.514444 * 900 = 6945 m (exceeds 1500m raw distance, but residual < 50m)
            {
                "case_name": "AIS-SAR Dead-Reckoning (15 min at 15 kts, Compliant)",
                "is_ground_truth_threat": False,
                "expected_action": "AUTO_CLOSED",
                "data": {
                    "item_id": "dr-compliant-15min",
                    "threat_score": 20,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419006611",
                    "ais_lat": 18.8450, "ais_lon": 72.8210,
                    # Actual sensor detects ship after 15 min at 15 kts heading 45 deg
                    "lat": 18.8450 + (6945.0 * math.cos(math.radians(45.0))) / 111139.0,
                    "lon": 72.8210 + (6945.0 * math.sin(math.radians(45.0))) / (111139.0 * math.cos(math.radians(18.8450))),
                    "speed_knots": 15.0,
                    "heading_deg": 45.0,
                    "time_offset_min": 15.0,
                    "heartbeat_age_hours": 0.25,
                    "is_in_geofence": False
                }
            },
            # Case 11: Subtle Spoof (650m deviation -> HUMAN_REVIEW)
            {
                "case_name": "Subtle Spoof (650m Deviation to Human Review)",
                "is_ground_truth_threat": False,
                "expected_action": "HUMAN_REVIEW",
                "data": {
                    "item_id": "subtle-spoof-650m",
                    "threat_score": 25,
                    "ais_status": "matched",
                    "kind": "Vessel",
                    "matched_identity": "419005511",
                    "lat": 18.8500, "lon": 72.8200,
                    "ais_lat": 18.8500 + (650.0 / 111139.0), "ais_lon": 72.8200,
                    "speed_knots": 12.0,
                    "is_in_geofence": False
                }
            }
        ]

        missed_threats = []
        false_escalations = []
        routing_mismatches = []

        for sc in scenarios:
            d = sc["data"]
            res = evaluate_contact(
                item_id=d["item_id"],
                threat_score=d["threat_score"],
                ais_status=d["ais_status"],
                kind=d["kind"],
                matched_identity=d["matched_identity"],
                contact_meta=d,
                cfg=self.cfg
            )
            act = res['triage_action']
            exp = sc["expected_action"]
            is_threat = sc["is_ground_truth_threat"]

            if is_threat and act == 'AUTO_CLOSED':
                missed_threats.append((sc["case_name"], res))
            elif not is_threat and act == 'ESCALATED_PRIORITY':
                false_escalations.append((sc["case_name"], res))

            if act != exp:
                routing_mismatches.append((sc["case_name"], f"Expected {exp}, got {act}"))

        total_threats = sum(1 for sc in scenarios if sc["is_ground_truth_threat"])
        missed_rate = len(missed_threats) / total_threats * 100.0

        # Safety requirement: Zero missed threats allowed!
        self.assertEqual(len(missed_threats), 0, f"Critical Safety Failure! Missed threats auto-closed: {missed_threats}")
        self.assertEqual(missed_rate, 0.0)
        self.assertEqual(len(false_escalations), 0, f"False escalations on benign contacts: {false_escalations}")
        self.assertEqual(len(routing_mismatches), 0, f"Routing mismatches in safety suite v2: {routing_mismatches}")


if __name__ == '__main__':
    unittest.main()
