# Georreferenciacion y visualizacion de radares IDEAM (F3.1a / F3.1b)

Estado: **overlay aproximado habilitado solo para GUA y MUN, siempre con aviso
visible**. BAR y CAR siguen bloqueados. Ningun radar es `verified` ni tiene
overlay verificado.

Modulos:
- `backend/services/radar_georef.py` (geometria y politica)
- `backend/services/ideam_radar_client.py` (manifiesto y probes)
- `backend/routes/public.py` (endpoints, metadatos y cache)

Pruebas:
- `backend/tests/test_radar_georef.py`
- `backend/tests/test_radar_f31b.py`
- `frontend/src/components/*.test.jsx` (Vitest)

## Que hace el modulo

- Declara los cuatro radares con bounds candidatos, estado de confianza,
  fuente, metodo, incertidumbre y limitaciones.
- Valida bounds y configuraciones (rechaza cajas invertidas, coordenadas fuera
  de rango, campos faltantes y estados desconocidos).
- Distingue tres decisiones separadas: estado de confianza, elegibilidad de
  visualizacion (`exact` / `approximate_with_warning` / `blocked`) y
  habilitacion de overlay (`overlay_enabled`, solo `verified`).
- Lee la cabecera geografica de un GeoTIFF local (tags `ModelPixelScale`,
  `ModelTiepoint`, `ModelTransformation` y `GeoKeyDirectory`) sin GDAL,
  Rasterio, Pillow ni NumPy.
- Compara dos bounds con metricas objetivas (IoU, offset de centro, delta de
  bordes) para decidir con numeros si una calibracion es aceptable.
- Expone `public_metadata(radar_id)` para que las respuestas publicas incluyan
  `state`, `visualization`, `render_allowed`, `overlay_enabled`, `warning`,
  `crs` y `bounds` sin permitir confundir un overlay aproximado con uno
  verificado.
- No hace peticiones de red, no escribe archivos y no importa Flask ni la base
  de datos.

## Que NO hace

- No declara calibrado ningun radar ni habilita `overlay_enabled=True`.
- No descarga GeoTIFF: el arnes recibe una ruta local.
- No crea proxy de imagenes, no almacena series historicas y no genera GIF.
- No afirma que los umbrales provisionales se hayan cumplido: no existe un par
  PNG/GeoTIFF del mismo instante.

## Estados de confianza y politica de visualizacion

| Estado | Significado | Visualizacion | Overlay |
| --- | --- | --- | --- |
| `verified` | Calibrado con evidencia suficiente, incluido un par PNG/GeoTIFF del mismo instante. | `exact` | `eligible` |
| `derived` | Bounds derivados de un GeoTIFF historico disponible, sin validacion temporal contra el PNG operativo. | `approximate_with_warning` | `eligible_with_warning` |
| `assumed` | Hipotesis sin calibracion (radio declarado + centro aproximado de estacion). | `blocked` | `blocked` |

`overlay_enabled` es `False` para los cuatro radares. Un radar `derived` o
`assumed` no puede construirse con `overlay_enabled=True`: el modulo lanza
`GeorefError`. Un `derived` exige `approximate_warning` no vacio; un `assumed`
no puede declarar advertencia. Asi un overlay aproximado nunca se representa
como verificado.

### Decision por radar (F3.1b)

| Radar | Estado | Visualizacion | En el mapa |
| --- | --- | --- | --- |
| Guaviare (GUA) | `derived` | `approximate_with_warning` | Si, con aviso |
| Munchique (MUN) | `derived` | `approximate_with_warning` | Si, con aviso |
| Barrancabermeja (BAR) | `assumed` | `blocked` | No |
| Carimagua (CAR) | `assumed` | `blocked` | No |

Advertencias exactas:

- GUA: "Posición aproximada: bounds derivados de GeoTIFF histórico, sin
  validación temporal con el PNG."
- MUN: "Posición aproximada: bounds derivados de GeoTIFF histórico;
  discrepancia aproximada de 10,5 km respecto a la estación."

La advertencia viaja en `georef.warning` y se muestra en el panel y sobre el
mapa mientras el overlay aproximado esta visible.

## Registro actual

CRS: `EPSG:4326`. Bounds en orden `(west, south, east, north)`, grados
decimales.

