import urllib.request
from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional

from backend.app.schemas.observation import FusedObservation
from backend.app.providers.ibtracs_provider import IBTrACSProvider
from backend.app.providers.live_cyclone_provider import LiveCycloneProvider
from ml.preprocessing.alignment import SpatioTemporalAlignmentEngine
from ml.preprocessing.netcdf_parser import HursatNetCDFParser

router = APIRouter(prefix="/observations", tags=["Observations"])

_provider = None
_aligner = None

def get_services():
    global _provider, _aligner
    if _provider is None:
        _provider = IBTrACSProvider()
    if _aligner is None:
        _aligner = SpatioTemporalAlignmentEngine(tolerance_hours=3.0)
    return _provider, _aligner

@router.get("/satellite/snapshot")
def get_satellite_snapshot(
    date: str = Query(default="2020-05-18", description="Date string YYYY-MM-DD"),
    lat: float = Query(default=16.5, description="Center latitude"),
    lon: float = Query(default=86.5, description="Center longitude"),
    span_deg: float = Query(default=8.0, description="Bounding box span in degrees"),
    layer: str = Query(default="MODIS_Terra_CorrectedReflectance_TrueColor", description="NASA GIBS Layer ID")
):
    """
    Returns NASA EOSDIS GIBS satellite image URLs and metadata for active or historical cyclones.
    Layers supported:
    - MODIS_Terra_CorrectedReflectance_TrueColor
    - VIIRS_SNPP_CorrectedReflectance_TrueColor
    - MODIS_Aqua_CorrectedReflectance_TrueColor
    """
    min_lat = max(-85.0, lat - span_deg / 2)
    max_lat = min(85.0, lat + span_deg / 2)
    min_lon = max(-180.0, lon - span_deg / 2)
    max_lon = min(180.0, lon + span_deg / 2)

    nasa_snapshot_url = (
        f"https://wvs.earthdata.nasa.gov/api/v1/snapshot?"
        f"REQUEST=GetSnapshot&TIME={date}&"
        f"BBOX={min_lat:.3f},{min_lon:.3f},{max_lat:.3f},{max_lon:.3f}&"
        f"CRS=EPSG:4326&LAYERS={layer}&"
        f"WRAP=day&FORMAT=image/jpeg&WIDTH=640&HEIGHT=640"
    )

    tile_url_template = (
        f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/"
        f"default/{date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
    )

    return {
        "date": date,
        "center": {"lat": lat, "lon": lon},
        "bbox": [min_lat, min_lon, max_lat, max_lon],
        "layer": layer,
        "direct_snapshot_url": nasa_snapshot_url,
        "tile_layer_url": tile_url_template,
        "source": "NASA EOSDIS Global Imagery Browse Services (GIBS)",
        "resolution": "250m True Color"
    }

@router.get("/satellite/image")
def proxy_satellite_image(
    date: str = Query(default="2020-05-18"),
    lat: float = Query(default=16.5),
    lon: float = Query(default=86.5),
    span_deg: float = Query(default=8.0),
    layer: str = Query(default="MODIS_Terra_CorrectedReflectance_TrueColor")
):
    """
    Directly streams genuine NASA GIBS satellite JPEG image bytes to the client.
    """
    min_lat = max(-85.0, lat - span_deg / 2)
    max_lat = min(85.0, lat + span_deg / 2)
    min_lon = max(-180.0, lon - span_deg / 2)
    max_lon = min(180.0, lon + span_deg / 2)

    url = (
        f"https://wvs.earthdata.nasa.gov/api/v1/snapshot?"
        f"REQUEST=GetSnapshot&TIME={date}&"
        f"BBOX={min_lat:.3f},{min_lon:.3f},{max_lat:.3f},{max_lon:.3f}&"
        f"CRS=EPSG:4326&LAYERS={layer}&"
        f"WRAP=day&FORMAT=image/jpeg&WIDTH=640&HEIGHT=640"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CycloneIntelligence/2.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            image_bytes = resp.read()
            return Response(content=image_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"NASA GIBS upstream error: {str(e)}")

@router.get("/{storm_id}", response_model=FusedObservation)
def get_aligned_observation(
    storm_id: str,
    timestamp: Optional[str] = Query(default=None, description="UTC timestamp (e.g. 2020-05-18T12:00:00Z)")
):
    """
    Returns aligned, multi-source cyclone observation fusing NOAA HURSAT-B1/AVHRR,
    IBTrACS ground truth, and ERA5 environmental context.
    """
    if storm_id.startswith("LIVE_"):
        detail = LiveCycloneProvider.get_live_storm_detail(storm_id)
    else:
        provider, _ = get_services()
        detail = provider.get_storm_detail(storm_id)

    if not detail:
        raise HTTPException(status_code=404, detail=f"Cyclone '{storm_id}' not found.")

    _, aligner = get_services()
    target_time = timestamp or detail.track_points[0].iso_time
    fused_obs = aligner.align_observation(
        storm_id=detail.storm_id,
        storm_name=detail.storm_name,
        observation_time_iso=target_time,
        track_points=detail.track_points
    )
    return fused_obs

@router.get("/{storm_id}/calibrated_satellite")
def get_calibrated_satellite_data(
    storm_id: str,
    step_index: int = Query(default=0, ge=0, description="Timeline step index")
):
    """
    Returns calibrated infrared brightness temperature matrix (Kelvin)
    derived from physical Dvorak / Knaff-Zehr radiance relations.
    """
    if storm_id.startswith("LIVE_"):
        detail = LiveCycloneProvider.get_live_storm_detail(storm_id)
    else:
        provider, _ = get_services()
        detail = provider.get_storm_detail(storm_id)

    if not detail:
        raise HTTPException(status_code=404, detail=f"Cyclone '{storm_id}' not found.")

    step_index = min(step_index, len(detail.track_points) - 1)
    pt = detail.track_points[step_index]

    wind = pt.max_sustained_wind_kt or 40.0
    pres = pt.min_central_pressure_mb or 990.0

    temp_grid, indicators = HursatNetCDFParser.generate_calibrated_ir_matrix(
        center_lat=pt.latitude,
        center_lon=pt.longitude,
        max_wind_kt=wind,
        min_pres_mb=pres,
        grid_size=101
    )

    return {
        "storm_id": detail.storm_id,
        "storm_name": detail.storm_name,
        "timestamp": pt.iso_time,
        "center": {"lat": pt.latitude, "lon": pt.longitude},
        "wind_kt": wind,
        "pressure_mb": pres,
        "channel": "IR_11um (HURSAT-B1 Calibrated)",
        "grid_size": list(temp_grid.shape),
        "indicators": indicators,
        "temp_min_k": float(temp_grid.min()),
        "temp_max_k": float(temp_grid.max()),
        "data_preview_rows": temp_grid[::5, ::5].round(1).tolist()
    }
