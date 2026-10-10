"""Unit and Integration Tests for Project Rakshak 2.0 Change Detection Engine.

Validates:
1. Synthetic bi-temporal pair construction from holdout val_report partition tiles.
2. Ground-truth edit log fidelity and labeling as SYNTHETIC.
3. ORB + RANSAC & Phase Correlation sub-pixel co-registration under shifts (0 to 8 px).
4. Class-aware 1-to-1 matching and change categorization (NEW, REMOVED, MOVED).
5. Radiometric normalisation and secondary pixel-difference structural anomaly extraction.
6. REST API contracts (/api/change-detection/run, /api/change-detection/last, /api/change-detection/demo, /api/change-detection/tiles).
7. Strict operational separation: change detection outputs are NOT fed into tactical threat scores.
"""
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.change_detection import (
    get_val_report_tile_paths,
    build_synthetic_pair,
    coregister_images,
    match_detections_and_classify_changes,
    compute_radiometric_pixel_difference,
    run_change_detection_analysis,
    get_last_change_detection_result
)
from backend.app.db import get_db
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_val_report_tiles_available():
    """Ensure val_report holdout tiles are loaded and exist on disk."""
    tiles = get_val_report_tile_paths()
    assert len(tiles) >= 50, f"Expected >= 50 tiles in val_report partition, found {len(tiles)}"
    assert tiles[0].exists()


def test_build_synthetic_pair():
    """Verify synthetic pair generation retains ground truth edits and SYNTHETIC label."""
    tiles = get_val_report_tile_paths()
    tile = tiles[0]
    pair = build_synthetic_pair(tile, seed=42, num_edits=3, shift_x=2.0, shift_y=-1.5)

    assert pair["pair_label"] == "SYNTHETIC"
    assert pair["before_img"].shape == pair["after_img"].shape
    assert len(pair["ground_truth_edits"]) > 0

    # Validate ground truth edit structure
    for edit in pair["ground_truth_edits"]:
        assert edit["change_type"] in {"NEW", "REMOVED", "MOVED"}
        assert "class_name" in edit
        assert len(edit["bbox"]) == 4
        assert -90.0 <= edit["lat"] <= 90.0
        assert -180.0 <= edit["lon"] <= 180.0


def test_coregister_accuracy():
    """Test ORB + RANSAC and Phase Correlation registration error on random shift (0 to 8 px)."""
    tiles = get_val_report_tile_paths()
    tile = tiles[0]
    injected_sx, injected_sy = 4.2, -3.1
    pair = build_synthetic_pair(tile, seed=99, shift_x=injected_sx, shift_y=injected_sy)

    aligned_after, reg_info = coregister_images(
        pair["before_img"],
        pair["after_img"],
        injected_shift=(injected_sx, injected_sy)
    )

    assert reg_info["status"] == "CO_REGISTERED"
    assert "shift_recovered" in reg_info
    # Registration error should be sub-pixel or near-pixel (<= 1.5 px)
    assert reg_info["registration_error_px"] < 1.5, f"High reg error: {reg_info['registration_error_px']}"


