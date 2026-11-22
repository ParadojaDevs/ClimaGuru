"""Georreferenciacion de los radares IDEAM (bloque F3.1a).

Este modulo es deliberadamente aislado:

- Solo usa la biblioteca estandar (sin GDAL, Rasterio, Pillow ni NumPy).
- No hace peticiones de red ni escribe archivos.
- No importa Flask, base de datos ni la zona autenticada.
- No habilita overlays: solo describe que se sabe y que no se sabe.

Contexto verificado en la auditoria F3:

- Los PNG ``*_z_Transp.png`` (800x800) y los GIF no llevan metadatos
  geograficos (sin world file, sin GeoTIFF, sin georreferencia en ``tEXt``).
- Existen GeoTIFF historicos de Guaviare y Munchique publicados por IDEAM
  en el AWS Open Data Registry. Su extension NO es comun entre radares y no
  hay pares PNG/GeoTIFF del mismo instante.
- Para Barrancabermeja y Carimagua no se identifico GeoTIFF utilizable.

Por eso cada radar lleva un estado de confianza explicito:

- ``verified``: calibrado con evidencia suficiente (ninguno hoy).
- ``derived``: bounds derivados de un GeoTIFF historico disponible, sin
  validacion temporal contra el PNG actual.
- ``assumed``: hipotesis sin calibracion (radio de cobertura + centro
  aproximado de la estacion).

Ningun valor de este modulo debe presentarse como georreferenciacion
verificada del PNG operativo.

Uso como CLI (desde ``backend/``)::

    python -m services.radar_georef --list
    python -m services.radar_georef --radar guaviare
    python -m services.radar_georef --geotiff ruta/al/archivo.tif
    python -m services.radar_georef --geotiff archivo.tif --compare guaviare
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

CRS_WGS84 = "EPSG:4326"

STATE_VERIFIED = "verified"
STATE_DERIVED = "derived"
STATE_ASSUMED = "assumed"

# De mayor a menor confianza. El orden importa: se usa para comparar estados.
CONFIDENCE_STATES: Tuple[str, ...] = (STATE_VERIFIED, STATE_DERIVED, STATE_ASSUMED)

OVERLAY_ELIGIBLE = "eligible"
OVERLAY_ELIGIBLE_WITH_WARNING = "eligible_with_warning"
OVERLAY_BLOCKED = "blocked"

# Politica de visualizacion (independiente de overlay_enabled).
# - exact: bounds con evidencia suficiente; el overlay verificado puede encenderse.
# - approximate_with_warning: se permite dibujar la imagen, siempre con aviso.
# - blocked: no se dibuja en el mapa (la imagen cruda del panel sigue disponible).
VISUALIZATION_EXACT = "exact"
VISUALIZATION_APPROXIMATE = "approximate_with_warning"
VISUALIZATION_BLOCKED = "blocked"

# Espejo de services.open_meteo_client.COLOMBIA_BBOX. Se duplica a proposito
# para que este modulo no dependa de ``requests``; una prueba verifica que
# ambas definiciones sigan siendo iguales.
COLOMBIA_BBOX = {
    "lat_min": -4.5,
    "lat_max": 13.7,
    "lon_min": -79.2,
    "lon_max": -66.8,
}

EARTH_KM_PER_DEG_LAT = 110.574
EARTH_KM_PER_DEG_LON_EQUATOR = 111.320


class GeorefError(ValueError):
    """Error base de configuracion geografica."""


class InvalidBoundsError(GeorefError):
    """Bounds mal formados, invertidos o fuera de rango."""


class UnknownRadarError(GeorefError, KeyError):
    """El radar solicitado no existe en el registro."""


class UnverifiedGeorefError(GeorefError):
    """Se exigio evidencia verificada y el radar no la tiene."""


class BlockedVisualizationError(GeorefError):
    """El radar no esta autorizado para dibujar una imagen en el mapa."""


class UnsupportedGeoTiffError(GeorefError):
    """El archivo no es un GeoTIFF legible o no tiene georreferencia."""


def _finite_float(value: Any, label: str) -> float:
    """Convierte a float rechazando bool, texto, NaN e infinito."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidBoundsError(f"{label} debe ser numerico (recibido: {value!r})")
    number = float(value)
    if not math.isfinite(number):
        raise InvalidBoundsError(f"{label} debe ser finito (recibido: {value!r})")
    return number


@dataclass(frozen=True)
class Bounds:
    """Bounding box geografico en WGS84 (grados decimales).

    ``west < east`` y ``south < north`` son obligatorios. No se admite una
    caja degenerada ni un cruce del antimeridiano: los radares IDEAM operan
    en Colombia y un cruce asi solo ocultaria un error de signo.
    """

    west: float
    south: float
    east: float
    north: float

    def __post_init__(self) -> None:
        west = _finite_float(self.west, "west")
        south = _finite_float(self.south, "south")
        east = _finite_float(self.east, "east")
        north = _finite_float(self.north, "north")
        if not (-180.0 <= west <= 180.0 and -180.0 <= east <= 180.0):
            raise InvalidBoundsError(f"longitud fuera de [-180, 180]: {west}, {east}")
        if not (-90.0 <= south <= 90.0 and -90.0 <= north <= 90.0):
            raise InvalidBoundsError(f"latitud fuera de [-90, 90]: {south}, {north}")
        if west >= east:
            raise InvalidBoundsError(f"bounds invertidos o vacios en longitud: west={west} >= east={east}")
        if south >= north:
            raise InvalidBoundsError(f"bounds invertidos o vacios en latitud: south={south} >= north={north}")
        object.__setattr__(self, "west", west)
        object.__setattr__(self, "south", south)
        object.__setattr__(self, "east", east)
        object.__setattr__(self, "north", north)

    @classmethod
    def from_sequence(cls, values: Sequence[float]) -> "Bounds":
        if isinstance(values, (str, bytes)) or len(values) != 4:
            raise InvalidBoundsError("los bounds deben ser (west, south, east, north)")
        return cls(*values)

    @property
    def center(self) -> Tuple[float, float]:
        """Centro geometrico como (lat, lon)."""
        return ((self.south + self.north) / 2.0, (self.west + self.east) / 2.0)

    def span_km(self) -> Tuple[float, float]:
        """Extension aproximada (ancho_km, alto_km) en el centro de la caja.

        Es una aproximacion equirectangular valida para la escala de un radar;
        no pretende ser geodesia de precision.
        """
        lat, _ = self.center
        width = (self.east - self.west) * EARTH_KM_PER_DEG_LON_EQUATOR * math.cos(math.radians(lat))
        height = (self.north - self.south) * EARTH_KM_PER_DEG_LAT
        return (width, height)

    def contains(self, lat: float, lon: float) -> bool:
        lat_f = _finite_float(lat, "lat")
        lon_f = _finite_float(lon, "lon")
        return self.south <= lat_f <= self.north and self.west <= lon_f <= self.east

    def intersects(self, other: "Bounds") -> bool:
        return not (
            self.east <= other.west
            or other.east <= self.west
            or self.north <= other.south
            or other.north <= self.south
        )

    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.west, self.south, self.east, self.north)

    def to_dict(self) -> Dict[str, float]:
        return {"west": self.west, "south": self.south, "east": self.east, "north": self.north}


