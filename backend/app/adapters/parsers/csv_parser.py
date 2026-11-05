"""CSV parser."""
from typing import List, Dict, Any
from io import StringIO
import csv
from app.adapters.parsers.base_parser import BaseParser


class CSVParser(BaseParser):
    def get_format_name(self) -> str:
        return "csv"

    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        if not isinstance(content, str):
            return []
        try:
            f = StringIO(content)
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
        except Exception:
            return []
