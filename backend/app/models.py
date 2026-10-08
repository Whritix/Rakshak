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


class RagQueryRequest(BaseModel):
    """Sovereign air-gapped doctrine retrieval query."""
    query: str = Field(..., min_length=2, description="Natural language defense doctrine query")
    category: Optional[str] = Field(None, description="Optional doctrine domain filter")


class RagDispatchMissionRequest(BaseModel):
    """One-click mission creation request generated by RAG tactical advisor."""
    title: str = Field(..., min_length=3, max_length=150)
    directive_summary: str = Field(..., min_length=5)
    checklist: List[str] = Field(default_factory=list)
