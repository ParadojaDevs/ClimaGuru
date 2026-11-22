# Georreferenciacion de radares IDEAM (F3.1a)

Estado: **infraestructura offline de calibracion, sin overlay y sin cambios de
interfaz**. Este documento describe que se sabe, que se supone y que falta para
poder dibujar un PNG de radar IDEAM sobre el mapa.

Modulo: `backend/services/radar_georef.py`
Pruebas: `backend/tests/test_radar_georef.py`

## Que hace el modulo

- Declara los cuatro radares con bounds candidatos, estado de confianza,
  fuente, metodo, incertidumbre y limitaciones.
- Valida bounds y configuraciones (rechaza cajas invertidas, coordenadas fuera
  de rango, campos faltantes y estados desconocidos).
- Lee la cabecera geografica de un GeoTIFF local (tags `ModelPixelScale`,
  `ModelTiepoint`, `ModelTransformation` y `GeoKeyDirectory`) sin GDAL,
  Rasterio, Pillow ni NumPy.
- Compara dos bounds con metricas objetivas (IoU, offset de centro, delta de
  bordes) para decidir con numeros si una calibracion es aceptable.
- No hace peticiones de red, no escribe archivos y no importa Flask ni la base
  de datos.

## Que NO hace

- No habilita overlays ni toca `PublicMap` o `RadarViewer`.
- No modifica endpoints, cache, throttle ni esquema SQLite.
- No declara calibrado ningun radar.
- No descarga GeoTIFF: el arnes recibe una ruta local.

## Estados de confianza

| Estado | Significado | Overlay |
| --- | --- | --- |
| `verified` | Calibrado con evidencia suficiente, incluido un par PNG/GeoTIFF del mismo instante. | `eligible` |
| `derived` | Bounds derivados de un GeoTIFF historico disponible, sin validacion temporal contra el PNG operativo. | `eligible_with_warning` |
| `assumed` | Hipotesis sin calibracion (radio declarado + centro aproximado de estacion). | `blocked` |

`overlay_enabled` es `False` para los cuatro radares. Un radar `derived` o
`assumed` no puede construirse con `overlay_enabled=True`: el modulo lanza
`GeorefError`.

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

## Arnes offline

Funciones publicas principales:

- `get_radar_georef(radar_id)` / `radar_ids()` / `calibration_report()`.
- `validate_bounds(bounds, require_colombia=True)`.
- `validate_georef(config)` para configuraciones externas.
- `overlay_readiness(state)` / `can_enable_overlay(radar_id)` /
  `require_verified(radar_id)`.
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

Este procedimiento es una propuesta para F3.1b; **no esta aprobado** y no
cambia el estado de ningun radar por si solo.

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
.venv/Scripts/python -m pytest backend/tests -q
```

Las pruebas construyen GeoTIFF sinteticos en memoria (cabecera valida, pixeles
de relleno) y no usan red.
