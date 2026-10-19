"""HDF5 parser stub (optional deps)."""
from typing import List, Dict, Any
from app.adapters.parsers.base_parser import BaseParser
try:
    import h5py
except Exception:
    h5py = None


class HDF5Parser(BaseParser):
    def get_format_name(self) -> str:
        return "hdf5"

    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        if h5py is None:
            return []
        return []
