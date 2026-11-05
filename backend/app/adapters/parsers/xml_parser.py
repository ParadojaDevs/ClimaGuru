"""XML parser (basic)."""
from typing import List, Dict, Any
from app.adapters.parsers.base_parser import BaseParser
try:
    import xml.etree.ElementTree as ET
except Exception:
    ET = None


class XMLParser(BaseParser):
    def get_format_name(self) -> str:
        return "xml"

    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        if ET is None:
            return []
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        try:
            root = ET.fromstring(content) if isinstance(content, str) else content
            # Flatten simple structure
            records = []
            for child in root:
                rec = {'tag': child.tag}
                rec.update(child.attrib)
                if child.text and child.text.strip():
                    rec['text'] = child.text.strip()
                records.append(rec)
            return records
        except Exception:
            return []