def validate_bounds(bounds: Any, require_colombia: bool = True) -> Bounds:
    """Valida y normaliza bounds; acepta Bounds o secuencia de 4 numeros."""
    if isinstance(bounds, Bounds):
        result = bounds
    else:
        result = Bounds.from_sequence(bounds)
    if require_colombia:
        colombia = Bounds(
            COLOMBIA_BBOX["lon_min"],
            COLOMBIA_BBOX["lat_min"],
            COLOMBIA_BBOX["lon_max"],
            COLOMBIA_BBOX["lat_max"],
        )
        if not result.intersects(colombia):
            raise InvalidBoundsError(f"bounds fuera del bbox de Colombia: {result.as_tuple()}")
    return result


def overlay_readiness(state: str) -> str:
    """Traduce un estado de confianza a readiness de overlay (no lo habilita).

    - ``verified`` -> ``eligible``
    - ``derived``  -> ``eligible_with_warning`` (requiere aviso visible)
    - ``assumed``  -> ``blocked``
    """
    if state == STATE_VERIFIED:
        return OVERLAY_ELIGIBLE
    if state == STATE_DERIVED:
        return OVERLAY_ELIGIBLE_WITH_WARNING
    if state == STATE_ASSUMED:
        return OVERLAY_BLOCKED
    raise GeorefError(f"estado de confianza desconocido: {state!r}")


def visualization_policy(state: str) -> str:
    """Politica de dibujo en el mapa, derivada del estado de confianza.

    Es una capa separada de ``overlay_enabled``: un radar ``derived`` puede
    dibujarse como aproximado (con aviso) aunque su overlay verificado siga
    apagado. Un ``assumed`` nunca se dibuja.
    """
    if state == STATE_VERIFIED:
        return VISUALIZATION_EXACT
    if state == STATE_DERIVED:
        return VISUALIZATION_APPROXIMATE
    if state == STATE_ASSUMED:
        return VISUALIZATION_BLOCKED
    raise GeorefError(f"estado de confianza desconocido: {state!r}")


