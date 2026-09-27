import urllib.request
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.app.schemas.storm import StormSummary, StormDetail, BestTrackPoint

ARCGIS_LIVE_HURRICANES_URL = (
    "https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/"
    "Active_Hurricanes_v1/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
)

class LiveCycloneProvider:
    """
    Fetches and standardizes live tropical cyclone data from NOAA / JTWC
    via the official ArcGIS Active Tropical Cyclones Feed.
    Includes memory caching with fallback.
    """
    _cache_data: Optional[Dict[str, Any]] = None
    _cache_time: float = 0.0
    _cache_ttl_sec: float = 120.0  # 2 minute cache

    @classmethod
    def fetch_live_data(cls) -> Dict[str, Any]:
        now = time.time()
        if cls._cache_data is not None and (now - cls._cache_time) < cls._cache_ttl_sec:
            return cls._cache_data

        try:
            req = urllib.request.Request(
                ARCGIS_LIVE_HURRICANES_URL,
                headers={"User-Agent": "CycloneIntelligencePlatform/2.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cls._cache_data = data
                cls._cache_time = now
                return data
        except Exception as e:
            if cls._cache_data is not None:
                return cls._cache_data
            # If network error and no cache, return empty
            return {"features": []}

    @classmethod
    def get_active_storms(cls) -> List[StormSummary]:
        raw = cls.fetch_live_data()
        features = raw.get("features", [])

        storms_by_name: Dict[str, List[Dict[str, Any]]] = {}
        for feat in features:
            props = feat.get("properties", {})
            name = (props.get("STORMNAME") or "").strip()
            if not name:
                continue
            basin = (props.get("BASIN") or "GL").strip()
            key = f"{name}_{basin}"
            if key not in storms_by_name:
                storms_by_name[key] = []
            storms_by_name[key].append(props)

        summaries = []
        for key, p_list in storms_by_name.items():
            first = p_list[0]
            name = (first.get("STORMNAME") or "").strip().title()
            basin = (first.get("BASIN") or "GL").strip()
            storm_id = f"LIVE_{name.upper()}_{basin}"

            winds = [p.get("MAXWIND") for p in p_list if p.get("MAXWIND") is not None and p.get("MAXWIND") > 0]
            peak_wind = float(max(winds)) if winds else 45.0

            pressures = [p.get("MSLP") for p in p_list if p.get("MSLP") is not None and 800 < p.get("MSLP") < 1050]
            min_pres = float(min(pressures)) if pressures else round(1013.25 - (peak_wind * 0.7), 1)

            date_lbl = first.get("FLDATELBL") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

            summaries.append(StormSummary(
                storm_id=storm_id,
                storm_name=f"[LIVE] {name} ({first.get('TCDVLP', 'Active')})",
                basin=basin,
                sub_basin=basin,
                year=datetime.now(timezone.utc).year,
                start_time=date_lbl,
                end_time=date_lbl,
                peak_wind_kt=peak_wind,
                min_pressure_mb=min_pres,
                total_observations=len(p_list),
                data_sources=["NOAA/JTWC Live Active Tropical Cyclones Feed", "ArcGIS FeatureService"]
            ))

        return summaries

    @classmethod
    def get_live_storm_detail(cls, storm_id_or_name: str) -> Optional[StormDetail]:
        raw = cls.fetch_live_data()
        features = raw.get("features", [])

        # Clean target name
        target = storm_id_or_name.upper().replace("LIVE_", "")
        # Remove basin suffix if present
        for b in ["_WP", "_EP", "_AL", "_NI", "_IO", "_CP", "_GL"]:
            if target.endswith(b):
                target = target[:-len(b)]

        matched_props = []
        for feat in features:
            props = feat.get("properties", {})
            name = (props.get("STORMNAME") or "").strip().upper()
            if name == target:
                matched_props.append(props)

        if not matched_props:
            return None

        # Sort points by forecast lead time TAU
        matched_props.sort(key=lambda p: p.get("TAU", 0))

        first = matched_props[0]
        storm_name = (first.get("STORMNAME") or "").strip().title()
        basin = (first.get("BASIN") or "GL").strip()
        storm_id = f"LIVE_{storm_name.upper()}_{basin}"

        track_points = []
        winds = []
        pressures = []

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for idx, p in enumerate(matched_props):
            lat = float(p.get("LAT", 0.0))
            lon = float(p.get("LON", 0.0))
            wind = float(p.get("MAXWIND") or 40.0)
            winds.append(wind)

            mslp = p.get("MSLP")
            if mslp and 850 < mslp < 1050:
                pres = float(mslp)
            else:
                pres = round(1013.25 - (wind * 0.7), 1)
            pressures.append(pres)

            tau = p.get("TAU", idx * 12)
            # Create synthetic or labeled timestamp
            date_str = p.get("FLDATELBL") or f"T+{tau}h"

            track_points.append(BestTrackPoint(
                iso_time=date_str,
                latitude=lat,
                longitude=lon,
                max_sustained_wind_kt=wind,
                min_central_pressure_mb=pres,
                nature=p.get("TCDVLP", "TS"),
                agency="NOAA/JTWC"
            ))

        peak_wind = max(winds) if winds else 45.0
        min_pres = min(pressures) if pressures else 995.0

        return StormDetail(
            storm_id=storm_id,
            storm_name=f"[LIVE] {storm_name} ({first.get('TCDVLP', 'Active')})",
            basin=basin,
            sub_basin=basin,
            year=datetime.now(timezone.utc).year,
            start_time=track_points[0].iso_time,
            end_time=track_points[-1].iso_time,
            peak_wind_kt=peak_wind,
            min_pressure_mb=min_pres,
            total_observations=len(track_points),
            data_sources=["NOAA / JTWC Live Active Storm Feed", "Real-Time Telemetry"],
            track_points=track_points
        )
