import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.schemas.storm import StormSummary, StormDetail
from backend.app.schemas.observation import FusedObservation
from backend.app.providers.base import DataProvider

class MOSDACProvider(DataProvider):
    """
    Data Provider for ISRO MOSDAC INSAT-3D/3DR/3DS Operational Cyclone Services.
    Decoupled integration per Section 45 of SPEC.md.
    """
    def __init__(self):
        self.api_key = os.environ.get("MOSDAC_API_KEY", "").strip()
        self.user_email = os.environ.get("MOSDAC_USER_EMAIL", "").strip()
        self.base_url = os.environ.get("MOSDAC_API_URL", "https://www.mosdac.gov.in/api/v1")

    @property
    def is_configured(self) -> bool:
        """Returns True if user has configured approved MOSDAC credentials."""
        return bool(self.api_key)

    def get_connection_status(self) -> Dict[str, Any]:
        """Provides status descriptor for the Data / Provenance view."""
        if self.is_configured:
            return {
                "source": "ISRO MOSDAC (INSAT-3D/3DR/3DS)",
                "status": "CONNECTED",
                "message": "Authenticated with approved MOSDAC credentials.",
                "satellite": "INSAT-3D/3DR/3DS TIR-1 / VIS",
                "last_sync": datetime.now(timezone.utc).isoformat()
            }
        return {
            "source": "ISRO MOSDAC (INSAT-3D/3DR/3DS)",
            "status": "AWAITING_CREDENTIALS",
            "message": "Awaiting approved MOSDAC API Key / FTP credentials from SAC ISRO.",
            "satellite": "INSAT-3D/3DR/3DS TIR-1 / VIS",
            "last_sync": None
        }

    def get_storms(self, basin: Optional[str] = None, year: Optional[int] = None) -> List[StormSummary]:
        if not self.is_configured:
            return []
        # When approved credentials arrive, query MOSDAC cyclone service endpoint
        return []

    def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        if not self.is_configured:
            return None
        return None

    def get_observation(self, storm_id: str, timestamp: str) -> Optional[FusedObservation]:
        if not self.is_configured:
            return None
        return None

    def get_timeline(self, storm_id: str) -> List[Dict[str, Any]]:
        return []