def test_match_detections_and_classify_changes():
    """Verify class-aware 1-to-1 matching and change classification with distance thresholds."""
    geo_meta = {"has_geotiff": False, "base_lat": 28.6, "base_lon": 77.2, "deg_per_px_x": 2.7e-6, "deg_per_px_y": -2.7e-6}

    # Before detections: 1 stationary vehicle, 1 moving vehicle, 1 vehicle to be removed
    dets_before = [
        {"class_name": "Vehicle", "confidence": 0.85, "x": 100, "y": 100, "w": 30, "h": 20, "xc": 115, "yc": 110},
        {"class_name": "Vehicle", "confidence": 0.88, "x": 300, "y": 300, "w": 32, "h": 22, "xc": 316, "yc": 311},
        {"class_name": "Vehicle", "confidence": 0.90, "x": 500, "y": 500, "w": 28, "h": 18, "xc": 514, "yc": 509},
    ]

    # After detections:
    # - Stationary vehicle (shifted 2 px -> <= 18 px)
    # - Moved vehicle (displaced 50 px -> 18 < d <= 120 px)
    # - New aircraft (unmatched)
    dets_after = [
        {"class_name": "Vehicle", "confidence": 0.86, "x": 102, "y": 101, "w": 30, "h": 20, "xc": 117, "yc": 111},
        {"class_name": "Vehicle", "confidence": 0.87, "x": 350, "y": 300, "w": 32, "h": 22, "xc": 366, "yc": 311},
        {"class_name": "Aircraft", "confidence": 0.92, "x": 700, "y": 700, "w": 60, "h": 60, "xc": 730, "yc": 730},
    ]

    changes, summary = match_detections_and_classify_changes(
        dets_before, dets_after, geo_meta,
        stationary_dist_thr=18.0,
        max_move_dist_thr=120.0
    )

    assert summary["UNCHANGED"] == 1
    assert summary["MOVED"] == 1
    assert summary["REMOVED"] == 1
    assert summary["NEW"] == 1

    # Verify WGS84 and pixel attributes on outputs
    for chg in changes:
        assert chg["change_type"] in {"NEW", "REMOVED", "MOVED"}
        assert -90.0 <= chg["lat"] <= 90.0
        assert -180.0 <= chg["lon"] <= 180.0


def test_radiometric_pixel_difference():
    """Verify radiometric normalisation and structural anomaly isolation."""
    geo_meta = {"has_geotiff": False, "base_lat": 28.6, "base_lon": 77.2, "deg_per_px_x": 2.7e-6, "deg_per_px_y": -2.7e-6}
    # Create synthetic imagery
    img1 = np.full((512, 512, 3), 100, dtype=np.uint8)
    img2 = np.full((512, 512, 3), 110, dtype=np.uint8)  # Global radiometric brightness offset

    # Inject new structure: 40x50 px bright pad
    img2[200:240, 200:250] = 220

    res = compute_radiometric_pixel_difference(img1, img2, geo_meta, min_structure_area=100)

    assert res["status"] == "COMPUTED"
    assert res["structural_anomalies_count"] >= 1
    assert res["changed_pixels_count"] > 100
    anomaly = res["structural_anomalies"][0]
    assert anomaly["w"] >= 40
    assert anomaly["h"] >= 35


def test_change_detection_api_endpoints(client):
    """Test REST API routes for change detection."""
    # 1. Tiles list
    resp_tiles = client.get('/api/change-detection/tiles')
    assert resp_tiles.status_code == 200
    assert resp_tiles.json()["count"] >= 50

    # 2. Run analysis
    payload = {
        "shift_x": 2.0,
        "shift_y": -1.5,
        "seed": 10,
        "confidence": 0.25,
        "num_edits": 3
    }
    resp_run = client.post('/api/change-detection/run', json=payload)
    assert resp_run.status_code == 200
    data = resp_run.json()
    assert data["status"] == "SUCCESS"
    assert data["pair_label"] == "SYNTHETIC"
    assert "registration" in data
    assert "object_changes" in data
    assert "pixel_difference" in data

    # 3. Last analysis
    resp_last = client.get('/api/change-detection/last')
    assert resp_last.status_code == 200
    assert resp_last.json()["pair_label"] == "SYNTHETIC"

    # 4. Demo endpoint
    resp_demo = client.get('/api/change-detection/demo')
    assert resp_demo.status_code == 200
    assert resp_demo.json()["status"] == "SUCCESS"


def test_changes_not_fed_to_threat_score(client):
    """Verify change detection objects are strictly isolated from the detections table and threat scores."""
    with get_db() as db:
        before_count = db.execute("SELECT COUNT(*) FROM detections").fetchone()[0]

    resp_run = client.post('/api/change-detection/run', json={"shift_x": 1.0, "shift_y": 1.0, "seed": 5})
    assert resp_run.status_code == 200

    with get_db() as db:
        after_count = db.execute("SELECT COUNT(*) FROM detections").fetchone()[0]

    assert before_count == after_count, "Change detection detections must NOT be inserted into detections table!"
