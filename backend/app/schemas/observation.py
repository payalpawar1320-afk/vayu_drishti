from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class SatelliteChannelInfo(BaseModel):
    available: bool = True
    sensor: str = Field(..., description="Sensor name (e.g. GOES/METEOSAT, AVHRR, INSAT-3D)")
    timestamp: str = Field(..., description="Acquisition timestamp in UTC")
    channel: str = Field(..., description="Spectral band/channel (e.g. IR_11um, Ch4_10.8um)")
    image_url: Optional[str] = Field(None, description="Static or dynamic URL to the processed image chip")
    grid_dim: List[int] = Field(default_factory=lambda: [301, 301], description="Raster dimensions [rows, cols]")
    resolution_km: float = Field(default=8.0, description="Spatial resolution in km")

class EnvironmentalFeatures(BaseModel):
    sea_surface_temp_c: Optional[float] = Field(None, description="Sea Surface Temperature in Celsius")
    vertical_wind_shear_kt: Optional[float] = Field(None, description="200-850 hPa vertical wind shear in knots")
    mid_troposphere_rh_pct: Optional[float] = Field(None, description="700-500 hPa relative humidity percentage")
    mean_sea_level_pressure_mb: Optional[float] = Field(None, description="ERA5 MSLP field value at center")
    source: str = Field(default="ERA5 Reanalysis")

class QualityFlags(BaseModel):
    temporal_delta_seconds: int = Field(default=0, description="Absolute difference between satellite and best track in seconds")
    spatial_offset_km: float = Field(default=0.0, description="Offset between estimated center and reported best track in km")
    data_complete: bool = True
    missing_channels: List[str] = Field(default_factory=list)

class FusedObservation(BaseModel):
    storm_id: str
    storm_name: str
    target_timestamp: str = Field(..., description="Normalized UTC timestamp for the time slice")
    center: Dict[str, Any] = Field(..., description="{'lat': float, 'lon': float, 'source': str}")
    satellite_channels: Dict[str, SatelliteChannelInfo] = Field(default_factory=dict)
    environmental_features: Optional[EnvironmentalFeatures] = None
    quality_flags: QualityFlags = Field(default_factory=QualityFlags)
    data_source_badge: str = Field(default="NOAA HURSAT-B1 + NOAA IBTrACS")
