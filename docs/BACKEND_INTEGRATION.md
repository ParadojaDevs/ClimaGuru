# BACKEND_INTEGRATION.md - Integración de fuentes IDEAM y SAB

## 1. Nueva estructura de módulos del backend

La refactorización introduce una arquitectura modular basada en el patrón Adapter/Strategy para abstraer fuentes de datos meteorológicas.

### Estructura actualizada

`
backend/
+-- app/
¦   +-- adapters/                    # Adaptadores para fuentes de datos externas
¦   ¦   +-- __init__.py
¦   ¦   +-- base.py                  # Interfaz abstracta WeatherDataSource
¦   ¦   +-- ideam_radar_adapter.py   # Adaptador IDEAM Radar (AWS S3)
¦   ¦   +-- sab_adapter.py           # Adaptador SAB (scraping)
¦   +-- models/
¦   ¦   +-- weather_observation.py   # Nuevo: observaciones normalizadas
¦   ¦   +-- ...
¦   +-- routes/
¦   ¦   +-- ingestion.py             # Nuevas rutas para ingesta
¦   ¦   +-- ...
¦   +-- services/
¦   ¦   +-- ingestion_service.py     # Orquestador de ingesta
¦   ¦   +-- weather_service.py       # Servicio meteorológico (refactorizado)
¦   ¦   +-- ...
¦   +-- ...
+-- migrations/versions/
¦   +-- feec0f5b76b9_add_weather_observations_table.py
+-- climaguru_database.sql           # Esquema actualizado
`

### Descripción de componentes

- **adapters/base.py**: Clase abstracta WeatherDataSource define contrato unificado (get_source_name, etch, 
ormalize, alidate, get_metadata).
- **adapters/sab_adapter.py**: Implementa scraping de https://app.sab.gov.co/sab/lluvias.htm con requests.Session, Retry (urllib3), HTTPAdapter, backoff exponencial, timeouts configurables, User-Agent, manejo de errores HTTP/timeout.
- **adapters/ideam_radar_adapter.py**: Integra módulos existentes de src/data_sources/ideam_radar_downloader.py y reutiliza lógica para listar/descargar datos radar IDEAM desde AWS S3.
- **models/weather_observation.py**: Modelo SQLAlchemy para almacenar observaciones normalizadas con metadatos flexibles (JSON).
- **services/ingestion_service.py**: Orquestador que registra adaptadores, ejecuta pipeline fetch?normalize?validate?persist, registra logs y métricas.
- **services/weather_service.py**: Servicio unificado para consulta e ingesta de datos meteorológicos (compatible con código existente).
- **routes/ingestion.py**: Endpoints REST para ejecutar ingesta desde fuentes, consultar observaciones y listar fuentes disponibles.

## 2. Flujo de ingesta de datos

### Flujo general (patrón Adapter)
1. Cliente solicita ingesta via API (POST /api/ingestion/<fuente>).
2. WeatherIngestionService selecciona adaptador correspondiente según source_name.
3. Adaptador ejecuta etch(**kwargs): obtiene datos crudos desde fuente externa con manejo de errores, timeouts y reintentos.
4. Adaptador ejecuta 
ormalize(raw_data): transforma a esquema interno común (WeatherObservation).
5. Adaptador ejecuta alidate(normalized): valida estructura y reglas básicas.
6. Servicio persiste datos válidos vía SQLAlchemy en weather_observations.
7. Se registra actividad en logs_actividad (si endpoint requiere autenticación JWT).