@dataclass(frozen=True)
class RadarGeoref:
    """Configuracion geografica de un radar, con su evidencia y limitaciones."""

    radar_id: str
    name: str
    code: str
    crs: str
    bounds: Bounds
    state: str
    source: str
    method: str
    uncertainty: str
    limitations: Tuple[str, ...]
    evidence: Tuple[str, ...]
    station_lat: float
    station_lon: float
    station_source: str
    approximate_warning: str = ""
    overlay_enabled: bool = False

    def __post_init__(self) -> None:
        for name in ("radar_id", "name", "code", "source", "method", "uncertainty", "station_source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise GeorefError(f"{name} es obligatorio y no puede estar vacio")
        if self.state not in CONFIDENCE_STATES:
            raise GeorefError(f"estado invalido: {self.state!r}; use uno de {CONFIDENCE_STATES}")
        if self.crs != CRS_WGS84:
            raise GeorefError(f"CRS no soportado: {self.crs!r}; solo se admite {CRS_WGS84}")
        station_lat = _finite_float(self.station_lat, "station_lat")
        station_lon = _finite_float(self.station_lon, "station_lon")
        if not (-90.0 <= station_lat <= 90.0):
            raise GeorefError(f"station_lat fuera de [-90, 90]: {station_lat}")
        if not (-180.0 <= station_lon <= 180.0):
            raise GeorefError(f"station_lon fuera de [-180, 180]: {station_lon}")
        object.__setattr__(self, "station_lat", station_lat)
        object.__setattr__(self, "station_lon", station_lon)
        if not isinstance(self.bounds, Bounds):
            raise GeorefError("bounds debe ser una instancia de Bounds")
        validate_bounds(self.bounds, require_colombia=True)
        if not self.limitations:
            raise GeorefError("todo radar debe declarar al menos una limitacion")
        if not self.evidence:
            raise GeorefError("todo radar debe declarar al menos una evidencia")
        warning = self.approximate_warning.strip()
        if self.state == STATE_DERIVED and not warning:
            # Un overlay aproximado sin aviso se leeria como verificado.
            raise GeorefError(f"{self.radar_id}: state=derived exige approximate_warning")
        if self.state == STATE_ASSUMED and warning:
            raise GeorefError(
                f"{self.radar_id}: state=assumed no puede declarar approximate_warning"
            )
        object.__setattr__(self, "approximate_warning", warning)
        if self.overlay_enabled and self.state != STATE_VERIFIED:
            # Regla dura: un radar derivado o asumido nunca se enciende.
            raise GeorefError(
                f"overlay_enabled=True exige state={STATE_VERIFIED!r}; "
                f"{self.radar_id} esta en {self.state!r}"
            )

    @property
    def readiness(self) -> str:
        return overlay_readiness(self.state)

    @property
    def visualization(self) -> str:
        return visualization_policy(self.state)

    def to_dict(self) -> Dict[str, Any]:
        span_width, span_height = self.bounds.span_km()
        return {
            "radar_id": self.radar_id,
            "name": self.name,
            "code": self.code,
            "crs": self.crs,
            "bounds": self.bounds.to_dict(),
            "state": self.state,
            "readiness": self.readiness,
            "visualization": self.visualization,
            "approximate_warning": self.approximate_warning or None,
            "overlay_enabled": self.overlay_enabled,
            "source": self.source,
            "method": self.method,
            "uncertainty": self.uncertainty,
            "limitations": list(self.limitations),
            "evidence": list(self.evidence),
            "station": {
                "lat": self.station_lat,
                "lon": self.station_lon,
                "source": self.station_source,
            },
            "span_km": {
                "width": round(span_width, 3),
                "height": round(span_height, 3),
            },
        }


REQUIRED_FIELDS: Tuple[str, ...] = (
    "radar_id",
    "name",
    "code",
    "crs",
    "bounds",
    "state",
    "source",
    "method",
    "uncertainty",
    "limitations",
    "evidence",
    "station_lat",
    "station_lon",
    "station_source",
)


def _coerce_bounds(value: Any) -> Bounds:
    if isinstance(value, Bounds):
        return value
    if isinstance(value, Mapping):
        try:
            return Bounds(value["west"], value["south"], value["east"], value["north"])
        except KeyError as exc:
            raise InvalidBoundsError(f"bounds incompletos: falta {exc.args[0]!r}") from None
    return Bounds.from_sequence(value)


def validate_georef(config: Mapping[str, Any]) -> RadarGeoref:
    """Construye y valida un RadarGeoref desde un mapping plano.

    Rechaza configuraciones incompletas o con campos desconocidos, para que
    una futura fuente de datos no cuele metadatos a medias.
    """
    if not isinstance(config, Mapping):
        raise GeorefError("la configuracion debe ser un mapping")
    missing = [name for name in REQUIRED_FIELDS if name not in config]
    if missing:
        raise GeorefError(f"configuracion incompleta: faltan {', '.join(missing)}")
    unknown = sorted(
        str(key)
        for key in set(config) - set(REQUIRED_FIELDS) - {"overlay_enabled", "approximate_warning"}
    )
    if unknown:
        raise GeorefError(f"campos desconocidos: {', '.join(unknown)}")
    limitations = config["limitations"]
    evidence = config["evidence"]
    if isinstance(limitations, str) or isinstance(evidence, str):
        raise GeorefError("limitations y evidence deben ser secuencias, no cadenas")
    return RadarGeoref(
        radar_id=config["radar_id"],
        name=config["name"],
        code=config["code"],
        crs=config["crs"],
        bounds=_coerce_bounds(config["bounds"]),
        state=config["state"],
        source=config["source"],
        method=config["method"],
        uncertainty=config["uncertainty"],
        limitations=tuple(limitations),
        evidence=tuple(evidence),
        station_lat=config["station_lat"],
        station_lon=config["station_lon"],
        station_source=config["station_source"],
        approximate_warning=config.get("approximate_warning", ""),
        overlay_enabled=bool(config.get("overlay_enabled", False)),
    )


_STATION_SOURCE = (
    "Coordenadas aproximadas de estacion en services.ideam_radar_client.RADAR_STATIONS "
    "(tesis RadarETL, Univ. Distrital 2025); Guaviare contrastada con metadatos IRIS."
)

_RADAR_GEOREF: Dict[str, RadarGeoref] = {
    "guaviare": RadarGeoref(
        radar_id="guaviare",
        name="San Jose del Guaviare",
        code="GUA",
        crs=CRS_WGS84,
        bounds=Bounds(-75.3216752210, -0.1718969128, -69.9312682939, 5.2347461798),
        state=STATE_DERIVED,
        source=(
            "GeoTIFF historico IDEAM (AWS Open Data Registry): "
            "GUA260519183040_rain_st.tif, 1992x1998, float32"
        ),
        method=(
            "ModelPixelScale=0.0027060275738625783 deg/px y "
            "ModelTiepoint=(-75.3216752210146, 5.234746179819134) leidos del GeoTIFF; "
            "RasterType=PixelIsArea; EPSG:4326; bounds = tiepoint + (width, height) * escala"
        ),
        uncertainty=(
            "Sin par PNG/GeoTIFF del mismo instante: no se verifico que el PNG operativo "
            "800x800 comparta extension, escala ni encuadre con este GeoTIFF."
        ),
        limitations=(
            "El GeoTIFF es de mayo de 2026; el PNG operativo auditado es de noviembre: no hay validacion temporal.",
            "El PNG transparente no incluye world file ni metadatos geograficos; el overlay exige un gate de calibracion.",
            "La extension derivada (~600x598 km) es propia de este GeoTIFF y no debe trasladarse a otros radares.",
            "El centro derivado queda a ~0.34 km de la estacion reportada, diferencia no explicada por metadatos oficiales.",
        ),
        evidence=(
            "Archivo: GUA260519183040_rain_st.tif (1992x1998, float32, EPSG:4326).",
            "Escala 0.0027060275738625783 deg/px (~300 m/px).",
            "Tiepoint (-75.3216752210146, 5.234746179819134) en el origen del raster.",
            "Bounds calculados: W -75.3216752210, S -0.1718969128, E -69.9312682939, N 5.2347461798.",
        ),
        station_lat=2.53375,
        station_lon=-72.62847,
        station_source=_STATION_SOURCE,
        approximate_warning=(
            "Posición aproximada: bounds derivados de GeoTIFF histórico, "
            "sin validación temporal con el PNG."
        ),
    ),
    "munchique": RadarGeoref(
        radar_id="munchique",
        name="Cerro Munchique",
        code="MUN",
        crs=CRS_WGS84,
        bounds=Bounds(-78.9784807762, 0.4823155074, -74.9314368071, 4.5483088462),
        state=STATE_DERIVED,
        source=(
            "GeoTIFF historico IDEAM (AWS Open Data Registry): "
            "MUN260519183121_rain_st.tif, 1495x1502, float32"
        ),
        method=(
            "ModelPixelScale=0.0027070528221321997 deg/px y "
            "ModelTiepoint=(-78.97848077616474, 4.548308846227644) leidos del GeoTIFF; "
            "RasterType=PixelIsArea; EPSG:4326; bounds = tiepoint + (width, height) * escala"
        ),
        uncertainty=(
            "Sin par PNG/GeoTIFF del mismo instante; ademas la extension derivada (~450x450 km) "
            "difiere de la de Guaviare (~600x598 km), lo que impide asumir un encuadre comun."
        ),
        limitations=(
            "El GeoTIFF es historico (mayo de 2026) y no hay validacion temporal contra el PNG actual.",
            "La extension derivada (~450x450 km) no coincide con la de Guaviare: no existe extension comun entre radares.",
            "El centro derivado queda a ~10.5 km de la estacion reportada (2.61, -76.96), diferencia sin explicacion oficial.",
            "El PNG transparente no incluye georreferencia; habilitar overlay requiere calibracion adicional.",
        ),
        evidence=(
            "Archivo: MUN260519183121_rain_st.tif (1495x1502, float32, EPSG:4326).",
            "Escala 0.0027070528221321997 deg/px (~300 m/px).",
            "Tiepoint (-78.97848077616474, 4.548308846227644) en el origen del raster.",
            "Bounds calculados: W -78.9784807762, S 0.4823155074, E -74.9314368071, N 4.5483088462.",
        ),
        station_lat=2.61,
        station_lon=-76.96,
        station_source=_STATION_SOURCE,
        approximate_warning=(
            "Posición aproximada: bounds derivados de GeoTIFF histórico; "
            "discrepancia aproximada de 10,5 km respecto a la estación."
        ),
    ),
    "barrancabermeja": RadarGeoref(
        radar_id="barrancabermeja",
        name="Barrancabermeja",
        code="BAR",
        crs=CRS_WGS84,
        bounds=Bounds(-76.5558763745, 4.4068848011, -71.1241236255, 9.8331151989),
        state=STATE_ASSUMED,
        source=(
            "Hipotesis H1: radio de cobertura de 300 km (guia IDEAM) centrado en las "
            "coordenadas aproximadas de la estacion; no existe GeoTIFF identificado."
        ),
        method=(
            "bounds = centro +- 300 km convertidos a grados con 110.574 km/grado (lat) y "
            "111.320 * cos(lat) km/grado (lon); sin medicion sobre el PNG"
        ),
        uncertainty=(
            "Hipotesis no medida: la guia oficial dice 'hasta 300 km de radio', no un radio exacto, "
            "y el centro de la estacion no fue verificado contra la imagen."
        ),
        limitations=(
            "No se identifico GeoTIFF ni world file para este radar.",
            "El radio de 300 km es un maximo declarado, no un valor medido en el PNG.",
            "Las coordenadas de estacion son aproximadas; una fuente legacy ubica el radar a ~6 km de distancia.",
            "El overlay permanece bloqueado: no hay evidencia suficiente ni aviso que lo haga honesto.",
        ),
        evidence=(
            "Guia oficial IDEAM: cada radar cubre un area de hasta 300 km de radio.",
            "Coordenadas de estacion 7.12, -73.84 (aprox.); variante legacy 7.0653, -73.8547.",
            "Ausencia de GeoTIFF en la auditoria F3 (noviembre de 2026).",
        ),
        station_lat=7.12,
        station_lon=-73.84,
        station_source=_STATION_SOURCE,
    ),
    "carimagua": RadarGeoref(
        radar_id="carimagua",
        name="Carimagua",
        code="CAR",
        crs=CRS_WGS84,
        bounds=Bounds(-74.0335287624, 1.8568848011, -68.6264712376, 7.2831151989),
        state=STATE_ASSUMED,
        source=(
            "Hipotesis H1: radio de cobertura de 300 km (guia IDEAM) centrado en las "
            "coordenadas aproximadas de la estacion; no existe GeoTIFF identificado."
        ),
        method=(
            "bounds = centro +- 300 km convertidos a grados con 110.574 km/grado (lat) y "
            "111.320 * cos(lat) km/grado (lon); sin medicion sobre el PNG"
        ),
        uncertainty=(
            "Hipotesis no medida: radio maximo declarado por IDEAM y centro aproximado; "
            "no hay ninguna comprobacion sobre la imagen operativa."
        ),
        limitations=(
            "No se identifico GeoTIFF ni world file para este radar.",
            "El radio de 300 km es un maximo declarado, no un valor medido en el PNG.",
            "Las coordenadas de estacion son aproximadas y no se contrastaron con metadatos oficiales.",
            "El overlay permanece bloqueado: no hay evidencia suficiente ni aviso que lo haga honesto.",
        ),
        evidence=(
            "Guia oficial IDEAM: cada radar cubre un area de hasta 300 km de radio.",
            "Coordenadas de estacion 4.57, -71.33 (aprox.).",
            "Ausencia de GeoTIFF en la auditoria F3 (noviembre de 2026).",
        ),
        station_lat=4.57,
        station_lon=-71.33,
        station_source=_STATION_SOURCE,
    ),
}

RADAR_GEOREF: Mapping[str, RadarGeoref] = MappingProxyType(_RADAR_GEOREF)


def radar_ids() -> Tuple[str, ...]:
    """IDs de radar en orden estable (alfabetico)."""
    return tuple(sorted(RADAR_GEOREF))


def get_radar_georef(radar_id: str) -> RadarGeoref:
    """Devuelve la configuracion inmutable de un radar."""
    try:
        return RADAR_GEOREF[radar_id]
    except (KeyError, TypeError):
        raise UnknownRadarError(
            f"radar desconocido: {radar_id!r}; validos: {', '.join(radar_ids())}"
        ) from None


def can_enable_overlay(radar_id: str) -> bool:
    """True solo si el estado permite overlay (con aviso si es ``derived``)."""
    return get_radar_georef(radar_id).readiness != OVERLAY_BLOCKED


def can_render_approximate(radar_id: str) -> bool:
    """True si la politica autoriza dibujar la imagen (exacta o aproximada)."""
    return get_radar_georef(radar_id).visualization != VISUALIZATION_BLOCKED


def require_renderable(radar_id: str) -> RadarGeoref:
    """Devuelve el radar o falla si su visualizacion esta bloqueada."""
    config = get_radar_georef(radar_id)
    if config.visualization == VISUALIZATION_BLOCKED:
        raise BlockedVisualizationError(
            f"{radar_id} esta en estado {config.state!r}: visualizacion bloqueada"
        )
    return config


def public_metadata(radar_id: str) -> Dict[str, Any]:
    """Metadatos geograficos seguros para las respuestas publicas.

    No expone nada que permita confundir un overlay aproximado con uno
    verificado: ``state``, ``visualization`` y ``overlay_enabled`` son campos
    separados y ``render_allowed`` resume la decision de dibujo.
    """
    config = get_radar_georef(radar_id)
    return {
        "state": config.state,
        "visualization": config.visualization,
        "render_allowed": config.visualization != VISUALIZATION_BLOCKED,
        "overlay_enabled": config.overlay_enabled,
        "warning": config.approximate_warning or None,
        "crs": config.crs,
        "bounds": config.bounds.to_dict(),
    }


def require_verified(radar_id: str) -> RadarGeoref:
    """Devuelve el radar o falla si su estado no es ``verified``."""
    config = get_radar_georef(radar_id)
    if config.state != STATE_VERIFIED:
        raise UnverifiedGeorefError(
            f"{radar_id} esta en estado {config.state!r}; se exige {STATE_VERIFIED!r}"
        )
    return config


def calibration_report() -> Tuple[Dict[str, Any], ...]:
    """Informe serializable de los cuatro radares (sin efectos secundarios)."""
    return tuple(get_radar_georef(radar_id).to_dict() for radar_id in radar_ids())


# ---------------------------------------------------------------------------
# Lectura offline de GeoTIFF (solo cabecera, sin decodificar pixeles)
# ---------------------------------------------------------------------------

_TIFF_TYPE_SIZES = {
    1: 1,   # BYTE
    2: 1,   # ASCII
    3: 2,   # SHORT
    4: 4,   # LONG
    5: 8,   # RATIONAL
    6: 1,   # SBYTE
    7: 1,   # UNDEFINED
    8: 2,   # SSHORT
    9: 4,   # SLONG
    10: 8,  # SRATIONAL
    11: 4,  # FLOAT
    12: 8,  # DOUBLE
    16: 8,  # LONG8
    17: 8,  # SLONG8
    18: 8,  # IFD8
}

_TIFF_TYPE_FORMATS = {
    1: "B", 2: "s", 3: "H", 4: "I", 5: "II", 6: "b", 7: "B",
    8: "h", 9: "i", 10: "ii", 11: "f", 12: "d", 16: "Q", 17: "q", 18: "Q",
}

TAG_IMAGE_WIDTH = 256
TAG_IMAGE_LENGTH = 257
TAG_BITS_PER_SAMPLE = 258
TAG_SAMPLES_PER_PIXEL = 277
TAG_SAMPLE_FORMAT = 339
TAG_MODEL_PIXEL_SCALE = 33550
TAG_MODEL_TIEPOINT = 33922
TAG_MODEL_TRANSFORMATION = 34264
TAG_GEO_KEY_DIRECTORY = 34735
TAG_GEO_DOUBLE_PARAMS = 34736
TAG_GEO_ASCII_PARAMS = 34737
TAG_GDAL_NODATA = 42113

GEOKEY_MODEL_TYPE = 1024
GEOKEY_RASTER_TYPE = 1025
GEOKEY_GEOGRAPHIC_CRS = 2048
GEOKEY_PROJECTED_CRS = 3072

RASTER_PIXEL_IS_AREA = 1
RASTER_PIXEL_IS_POINT = 2


def _decode_entry(data: bytes, endian: str, entry: Tuple[int, int, bytes]) -> Tuple[Any, ...]:
    type_id, count, raw = entry
    if type_id not in _TIFF_TYPE_SIZES:
        raise UnsupportedGeoTiffError(f"tipo TIFF no soportado: {type_id}")
    total = _TIFF_TYPE_SIZES[type_id] * count
    if total <= 4:
        payload = raw[:total]
    else:
        offset = struct.unpack(endian + "I", raw)[0]
        if offset + total > len(data):
            raise UnsupportedGeoTiffError("entrada TIFF apunta fuera del archivo")
        payload = data[offset:offset + total]
    if type_id == 2:
        return (payload.rstrip(b"\x00").decode("latin-1"),)
    fmt = endian + _TIFF_TYPE_FORMATS[type_id] * count
    values = struct.unpack(fmt, payload)
    if type_id in (5, 10):
        return tuple(values)
    return values


def _read_ifd(data: bytes, offset: int, endian: str) -> Dict[int, Tuple[int, int, bytes]]:
    if offset <= 0 or offset + 2 > len(data):
        raise UnsupportedGeoTiffError("offset de IFD invalido")
    count = struct.unpack_from(endian + "H", data, offset)[0]
    entries: Dict[int, Tuple[int, int, bytes]] = {}
    position = offset + 2
    for _ in range(count):
        if position + 12 > len(data):
            raise UnsupportedGeoTiffError("IFD truncado")
        tag, type_id, value_count = struct.unpack_from(endian + "HHI", data, position)
        raw = data[position + 8:position + 12]
        entries[tag] = (type_id, value_count, raw)
        position += 12
    return entries


def _single_value(data: bytes, endian: str, entries: Mapping[int, Any], tag: int, label: str) -> float:
    entry = entries.get(tag)
    if entry is None:
        raise UnsupportedGeoTiffError(f"falta el tag obligatorio {label} ({tag})")
    values = _decode_entry(data, endian, entry)
    if not values:
        raise UnsupportedGeoTiffError(f"tag {label} vacio")
    return float(values[0])


def _parse_geokeys(
    directory: Sequence[int],
    doubles: Sequence[float],
    ascii_params: str,
) -> Dict[int, Any]:
    if len(directory) < 4:
        raise UnsupportedGeoTiffError("GeoKeyDirectory truncado")
    key_count = int(directory[3])
    keys: Dict[int, Any] = {}
    for index in range(key_count):
        base = 4 + index * 4
        if base + 4 > len(directory):
            raise UnsupportedGeoTiffError("GeoKeyDirectory truncado")
        key_id, location, count, value = (int(v) for v in directory[base:base + 4])
        if location == 0:
            keys[key_id] = value
        elif location == TAG_GEO_DOUBLE_PARAMS:
            keys[key_id] = tuple(doubles[value:value + count])
        elif location == TAG_GEO_ASCII_PARAMS:
            keys[key_id] = ascii_params[value:value + count]
        else:
            keys[key_id] = value
    return keys


def _geokey_values(data: bytes, endian: str, entries: Mapping[int, Any]) -> Dict[int, Any]:
    directory_entry = entries.get(TAG_GEO_KEY_DIRECTORY)
    if directory_entry is None:
        raise UnsupportedGeoTiffError(
            "sin GeoKeyDirectory: no se puede confirmar el CRS ni el tipo de raster"
        )
    directory = _decode_entry(data, endian, directory_entry)
    doubles: Sequence[float] = ()
    if TAG_GEO_DOUBLE_PARAMS in entries:
        doubles = _decode_entry(data, endian, entries[TAG_GEO_DOUBLE_PARAMS])
    ascii_params = ""
    if TAG_GEO_ASCII_PARAMS in entries:
        ascii_params = _decode_entry(data, endian, entries[TAG_GEO_ASCII_PARAMS])[0]
    return _parse_geokeys(directory, doubles, ascii_params)


_SAMPLE_FORMATS = {1: "unsigned", 2: "signed", 3: "float"}


@dataclass(frozen=True)
class GeoTiffGeoref:
    """Cabecera geografica de un GeoTIFF, sin decodificar la imagen."""

    source: str
    width: int
    height: int
    crs: str
    epsg: int
    raster_type: str
    bounds: Bounds
    scale: Optional[Tuple[float, float]]
    tiepoint: Optional[Tuple[float, float, float, float]]
    transformation: Optional[Tuple[float, ...]]
    bits_per_sample: Optional[int] = None
    samples_per_pixel: Optional[int] = None
    sample_format: Optional[str] = None
    nodata: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "width": self.width,
            "height": self.height,
            "crs": self.crs,
            "epsg": self.epsg,
            "raster_type": self.raster_type,
            "bounds": self.bounds.to_dict(),
            "span_km": {
                "width": round(self.bounds.span_km()[0], 3),
                "height": round(self.bounds.span_km()[1], 3),
            },
            "scale_deg_per_px": self.scale,
            "tiepoint": self.tiepoint,
            "has_transformation": self.transformation is not None,
            "bits_per_sample": self.bits_per_sample,
            "samples_per_pixel": self.samples_per_pixel,
            "sample_format": self.sample_format,
            "nodata": self.nodata,
        }


