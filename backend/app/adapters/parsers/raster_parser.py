"""Raster/GeoTIFF parser stub (optional deps)."""
from typing import List, Dict, Any
from app.adapters.parsers.base_parser import BaseParser
try:
    import rasterio
except Exception:
    rasterio = None


class RasterParser(BaseParser):
    def get_format_name(self) -> str:
        return "geotiff"

    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        if rasterio is None:
            return []
        # Return metadata only as stub
        return []
