"""Adapter registry (Factory pattern)."""
from typing import Dict, Type, List, Any, Optional
from app.adapters.base import WeatherDataSource


class AdapterRegistry:
    _instance = None
    _adapters: Dict[str, Type[WeatherDataSource]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdapterRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, name: str, adapter_cls: Type[WeatherDataSource]):
        self._adapters[name] = adapter_cls

    def get(self, name: str) -> Type[WeatherDataSource]:
        if name not in self._adapters:
            raise KeyError(f"Adapter '{name}' not registered")
        return self._adapters[name]

    def create(self, name: str, **kwargs) -> WeatherDataSource:
        cls = self.get(name)
        return cls(**kwargs)

    def list(self) -> List[str]:
        return list(self._adapters.keys())

    def is_registered(self, name: str) -> bool:
        return name in self._adapters