def bounds_from_pixel_scale(
    width: float,
    height: float,
    scale_x: float,
    scale_y: float,
    tie_x: float,
    tie_y: float,
    tie_i: float = 0.0,
    tie_j: float = 0.0,
    raster_type: str = "PixelIsArea",
) -> Bounds:
    """Calcula bounds a partir de ModelPixelScale + ModelTiepoint.

    Funcion pura y sin I/O; es la misma formula que usa el parser, expuesta
    para poder reproducir y auditar los bounds registrados de cada radar.
    """
    width_f = _finite_float(width, "width")
    height_f = _finite_float(height, "height")
    scale_x_f = _finite_float(scale_x, "scale_x")
    scale_y_f = _finite_float(scale_y, "scale_y")
    tie_x_f = _finite_float(tie_x, "tie_x")
    tie_y_f = _finite_float(tie_y, "tie_y")
    tie_i_f = _finite_float(tie_i, "tie_i")
    tie_j_f = _finite_float(tie_j, "tie_j")
    if width_f <= 0 or height_f <= 0:
        raise InvalidBoundsError(f"dimensiones invalidas: {width}x{height}")
    if raster_type not in ("PixelIsArea", "PixelIsPoint"):
        raise InvalidBoundsError(f"raster_type desconocido: {raster_type!r}")

    x0 = tie_x_f - tie_i_f * scale_x_f
    x1 = x0 + width_f * scale_x_f
    y0 = tie_y_f + tie_j_f * scale_y_f
    y1 = y0 - height_f * scale_y_f
    west, east = sorted((x0, x1))
    south, north = sorted((y0, y1))
    if raster_type == "PixelIsPoint":
        half_x = abs(scale_x_f) / 2.0
        half_y = abs(scale_y_f) / 2.0
        west -= half_x
        east += half_x
        south -= half_y
        north += half_y
    return Bounds(west, south, east, north)