### IDEAM Radar
- Fuente: AWS S3 público (s3://s3-radaresideam, región us-east-1).
- Implementación: reutiliza IDEAMRadarDownloader desde src/data_sources/ideam_radar_downloader.py (acceso anónimo, listado por radar/fecha).
- Normalización: genera registros con uente='ideam_radar', estacion (nombre radar), 	imestamp_observacion, 	ipo_dato='radar_reflectividad', metadatos con info de archivo.
- Parámetros soportados: adar (defecto Barrancabermeja), echa, limite.

### SAB (Sistema de Alerta de Bogotá / Lluvias)
- Fuente: https://app.sab.gov.co/sab/lluvias.htm
- Implementación: scraping con equests + BeautifulSoup (lxml), sesión con Retry configurado (status_forcelist incluye 429/5xx, backoff exponencial, métodos GET/HEAD), HTTPAdapter, timeouts configurables, headers User-Agent realistas.
- Extracción: parseo de tablas HTML (<table>), headers dinámicos, extracción por filas.
- Normalización: uente='sab_lluvias', ciudad='Bogota', 	ipo_dato='precipitacion', unidad='mm', parseo seguro de valores numéricos (soporta coma decimal, valores nulos/ND).
- Validación: verifica estructura mínima y coherencia de fuente.

## 3. Modelo de datos/esquema actualizado

### Nueva tabla: weather_observations
Tabla normalizada para consolidar observaciones de múltiples fuentes.

| Campo | Tipo | Descripción |
|---|---|---|
| id | INT (PK, AI) | Identificador único |
| fuente | ENUM('ideam_radar','sab_lluvias') | Origen de los datos (indexado) |
| estacion | VARCHAR(100) | Nombre de estación/radar |
| ciudad | VARCHAR(100) | Ciudad/ubicación (indexado) |
| latitud | DECIMAL(10,8) | Latitud (indexado) |
| longitud | DECIMAL(11,8) | Longitud (indexado) |
| timestamp_observacion | DATETIME | Fecha/hora de observación (indexado, NOT NULL) |
| tipo_dato | VARCHAR(50) | Tipo de dato (precipitacion, radar_reflectividad, etc.) (indexado) |
| valor | DECIMAL(12,4) | Valor numérico |
| unidad | VARCHAR(20) | Unidad de medida (mm, dBZ, etc.) |
| calidad | VARCHAR(20) | Indicador de calidad (default 'unknown') |
| metadatos | JSON | Metadatos específicos de fuente |
| datos_crudos | JSON | Datos crudos relevantes |
| procesado_en | TIMESTAMP | Fecha de procesamiento (indexado, default CURRENT_TIMESTAMP) |
| actualizado_en | TIMESTAMP | Fecha actualización (auto-update) |

**Índices**: idx_fuente, idx_ciudad, idx_coordenadas, idx_timestamp, idx_tipo_dato, idx_fuente_timestamp.

### Migraciones
- Alembic: ackend/migrations/versions/feec0f5b76b9_add_weather_observations_table.py (upgrade/downgrade implementados).
- SQL: ackend/climaguru_database.sql actualizado con definición de weather_observations.

### Compatibilidad
Modelos existentes (Consulta, DatosClima, etc.) se mantienen sin cambios. Nueva tabla es complementaria para ingesta independiente.

## 4. Instrucciones para ejecutar las tareas de ingesta o servicios localmente

### Requisitos
- Python 3.10+ (entorno configurado en proyecto)
- Dependencias instaladas (ver ackend/requirements.txt y equirements.txt)
- Base de datos accesible (MySQL o SQLite según config). Para pruebas locales puede usarse SQLite configurado vía FLASK_ENV.

### Configuración
`ash
cd backend
# Configurar variables de entorno (.env) según backend/.env.example
# FLASK_ENV: development|testing|production
`

### Ejecutar servidor Flask
`ash
cd backend
python app.py
# o
flask --app app run
`

Servidor disponible en http://localhost:5000. Health check: GET /health.

### Ejecutar ingesta vía API (autenticado con JWT)

1. Autenticarse: POST /api/auth/login (obtener token JWT)
2. Ingestar SAB: POST /api/ingestion/sab (Bearer token)
3. Ingestar IDEAM: POST /api/ingestion/ideam (opcional body con radar/fecha/limite)
4. Ingestar todo: POST /api/ingestion/all
5. Consultar observaciones: GET /api/ingestion/observations?fuente=sab_lluvias&limit=50
6. Listar fuentes: GET /api/ingestion/sources

### Ejecutar ingesta programáticamente (sin API)
`python
from app import create_app
from app.services.weather_service import weather_service

app = create_app('development')
with app.app_context():
    # Ingestar SAB
    result = weather_service.ingest_data('sab_lluvias')
    print(result)
    # Ingestar IDEAM
    result = weather_service.ingest_data('ideam_radar', radar='Barrancabermeja', limite=10)
    print(result)
`

### Pruebas rápidas
`ash
cd backend
python -c "
from app.adapters import SABSourceAdapter, IDEAMRadarSourceAdapter
from app.services import WeatherIngestionService, WeatherService
print('OK')
"
`

### Notas
- El adaptador IDEAM reutiliza módulos de src/; asegúrese de que src/ esté en ruta (se añade automáticamente).
- Para scraping SAB, requiere conexión a internet. En entornos sin red, el fetch fallará con error controlado.
- Todas las operaciones siguen principios SOLID, con manejo de errores, timeouts y reintentos donde aplica.
- Código documentado con docstrings técnicos (Python). Restricciones de tono: documentación estrictamente profesional, técnica y formal.
