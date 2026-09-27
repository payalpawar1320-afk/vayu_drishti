from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class DistrictOverlap(BaseModel):
    district_id: str
    district_name: str
    state_name: str
    area_overlap_pct: float = Field(..., ge=0.0, le=100.0)
    risk_classification: str = Field(..., description="CRITICAL_LANDFALL, HIGH, MODERATE, LOW")
    estimated_population: int
    coastal_length_km: float = 0.0

class InfrastructureExposure(BaseModel):
    major_ports: int = 0
    airports: int = 0
    hospitals: int = 0
    national_highway_km: float = 0.0

class SummaryExposure(BaseModel):
    estimated_population_exposed: int
    total_districts_intersected: int
    critical_infrastructure_counts: InfrastructureExposure

class GISExposureResponse(BaseModel):
    scenario_id: str = Field(default="BASE_PREDICTION")
    is_simulation: bool = False
    corridor_parameters: Dict[str, Any]
    risk_corridor_geojson: Dict[str, Any]
    summary_exposure: SummaryExposure
    intersected_districts: List[DistrictOverlap]

class ScenarioShiftRequest(BaseModel):
    storm_id: str
    base_prediction_id: Optional[str] = "BASE_PREDICTION"
    track_shift_direction: str = Field(default="NONE", description="'NONE', 'EAST', 'WEST', 'NORTH', 'SOUTH'")
    track_shift_km: float = Field(default=0.0, ge=0.0, le=300.0)
    intensity_modifier: str = Field(default="CURRENT", description="'LOWER', 'CURRENT', 'HIGHER'")
    corridor_width_multiplier: float = Field(default=1.0, ge=0.5, le=3.0)

class ScenarioShiftResponse(BaseModel):
    scenario_name: str
    simulation_flag: str = "SIMULATED_SCENARIO"
    corridor_geojson: Dict[str, Any]
    base_corridor_geojson: Optional[Dict[str, Any]] = None
    base_exposure: SummaryExposure
    simulated_exposure: SummaryExposure
    exposure_delta: Dict[str, Any]
    districts_added: List[str]
    districts_dropped: List[str]
