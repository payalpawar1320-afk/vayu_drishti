from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from backend.app.schemas.prediction import IntensityTrendInfo, ExplainabilityInfo
from backend.app.schemas.storm import BestTrackPoint
from backend.app.schemas.evolution import EvolutionFingerprint

TupleTrend = Tuple[IntensityTrendInfo, ExplainabilityInfo]

class PhysicalIntensityTrendBaseline:

    """
    Physical Pressure Tendency & Environmental Intensity Baseline Model.
    Predicts STRENGTHENING, STABLE, or WEAKENING with explainability factors.
    Implements Sections 24 and 25 of SPEC.md.
    """

    @staticmethod
    def predict_intensity_trend(
        recent_points: List[BestTrackPoint],
        evolution_fingerprint: Optional[EvolutionFingerprint] = None,
        sst_c: float = 30.2,
        shear_kt: float = 10.5
    ) -> TupleTrend:
        """
        Calculates intensity trend based on:
        1. 24h central pressure change (dp/dt)
        2. 24h sustained wind change (dv/dt)
        3. Environmental sea surface temperature (SST) & vertical wind shear
        4. Central Dense Overcast (CDO) deepening from evolution fingerprint
        """
        if not recent_points:
            raise ValueError("Recent points required")

        curr_pt = recent_points[-1]
        earliest_pt = recent_points[0]

        curr_wind = curr_pt.max_sustained_wind_kt or 45.0
        earliest_wind = earliest_pt.max_sustained_wind_kt or curr_wind
        wind_delta = curr_wind - earliest_wind

        curr_pres = curr_pt.min_central_pressure_mb
        earliest_pres = earliest_pt.min_central_pressure_mb
        pres_delta = (curr_pres - earliest_pres) if (curr_pres and earliest_pres) else -wind_delta * 0.7

        # Explainability evidence list
        explainability_drivers = []
        structural_weights = {}

        # 1. Kinematic / best-track pressure factor
        if pres_delta <= -12.0 or wind_delta >= 15.0:
            pressure_vote = "STRENGTHENING"
            explainability_drivers.append(f"Recent central pressure dropped significantly ({pres_delta:.1f} mb in sequence)")
            structural_weights["pressure_drop_factor"] = 0.35
        elif pres_delta >= 10.0 or wind_delta <= -15.0:
            pressure_vote = "WEAKENING"
            explainability_drivers.append(f"Central pressure increased (+{pres_delta:.1f} mb in sequence)")
            structural_weights["pressure_rise_factor"] = 0.35
        else:
            pressure_vote = "STABLE"
            explainability_drivers.append("Central pressure and sustained wind remained steady over past 12-24 hours")
            structural_weights["pressure_stability"] = 0.25

        # 2. Environmental SST factor (warm waters > 28C encourage intensification)
        if sst_c >= 29.5:
            explainability_drivers.append(f"High Sea Surface Temperature ({sst_c:.1f}°C) exceeds rapid intensification threshold (>28.5°C)")
            structural_weights["favorable_sst"] = 0.25
        elif sst_c < 26.5:
            explainability_drivers.append(f"Cooler Sea Surface Temperature ({sst_c:.1f}°C) inhibits deep convection")
            structural_weights["unfavorable_sst"] = 0.25

        # 3. Environmental vertical wind shear (< 12 kt is favorable)
        if shear_kt <= 12.0:
            explainability_drivers.append(f"Low vertical wind shear ({shear_kt:.1f} kt) provides favorable dynamic conditions for vertical vortex alignment")
            structural_weights["low_wind_shear"] = 0.20
        else:
            explainability_drivers.append(f"Moderate to high vertical wind shear ({shear_kt:.1f} kt) exerts convective tilting")
            structural_weights["high_wind_shear"] = 0.20

        # 4. Satellite evolution structural indicator
        if evolution_fingerprint:
            ind = evolution_fingerprint.indicators
            if ind.cdo_deepening_trend in ["COOLING_RAPID", "COOLING"]:
                explainability_drivers.append(f"Central Dense Overcast cloud tops cooled to {ind.central_dense_overcast_temp_k:.1f} K indicating vigorous convection")
                structural_weights["cdo_deepening"] = 0.20
            if ind.symmetry_change_24h and ind.symmetry_change_24h > 0.05:
                explainability_drivers.append(f"Azimuthal symmetry increased (+{ind.symmetry_change_24h:.2f}) showing spiral organization")
                structural_weights["spiral_organization"] = 0.15

        # Consensus determination
        if pressure_vote == "STRENGTHENING" or (sst_c >= 29.5 and shear_kt <= 12.0 and wind_delta >= 0):
            trend_label = "STRENGTHENING"
            confidence = 0.84 if pressure_vote == "STRENGTHENING" else 0.72
        elif pressure_vote == "WEAKENING":
            trend_label = "WEAKENING"
            confidence = 0.81
        else:
            trend_label = "STABLE"
            confidence = 0.75

        trend_info = IntensityTrendInfo(
            trend_label=trend_label,
            trend_confidence=confidence,
            confidence_derivation="AGREEMENT_BETWEEN_SST_SHEAR_CDO_AND_HISTORICAL_PRESSURE_DELTA"
        )

        explain_info = ExplainabilityInfo(
            key_drivers=explainability_drivers,
            structural_contributions=structural_weights
        )

        return trend_info, explain_info

