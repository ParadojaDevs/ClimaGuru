"""JSON parser."""
import json
from typing import List, Dict, Any
from app.adapters.parsers.base_parser import BaseParser


class JSONParser(BaseParser):
    def get_format_name(self) -> str:
        return "json"

    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        if isinstance(content, str):
            data = json.loads(content)
        elif isinstance(content, bytes):
            data = json.loads(content.decode('utf-8'))
        else:
            data = content
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        return []
