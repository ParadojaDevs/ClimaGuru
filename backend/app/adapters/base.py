"""Base adapter interface for weather data sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class WeatherDataSource(ABC):
    @abstractmethod
    def get_source_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        raise NotImplementedError

    def get_version(self) -> str:
        return "1.0.0"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source": self.get_source_name(),
            "version": self.get_version(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_supported_formats(self) -> List[str]:
        return ["json", "html"]

    def supports_spatial_queries(self) -> bool:
        return False

    def get_spatial_bounds(self) -> Optional[Dict[str, float]]:
        return None

    def query_by_coords(self, lat: float, lon: float, **kwargs) -> List[Dict[str, Any]]:
        return []

    def get_rate_limit(self) -> Optional[Dict[str, Any]]:
        return None
