import numpy as np
from typing import List, Dict, Any, Tuple
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union
import pyproj
from shapely.ops import transform

class RiskCorridorGenerator:
    """
    Generates a scientifically modeled cyclone risk corridor (cone of uncertainty)
    along a predicted or observed cyclone track.
    Implements Section 27 of SPEC.md.
    """

    def __init__(self, base_radius_km: float = 40.0, hourly_expansion_km: float = 2.5):
        self.base_radius_km = base_radius_km
        self.hourly_expansion_km = hourly_expansion_km

        # Pyproj transformers for accurate geodesic metric buffering
        # WGS84 (degrees) <-> Web Mercator / Geodesic Metric (meters)
        self.wgs84_to_mercator = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
        self.mercator_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform

    def generate_corridor(
        self,
        forecast_points: List[Dict[str, Any]],
        corridor_width_multiplier: float = 1.0,
        shift_vector_km: Tuple[float, float] = (0.0, 0.0)
    ) -> Tuple[Polygon, Dict[str, Any]]:
        """
        Builds the expanding risk corridor polygon.
        forecast_points: list of dicts with 'lat', 'lon', and optional 'horizon_hours'.
        shift_vector_km: (dx_km, dy_km) offset in kilometers (used for scenario simulation).
        """
        if not forecast_points:
            raise ValueError("forecast_points cannot be empty")

        if len(forecast_points) == 1:
            # Single point: circular buffer
            pt = forecast_points[0]
            lat = pt['lat'] + (shift_vector_km[1] / 111.0)
            lon = pt['lon'] + (shift_vector_km[0] / (111.0 * np.cos(np.radians(pt['lat']))))
            horizon = pt.get('horizon_hours', 0)
            radius_km = (self.base_radius_km + self.hourly_expansion_km * horizon) * corridor_width_multiplier
            
            p_geom = Point(lon, lat)
            p_metric = transform(self.wgs84_to_mercator, p_geom)
            corridor_metric = p_metric.buffer(radius_km * 1000.0)
            corridor_wgs84 = transform(self.mercator_to_wgs84, corridor_metric)
            
            return corridor_wgs84, {
                "buffer_type": "CIRCULAR_BUFFER",
                "radius_km": radius_km,
                "points_count": 1
            }

        # Multiple points: expanding uncertainty envelope along track segments
        buffers = []
        for i, pt in enumerate(forecast_points):
            lat = pt['lat'] + (shift_vector_km[1] / 111.0)
            lon = pt['lon'] + (shift_vector_km[0] / (111.0 * max(0.1, np.cos(np.radians(pt['lat'])))))
            horizon = pt.get('horizon_hours', i * 6)
            
            radius_km = (self.base_radius_km + self.hourly_expansion_km * horizon) * corridor_width_multiplier
            radius_meters = radius_km * 1000.0

            p_geom = Point(lon, lat)
            p_metric = transform(self.wgs84_to_mercator, p_geom)
            buffers.append(p_metric.buffer(radius_meters))

        # Also buffer the connecting track line to prevent necking
        coords_metric = []
        for pt in forecast_points:
            lat = pt['lat'] + (shift_vector_km[1] / 111.0)
            lon = pt['lon'] + (shift_vector_km[0] / (111.0 * max(0.1, np.cos(np.radians(pt['lat'])))))
            p_metric = transform(self.wgs84_to_mercator, Point(lon, lat))
            coords_metric.append((p_metric.x, p_metric.y))

        line_metric = LineString(coords_metric)
        initial_radius_meters = self.base_radius_km * corridor_width_multiplier * 1000.0
        line_buffer = line_metric.buffer(initial_radius_meters)
        buffers.append(line_buffer)

        # Merge all metric buffers into single contiguous polygon
        merged_metric = unary_union(buffers)
        if isinstance(merged_metric, MultiPolygon):
            merged_metric = merged_metric.convex_hull

        # Transform back to WGS84 (EPSG:4326)
        corridor_wgs84 = transform(self.mercator_to_wgs84, merged_metric)

        params = {
            "buffer_type": "EXPANDING_CONE_OF_UNCERTAINTY",
            "base_radius_km": self.base_radius_km * corridor_width_multiplier,
            "hourly_expansion_km": self.hourly_expansion_km * corridor_width_multiplier,
            "multiplier": corridor_width_multiplier,
            "points_count": len(forecast_points),
            "area_sq_km": round(merged_metric.area / 1e6, 1)
        }

        return corridor_wgs84, params

    @staticmethod
    def polygon_to_geojson_feature(polygon: Polygon, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Converts Shapely Polygon to standard GeoJSON Feature."""
        return {
            "type": "Feature",
            "geometry": mapping(polygon),
            "properties": properties or {"level": "MODELED_RISK_CORRIDOR"}
        }
