from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class MotionVector(BaseModel):
    speed_knots: float = Field(..., description="Translation speed in knots")
    heading_degrees: float = Field(..., description="Azimuth motion heading in degrees (0-360)")

class EvolutionIndicators(BaseModel):
    symmetry_score: float = Field(..., ge=0.0, le=1.0, description="Azimuthal cloud brightness symmetry index (0-1)")
    symmetry_change_24h: Optional[float] = Field(None, description="24h delta in symmetry score")
    cloud_organization_score: float = Field(..., ge=0.0, le=1.0, description="Spatial entropy/organization index (0-1)")
    organization_change_24h: Optional[float] = Field(None, description="24h delta in cloud organization")
    central_dense_overcast_temp_k: Optional[float] = Field(None, description="Mean temperature of inner core cloud tops in Kelvin")
    cdo_deepening_trend: str = Field(default="STEADY", description="COOLING_RAPID, COOLING, STEADY, WARMING")
    eye_clarity_index: Optional[float] = Field(None, ge=0.0, le=1.0, description="Eye temperature anomaly contrast (0-1)")
    motion_vector: MotionVector

class EvolutionFingerprint(BaseModel):
    storm_id: str
    current_timestamp: str
    sequence_length_hours: int = Field(default=24)
    indicators: EvolutionIndicators
    derived_evolution_phase: str = Field(..., description="RAPID_ORGANIZATION, STEADY_INTENSIFICATION, MATURE_STABLE, WEAKENING, EXTRATROPICAL_TRANSITION")
    derivation_method: str = Field(default="ALGORITHMIC_SPATIAL_MOMENTS_AND_RADIAL_PROFILES")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class EyeStructure(BaseModel):
    storm_id: str
    timestamp: str
    eye_detected: bool
    eye_center: Dict[str, float]
    eye_radius_km: float
    eyewall_radius_km: float
    cdo_radius_km: float
    eye_clarity: float
    cdo_min_temp_k: float
    cdo_min_temp_c: float
    convective_symmetry_pct: float
    eyewall_intensity_kt: float
    classification: str
    description: str
