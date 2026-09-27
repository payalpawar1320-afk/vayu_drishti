from typing import List, Dict, Any
from backend.app.schemas.gis import DistrictOverlap

class PopulationExposureEngine:
    """
    Computes estimated population exposure within a modeled cyclone risk corridor.
    Implements Section 29 of SPEC.md.
    Strictly uses scientific terminology: 'Estimated population within modeled risk zone'.
    """

    @staticmethod
    def calculate_total_exposure(intersected_districts: List[DistrictOverlap]) -> Dict[str, Any]:
        total_pop = sum(d.estimated_population for d in intersected_districts)
        
        # State-level breakdown
        state_breakdown = {}
        for d in intersected_districts:
            state_breakdown[d.state_name] = state_breakdown.get(d.state_name, 0) + d.estimated_population

        return {
            "label": "Estimated population within modeled risk zone",
            "total_population_exposed": total_pop,
            "districts_count": len(intersected_districts),
            "state_breakdown": state_breakdown,
            "scientific_disclaimer": "Modeled spatial exposure based on administrative census density. Not a prediction of casualties or damage."
        }