| Radar | Codigo | Estado | Oeste | Sur | Este | Norte | Extension aprox. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| San Jose del Guaviare | GUA | `derived` | -75.321675 | -0.171897 | -69.931268 | 5.234746 | 599.5 x 597.8 km |
| Cerro Munchique | MUN | `derived` | -78.978481 | 0.482316 | -74.931437 | 4.548309 | 450.1 x 449.6 km |
| Barrancabermeja | BAR | `assumed` | -76.555876 | 4.406885 | -71.124124 | 9.833115 | 600.0 x 600.0 km |
| Carimagua | CAR | `assumed` | -74.033529 | 1.856885 | -68.626471 | 7.283115 | 600.0 x 600.0 km |

Fuente de los bounds:

- **GUA**: `GUA260519183040_rain_st.tif` (1992x1998, float32), escala
  `0.0027060275738625783 deg/px`, tiepoint
  `(-75.3216752210146, 5.234746179819134)`, `PixelIsArea`, `EPSG:4326`.
- **MUN**: `MUN260519183121_rain_st.tif` (1495x1502, float32), escala
  `0.0027070528221321997 deg/px`, tiepoint
  `(-78.97848077616474, 4.548308846227644)`, `PixelIsArea`, `EPSG:4326`.
- **BAR / CAR**: hipotesis H1, `hypothesis_bounds_from_center(lat, lon, 300)`.
  El radio de 300 km es el maximo declarado por la guia IDEAM, no una medicion.

## Por que ningun radar es `verified`

1. Los PNG `*_z_Transp.png` (800x800) y los GIF no incluyen world file ni
   metadatos geograficos; `pHYs` solo aporta densidad de impresion.
2. Los GeoTIFF disponibles son historicos (mayo) y no existe un par
   PNG/GeoTIFF del mismo instante que permita validar la correspondencia.
3. GUA y MUN no comparten extension (~600 km vs ~450 km), asi que no se puede
   asumir un encuadre comun entre radares.
4. Para BAR y CAR no se identifico GeoTIFF utilizable.
5. La aplicacion oficial de IDEAM muestra los GIF con el basemap incorporado,
   sin georreferenciacion reutilizable.

## Overlay en el mapa (F3.1b)

- `frontend/src/components/RadarOverlayLayer.jsx` usa `ImageOverlay` de
  React-Leaflet con `bounds` explicitos que vienen del backend. No calcula
  bounds por tamano de pantalla ni los comparte entre radares.
- `frontend/src/components/radarOverlayPolicy.js` centraliza la decision de
  dibujo en el cliente: exige `render_allowed === true`, exige aviso cuando la
  visualizacion es aproximada y no dibuja frames con mas de 60 minutos de edad.
  Esa ventana de 60 minutos es una **politica del cliente ClimaGuru** para no
  presentar imagenes viejas como actuales; **IDEAM no garantiza la frescura ni
  la puntualidad** de sus publicaciones.
- `PublicMap.jsx` monta una sola capa (con `key` por URL) y muestra el aviso
  geografico mientras el overlay aproximado esta visible.
- `RadarViewer.jsx` publica el overlay activo y ofrece mostrar/ocultar y
  opacidad. Al cambiar de radar o desmontar el panel, la capa se retira.
- Si la imagen falla, la capa se oculta y se informa el error. No se presenta
  una imagen antigua como dato actual.

Las imagenes se cargan directamente desde `bart.ideam.gov.co`; no hay proxy ni
almacenamiento de series historicas.

## Manifiesto IDEAM (F3.1b)

`latest_transparent_manifest()` procesa el `.txt` de IDEAM con `split()` (el
manifiesto puede llegar en una sola linea separada por espacios), valida cada
token contra `https://bart.ideam.gov.co` y la ruta `/ospa/`, descarta
credenciales, query, fragment, traversal y esquemas distintos de `https`,
elimina duplicados, ordena de forma ascendente y conserva como maximo 24
frames. Cada frame incluye `stamp`, `url`, `timestamp` ISO 8601 COT y
`age_minutes`. Un manifiesto vacio, malformado o sin sellos verificables lanza
`RadarUnavailable`.

## Cache de descubrimiento (F3.1b)

