"""IDEAM Radar data source adapter.

Integrates existing IDEAM radar processing from src/ modules
into backend with adapter pattern.
"""
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.adapters.base import WeatherDataSource

logger = logging.getLogger(__name__)

# Add src to path for reuse of existing modules
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


class IDEAMRadarSourceAdapter(WeatherDataSource):
    """
    Adapter for IDEAM radar data.

    Reuses logic from src.data_sources.ideam_radar_downloader
    and src.processors.radar_processor for consistency.
    """

    def __init__(self, data_dir: str = "data/Radar_IDEAM") -> None:
        """
        Initialize IDEAM radar adapter.

        Args:
            data_dir: Directory to store/read radar data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        try:
            from data_sources.ideam_radar_downloader import IDEAMRadarDownloader
            self.downloader = IDEAMRadarDownloader(base_dir=str(self.data_dir))
        except Exception as e:
            logger.warning(f"Could not initialize IDEAM downloader: {e}")
            self.downloader = None

    def get_source_name(self) -> str:
        """Return source identifier."""
        return "ideam_radar"

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch IDEAM radar data.

        Args:
            **kwargs: radar, fecha, limite, etc.

        Returns:
            List of raw metadata/records
        """
        records = []
        radar = kwargs.get("radar", "Barrancabermeja")
        fecha = kwargs.get("fecha")

        if self.downloader is None:
            logger.warning("Downloader not available")
            return records

        try:
            archivos = self.downloader.listar_archivos_disponibles(
                radar=radar,
                fecha=fecha,
                limite=kwargs.get("limite", 100)
            )
            for arch in archivos:
                records.append({
                    "radar": radar,
                    "archivo": arch.get("clave") or arch.get("archivo"),
                    "tamanio": arch.get("tamanio"),
                    "fecha": str(fecha) if fecha else None,
                    "raw": arch
                })
        except Exception as e:
            logger.error(f"Error fetching IDEAM radar data: {e}")
            raise

        return records

    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize IDEAM radar data."""
        normalized = []
        now = datetime.utcnow()

        for rec in raw_data:
            norm_record = {
                "fuente": "ideam_radar",
                "estacion": rec.get("radar"),
                "ciudad": rec.get("radar"),
                "latitud": None,
                "longitud": None,
                "timestamp_observacion": now,
                "tipo_dato": "radar_reflectividad",
                "valor": None,
                "unidad": "dBZ",
                "calidad": "raw_metadata",
                "metadatos": rec,
                "datos_crudos": rec.get("raw")
            }
            normalized.append(norm_record)

        return normalized

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        """Validate normalized IDEAM data."""
        if not isinstance(normalized_data, list):
            return False
        if not normalized_data:
            return True
        for rec in normalized_data:
            if rec.get("fuente") != "ideam_radar":
                return False
        return True
