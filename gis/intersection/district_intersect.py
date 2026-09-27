import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import geopandas as gpd
from shapely.geometry import Polygon

from backend.app.schemas.gis import DistrictOverlap

class DistrictIntersectionEngine:
    """
    Computes precise spatial intersection between a modeled cyclone risk corridor
    and Indian administrative district boundaries.
    Implements Section 28 of SPEC.md.
    """

    _cached_gdf: Optional[gpd.GeoDataFrame] = None
    _cached_pop_data: Optional[Dict[str, int]] = None

    def __init__(
        self,
        districts_geojson_path: Optional[Path] = None,
        population_ref_path: Optional[Path] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.districts_path = districts_geojson_path or (base_dir / "data" / "raw" / "gis" / "india_districts.geojson")
        self.pop_path = population_ref_path or (base_dir / "data" / "raw" / "gis" / "district_population_reference.json")
        self._cache_pkl_path = self.districts_path.with_suffix('.pkl')
        
        self._load_datasets()

    @property
    def _gdf(self) -> gpd.GeoDataFrame:
        return DistrictIntersectionEngine._cached_gdf

    @property
    def _pop_data(self) -> Dict[str, int]:
        return DistrictIntersectionEngine._cached_pop_data or {}

    def _load_datasets(self):
        # 1. Reuse existing in-memory cache if already loaded
        if DistrictIntersectionEngine._cached_gdf is not None and DistrictIntersectionEngine._cached_pop_data is not None:
            return

        # 2. Try loading fast pre-compiled pickle cache
        if self._cache_pkl_path.exists():
            try:
                import pickle
                with open(self._cache_pkl_path, "rb") as f:
                    cached_obj = pickle.load(f)
                    if isinstance(cached_obj, tuple) and len(cached_obj) == 2:
                        DistrictIntersectionEngine._cached_gdf, DistrictIntersectionEngine._cached_pop_data = cached_obj
                        return
            except Exception as e:
                print(f"[DistrictIntersectionEngine] Warning: Failed to load pkl cache: {e}")

        if not self.districts_path.exists():
            raise FileNotFoundError(f"Districts GeoJSON not found at {self.districts_path}")
        
        print(f"[DistrictIntersectionEngine] Loading {self.districts_path} (generating fast cache)...")
        gdf = gpd.read_file(self.districts_path)
        
        # Standardize state and district names
        if 'NAME_1' in gdf.columns:
            gdf['STATE_NORM'] = gdf['NAME_1'].replace({"Orissa": "Odisha"})
        else:
            gdf['STATE_NORM'] = "India"
            
        if 'NAME_2' in gdf.columns:
            gdf['DISTRICT_NORM'] = gdf['NAME_2']
        else:
            gdf['DISTRICT_NORM'] = gdf.get('district', 'Unknown')

        pop_data = {}
        # Load census population references
        if self.pop_path.exists():
            with open(self.pop_path, "r", encoding="utf-8") as f:
                pop_data = json.load(f)

        DistrictIntersectionEngine._cached_gdf = gdf
        DistrictIntersectionEngine._cached_pop_data = pop_data

        # Save fast pickle cache for instant subsequent startups
        try:
            import pickle
            with open(self._cache_pkl_path, "wb") as f:
                pickle.dump((gdf, pop_data), f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"[DistrictIntersectionEngine] Saved fast binary cache to {self._cache_pkl_path}")
        except Exception as e:
            print(f"[DistrictIntersectionEngine] Notice: Could not write pickle cache: {e}")

    def intersect(self, corridor_polygon: Polygon) -> List[DistrictOverlap]:
        """
        Intersects the corridor polygon with all district boundaries.
        Returns sorted list of affected districts by overlap percentage.
        """
        if self._gdf is None:
            self._load_datasets()

        # Bounding box pre-filter for performance
        minx, miny, maxx, maxy = corridor_polygon.bounds
        candidates = self._gdf.cx[minx:maxx, miny:maxy]

        results: List[DistrictOverlap] = []

        for idx, row in candidates.iterrows():
            dist_geom = row.geometry
            if dist_geom is None or not dist_geom.is_valid:
                continue

            if not corridor_polygon.intersects(dist_geom):
                continue

            # Compute intersection polygon
            try:
                intersection_geom = corridor_polygon.intersection(dist_geom)
            except Exception:
                intersection_geom = corridor_polygon.buffer(0).intersection(dist_geom.buffer(0))

            if intersection_geom.is_empty:
                continue

            # Area overlap ratio
            dist_area = dist_geom.area
            inter_area = intersection_geom.area
            overlap_pct = min(100.0, max(0.1, round((inter_area / dist_area) * 100.0, 1)))

            state_name = str(row['STATE_NORM'])
            dist_name = str(row['DISTRICT_NORM'])
            dist_id = f"IND_{state_name[:3].upper()}_{dist_name.replace(' ', '_').upper()}"

            # Population lookup with fallback based on state density
            census_pop = self._pop_data.get(dist_name)
            if not census_pop:
                # Approximate fallback by district area in degrees (~2M per district average in coastal India)
                census_pop = int(max(400000, min(8000000, dist_area * 15000000)))

            # Estimated population within modeled risk zone
            estimated_exposed = int(census_pop * (overlap_pct / 100.0))

            # Coastal classification
            is_coastal = state_name in ["West Bengal", "Odisha", "Andhra Pradesh", "Tamil Nadu", "Gujarat", "Maharashtra"]
            risk_class = self._determine_risk_level(overlap_pct, is_coastal)

            results.append(DistrictOverlap(
                district_id=dist_id,
                district_name=dist_name,
                state_name=state_name,
                area_overlap_pct=overlap_pct,
                risk_classification=risk_class,
                estimated_population=estimated_exposed,
                coastal_length_km=round(float(dist_area * 150.0), 1) if is_coastal else 0.0
            ))

        # Sort by overlap percentage descending
        results.sort(key=lambda d: d.area_overlap_pct, reverse=True)
        return results

    @staticmethod
    def _determine_risk_level(overlap_pct: float, is_coastal: bool) -> str:
        """Categorizes risk level based on Section 28 rules."""
        if is_coastal and overlap_pct >= 50.0:
            return "CRITICAL_LANDFALL"
        elif overlap_pct >= 40.0:
            return "HIGH"
        elif overlap_pct >= 15.0:
            return "MODERATE"
        else:
            return "LOW"
