"""Base adapter interface for weather data sources.

Provides abstraction to collect, normalize and validate data
from multiple meteorological sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class WeatherDataSource(ABC):
    """
    Abstract base class for weather data source adapters.

    All concrete adapters must implement fetch, normalize, validate
    and metadata methods following SOLID principles.
    """

    @abstractmethod
    def get_source_name(self) -> str:
        """Return unique source identifier."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch raw data from source.

        Args:
            **kwargs: Source-specific parameters (dates, locations, etc.)

        Returns:
            List of raw data records
        """
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize raw data to internal schema.

        Args:
            raw_data: Raw data from fetch()

        Returns:
            List of normalized records conforming to WeatherObservation structure
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        """
        Validate normalized data structure.

        Args:
            normalized_data: Normalized data records

        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError

    def get_version(self) -> str:
        """Return adapter version."""
        return "1.0.0"

    def get_metadata(self) -> Dict[str, Any]:
        """Return adapter metadata."""
        return {
            "source": self.get_source_name(),
            "version": self.get_version(),
            "timestamp": datetime.utcnow().isoformat()
        }
