import numpy as np
from typing import Dict, Any, List, Optional
from shapely.geometry import Polygon

from ..corridor.risk_corridor_generator import RiskCorridorGenerator
from ..intersection.district_intersect import DistrictIntersectionEngine
from ..infrastructure.asset_exposure import AssetExposureEngine
from ..population.population_exposure import PopulationExposureEngine
from backend.app.schemas.gis import (
    ScenarioShiftRequest, ScenarioShiftResponse,
    SummaryExposure, InfrastructureExposure, DistrictOverlap
)

class ImpactShiftSimulator:
    """
    Scenario Analysis & Impact Shift Simulator engine.
    Computes real-time exposure differentials under parametric track,
    intensity, and corridor width variations.
    Implements Section 31 of SPEC.md.
    """

    def __init__(
        self,
        corridor_gen: Optional[RiskCorridorGenerator] = None,
        district_engine: Optional[DistrictIntersectionEngine] = None,
        asset_engine: Optional[AssetExposureEngine] = None
    ):
        self.corridor_gen = corridor_gen or RiskCorridorGenerator()
        self.district_engine = district_engine or DistrictIntersectionEngine()
        self.asset_engine = asset_engine or AssetExposureEngine()

    def simulate(
        self,
        forecast_points: List[Dict[str, Any]],
        request: ScenarioShiftRequest
    ) -> ScenarioShiftResponse:
        """
        Executes comparative scenario analysis between baseline forecast
        and perturbed track/intensity/width scenario.
        """
        if not forecast_points:
            raise ValueError("forecast_points cannot be empty")

        # 1. Compute Base Corridor & Exposure
        base_poly, base_params = self.corridor_gen.generate_corridor(
            forecast_points,
            corridor_width_multiplier=1.0,
            shift_vector_km=(0.0, 0.0)
        )
        base_districts = self.district_engine.intersect(base_poly)
        base_infra_summary, _ = self.asset_engine.calculate_exposure(base_poly)
        base_pop_summary = PopulationExposureEngine.calculate_total_exposure(base_districts)

        base_summary = SummaryExposure(
            estimated_population_exposed=base_pop_summary["total_population_exposed"],
            total_districts_intersected=len(base_districts),
            critical_infrastructure_counts=base_infra_summary
        )

        # 2. Determine Perturbation Vector (dx_km, dy_km)
        shift_km = request.track_shift_km
        direction = request.track_shift_direction.upper()
        
        dx_km = 0.0
        dy_km = 0.0
        if direction == "EAST":
            dx_km = shift_km
        elif direction == "WEST":
            dx_km = -shift_km
        elif direction == "NORTH":
            dy_km = shift_km
        elif direction == "SOUTH":
            dy_km = -shift_km

        # Intensity modifier influences corridor buffer expansion factor
        intensity_factor = 1.0
        if request.intensity_modifier.upper() == "HIGHER":
            intensity_factor = 1.25
        elif request.intensity_modifier.upper() == "LOWER":
            intensity_factor = 0.85

        effective_width_mult = max(0.5, min(3.0, request.corridor_width_multiplier * intensity_factor))

        # 3. Compute Simulated Corridor & Exposure
        sim_poly, sim_params = self.corridor_gen.generate_corridor(
            forecast_points,
            corridor_width_multiplier=effective_width_mult,
            shift_vector_km=(dx_km, dy_km)
        )
        sim_districts = self.district_engine.intersect(sim_poly)
        sim_infra_summary, _ = self.asset_engine.calculate_exposure(sim_poly)
        sim_pop_summary = PopulationExposureEngine.calculate_total_exposure(sim_districts)

        sim_summary = SummaryExposure(
            estimated_population_exposed=sim_pop_summary["total_population_exposed"],
            total_districts_intersected=len(sim_districts),
            critical_infrastructure_counts=sim_infra_summary
        )

        # 4. Compute Differentials (Added/Dropped Districts & Exposure Delta)
        base_dist_names = set(d.district_name for d in base_districts)
        sim_dist_names = set(d.district_name for d in sim_districts)

        districts_added = sorted(list(sim_dist_names - base_dist_names))
        districts_dropped = sorted(list(base_dist_names - sim_dist_names))

        pop_delta = sim_summary.estimated_population_exposed - base_summary.estimated_population_exposed
        pop_pct_delta = round((pop_delta / max(1, base_summary.estimated_population_exposed)) * 100.0, 1)

        exposure_delta = {
            "population_delta": pop_delta,
            "population_percent_change": pop_pct_delta,
            "districts_count_delta": len(sim_districts) - len(base_districts),
            "ports_delta": sim_infra_summary.major_ports - base_infra_summary.major_ports,
            "airports_delta": sim_infra_summary.airports - base_infra_summary.airports,
            "hospitals_delta": sim_infra_summary.hospitals - base_infra_summary.hospitals,
            "highway_km_delta": round(sim_infra_summary.national_highway_km - base_infra_summary.national_highway_km, 1)
        }

        scenario_label = f"TRACK_{direction}_{int(shift_km)}KM_{request.intensity_modifier.upper()}"
        corridor_geojson = self.corridor_gen.polygon_to_geojson_feature(
            sim_poly,
            properties={
                "scenario_name": scenario_label,
                "is_simulation": True,
                "shift_km": shift_km,
                "direction": direction,
                "effective_width_multiplier": round(effective_width_mult, 2)
            }
        )

        base_corridor_geojson = self.corridor_gen.polygon_to_geojson_feature(
            base_poly,
            properties={
                "scenario_name": "BASELINE_FORECAST",
                "is_simulation": False,
                "shift_km": 0.0,
                "direction": "NONE"
            }
        )

        return ScenarioShiftResponse(
            scenario_name=scenario_label,
            simulation_flag="SIMULATED_SCENARIO (NOT AN OFFICIAL FORECAST)",
            corridor_geojson=corridor_geojson,
            base_corridor_geojson=base_corridor_geojson,
            base_exposure=base_summary,
            simulated_exposure=sim_summary,
            exposure_delta=exposure_delta,
            districts_added=districts_added,
            districts_dropped=districts_dropped
        )
