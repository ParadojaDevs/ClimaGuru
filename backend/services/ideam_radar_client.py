"""Cliente de radares IDEAM para la zona publica.

Fuentes verificadas (nov 2026), todas publicas y sin autenticacion:
- Imagen compuesta nacional (cada 5 min, PNG opaco con basemap):
    https://bart.ideam.gov.co/ospa/DatosAbiertos/Imagenes_Radar_Compuesto/{Y}/{M}/{D}/
        Composite_{YYMMDDHHMM}_basemap.png
- PNG transparente de reflectividad por radar (cada 5 min, 800x800):
    https://bart.ideam.gov.co/ospa/radarcol/transparent/{Radar}/z/{Y}/{M}/{D}/
        {CODE}{YYMMDDHHMM}_z_Transp.png
- GIF animado continuo (ultimas ~2 h, 24 frames, transparente):
    https://bart.ideam.gov.co/ospa/gifs/Radar/Transp/{Radar}/{Radar}_z.gif
- Manifiesto de escaneos recientes:
    https://bart.ideam.gov.co/ospa/gifs/Radar/Transp/{Radar}/{Radar}_z.txt
  (rutas internas prefijo /radares/interno/ que se reescriben a /ospa/)

Licencia: CC BY 4.0 (atribucion IDEAM obligatoria).

Nota: los endpoints de bart.ideam.gov.co no tienen contrato documentado; si
IDEAM cambia la estructura, este modulo es el unico punto a ajustar.

Verificado empiricamente (nov 2026):
- Los sellos YYMMDDHHMM estan en hora local de Colombia (UTC-5), no en UTC.
  Ej.: el archivo para las 13:20 COT aparece como GUA2611151320.
- El PNG transparente por radar aparece con ~10 min de retraso.
- La imagen compuesta nacional aparece con retraso irregular (minutos a
  horas) y no siempre cada 5 min; se probea hacia atras hasta ~8 h.
"""

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlsplit

import requests

COMPOSITE_BASE = "https://bart.ideam.gov.co/ospa/DatosAbiertos/Imagenes_Radar_Compuesto"
TRANSPARENT_BASE = "https://bart.ideam.gov.co/ospa/radarcol/transparent"
TRANSP_GIF_BASE = "https://bart.ideam.gov.co/ospa/gifs/Radar/Transp"

# Hora local de Colombia: los sellos de archivo IDEAM usan esta zona.
COT_TZ = timezone(timedelta(hours=-5))

SOURCE_INFO = {
    "name": "IDEAM - Red de radares meteorologicos",
    "url": "https://bart.ideam.gov.co/ospa/DatosAbiertos/",
    "license": "CC BY 4.0",
}

# Coordenadas aproximadas de los 4 radares operativos.
# Fuente: tabla 2.2 de la tesis RadarETL (Univ. Distrital, 2025); la del radar
# Guaviare fue verificada contra metadatos IRIS reales del bucket AWS
# (2.53375, -72.62847). Radio de accion ~240 km segun IDEAM.
RADAR_STATIONS = [
    {
        "id": "barrancabermeja",
        "name": "Barrancabermeja",
        "folder": "Barrancabermeja",
        "code": "BAR",
        "department": "Santander",
        "lat": 7.1200,
        "lon": -73.8400,
        "range_km": 240,
    },
    {
        "id": "carimagua",
        "name": "Carimagua",
        "folder": "Carimagua",
        "code": "CAR",
        "department": "Meta",
        "lat": 4.5700,
        "lon": -71.3300,
        "range_km": 240,
    },
    {
        "id": "guaviare",
        "name": "San Jose del Guaviare",
        "folder": "Guaviare",
        "code": "GUA",
        "department": "Guaviare",
        "lat": 2.53375,
        "lon": -72.62847,
        "range_km": 240,
    },
    {
        "id": "munchique",
        "name": "Cerro Munchique",
        "folder": "Munchique",
        "code": "MUN",
        "department": "Cauca",
        "lat": 2.6100,
        "lon": -76.9600,
        "range_km": 240,
    },
]

STATION_BY_ID = {s["id"]: s for s in RADAR_STATIONS}

STAMP_PATTERN = re.compile(r"^\d{10}$")