`routes/public.py` cachea solo respuestas exitosas de `/radar/latest`,
`/radar/overlay` y `/radar/frames` en `weather_cache`, con claves
`radar:v1:{composite|overlay:<id>|frames:<id>}` y TTL
`RADAR_DISCOVERY_TTL` (300 s por defecto). Los errores 400/502 no se cachean,
de modo que una recuperacion del proveedor se refleja de inmediato. No hay
cambios de esquema ni endpoints nuevos.

## Arnes offline

Funciones publicas principales:

- `get_radar_georef(radar_id)` / `radar_ids()` / `calibration_report()`.
- `validate_bounds(bounds, require_colombia=True)`.
- `validate_georef(config)` para configuraciones externas.
- `overlay_readiness(state)` / `can_enable_overlay(radar_id)` /
  `require_verified(radar_id)`.
- `visualization_policy(state)` / `can_render_approximate(radar_id)` /
  `require_renderable(radar_id)` / `public_metadata(radar_id)`.
- `bounds_from_pixel_scale(...)`.
- `parse_geotiff_georef(data)` / `read_geotiff_georef(path)`.
- `hypothesis_bounds_from_center(lat, lon, radius_km)`.
- `compare_bounds(reference, candidate)`.

CLI (desde `backend/`):

```bash
python -m services.radar_georef --list
python -m services.radar_georef --radar guaviare
python -m services.radar_georef --geotiff ruta/GUA260519183040_rain_st.tif
python -m services.radar_georef --geotiff ruta/GUA260519183040_rain_st.tif --compare guaviare
```

Salida en JSON, sin red y sin escritura.

## Procedimiento de calibracion propuesto

Este procedimiento sigue **pendiente de ejecucion**. La politica de
visualizacion de F3.1b no cambia el estado de ningun radar por si sola.

1. Reunir, por radar, un GeoTIFF y el PNG operativo del **mismo dia y hora**
   (o el mas cercano posible), anotando la diferencia temporal.
2. Ejecutar `--geotiff ... --compare <radar>` y registrar `iou`,
   `center_offset_km` y `edge_delta_km`.
3. Criterio candidato a discutir: `iou >= 0.90`, `|center_offset_km| <= 5` y
   `|edge_delta_km| <= 10` con diferencia temporal menor a 15 minutos.
4. Si el par temporal no existe, el radar permanece `derived` y el overlay, si
   se habilita, debe mostrar un aviso visible de posicion aproximada.
5. Cualquier cambio de estado exige evidencia adjunta en el informe; no se
   edita el registro "a ojo".

Los umbrales son una propuesta, no una verdad medida.

## Limitaciones conocidas

- No hay georreferenciacion absoluta verificada para el PNG operativo.
- La hipotesis H1 (+-300 km) no fue medida sobre la imagen.
- Las coordenadas de estacion son aproximadas; para BAR existe una variante
  legacy a ~6 km y el centro del GeoTIFF de MUN queda a ~10.5 km de la
  estacion reportada.
- La extension del GeoTIFF de GUA no debe trasladarse a MUN, BAR ni CAR.
- El GeoTIFF solo se verifico para mayo; no hay garantia de que IDEAM mantenga
  la misma grilla en otros periodos.
- No existe evidencia cuantitativa de que los umbrales provisionales (IoU,
  centro, bordes, diferencia temporal) se cumplan. La ausencia de pares
  PNG/GeoTIFF coincidentes es una limitacion explicita, no un detalle menor.
- Los avisos de posicion aproximada no deben eliminarse mientras el estado
  siga siendo `derived`.

## Fuentes

- Guia oficial IDEAM: cobertura de hasta 300 km de radio, escaneos volumetricos
  cada 5 min, PPI, dBZ, licencia CC BY 4.0.
- AWS Open Data Registry (IDEAM): GeoTIFF `*_rain_st.tif` de Guaviare y
  Munchique.
- Auditoria F3 (noviembre de 2026): estructura de PNG/GIF/manifiesto y
  ausencia de metadatos geograficos.

## Pruebas

```bash
.venv/Scripts/python -m pytest backend/tests/test_radar_georef.py -q
.venv/Scripts/python -m pytest backend/tests/test_radar_f31b.py -q
.venv/Scripts/python -m pytest backend/tests -q
cd frontend && npm test
```

Las pruebas backend construyen GeoTIFF sinteticos en memoria (cabecera valida,
pixeles de relleno) y no usan red. Las pruebas frontend usan Vitest + jsdom y
mockean Leaflet y el servicio de API.
