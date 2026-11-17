# ClimaGuru

Refactor del proyecto orientado a arquitectura cliente-servidor limpia:

- Backend: Flask API REST
- Frontend: React (Vite)

## Estructura actual

```text
ClimaGuru/
    backend/
        app.py
        config.py
        database/
        models/
        routes/
    frontend/
        src/
        components/
        services/
```

## Pagina publica (MVP meteorologico)

Nueva entrada sin autenticacion: `http://localhost:5173/` (ruta `/` del frontend).

- Mapa interactivo (Leaflet + tiles abiertos de OpenStreetMap, sin API key).
- Clima actual por ciudad via Open-Meteo (temperatura, sensacion, humedad,
  viento, precipitacion, nubosidad, presion).
- Radares IDEAM: marcadores con cobertura (240 km), visor del compuesto
  nacional, PNG transparente por radar y navegacion temporal por frames.
- Almacenamiento experimental en SQLite (aislado de MySQL): cache de clima
  con TTL, metadatos de scans radar y log de peticiones con throttle.

### Endpoints publicos (sin JWT)

- GET /api/public/cities
- GET /api/public/weather?lat=&lon=
- GET /api/public/radar/stations
- GET /api/public/radar/latest
- GET /api/public/radar/overlay?radar=<id>
- GET /api/public/radar/frames?radar=<id>

Atribucion requerida: Open-Meteo (CC BY 4.0), IDEAM radar (CC BY 4.0),
OpenStreetMap. La zona autenticada (`/login`, `/dashboard`) queda intacta.

## Backend Flask

Ubicacion: `backend/`

### Endpoints

- POST /login
- GET /users
- POST /users
- PUT /users/<id>
- DELETE /users/<id>
- GET /health

### Ejecutar backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Variables de entorno

Archivo: `backend/.env.example`

- SECRET_KEY
- DATABASE_URL (por defecto SQLite)
- CORS_ORIGINS

### Usuario inicial para pruebas

- username: admin
- password: admin123

## Frontend React

Ubicacion: `frontend/`

### Ejecutar frontend

```bash
cd frontend
npm install
npm run dev
```

### Variable de entorno API

Archivo: `frontend/.env.example`

- VITE_API_BASE_URL=http://localhost:5000

## Pruebas

Backend (sin MySQL ni red real: SQLite en temporales y upstreams mockeados):

```bash
E:\GIT\ClimaGuru\.venv\Scripts\python.exe -m pytest backend\tests -q
# en CI: .github/workflows/backend-tests.yml corre pytest en cada push/PR a main
```

## Pruebas con Postman

Flujo recomendado:

1. POST /login para obtener token.
2. Usar Authorization: Bearer <token> en rutas /users.
3. Ejecutar CRUD completo de usuarios.

## Notas de arquitectura

- La zona autenticada usa Flask + JWT (cookies httpOnly) + MySQL via Tailscale.
- La zona publica usa SQLite propio (`backend/data/climaguru_public.sqlite`), aislado de MySQL.
- Existe un Backend B (`backend/app_pkg/`) reservado para la fase privada posterior.

## Tecnologias Utilizadas

- **Python 3.10+** / Flask 3
- **Flask-JWT-Extended** - Autenticacion JWT (cookies httpOnly)
- **Flask-SQLAlchemy + PyMySQL** - MySQL (zona privada)
- **SQLite** (sqlite3 directo) - zona publica
- **Flask-Limiter / throttle propio** - limites de tasa
- **Open-Meteo** - clima actual (sin API key, CC BY 4.0)
- **IDEAM (bart.ideam.gov.co)** - radares (CC BY 4.0)
- **React 18 + Vite + Leaflet** - frontend

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
| **API REST** | Endpoints públicos y privados | Flask 3 |
| **Autenticación** | Login seguro | JWT (Flask-JWT-Extended, cookies httpOnly) |
| **Base de Datos** | Usuarios, consultas, API keys (fase privada) | MySQL 8.0 |
| **ORM** | Mapeo objeto-relacional | SQLAlchemy |
| **Migraciones** | Control de cambios en BD | Flask-Migrate |
| **Persistencia pública** | Cache, scans radar, log de peticiones | SQLite (WAL) |
| **CORS** | Acceso desde frontend con credenciales | Flask-CORS |

---

## MODELO DE BASE DE DATOS (zona privada - `backend/app_pkg`, fase posterior)

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

---

## 📝 Licencia

Este proyecto está bajo la licencia especificada en el archivo [LICENSE](LICENSE).

## 👥 Autores

- **Paradoja Devs*

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Última actualización:** Noviembre 2026


