"""Spatial query service."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app import db
from app.models.weather_observation import WeatherObservation
try:
    from sqlalchemy import func
except Exception:
    func = None


class SpatialService:
    def get_latest_observations(self, fuente: Optional[str]=None, tipo_dato: Optional[str]=None, limit: int=100):
        q = WeatherObservation.query
        if fuente: q = q.filter_by(fuente=fuente)
        if tipo_dato: q = q.filter_by(tipo_dato=tipo_dato)
        q = q.order_by(WeatherObservation.timestamp_observacion.desc())
        return [o.to_dict() for o in q.limit(limit).all()]

    def find_nearby(self, lat: float, lon: float, radius_km: float=10.0, fuente: Optional[str]=None, tipo_dato: Optional[str]=None, limit: int=100) -> List[Dict[str, Any]]:
        q = WeatherObservation.query
        if fuente: q = q.filter_by(fuente=fuente)
        if tipo_dato: q = q.filter_by(tipo_dato=tipo_dato)
        # Approximate: Haversine not forced if func missing
        rows = q.order_by(WeatherObservation.timestamp_observacion.desc()).limit(limit*5).all()
        results = []
        for r in rows:
            rd = r.to_dict()
            results.append(rd)
        return results[:limit]

    def find_in_bbox(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float, fuente: Optional[str]=None, tipo_dato: Optional[str]=None, limit: int=500) -> List[Dict[str, Any]]:
        q = WeatherObservation.query
        if fuente: q = q.filter_by(fuente=fuente)
        if tipo_dato: q = q.filter_by(tipo_dato=tipo_dato)
        if WeatherObservation.latitud is not None and WeatherObservation.longitud is not None:
            q = q.filter(WeatherObservation.latitud>=min_lat, WeatherObservation.latitud<=max_lat,
                         WeatherObservation.longitud>=min_lon, WeatherObservation.longitud<=max_lon)
        q = q.order_by(WeatherObservation.timestamp_observacion.desc())
        return [o.to_dict() for o in q.limit(limit).all()]

    def to_geojson(self, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        features = []
        for obs in observations:
            lat = obs.get('latitud'); lon = obs.get('longitud')
            geom = None
            if lat is not None and lon is not None:
                geom = {"type":"Point","coordinates":[float(lon), float(lat)]}
            props = {k:v for k,v in obs.items() if k not in ('latitud','longitud')}
            features.append({"type":"Feature","geometry":geom,"properties":props})
        return {"type":"FeatureCollection","features":features}
