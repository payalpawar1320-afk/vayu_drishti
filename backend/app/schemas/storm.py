from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class StormBase(BaseModel):
    storm_id: str = Field(..., description="Unique Storm Identifier (e.g. 2020136N10088)")
    storm_name: str = Field(..., description="Official Storm Name (e.g. AMPHAN, FANI, TAUKTAE)")
    basin: str = Field(default="NI", description="Ocean Basin (NI = North Indian Ocean)")
    sub_basin: Optional[str] = Field(default="BB", description="Sub-basin (BB = Bay of Bengal, AS = Arabian Sea)")
    year: int = Field(..., description="Year of occurrence")

class BestTrackPoint(BaseModel):
    iso_time: str = Field(..., description="ISO 8601 UTC timestamp")
    latitude: float = Field(..., description="Storm center latitude (decimal degrees)")
    longitude: float = Field(..., description="Storm center longitude (decimal degrees)")
    max_sustained_wind_kt: Optional[float] = Field(None, description="Max sustained 1-min or 3-min wind in knots")
    min_central_pressure_mb: Optional[float] = Field(None, description="Minimum central sea-level pressure in hPa/mb")
    nature: Optional[str] = Field(default="TS", description="Storm nature / classification (e.g. TS, ET, NR)")
    agency: Optional[str] = Field(default="IMD", description="Reporting agency (IMD, JTWC, WMO)")

class StormSummary(StormBase):
    start_time: str
    end_time: str
    peak_wind_kt: Optional[float] = None
    min_pressure_mb: Optional[float] = None
    total_observations: int
    data_sources: List[str] = Field(default_factory=lambda: ["NOAA IBTrACS v04r01"])

class StormDetail(StormSummary):
    track_points: List[BestTrackPoint]