# El manifiesto puede venir en una sola linea con tokens separados por espacios.
MANIFEST_MAX_FRAMES = 24
MANIFEST_HOST = "bart.ideam.gov.co"
MANIFEST_FRAME_PATTERN = re.compile(r"/([A-Z]{3})(\d{10})_z_Transp\.png$")


class RadarUnavailable(Exception):
    """No se encontro un frame disponible en la ventana probeada."""


def stamp_for(dt: datetime) -> str:
    """Formato de sello usado por IDEAM: YYMMDDHHMM en UTC."""
    return dt.strftime("%y%m%d%H%M")


def floor_to_5min(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0, minute=(dt.minute // 5) * 5)


def composite_url(stamp: str) -> str:
    year = 2000 + int(stamp[:2])
    month = int(stamp[2:4])
    day = int(stamp[4:6])
    return f"{COMPOSITE_BASE}/{year}/{month:02d}/{day:02d}/Composite_{stamp}_basemap.png"


def transparent_z_url(radar_id: str, stamp: str) -> str:
    station = STATION_BY_ID[radar_id]
    year = 2000 + int(stamp[:2])
    month = int(stamp[2:4])
    day = int(stamp[4:6])
    return (
        f"{TRANSPARENT_BASE}/{station['folder']}"
        f"/z/{year}/{month:02d}/{day:02d}/{station['code']}{stamp}_z_Transp.png"
    )


def _resource(session: requests.Session, url: str):
    try:
        return session.head(url, timeout=8, allow_redirects=True)
    except requests.RequestException:
        return None


def probe_composite(now_utc: datetime, max_back_slots: int = 96):
    """Busca la imagen compuesta mas reciente probeando hacia atras cada 5 min.

    La generacion del compuesto es irregular (retraso de minutos a horas),
    por eso la ventana por defecto cubre ~8 h.
    Devuelve (stamp, url) o lanza RadarUnavailable.
    """
    cursor = floor_to_5min(now_utc.astimezone(COT_TZ))
    with requests.Session() as session:
        for _ in range(max_back_slots):
            stamp = stamp_for(cursor)
            url = composite_url(stamp)
            response = _resource(session, url)
            if response is not None and response.status_code == 200:
                return stamp, url
            cursor -= timedelta(minutes=5)
    raise RadarUnavailable("no hay imagen compuesta disponible en la ultima ventana")


def probe_transparent_z(radar_id: str, now_utc: datetime, max_back_slots: int = 12):
    """PNG transparente de reflectividad mas reciente para un radar (~10 min de lag)."""
    if radar_id not in STATION_BY_ID:
        raise ValueError(f"radar desconocido: {radar_id}")
    cursor = floor_to_5min(now_utc.astimezone(COT_TZ))
    with requests.Session() as session:
        for _ in range(max_back_slots):
            stamp = stamp_for(cursor)
            url = transparent_z_url(radar_id, stamp)
            response = _resource(session, url)
            if response is not None and response.status_code == 200:
                return stamp, url
            cursor -= timedelta(minutes=5)
    raise RadarUnavailable(f"no hay frame transparente disponible para {radar_id}")


def _stamp_datetime(stamp: str) -> datetime:
    """Convierte un sello YYMMDDHHMM (hora local Colombia) a datetime aware."""
    return datetime.strptime(stamp, "%y%m%d%H%M").replace(tzinfo=COT_TZ)


def _manifest_public_path(token: str):
    """Normaliza un token del manifiesto a una ruta publica bajo /ospa/.

    Devuelve None si el token no es una ruta PNG de IDEAM. Se rechazan
    esquemas distintos de https, hosts ajenos, credenciales, query/fragment y
    traversal para no abrir un vector SSRF.
    """
    token = (token or "").strip()
    if not token or "\\" in token or ".." in token:
        return None
    if token.startswith("http://") or token.startswith("https://"):
        parsed = urlsplit(token)
        if parsed.scheme != "https" or parsed.netloc != MANIFEST_HOST:
            return None
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            return None
        path = parsed.path
    else:
        if not token.startswith("/") or "?" in token or "#" in token:
            return None
        path = token
    if not path.lower().endswith(".png"):
        return None
    path = path.replace("/radares/interno/", "/ospa/", 1)
    if not path.startswith("/ospa/"):
        return None
    return path


def _manifest_get(url: str, max_redirects: int = 3):
    """GET del manifiesto validando cada redireccion antes de seguirla.

    ``requests`` sigue redirecciones por defecto, lo que permitiria que un
    manifiesto comprometido enviara la peticion a otro host. Aqui se desactiva
    ese comportamiento y solo se aceptan saltos ``https`` al mismo host IDEAM.
    """
    current = url
    for _ in range(max_redirects + 1):
        response = requests.get(current, timeout=10, allow_redirects=False)
        if response.status_code not in (301, 302, 303, 307, 308):
            return response
        location = response.headers.get("Location")
        if not location:
            raise RadarUnavailable("redireccion sin Location en el manifiesto")
        target = urljoin(current, location)
        parsed = urlsplit(target)
        if parsed.scheme != "https" or parsed.netloc != MANIFEST_HOST:
            raise RadarUnavailable("redireccion no permitida en el manifiesto")
        current = target
    raise RadarUnavailable("demasiadas redirecciones en el manifiesto")


def latest_transparent_manifest(
    radar_id: str,
    limit: int = MANIFEST_MAX_FRAMES,
    now_utc: datetime = None,
):
    """Lista los ultimos frames disponibles segun el manifiesto IDEAM.

    El manifiesto (.txt) lista rutas internas con prefijo /radares/interno/;
    se reescriben a la ruta publica verificada bajo /ospa/. Puede llegar en
    una sola linea con tokens separados por espacios, por eso se usa split()
    y no splitlines().

    Devuelve como maximo ``MANIFEST_MAX_FRAMES`` frames en orden cronologico
    ascendente, sin duplicados. Cada frame incluye ``stamp``, ``url``,
    ``timestamp`` (ISO 8601 COT) y ``age_minutes``. No se inventan horas: si
    el nombre no contiene un sello valido, el token se descarta.
    """
    station = STATION_BY_ID[radar_id]
    limit = max(1, min(int(limit), MANIFEST_MAX_FRAMES))
    manifest_url = f"{TRANSP_GIF_BASE}/{station['folder']}/{station['folder']}_z.txt"
    try:
        response = _manifest_get(manifest_url)
    except requests.RequestException as exc:
        raise RadarUnavailable(f"manifiesto no disponible para {radar_id}: {exc}") from exc
    if response.status_code != 200:
        raise RadarUnavailable(f"manifiesto respondio {response.status_code} para {radar_id}")

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    by_stamp = {}
    for token in response.text.split():
        public_path = _manifest_public_path(token)
        if public_path is None:
            continue
        match = MANIFEST_FRAME_PATTERN.search(public_path)
        if not match:
            continue
        code, stamp = match.groups()
        if code != station["code"] or not STAMP_PATTERN.match(stamp):
            continue
        if stamp in by_stamp:
            continue
        try:
            timestamp = _stamp_datetime(stamp)
        except ValueError:
            continue
        age_minutes = int(
            (now - timestamp.astimezone(timezone.utc)).total_seconds() // 60
        )
        by_stamp[stamp] = {
            "stamp": stamp,
            "url": f"https://{MANIFEST_HOST}{public_path}",
            "timestamp": timestamp.isoformat(),
            "age_minutes": max(0, age_minutes),
        }

    if not by_stamp:
        raise RadarUnavailable(f"manifiesto vacio o sin frames validos para {radar_id}")

    frames = sorted(by_stamp.values(), key=lambda frame: (frame["timestamp"], frame["stamp"]))
    return frames[-limit:]


def animated_gif_url(radar_id: str) -> str:
    station = STATION_BY_ID[radar_id]
    return f"{TRANSP_GIF_BASE}/{station['folder']}/{station['folder']}_z.gif"


def station_payload(station: dict) -> dict:
    return {
        "id": station["id"],
        "name": station["name"],
        "code": station["code"],
        "department": station["department"],
        "lat": station["lat"],
        "lon": station["lon"],
        "range_km": station["range_km"],
        "coords_note": "aproximada (fuente RadarETL 2025; Guaviare verificada con metadatos IRIS)",
    }
