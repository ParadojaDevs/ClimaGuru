"""HTML parser wrapper."""
from typing import List, Dict, Any
from app.adapters.parsers.base_parser import BaseParser
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None


class HTMLParser(BaseParser):
    def get_format_name(self) -> str:
        return "html"

    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        if BeautifulSoup is None:
            return []
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(content, 'html.parser')
        records = []
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th','td'])]
            for row in rows[1:]:
                cells = row.find_all(['td','th'])
                rec = {}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f'col_{i}'
                    rec[key] = cell.get_text(strip=True)
                records.append(rec)
        return records
