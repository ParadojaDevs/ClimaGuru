"""Weather data ingestion service.

Orchestrates data collection from multiple sources using adapter pattern,
normalizes data, and persists to database following SOLID principles.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app import db
from app.models.weather_observation import WeatherObservation
from app.adapters.base import WeatherDataSource
from app.adapters.sab_adapter import SABSourceAdapter
from app.adapters.ideam_radar_adapter import IDEAMRadarSourceAdapter

logger = logging.getLogger(__name__)


class WeatherIngestionService:
    """
    Service for orchestrating weather data ingestion.

    Uses adapter pattern to abstract data sources and provides
    unified interface for ingestion and persistence.
    """

    def __init__(self) -> None:
        """Initialize ingestion service with available adapters."""
        self.adapters: Dict[str, WeatherDataSource] = {}
        self._register_adapters()

    def _register_adapters(self) -> None:
        """Register available data source adapters."""
        try:
            self.adapters["sab_lluvias"] = SABSourceAdapter()
            logger.info("Registered SAB adapter")
        except Exception as e:
            logger.warning(f"Failed to register SAB adapter: {e}")

        try:
            self.adapters["ideam_radar"] = IDEAMRadarSourceAdapter()
            logger.info("Registered IDEAM radar adapter")
        except Exception as e:
            logger.warning(f"Failed to register IDEAM radar adapter: {e}")

    def get_available_sources(self) -> List[str]:
        """Return list of available data sources."""
        return list(self.adapters.keys())

    def ingest_from_source(
        self,
        source_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ingest data from specified source.

        Args:
            source_name: Name of source to ingest from
            **kwargs: Source-specific parameters

        Returns:
            Ingestion result summary
        """
        if source_name not in self.adapters:
            raise ValueError(
                f"Source '{source_name}' not available. "
                f"Available: {self.get_available_sources()}"
            )

        adapter = self.adapters[source_name]
        logger.info(f"Starting ingestion from {source_name}")

        try:
            raw_data = adapter.fetch(**kwargs)
            normalized_data = adapter.normalize(raw_data)
            if not adapter.validate(normalized_data):
                raise ValueError("Normalized data validation failed")

            saved_count = self._persist(normalized_data)
            logger.info(
                f"Ingestion from {source_name} completed: "
                f"{saved_count} records saved"
            )

            return {
                "source": source_name,
                "status": "success",
                "raw_count": len(raw_data),
                "normalized_count": len(normalized_data),
                "saved_count": saved_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Ingestion from {source_name} failed: {e}")
            return {
                "source": source_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _persist(self, normalized_data: List[Dict[str, Any]]) -> int:
        """
        Persist normalized data to database.

        Args:
            normalized_data: List of normalized observation records

        Returns:
            Number of records saved
        """
        saved_count = 0
        for record in normalized_data:
            try:
                obs = WeatherObservation(**record)
                db.session.add(obs)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to persist record: {e}")
                continue
        db.session.commit()
        return saved_count

    def ingest_all(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Ingest from all available sources.

        Args:
            **kwargs: Parameters passed to each adapter

        Returns:
            List of ingestion results per source
        """
        results = []
        for source_name in self.get_available_sources():
            results.append(self.ingest_from_source(source_name, **kwargs))
        return results
