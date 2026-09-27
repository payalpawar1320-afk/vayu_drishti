from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString

from backend.app.schemas.gis import InfrastructureExposure

TupleExposure = Tuple[InfrastructureExposure, List[Dict[str, Any]]]

class AssetExposureEngine:
    """
    Computes spatial exposure of critical infrastructure assets
    (Ports, Airports, Hospitals, National Highways) inside the modeled cyclone risk corridor.
    Implements Section 30 of SPEC.md.
    """

    def __init__(self, infra_geojson_path: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.infra_path = infra_geojson_path or (base_dir / "data" / "raw" / "gis" / "coastal_infrastructure.geojson")
        self._gdf = None
        self._load_dataset()

    def _load_dataset(self):
        if not self.infra_path.exists():
            raise FileNotFoundError(f"Infrastructure GeoJSON not found at {self.infra_path}")
        self._gdf = gpd.read_file(self.infra_path)

    def calculate_exposure(self, corridor_polygon: Polygon) -> TupleExposure:
        """
        Intersects infrastructure features with corridor_polygon.
        Returns:
          - InfrastructureExposure summary counts
          - Detailed list of intersected asset records
        """
        if self._gdf is None:
            self._load_dataset()

        ports_count = 0
        airports_count = 0
        hospitals_count = 0
        highway_km = 0.0
        detailed_assets = []

        for idx, row in self._gdf.iterrows():
            geom = row.geometry
            if geom is None or not geom.is_valid:
                continue

            if not corridor_polygon.intersects(geom):
                continue

            category = str(row.get('category', 'OTHER')).upper()
            name = str(row.get('name', 'Unknown Facility'))
            district = str(row.get('district', 'Coastal Zone'))
            state = str(row.get('state', 'India'))

            if category == "PORT":
                ports_count += 1
            elif category == "AIRPORT":
                airports_count += 1
            elif category == "HOSPITAL":
                hospitals_count += 1
            elif category == "HIGHWAY":
                # Compute intersecting length of highway
                inter_line = corridor_polygon.intersection(geom)
                # Degrees to km rough approximation in tropical latitudes (~111 km/deg)
                highway_km += round(inter_line.length * 111.0, 1)

            detailed_assets.append({
                "name": name,
                "category": category,
                "district": district,
                "state": state
            })

        summary = InfrastructureExposure(
            major_ports=ports_count,
            airports=airports_count,
            hospitals=hospitals_count,
            national_highway_km=highway_km
        )

        return summary, detailed_assets
