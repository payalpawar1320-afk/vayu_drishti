import torch
import numpy as np
from typing import Dict, Any, List

class SequenceFeatureAttribution:
    """
    Computes gradient-based feature attribution and sensitivity
    for CycloneTemporalTrackNet predictions per Section 25 of SPEC.md.
    """

    FEATURE_NAMES = [
        "Latitude Position",
        "Longitude Position",
        "Meridional Translation Velocity (dLat)",
        "Zonal Translation Velocity (dLon)",
        "Sustained Wind Intensity",
        "Central Minimum Pressure",
        "Azimuthal Cloud Symmetry",
        "Spatial Cloud Organization",
        "Central Dense Overcast Core Temperature",
        "Sea Surface Temperature (SST)",
        "Vertical Wind Shear"
    ]

    @classmethod
    def attribute(cls, model: torch.nn.Module, sequence_tensor: torch.Tensor, target_horizon_idx: int = 0) -> Dict[str, float]:
        """
        Computes input gradient magnitude for each feature dimension
        indicating which meteorological factor most influenced the trajectory.
        target_horizon_idx: 0 (6h), 1 (12h), 2 (24h), 3 (48h)
        """
        model.eval()
        if len(sequence_tensor.shape) == 2:
            sequence_tensor = sequence_tensor.unsqueeze(0)

        # Clone tensor with grad enabled
        x = sequence_tensor.clone().detach().requires_grad_(True)
        track_deltas, stage_logits = model(x)

        # Select target coordinate delta (e.g. 6h dlat)
        target = track_deltas[0, target_horizon_idx * 2]
        model.zero_grad()
        target.backward()

        # Compute mean absolute gradient over temporal dimension
        grads = x.grad[0].abs().mean(dim=0).cpu().numpy()
        total_grad = np.sum(grads) + 1e-8
        normalized_importance = grads / total_grad

        attributions = {
            cls.FEATURE_NAMES[i]: round(float(normalized_importance[i]), 4)
            for i in range(len(cls.FEATURE_NAMES))
        }

        # Sort descending by importance
        sorted_attr = dict(sorted(attributions.items(), key=lambda item: item[1], reverse=True))
        return sorted_attr
