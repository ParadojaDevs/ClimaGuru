"""SAB (Sistema de Alerta de Bogota / Lluvias) data source adapter.

Implements scraping from https://app.sab.gov.co/sab/lluvias.htm with
proper error handling, timeouts, and retry mechanisms.
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.adapters.base import WeatherDataSource

logger = logging.getLogger(__name__)


class SABSourceAdapter(WeatherDataSource):
    """
    Adapter for SAB (Sistema de Alerta de Bogota) rainfall data.

    Fetches data from official SAB website with robust error handling,
    configurable timeouts, and retry logic with exponential backoff.
    """

    def __init__(
        self,
        base_url: str = "https://app.sab.gov.co/sab/lluvias.htm",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5
    ) -> None:
        """
        Initialize SAB adapter.

        Args:
            base_url: URL to SAB rainfall page
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            backoff_factor: Backoff factor for retry delays
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            backoff_factor=self.backoff_factor
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9",
            "Connection": "keep-alive"
        })
        return session

    def get_source_name(self) -> str:
        """Return source identifier."""
        return "sab_lluvias"

    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch rainfall data from SAB website.

        Args:
            **kwargs: Optional parameters (force_refresh, etc.)

        Returns:
            List of raw HTML/parsed records

        Raises:
            requests.RequestException: If fetch fails after retries
        """
        logger.info(f"Fetching data from SAB: {self.base_url}")
        try:
            response = self.session.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()

            if not response.encoding:
                response.encoding = response.apparent_encoding

            raw_content = response.text
            logger.info(f"SAB fetch successful: {len(raw_content)} chars")

            # Parse HTML and extract records
            records = self._parse_html(raw_content)
            logger.info(f"Extracted {len(records)} raw records from SAB")
            return records

        except requests.exceptions.Timeout as e:
            logger.error(f"SAB fetch timeout after {self.timeout}s: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"SAB fetch error: {e}")
            raise

    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content to extract rainfall data.

        Args:
            html: Raw HTML content

        Returns:
            List of parsed raw records
        """
        soup = BeautifulSoup(html, "html.parser")
        records = []

        # Try to find tables containing rainfall data
        tables = soup.find_all("table")
        if not tables:
            logger.warning("No tables found in SAB page")
            return records

        for idx, table in enumerate(tables):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                record = {"table_index": idx, "headers": headers, "raw_html": str(row)}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    record[key] = cell.get_text(strip=True)
                records.append(record)

        return records

    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize SAB raw data to internal schema.

        Args:
            raw_data: Raw data from fetch()

        Returns:
            List of normalized records
        """
        normalized = []
        now = datetime.utcnow()

        for idx, record in enumerate(raw_data):
            norm_record = {
                "fuente": "sab_lluvias",
                "estacion": record.get("estacion") or record.get("nombre") or record.get("punto"),
                "ciudad": "Bogota",
                "latitud": None,
                "longitud": None,
                "timestamp_observacion": now,
                "tipo_dato": "precipitacion",
                "valor": self._parse_float(record.get("lluvia") or record.get("precipitacion") or record.get("valor")),
                "unidad": "mm",
                "calidad": "parsed",
                "metadatos": {
                    "table_index": record.get("table_index"),
                    "headers": record.get("headers")
                },
                "datos_crudos": {k: v for k, v in record.items() if k != "raw_html"}
            }
            normalized.append(norm_record)

        return normalized

    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float value safely."""
        if value is None:
            return None
        try:
            # Remove non-numeric chars except . , -
            text = str(value).strip()
            if text == "" or text.lower() in ("nd", "n/d", "-", "s/d"):
                return None
            # Handle comma as decimal
            text = text.replace(",", ".")
            return float(text)
        except (ValueError, TypeError):
            return None

    def validate(self, normalized_data: List[Dict[str, Any]]) -> bool:
        """Validate normalized data."""
        if not isinstance(normalized_data, list):
            return False
        if not normalized_data:
            return True
        required = ["fuente", "timestamp_observacion", "tipo_dato"]
        for rec in normalized_data:
            if not all(k in rec for k in required):
                return False
            if rec.get("fuente") != "sab_lluvias":
                return False
        return True
