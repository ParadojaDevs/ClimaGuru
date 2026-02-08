# 🌦️ ClimaGuru

Sistema integrado de consulta y análisis de datos climáticos desde múltiples fuentes meteorológicas.

## 📋 Descripción

**ClimaGuru** (CLIMAPI) es una plataforma que recopila, procesa y analiza datos meteorológicos desde diversas APIs especializadas, proporcionando información completa sobre:
- ⛅ Pronósticos meteorológicos
- 🌡️ Datos climáticos actuales e históricos
- 💨 Calidad del aire
- 📡 Imágenes de radares meteorológicos
- 📊 Análisis y visualizaciones de datos

## 🎯 Estado del Proyecto

**Estado:** ✅ Funcional y en desarrollo activo

### APIs Integradas:
- ✅ **Meteoblue** - Pronósticos detallados y meteogramas
- ✅ **Open-Meteo** - Pronósticos gratuitos y datos históricos
- ✅ **OpenWeatherMap** - Clima actual, pronóstico 5 días y calidad del aire
- ✅ **Meteosource** - Datos meteorológicos completos
- ✅ **IDEAM** - Radares meteorológicos de Colombia (AWS público)
- ✅ **SIATA** - Datos históricos de Medellín y región

## ✨ Características

- 🔄 Consulta unificada de múltiples fuentes meteorológicas
- 📍 Soporte para ubicaciones personalizadas (coordenadas GPS)
- 💾 Almacenamiento automático de datos en formatos JSON y CSV
- 📊 Procesamiento y análisis de datos de radar
- 🖼️ Descarga de meteogramas e imágenes de radar
- 🗂️ Estructura organizada de datos por fuente
- 📡 Descarga de datos históricos SIATA
- 🎯 Menú interactivo para consultas rápidas

## 🔧 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Conexión a Internet
- Claves API (para servicios que las requieren)

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/xtatikmel/ClimaGuru.git
cd ClimaGuru
```

### 2. Crear entorno virtual

**En Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

### 1. Crear archivo de variables de entorno

Crear un archivo `.env` en la raíz del proyecto con las siguientes claves API:

```env
# Meteoblue (Opcional - requiere registro)
METEOBLUE_API_KEY=tu_api_key_aqui
METEOBLUE_SHARED_SECRET=tu_shared_secret_aqui

# OpenWeatherMap (Opcional - requiere registro)
OPENWEATHER_API_KEY=tu_api_key_aqui

# Meteosource (Opcional - requiere registro)
METEOSOURCE_API_KEY=tu_api_key_aqui

# Open-Meteo (Gratuito - No requiere API key)
# IDEAM (Público - No requiere credenciales)
# SIATA (Público - No requiere credenciales)
```

### 2. Obtener claves API

Las APIs que requieren registro ofrecen planes gratuitos:

- **Meteoblue**: [https://www.meteoblue.com/](https://www.meteoblue.com/)
- **OpenWeatherMap**: [https://openweathermap.org/](https://openweathermap.org/)
- **Meteosource**: [https://www.meteosource.com/](https://www.meteosource.com/)
- **Open-Meteo**: [https://open-meteo.com/](https://open-meteo.com/) (no requiere clave)

**Documentación:**
- [Meteoblue API Docs](https://docs.meteoblue.com/)

## 🚀 Uso

### Modo Interactivo

Ejecutar el menú principal:

```bash
python main.py
```

El sistema mostrará un menú con las siguientes opciones:

```
1. Consulta completa (todas las APIs)
2. Consultar solo Meteoblue
3. Consultar solo Open-Meteo (pronóstico)
4. Consultar solo Open-Meteo (histórico)
5. Consultar solo OpenWeatherMap
6. Consultar solo Meteosource
7. Consultar radares IDEAM
8. Listar radares IDEAM disponibles
9. Descargar datos SIATA históricos
10. Salir
```

### Ubicaciones Predefinidas

El sistema incluye ubicaciones principales de Colombia:
- 🏙️ Medellín
- 🏛️ Bogotá
- 🏖️ Cartagena
- 🌆 Cali
- 🌴 Barranquilla

También permite ingresar coordenadas personalizadas.

### Ejemplo de Uso en Código

```python
from main import ClimAPIManager

# Inicializar el gestor
manager = ClimAPIManager()

# Consulta completa para Medellín
resultados = manager.consulta_completa(
    lat=6.245,
    lon=-75.5715,
    location_name="Medellin",
    asl=1495
)

# Consultar solo OpenWeatherMap
datos = manager.consultar_openweather(6.245, -75.5715, "Medellin")

# Consultar radares IDEAM
archivos_radar = manager.consultar_ideam_radar("Barrancabermeja")
```

## 📁 Estructura del Proyecto

```
ClimaGuru/
├── main.py                          # Script principal con menú interactivo
├── requirements.txt                 # Dependencias del proyecto
├── .env                            # Variables de entorno (API keys)
├── README.md                       # Documentación
├── LICENSE                         # Licencia del proyecto
│
├── data/                           # Datos descargados
│   ├── data_meteoblue/            # Pronósticos Meteoblue
│   ├── data_openmeteo/            # Datos Open-Meteo (CSV/JSON)
│   ├── data_openweathermap/       # Datos OpenWeatherMap
│   ├── data_meteosource/          # Datos Meteosource
│   ├── images_meteo_blue/         # Meteogramas
│   ├── Radar_IDEAM/               # Imágenes de radar IDEAM
│   └── siata_historico/           # Datos históricos SIATA
│
├── logs/                          # Archivos de log
│   ├── ideam/                     # Logs de IDEAM
│   └── siata/                     # Logs de SIATA
│
└── src/                           # Código fuente
    ├── data_sources/              # Clientes de APIs
    │   ├── meteoblue.py          # Cliente Meteoblue
    │   ├── open_meteo.py         # Cliente Open-Meteo
    │   ├── openweather.py        # Cliente OpenWeatherMap
    │   ├── Meteosource.py        # Cliente Meteosource
    │   ├── ideam_radar_downloader.py  # Descargador IDEAM
    │   └── siata_cliente.py      # Cliente SIATA
    │
    ├── processors/                # Procesadores de datos
    │   ├── radar_processor.py    # Procesador de datos radar
    │   ├── radar_advanced_processor.py
    │   └── radar_raw_processor.py
    │
    └── data_loaders/              # Cargadores de datos
        ├── file_loader.py        # Cargador de archivos
        ├── json_loader.py        # Cargador JSON
        └── unified_loader.py     # Cargador unificado
