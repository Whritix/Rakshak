"""Pydantic Schema Contracts and Validation Models for Project Rakshak 2.0.

Provides strict defense-grade validation:
- Geospatial coordinate bounds (WGS84 lat [-90, 90], lon [-180, 180]).
- Physical buffer zones (radius_km [0.1, 500]).
- Velocity bounds (speed_knots [0, 120], heading [0, 360]).
- Probability & confidence ranges ([0.0, 1.0]).
- Operational lifecycle status regex matching (ACTIVE | ACKNOWLEDGED | RESOLVED).
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Assoc(BaseModel):
    """AIS contact correlation status update."""
    status: str = Field(..., description="matched, unmatched, or unknown")
    mmsi: Optional[str] = Field(None, description="9-digit Maritime Mobile Service Identity")


class ZoneCreate(BaseModel):
    """Geofenced defense operational buffer zone creation model."""
    name: str = Field(..., min_length=2, max_length=120, description="Zone designator name")
    zone_type: str = Field("DEFENSE_BUFFER", description="CRITICAL_OFFSHORE, NAVAL_EXCLUSION, etc.")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Center latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Center longitude in decimal degrees")
    radius_km: float = Field(10.0, ge=0.1, le=500.0, description="Zone buffer radius in km (0.1 to 500.0)")


class MissionCreate(BaseModel):
    """Tactical mission plan creation request."""
    title: str = Field("Tactical Intercept & Patrol Route", min_length=3, max_length=150)
    notes: str = Field("", description="Operational mission orders & ROE directives")


class PipeReview(BaseModel):
    """Commercial / Ground Truth inspection log."""
    month: str
    detection_id: str
    status: str
    mmsi: Optional[str] = None


class SarDetectionCreate(BaseModel):
    """Sentinel-1 Synthetic Aperture Radar (SAR) target insertion model."""
    scene_id: str = Field("S1A_IW_GRDH_1SDV", description="Sentinel-1 scene product identifier")
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    rcs_sigma0_db: float = Field(-8.5, description="Calibrated radar backscatter cross-section in dB")
    estimated_length_m: float = Field(65.0, ge=1.0, le=600.0, description="Estimated waterline length in meters")
    cfar_confidence: float = Field(0.88, ge=0.0, le=1.0, description="Normalized CFAR detection confidence")
    speed_knots: Optional[float] = Field(14.2, ge=0.0, le=120.0, description="Estimated velocity in knots")
    heading_deg: Optional[float] = Field(225.0, ge=0.0, le=360.0, description="Heading in degrees from true north")
    notes: Optional[str] = Field("High metallic backscatter detected with no AIS broadcast")


class ArmyFeedCreate(BaseModel):
    """Army tactical ground/aerial alert creation model."""
    domain: str = Field(..., description="DRONE_UAV, UGS_GROUND, or SIGINT_TEXT")
    source_ref: str = Field("UAV-GARUDA-01", description="Sensor node or UAV callsign")
    target_class: str = Field("Military Convoy", description="Classification name")
    confidence: float = Field(0.89, ge=0.0, le=1.0, description="Detection confidence score [0.0 - 1.0]")
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    signal_strength: float = Field(0.92, ge=0.0, le=1.0, description="Signal-to-noise or sensor fidelity [0.0 - 1.0]")
    alert_summary: str = Field(..., min_length=3, description="Operational alert synopsis")
    raw_payload: str = Field("{}", description="Serialized sensor JSON telemetry")
    threat_score: int = Field(75, ge=0, le=100, description="Evaluated threat score [0 - 100]")
    threat_level: str = Field("HIGH", pattern="^(LOW|MEDIUM|HIGH)$", description="Tiered military priority")


class ArmyFeedStatusUpdate(BaseModel):
    """Operational lifecycle status transition for Army tactical alerts."""
    status: str = Field(..., pattern="^(ACTIVE|ACKNOWLEDGED|RESOLVED)$", description="Target lifecycle state")


class TrajectoryProjectionRequest(BaseModel):
    """Dead-reckoning target projection parameters."""
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    speed_knots: float = Field(..., ge=0.0, le=120.0, description="Target speed in knots (0.0 to 120.0)")
    heading_deg: float = Field(..., ge=0.0, le=360.0, description="Target heading (0.0 to 360.0 degrees)")
    intervals_min: List[int] = Field(default_factory=lambda: [15, 30, 60], description="Projection time windows in minutes")
    target_class: Optional[str] = Field("default", description="Vessel, Aircraft, Vehicle, or default")


class ContactTrackRequest(TrajectoryProjectionRequest):
    """Extended kinematic trajectory projection with explicit target class categorization."""
    target_class: str = Field("default", description="Target class for calibrated dispersion modeling")


class SampleLoadRequest(BaseModel):
    """Local demo sample raster evaluation request."""
    sample_name: str
    model_type: str = Field("multiclass", description="multiclass or vessel_specialist")
    confidence: float = Field(0.35, ge=0.05, le=1.0, description="Inference threshold [0.05 - 1.0]")


class LoginRequest(BaseModel):
    """Operator authentication credentials."""
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4, max_length=128)


class RegisterRequest(BaseModel):
    """New tactical operator registration."""
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    callsign: Optional[str] = Field(None, max_length=50)
    rank: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field("OPERATOR", max_length=50)
    clearance: Optional[str] = Field("SECRET", max_length=50)


class ChangePasswordRequest(BaseModel):
    """Tactical operator credential rotation request."""
    old_password: str = Field(..., min_length=4, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class RagQueryRequest(BaseModel):
    """Sovereign air-gapped doctrine retrieval query."""
    query: str = Field(..., min_length=2, description="Natural language defense doctrine query")
    category: Optional[str] = Field(None, description="Optional doctrine domain filter")


class RagDispatchMissionRequest(BaseModel):
    """One-click mission creation request generated by RAG tactical advisor."""
    title: str = Field(..., min_length=3, max_length=150)
    directive_summary: str = Field(..., min_length=5)
    checklist: List[str] = Field(default_factory=list)


class TriageReopenRequest(BaseModel):
    """Operator manual override request to reopen an auto-closed contact."""
    item_id: Optional[str] = Field(None, description="Optional target ID if not in URL path")
    reason: Optional[str] = Field("Operator manual inspection override", max_length=250)
    operator: Optional[str] = Field("OPERATOR", max_length=50)
    operator_role: Optional[str] = Field("OPERATOR", max_length=50)


class TriageConfigUpdate(BaseModel):
    """Optional runtime configuration override for auto-triage thresholds."""
    low_threat_max: Optional[int] = Field(None, ge=0, le=100)
    medium_threat_min: Optional[int] = Field(None, ge=0, le=100)
    medium_threat_max: Optional[int] = Field(None, ge=0, le=100)
    high_threat_min: Optional[int] = Field(None, ge=0, le=100)
    manual_review_seconds_per_item: Optional[float] = Field(None, ge=1.0, le=3600.0)


class MeasurementInput(BaseModel):
    """Input sensor measurement for kinematic track fusion."""
    sensor_type: str = Field("AIS", description="AIS, SAR, OPTICAL, or RADAR")
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    alt: float = Field(0.0)
    identity: Optional[str] = Field(None, description="MMSI, callsign, or null")
    detected_class: Optional[str] = Field("Vessel", description="Vessel, Vehicle, Aircraft")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    speed_knots: Optional[float] = Field(None, ge=0.0, le=120.0)
    heading_deg: Optional[float] = Field(None, ge=0.0, le=360.0)
    timestamp: Optional[float] = Field(None, description="Epoch seconds or null for now")


class FuseStepRequest(BaseModel):
    """Batch sensor fusion step request."""
    measurements: List[MeasurementInput] = Field(default_factory=list)
    timestamp: Optional[float] = Field(None, description="Optional time step in epoch seconds")
    association_method: Optional[str] = Field("hungarian", description="hungarian, jpda, or nn")


class DdilAlertItem(BaseModel):
    """Individual tactical alert item for store-and-forward synchronization."""
    alert_id: str = Field(..., description="Globally unique alert ID")
    seq_num: int = Field(..., description="Monotonic sequence number at edge node")
    node_id: Optional[str] = Field("EDGE-JETSON-ORIN-01", description="Originating edge node identifier")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary detection payload JSON")
    threat_score: int = Field(0, ge=0, le=100)
    threat_level: str = Field("LOW", pattern="^(LOW|MEDIUM|HIGH)$")
    created_at: str = Field(..., description="ISO 8601 creation timestamp at edge node")


class DdilSyncBatchRequest(BaseModel):
    """Batch alert synchronization payload transmitted across tactical link."""
    node_id: str = Field("EDGE-JETSON-ORIN-01", description="Edge node identifier")
    alerts: List[DdilAlertItem] = Field(default_factory=list, description="Ordered batch of pending outbox alerts")


class DdilChannelUpdateRequest(BaseModel):
    """Runtime channel state override for DDIL testing and UI demonstration."""
    status: str = Field(..., pattern="^(CONNECTED|DEGRADED|DENIED)$", description="Physical link condition")
    latency_ms: Optional[float] = Field(25.0, ge=0.0, le=10000.0)
    packet_loss_pct: Optional[float] = Field(0.0, ge=0.0, le=100.0)
    bandwidth_kbps: Optional[float] = Field(256.0, ge=1.0, le=100000.0)


class ChangeDetectionRunRequest(BaseModel):
    """Multi-temporal change detection run request."""
    tile_path: Optional[str] = Field(None, description="Optional path to holdout val_report tile")
    shift_x: float = Field(0.0, ge=-20.0, le=20.0, description="Injected horizontal shift in pixels")
    shift_y: float = Field(0.0, ge=-20.0, le=20.0, description="Injected vertical shift in pixels")
    seed: int = Field(42, ge=0, le=1000000, description="Deterministic pseudo-random seed for synthetic edits")
    confidence: float = Field(0.25, ge=0.05, le=1.0, description="YOLO detection confidence threshold")
    num_edits: int = Field(3, ge=1, le=10, description="Number of synthetic object edits to inject")

