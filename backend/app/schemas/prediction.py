from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ForecastPoint(BaseModel):
    horizon_hours: int = Field(..., description="Hours ahead from initialization (e.g. 6, 12, 18, 24, 36, 48)")
    forecast_time: str = Field(..., description="Forecast valid UTC timestamp")
    latitude: float = Field(..., description="Forecasted latitude")
    longitude: float = Field(..., description="Forecasted longitude")
    uncertainty_radius_km: float = Field(..., description="Uncertainty buffer radius in km")
    predicted_wind_speed_kt: Optional[float] = Field(None, description="Forecasted max sustained wind speed in kt")

class IntensityTrendInfo(BaseModel):
    trend_label: str = Field(..., description="STRENGTHENING, STABLE, WEAKENING")
    trend_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_derivation: str = Field(default="AGREEMENT_BETWEEN_SST_CDO_AND_HISTORICAL_PRESSURE")

class ExplainabilityInfo(BaseModel):
    key_drivers: List[str] = Field(default_factory=list, description="List of physical/model drivers behind the prediction")
    structural_contributions: Dict[str, float] = Field(default_factory=dict)

class TrackIntensityPrediction(BaseModel):
    storm_id: str
    forecast_init_time: str
    model_meta: Dict[str, str] = Field(..., description="Model names, versions, training status ('EVALUATED', 'BASELINE_ACTIVE', 'MODEL_PENDING')")
    forecast_points: List[ForecastPoint]
    intensity_trend: IntensityTrendInfo
    explainability: ExplainabilityInfo
    data_badge: str = Field(default="[MODELED PREDICTION]")
