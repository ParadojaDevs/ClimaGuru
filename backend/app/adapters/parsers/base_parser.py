"""Base parser interface for heterogeneous data formats."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    """Abstract base parser for weather data formats."""

    @abstractmethod
    def parse(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        """Parse content into list of dict records."""
        raise NotImplementedError

    def get_format_name(self) -> str:
        """Return format name."""
        raise NotImplementedError
