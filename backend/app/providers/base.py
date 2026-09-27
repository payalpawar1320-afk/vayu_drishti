from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..schemas.storm import StormSummary, StormDetail, BestTrackPoint
from ..schemas.observation import FusedObservation

class DataProvider(ABC):
    """
    Abstract Base Class for Cyclone Intelligence Data Providers.
    Follows Section 45 of SPEC.md to decouple storage/sources from core logic.
    """

    @abstractmethod
    def get_storms(self, basin: Optional[str] = None, year: Optional[int] = None) -> List[StormSummary]:
        """Returns list of monitored or historical storms."""
        pass

    @abstractmethod
    def get_storm_detail(self, storm_id: str) -> Optional[StormDetail]:
        """Returns complete storm best-track history and lifecycle."""
        pass

    @abstractmethod
    def get_observation(self, storm_id: str, timestamp: str) -> Optional[FusedObservation]:
        """Returns normalized, multi-source observation for a given time step."""
        pass

    @abstractmethod
    def get_timeline(self, storm_id: str) -> List[Dict[str, Any]]:
        """Returns observation timeline intervals for temporal analysis."""
        pass