def parse_geotiff_georef(data: bytes, source: str = "<bytes>") -> GeoTiffGeoref:
    """Extrae CRS, escala y bounds de un GeoTIFF en memoria.

    Funcion pura: no toca disco ni red. Solo admite EPSG:4326 porque el resto
    de bounds del proyecto (y Leaflet) trabajan en grados WGS84; aceptar otra
    proyeccion en silencio produciria un overlay desplazado.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data debe ser bytes")
    data = bytes(data)
    if len(data) < 8:
        raise UnsupportedGeoTiffError("archivo demasiado corto para ser TIFF")
    if data[:2] == b"II":
        endian = "<"
    elif data[:2] == b"MM":
        endian = ">"
    else:
        raise UnsupportedGeoTiffError("orden de bytes TIFF desconocido (se esperaba II o MM)")
    magic = struct.unpack_from(endian + "H", data, 2)[0]
    if magic == 43:
        raise UnsupportedGeoTiffError("BigTIFF no soportado")
    if magic != 42:
        raise UnsupportedGeoTiffError(f"firma TIFF invalida: {magic}")
    ifd_offset = struct.unpack_from(endian + "I", data, 4)[0]
    entries = _read_ifd(data, ifd_offset, endian)

    width = int(_single_value(data, endian, entries, TAG_IMAGE_WIDTH, "ImageWidth"))
    height = int(_single_value(data, endian, entries, TAG_IMAGE_LENGTH, "ImageLength"))
    if width <= 0 or height <= 0:
        raise UnsupportedGeoTiffError(f"dimensiones invalidas: {width}x{height}")

    geokeys = _geokey_values(data, endian, entries)
    epsg = geokeys.get(GEOKEY_GEOGRAPHIC_CRS)
    if epsg != 4326:
        projected = geokeys.get(GEOKEY_PROJECTED_CRS)
        raise UnsupportedGeoTiffError(
            f"solo se admite EPSG:4326; GeographicTypeGeoKey={epsg!r}, "
            f"ProjectedCSTypeGeoKey={projected!r}"
        )
    raster_key = int(geokeys.get(GEOKEY_RASTER_TYPE, RASTER_PIXEL_IS_AREA))
    if raster_key not in (RASTER_PIXEL_IS_AREA, RASTER_PIXEL_IS_POINT):
        raise UnsupportedGeoTiffError(f"GTRasterTypeGeoKey desconocido: {raster_key}")
    raster_type = "PixelIsArea" if raster_key == RASTER_PIXEL_IS_AREA else "PixelIsPoint"

    scale: Optional[Tuple[float, float]] = None
    if TAG_MODEL_PIXEL_SCALE in entries:
        values = _decode_entry(data, endian, entries[TAG_MODEL_PIXEL_SCALE])
        if len(values) < 2:
            raise UnsupportedGeoTiffError("ModelPixelScale incompleto")
        scale = (float(values[0]), float(values[1]))

    tiepoint: Optional[Tuple[float, float, float, float]] = None
    if TAG_MODEL_TIEPOINT in entries:
        values = _decode_entry(data, endian, entries[TAG_MODEL_TIEPOINT])
        if len(values) < 6:
            raise UnsupportedGeoTiffError("ModelTiepoint incompleto")
        tiepoint = (float(values[0]), float(values[1]), float(values[2]), float(values[3]))

    transformation: Optional[Tuple[float, ...]] = None
    if TAG_MODEL_TRANSFORMATION in entries:
        values = _decode_entry(data, endian, entries[TAG_MODEL_TRANSFORMATION])
        if len(values) != 16:
            raise UnsupportedGeoTiffError("ModelTransformation debe tener 16 valores")
        transformation = tuple(float(v) for v in values)

    if transformation is not None:
        a, b, _, d = transformation[0:4]
        e, f, _, h = transformation[4:8]
        corners = [(0, 0), (width, 0), (0, height), (width, height)]
        xs = [a * i + b * j + d for i, j in corners]
        ys = [e * i + f * j + h for i, j in corners]
        try:
            bounds = Bounds(min(xs), min(ys), max(xs), max(ys))
        except InvalidBoundsError as exc:
            raise UnsupportedGeoTiffError(f"bounds invalidos en {source}: {exc}") from None
    elif scale is not None and tiepoint is not None:
        try:
            bounds = bounds_from_pixel_scale(
                width, height, scale[0], scale[1], *tiepoint, raster_type=raster_type
            )
        except InvalidBoundsError as exc:
            raise UnsupportedGeoTiffError(f"bounds invalidos en {source}: {exc}") from None
    else:
        raise UnsupportedGeoTiffError(
            "sin ModelPixelScale+ModelTiepoint ni ModelTransformation"
        )

    def _optional_int(tag: int) -> Optional[int]:
        entry = entries.get(tag)
        if entry is None:
            return None
        return int(_decode_entry(data, endian, entry)[0])

    sample_format_id = _optional_int(TAG_SAMPLE_FORMAT)
    nodata = None
    if TAG_GDAL_NODATA in entries:
        nodata = _decode_entry(data, endian, entries[TAG_GDAL_NODATA])[0].strip("\x00 ")

    return GeoTiffGeoref(
        source=source,
        width=width,
        height=height,
        crs=CRS_WGS84,
        epsg=4326,
        raster_type=raster_type,
        bounds=bounds,
        scale=scale,
        tiepoint=tiepoint,
        transformation=transformation,
        bits_per_sample=_optional_int(TAG_BITS_PER_SAMPLE),
        samples_per_pixel=_optional_int(TAG_SAMPLES_PER_PIXEL),
        sample_format=_SAMPLE_FORMATS.get(sample_format_id),
        nodata=nodata or None,
    )


def read_geotiff_georef(path: str) -> GeoTiffGeoref:
    """Lee un GeoTIFF del disco y delega en ``parse_geotiff_georef``."""
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        raise UnsupportedGeoTiffError(f"no se pudo leer {path}: {exc}") from exc
    return parse_geotiff_georef(data, source=str(path))


def hypothesis_bounds_from_center(
    lat: float, lon: float, radius_km: float = 300.0
) -> Bounds:
    """Bounds hipoteticos H1 para un centro y radio de cobertura.

    NO es calibracion: materializa la hipotesis "hasta 300 km de radio" de la
    guia IDEAM para poder compararla y discutirla. Cualquier resultado debe
    seguir marcado como ``assumed``.
    """
    lat_f = _finite_float(lat, "lat")
    lon_f = _finite_float(lon, "lon")
    radius = _finite_float(radius_km, "radius_km")
    if not (-90.0 < lat_f < 90.0):
        raise InvalidBoundsError(f"lat fuera de (-90, 90): {lat_f}")
    if radius <= 0.0:
        raise InvalidBoundsError(f"radius_km debe ser positivo: {radius}")
    delta_lat = radius / EARTH_KM_PER_DEG_LAT
    cos_lat = math.cos(math.radians(lat_f))
    if cos_lat <= 0.0:
        raise InvalidBoundsError("latitud incompatible con la conversion a grados")
    delta_lon = radius / (EARTH_KM_PER_DEG_LON_EQUATOR * cos_lat)
    return Bounds(lon_f - delta_lon, lat_f - delta_lat, lon_f + delta_lon, lat_f + delta_lat)


def _box_area_km2(west: float, south: float, east: float, north: float, ref_lat: float) -> float:
    width = (east - west) * EARTH_KM_PER_DEG_LON_EQUATOR * math.cos(math.radians(ref_lat))
    height = (north - south) * EARTH_KM_PER_DEG_LAT
    return max(0.0, width) * max(0.0, height)


def compare_bounds(reference: Any, candidate: Any) -> Dict[str, Any]:
    """Compara dos bounds y devuelve metricas objetivas (IoU, centro, bordes).

    Pensado para el arnes de calibracion: permite decidir con numeros si un
    bounds candidato es aceptable, en lugar de ajustar a ojo.
    """
    ref = validate_bounds(reference)
    cand = validate_bounds(candidate)
    ref_lat, _ = ref.center
    cand_lat, _ = cand.center
    mean_lat = (ref_lat + cand_lat) / 2.0

    inter_west = max(ref.west, cand.west)
    inter_south = max(ref.south, cand.south)
    inter_east = min(ref.east, cand.east)
    inter_north = min(ref.north, cand.north)
    has_intersection = inter_west < inter_east and inter_south < inter_north

    ref_area = _box_area_km2(ref.west, ref.south, ref.east, ref.north, ref_lat)
    cand_area = _box_area_km2(cand.west, cand.south, cand.east, cand.north, cand_lat)
    inter_area = (
        _box_area_km2(inter_west, inter_south, inter_east, inter_north, mean_lat)
        if has_intersection
        else 0.0
    )
    union_area = ref_area + cand_area - inter_area
    iou = inter_area / union_area if union_area > 0 else 0.0

    delta_lon_km = (cand.center[1] - ref.center[1]) * EARTH_KM_PER_DEG_LON_EQUATOR * math.cos(
        math.radians(mean_lat)
    )
    delta_lat_km = (cand.center[0] - ref.center[0]) * EARTH_KM_PER_DEG_LAT
    center_offset = math.hypot(delta_lon_km, delta_lat_km)

    lon_km = EARTH_KM_PER_DEG_LON_EQUATOR * math.cos(math.radians(mean_lat))
    edge_delta = {
        "west": (cand.west - ref.west) * lon_km,
        "south": (cand.south - ref.south) * EARTH_KM_PER_DEG_LAT,
        "east": (cand.east - ref.east) * lon_km,
        "north": (cand.north - ref.north) * EARTH_KM_PER_DEG_LAT,
    }

    return {
        "reference_bounds": ref.to_dict(),
        "candidate_bounds": cand.to_dict(),
        "intersection": (
            {
                "west": inter_west,
                "south": inter_south,
                "east": inter_east,
                "north": inter_north,
            }
            if has_intersection
            else None
        ),
        "iou": round(iou, 6),
        "center_offset_km": round(center_offset, 3),
        "edge_delta_km": {key: round(value, 3) for key, value in edge_delta.items()},
        "reference_area_km2": round(ref_area, 3),
        "candidate_area_km2": round(cand_area, 3),
        "candidate_area_ratio": round(cand_area / ref_area, 6) if ref_area > 0 else 0.0,
        "candidate_contains_reference_center": cand.contains(*ref.center),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI de inspeccion offline (sin red, sin escritura)."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m services.radar_georef",
        description="Inspecciona bounds candidatos de radares IDEAM y GeoTIFF locales.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="lista los cuatro radares")
    group.add_argument("--radar", metavar="ID", help="detalle de un radar")
    group.add_argument("--geotiff", metavar="PATH", help="cabecera geografica de un GeoTIFF")
    parser.add_argument(
        "--compare",
        metavar="ID",
        help="compara el GeoTIFF con los bounds registrados de un radar",
    )
    args = parser.parse_args(argv)
    if args.compare and not args.geotiff:
        parser.error("--compare requiere --geotiff")

    try:
        if args.list:
            payload: Dict[str, Any] = {"crs": CRS_WGS84, "radars": list(calibration_report())}
        elif args.radar:
            payload = get_radar_georef(args.radar).to_dict()
        else:
            geotiff = read_geotiff_georef(args.geotiff)
            payload = geotiff.to_dict()
            if args.compare:
                payload["comparison"] = compare_bounds(
                    get_radar_georef(args.compare).bounds, geotiff.bounds
                )
    except GeorefError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
