"""Weather service for retrieving and processing weather data.

Refactored to use the new adapter/ingestion architecture
while maintaining backward compatibility.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.ingestion_service import WeatherIngestionService
from app.models.weather_observation import WeatherObservation

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Weather service providing unified access to weather data.
    """

    def __init__(self) -> None:
        """Initialize weather service."""
        self.ingestion_service = WeatherIngestionService()

    def get_latest_observations(
        self,
        fuente: Optional[str] = None,
        tipo_dato: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get latest weather observations.

        Args:
            fuente: Filter by source (ideam_radar, sab_lluvias)
            tipo_dato: Filter by data type
            limit: Maximum number of records

        Returns:
            List of observation records
        """
        query = WeatherObservation.query

        if fuente:
            query = query.filter_by(fuente=fuente)
        if tipo_dato:
            query = query.filter_by(tipo_dato=tipo_dato)

        query = query.order_by(WeatherObservation.timestamp_observacion.desc())
        observations = query.limit(limit).all()
        return [obs.to_dict() for obs in observations]

    def ingest_data(self, source_name: str, **kwargs) -> Dict[str, Any]:
        """
        Trigger data ingestion from specific source.

        Args:
            source_name: Source to ingest from
            **kwargs: Source-specific parameters

        Returns:
            Ingestion result
        """
        return self.ingestion_service.ingest_from_source(source_name, **kwargs)

    def ingest_all_sources(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Trigger ingestion from all available sources.

        Args:
            **kwargs: Parameters for each source

        Returns:
            List of ingestion results
        """
        return self.ingestion_service.ingest_all(**kwargs)

    def get_sources_info(self) -> Dict[str, Any]:
        """Get information about available sources."""
        return {
            "available_sources": self.ingestion_service.get_available_sources(),
            "timestamp": datetime.utcnow().isoformat()
        }


# Maintain backward compatibility - expose WeatherService as default
weather_service = WeatherService()
