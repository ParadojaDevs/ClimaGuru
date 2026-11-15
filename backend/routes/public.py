"""Blueprint publico: lectura sin autenticacion.

Reglas de la zona publica:
- Solo GET, solo datos meteorologicos/radar. Cero acceso a tablas de usuarios
  o consultas autenticadas.
- Coordenadas siempre validadas contra el bbox de Colombia.
- Throttle propio por IP hasheada sobre public_requests_log (no depende de
  flask_limiter, que hoy solo esta garantizado en la app principal).
- Cache SQLite con TTL para no castigar a los upstream (Open-Meteo / IDEAM).
"""

from datetime import datetime, timezone
import logging

from flask import Blueprint, current_app, jsonify, request

from database import public_db
from services import ideam_radar_client as ideam
from services import open_meteo_client as om

public_bp = Blueprint("public", __name__)
logger = logging.getLogger(__name__)

# Semilla de ciudades con datos del servicio (nombre, departamento, lat, lon).
CITIES = [
    {"name": "Bogota", "department": "Cundinamarca", "lat": 4.7110, "lon": -74.0721, "default": True},
    {"name": "Medellin", "department": "Antioquia", "lat": 6.2442, "lon": -75.5812, "default": True},
    {"name": "Cali", "department": "Valle del Cauca", "lat": 3.4516, "lon": -76.5320, "default": True},
    {"name": "Barranquilla", "department": "Atlantico", "lat": 10.9685, "lon": -74.7813, "default": False},
    {"name": "Bucaramanga", "department": "Santander", "lat": 7.1193, "lon": -73.1227, "default": False},
    {"name": "Manizales", "department": "Caldas", "lat": 5.0702, "lon": -75.5138, "default": False},
    {"name": "Villavicencio", "department": "Meta", "lat": 4.1420, "lon": -73.6266, "default": False},
    {"name": "San Jose del Guaviare", "department": "Guaviare", "lat": 3.8551, "lon": -72.9964, "default": False},
    {"name": "Popayan", "department": "Cauca", "lat": 2.4419, "lon": -76.6063, "default": False},
    {"name": "Cartagena", "department": "Bolivar", "lat": 10.3910, "lon": -75.4794, "default": False},
]

# Ventana de throttle por endpoint: (limite, segundos)
THROTTLES = {
    "weather": (30, 60),
    "radar": (12, 60),
    "catalog": (10, 60),
}


_DB_READY = False


def _db_path() -> str:
    global _DB_READY
    path = current_app.config["PUBLIC_DB_PATH"]
    if not _DB_READY:
        public_db.init_db(path)
        _DB_READY = True
    return path


def _client_ip_hash() -> str:
    salt = current_app.config.get("SECRET_KEY", "climaguru")
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "unknown")
    return public_db.hash_ip(ip, salt)


def _throttle(endpoint: str):
    limit, window = THROTTLES[endpoint]
    ip_hash = _client_ip_hash()
    count = public_db.requests_in_window(_db_path(), endpoint, ip_hash, window)
    if count >= limit:
        public_db.log_request(_db_path(), endpoint, ip_hash, 429)
        return True
    return False


def _log(endpoint: str, status: int) -> None:
    public_db.log_request(_db_path(), endpoint, _client_ip_hash(), status)


@public_bp.get("/api/public/cities")
def cities():
    if _throttle("catalog"):
        return jsonify({"error": "limite de tasa excedido"}), 429
    _log("catalog", 200)
    return jsonify({"cities": CITIES}), 200


