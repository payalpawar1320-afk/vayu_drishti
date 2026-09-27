import torch
import torch.nn as nn
from typing import Tuple, Dict, Any, List

class CycloneTemporalTrackNet(nn.Module):
    """
    Deep Bidirectional Recurrent Neural Network for Tropical Cyclone
    Multi-Horizon Track Prediction and Stage Classification.
    Implements Sections 23, 44, and 87 of SPEC.md.
    """

    def __init__(self, input_dim: int = 11, hidden_dim: int = 64, num_layers: int = 2):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # Input feature projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # Bi-directional GRU temporal sequence encoder
        self.recurrent = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.15 if num_layers > 1 else 0.0
        )

        # Multi-head attention pooling over temporal sequence states
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.Tanh(),
            nn.Linear(32, 1),
            nn.Softmax(dim=1)
        )

        # Track Prediction Head: 4 horizons (6h, 12h, 24h, 48h) -> 8 coordinates (dlat, dlon)
        self.track_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 8)
        )

        # Pattern / Stage Classification Head (5 classes: FORMING, DEVELOPING, MATURE, WEAKENING, REORGANIZING)
        self.stage_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, 5)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        x: (Batch, Sequence_Len, Input_Dim)
        Returns:
          track_deltas: (Batch, 8) -> [dlat_6h, dlon_6h, dlat_12h, dlon_12h, dlat_24h, dlon_24h, dlat_48h, dlon_48h]
          stage_logits: (Batch, 5)
        """
        b, t, d = x.shape
        proj = self.input_proj(x)
        out, _ = self.recurrent(proj) # (Batch, T, hidden_dim * 2)

        # Attention pooling over time
        attn_weights = self.attention(out) # (Batch, T, 1)
        context = torch.sum(out * attn_weights, dim=1) # (Batch, hidden_dim * 2)

        track_deltas = self.track_head(context)
        stage_logits = self.stage_head(context)

        return track_deltas, stage_logits

    def predict_horizons(
        self,
        sequence_tensor: torch.Tensor,
        current_lat: float,
        current_lon: float
    ) -> Dict[str, Any]:
        """Inference helper returning actual forecast coordinates."""
        self.eval()
        with torch.no_grad():
            if len(sequence_tensor.shape) == 2:
                sequence_tensor = sequence_tensor.unsqueeze(0)
            
            deltas, stage_logits = self.forward(sequence_tensor)
            d = deltas.squeeze(0).cpu().numpy()
            probs = torch.softmax(stage_logits, dim=-1).squeeze(0).cpu().numpy()

            stages = ["FORMING", "DEVELOPING", "MATURE", "WEAKENING", "REORGANIZING"]
            pred_stage_idx = int(probs.argmax())

            return {
                "forecast_points": [
                    {"horizon": 6, "lat": round(current_lat + float(d[0]), 2), "lon": round(current_lon + float(d[1]), 2)},
                    {"horizon": 12, "lat": round(current_lat + float(d[2]), 2), "lon": round(current_lon + float(d[3]), 2)},
                    {"horizon": 24, "lat": round(current_lat + float(d[4]), 2), "lon": round(current_lon + float(d[5]), 2)},
                    {"horizon": 48, "lat": round(current_lat + float(d[6]), 2), "lon": round(current_lon + float(d[7]), 2)}
                ],
                "stage": stages[pred_stage_idx],
                "stage_confidence": round(float(probs[pred_stage_idx]), 3),
                "stage_probabilities": {stages[i]: round(float(probs[i]), 3) for i in range(5)}
            }