```

## 📊 Salida de Datos

Los datos se guardan automáticamente en el directorio `data/` con las siguientes características:

- **JSON**: Datos estructurados de APIs
- **CSV**: Series temporales (Open-Meteo)
- **PNG/JPG**: Imágenes de meteogramas y radares
- **Timestamp**: Cada archivo incluye fecha y hora de descarga
- **Organización**: Separados por fuente de datos

## 🛠️ Tecnologías Utilizadas

- **Python 3.8+**
- **requests** - Consultas HTTP
- **pandas** - Análisis de datos
- **boto3** - AWS S3 (IDEAM)
- **Pillow** - Procesamiento de imágenes
- **matplotlib/seaborn** - Visualizaciones
- **beautifulsoup4** - Web scraping (SIATA)
- **streamlit** - Dashboard (opcional)

## 🤝 Contribución

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request


###  ARQUITECTURA GENERAL

### 🏗️ Diagrama de la Infraestructura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIMAGURU BACKEND                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐         ┌─────────────────────┐                   │
│   │   VM 1: Ubuntu      │         │   VM 2: MySQL       │                   │
│   │   Server (Flask)    │◄───────►│   Database          │                   │
│   │                     │  Tailscale│                   │                   │
│   │   IP: 100.x.x.x     │   VPN   │   IP: 100.x.x.x     │                   │
│   │                     │         │                     │                   │
│   │  ┌───────────────┐  │         │  ┌───────────────┐  │                   │
│   │  │  Flask App    │  │         │  │  MySQL 8.0    │  │                   │
│   │  │  - API REST   │  │         │  │  - Usuarios   │  │                   │
│   │  │  - Auth JWT   │  │         │  │  - Consultas  │  │                   │
│   │  │  - Cache      │  │         │  │  - API Keys   │  │                   │
│   │  └───────────────┘  │         │  └───────────────┘  │                   │
│   └─────────────────────┘         └─────────────────────┘                   │
│            │                                   ▲                            │
│            │         ┌───────────────────────┘                              │
│            │         │                                                      │
│            ▼         │                                                      │
│   ┌─────────────────────┐                                                   │
│   │  APIs Externas      │                                                   │
│   │  - OpenWeatherMap   │                                                   │
│   │  - Open-Meteo       │                                                   │
│   │  - Meteoblue        │                                                   │
│   │  - Meteosource      │                                                   │
│   │  - IDEAM            │                                                   │
│   │  - SIATA            │                                                   │
│   └─────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 📦 Componentes Principales

| Componente | Función | Tecnología |
|------------|---------|------------|
| **API REST** | Exponer endpoints para el frontend | Flask + Flask-RESTful |
| **Autenticación** | Login seguro de operarios | JWT (PyJWT) |
| **Base de Datos** | Almacenar usuarios, consultas, API keys | MySQL 8.0 |
| **ORM** | Mapeo objeto-relacional | SQLAlchemy |
| **Migraciones** | Control de cambios en BD | Flask-Migrate |
| **Validación** | Validar datos de entrada | Marshmallow |
| **CORS** | Permitir acceso desde frontend | Flask-CORS |

---

## . MODELO DE BASE DE DATOS

### 📊 Diagrama Entidad-Relación

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODELO ENTIDAD-RELACIÓN                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         ┌──────────────────┐         ┌─────────────────┐ │
│   │   usuarios   │         │    consultas     │         │  api_keys       │ │
│   ├──────────────┤         ├──────────────────┤         ├─────────────────┤ │
│   │ PK id        │◄────────┤ PK id            │         │ PK id           │ │
│   │    username  │    1:N  │ FK usuario_id    │         │ FK usuario_id   │─┘
│   │    email     │         │    tipo_consulta │         │    proveedor    │
│   │    password  │         │    ciudad        │         │    api_key      │
│   │    rol       │         │    latitud       │         │    activa       │
│   │    activo    │         │    longitud      │         │    creada_en    │
│   │    creado_en │         │    fecha_inicio  │         └─────────────────┘
│   └──────────────┘         │    fecha_fin     │
│                            │    formato       │         ┌─────────────────┐
│                            │    parametros    │         │  datos_clima    │
│                            │    respuesta_api │         ├─────────────────┤
│                            │    promedios     │◄────────┤ PK id           │
│                            │    estado        │    1:1  │ FK consulta_id  │
│                            │    creada_en     │         │    temperatura  │
│                            └──────────────────┘         │    presion      │
│                                                         │    humedad      │
│                                                         │    viento_vel   │
│                                                         │    viento_dir   │
│                                                         │    fuentes      │
│                                                         │    guardado_en  │
│                                                         └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```


## 📝 Licencia

Este proyecto está bajo la licencia especificada en el archivo [LICENSE](LICENSE).

## 👥 Autores

- **ClimAPI Team**

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Última actualización:** Febrero 2026