@public_bp.get("/api/public/weather")
def weather():
    if _throttle("weather"):
        return jsonify({"error": "limite de tasa excedido"}), 429

    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat is None or lon is None:
        _log("weather", 400)
        return jsonify({"error": "lat y lon son obligatorios"}), 400

    try:
        lat_f, lon_f = om.validate_coords(lat, lon)
    except ValueError as exc:
        _log("weather", 400)
        return jsonify({"error": str(exc)}), 400

    cache_key = f"om:v1:{lat_f}:{lon_f}"
    db_path = _db_path()

    cached = public_db.cache_get(db_path, cache_key)
    if cached is not None:
        _log("weather", 200)
        return jsonify(cached), 200

    try:
        forecast = om.fetch_point_forecast(lat_f, lon_f)
    except om.UpstreamError as exc:
        _log("weather", 502)
        logger.warning("open-meteo fallo: %s", exc)
        return jsonify({"error": "fuente meteorologica no disponible", "detail": str(exc)}), 502

    payload = {
        "location": {"lat": lat_f, "lon": lon_f},
        "current": forecast.get("current"),
        "hourly": forecast.get("hourly"),
        "daily": forecast.get("daily"),
        "timezone": forecast.get("timezone"),
        "utc_offset_seconds": forecast.get("utc_offset_seconds"),
        "source": om.SOURCE_INFO,
        "fetched_at": public_db.utcnow_iso(),
    }
    ttl = current_app.config.get("PUBLIC_WEATHER_TTL", 600)
    public_db.cache_put(db_path, cache_key, payload, ttl)
    _log("weather", 200)
    return jsonify(payload), 200


@public_bp.get("/api/public/radar/stations")
def radar_stations():
    if _throttle("catalog"):
        return jsonify({"error": "limite de tasa excedido"}), 429
    _log("catalog", 200)
    return jsonify({
        "stations": [ideam.station_payload(s) for s in ideam.RADAR_STATIONS],
        "source": ideam.SOURCE_INFO,
    }), 200


@public_bp.get("/api/public/radar/latest")
def radar_latest():
    """Imagen compuesta nacional mas reciente (PNG con basemap, para el visor)."""
    if _throttle("radar"):
        return jsonify({"error": "limite de tasa excedido"}), 429

    db_path = _db_path()
    now_utc = datetime.now(timezone.utc)

    try:
        stamp, url = ideam.probe_composite(now_utc)
    except ideam.RadarUnavailable as exc:
        _log("radar", 502)
        return jsonify({"error": "radar no disponible", "detail": str(exc)}), 502

    public_db.scan_upsert(db_path, "composite", stamp, url, "available")
    _log("radar", 200)
    return jsonify({
        "kind": "composite",
        "stamp": stamp,
        "url": url,
        "source": ideam.SOURCE_INFO,
    }), 200


@public_bp.get("/api/public/radar/overlay")
def radar_overlay():
    """PNG transparente de reflectividad de un radar (para el visor)."""
    if _throttle("radar"):
        return jsonify({"error": "limite de tasa excedido"}), 429

    radar_id = request.args.get("radar", "guaviare")
    if radar_id not in ideam.STATION_BY_ID:
        _log("radar", 400)
        return jsonify({
            "error": "radar desconocido",
            "valid": list(ideam.STATION_BY_ID.keys()),
        }), 400

    db_path = _db_path()
    kind = f"overlay:{radar_id}"
    now_utc = datetime.now(timezone.utc)

    try:
        stamp, url = ideam.probe_transparent_z(radar_id, now_utc)
    except ideam.RadarUnavailable as exc:
        _log("radar", 502)
        return jsonify({"error": "radar no disponible", "detail": str(exc)}), 502

    public_db.scan_upsert(db_path, kind, stamp, url, "available")
    _log("radar", 200)
    return jsonify({
        "kind": kind,
        "stamp": stamp,
        "url": url,
        "station": ideam.station_payload(ideam.STATION_BY_ID[radar_id]),
        "source": ideam.SOURCE_INFO,
    }), 200


@public_bp.get("/api/public/radar/frames")
def radar_frames():
    """Frames recientes de un radar segun el manifiesto IDEAM (navegacion temporal)."""
    if _throttle("radar"):
        return jsonify({"error": "limite de tasa excedido"}), 429

    radar_id = request.args.get("radar", "guaviare")
    if radar_id not in ideam.STATION_BY_ID:
        _log("radar", 400)
        return jsonify({
            "error": "radar desconocido",
            "valid": list(ideam.STATION_BY_ID.keys()),
        }), 400

    try:
        frames = ideam.latest_transparent_manifest(radar_id)
    except ideam.RadarUnavailable as exc:
        _log("radar", 502)
        return jsonify({"error": "manifiesto no disponible", "detail": str(exc)}), 502

    _log("radar", 200)
    return jsonify({
        "radar": radar_id,
        "frames": frames,
        "source": ideam.SOURCE_INFO,
    }), 200
