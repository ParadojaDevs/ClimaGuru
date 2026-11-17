"""Cliente de Open-Meteo para la zona publica.

API: https://api.open-meteo.com/v1/forecast (sin API key, licencia CC BY 4.0).
Toda entrada se valida contra el bbox de Colombia para evitar uso como proxy
abierto (SSRF/abuso de upstream).
"""

import requests
from flask import current_app

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Bbox aproximado de Colombia (incluye aguas y Leticia/Amazonas).
COLOMBIA_BBOX = {
    "lat_min": -4.5,
    "lat_max": 13.7,
    "lon_min": -79.2,
    "lon_max": -66.8,
}

CURRENT_VARS = ",".join([
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
    "wind_direction_10m",
    "cloud_cover",
    "pressure_msl",
    "is_day",
])

HOURLY_VARS = ",".join([
    "temperature_2m",
    "precipitation_probability",
    "precipitation",
    "weather_code",
])

DAILY_VARS = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "weather_code",
    "sunrise",
    "sunset",
])

SOURCE_INFO = {
    "name": "Open-Meteo",
    "url": OPEN_METEO_URL,
    "license": "CC BY 4.0",
}


class UpstreamError(Exception):
    """Open-Meteo no respondio o respondio con error."""


def validate_coords(lat, lon):
    """Devuelve (lat, lon) como float o lanza ValueError con mensaje claro."""
    try:
        lat_f = round(float(lat), 4)
        lon_f = round(float(lon), 4)
    except (TypeError, ValueError):
        raise ValueError("lat y lon deben ser numericos")
    if not (COLOMBIA_BBOX["lat_min"] <= lat_f <= COLOMBIA_BBOX["lat_max"]):
        raise ValueError("lat fuera del rango de Colombia (-4.5 a 13.7)")
    if not (COLOMBIA_BBOX["lon_min"] <= lon_f <= COLOMBIA_BBOX["lon_max"]):
        raise ValueError("lon fuera del rango de Colombia (-79.2 a -66.8)")
    return lat_f, lon_f


def fetch_point_forecast(lat: float, lon: float) -> dict:
    """Consulta forecast actual + horario + diario para un punto.

    Devuelve el JSON de Open-Meteo tal cual; las rutas lo envuelven con
    metadatos de fuente y fecha de consulta.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": CURRENT_VARS,
        "hourly": HOURLY_VARS,
        "daily": DAILY_VARS,
        "forecast_days": 5,
        "timezone": "America/Bogota",
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    except requests.RequestException as exc:
        raise UpstreamError(f"Open-Meteo no disponible: {exc}") from exc

    if response.status_code != 200:
        raise UpstreamError(f"Open-Meteo respondio {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise UpstreamError("Open-Meteo devolvio JSON invalido") from exc

    if data.get("error"):
        raise UpstreamError(data.get("reason", "error de Open-Meteo"))

    return data
