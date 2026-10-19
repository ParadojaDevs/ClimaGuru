# BACKEND_INTEGRATION.md - Integración espacial y fuentes plurales

## 1. Nueva estructura modular

`
backend/app/
+-- adapters/
¦   +-- base.py (interfaz extendida con consultas espaciales/rate limit)
¦   +-- registry.py (Factory/Registry)
¦   +-- parsers/ (JSON/XML/CSV/HTML/GeoTIFF/HDF5 stubs)
¦   +-- sab_adapter.py
¦   +-- ideam_radar_adapter.py
¦   +-- (nuevas fuentes)
+-- jobs/ (APScheduler + tasks con retry/rate limit)
+-- services/
¦   +-- ingestion_service.py
¦   +-- spatial_service.py (consultas espaciales, GeoJSON)
¦   +-- weather_service.py
+-- routes/
¦   +-- ingestion.py
¦   +-- spatial.py (endpoints geoespaciales)
+-- models/
    +-- weather_observation.py (+ geom condicional)
`

## 2. Guía paso a paso para agregar una nueva fuente

1. **Crear adaptador**: heredar WeatherDataSource en pp/adapters/nueva_fuente.py.
2. **Implementar métodos obligatorios**: get_source_name(), etch(), 
ormalize(), alidate().
3. **Extender metadata**: opcional get_supported_formats(), supports_spatial_queries(), get_spatial_bounds(), get_rate_limit(), query_by_coords().
4. **Usar parsers**: rom app.adapters.parsers import * para JSON/XML/CSV/HTML.
5. **Registrar**: añadir a registry o registrar en ingestion_service (o usar AdapterRegistry).
6. **Documentar**: docstrings técnicos para clase/métodos.
7. **Probar**: instancia + etch/normalize/validate.

Ejemplo mínimo:
`python
class MiFuente(WeatherDataSource):
    def get_source_name(self): return 'mi_fuente'
    def fetch(self, **k): return []
    def normalize(self, r): return []
    def validate(self, n): return isinstance(n,list)
`

## 3. Diccionario de datos y esquema geoespacial

Tabla weather_observations:
- id (INT PK)
- fuente (ENUM)
- estacion, ciudad (VARCHAR)
- latitud, longitud (DECIMAL)
- timestamp_observacion (DATETIME)
- tipo_dato (VARCHAR)
- valor, unidad, calidad
- metadatos, datos_crudos (JSON)
- procesado_en, actualizado_en (TIMESTAMP)
- geom (POINT SRID 4326) - solo MySQL cuando aplica; SQLite usa lat/lon

Índices: B-Tree por campos clave; SPATIAL index en geom (MySQL). Consultas espaciales usan filtros por bbox/lat-lon (fallback portable).

## 4. Endpoints API para consulta por coordenadas y capas de mapas

Endpoints bajo /api/spatial:

- GET /observations/nearby?lat&lon&radius_km=10&fuente&tipo_dato&limit=100 - cercanas
- GET /observations/bbox?min_lat&max_lat&min_lon&max_lon&fuente&tipo_dato&limit=500 - rango
- GET /observations/geojson?fuente&tipo_dato&limit=200 - GeoJSON FeatureCollection
- GET /observations/tiles/info - info para capas vectoriales

Formatos preparados para visualización: GeoJSON; estructura tile-info para integración futura.

## 5. Ingestión asíncrona y tolerancia a fallos

- jobs/scheduler.py: APScheduler (interval 6h por defecto)
- jobs/tasks.py: retry con tenacity (si disponible), TokenBucket rate limiting
- ingestion_service: orquesta adaptadores con validación
