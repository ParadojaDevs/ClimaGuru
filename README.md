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

## Pruebas con Postman

Flujo recomendado:

1. POST /login para obtener token.
2. Usar Authorization: Bearer <token> en rutas /users.
3. Ejecutar CRUD completo de usuarios.

## Notas de limpieza

- Se removio la logica de Streamlit del flujo principal.
- Se eliminó el frontend Next.js y se reemplazo por React limpio.
- Se eliminó codigo de scripts legacy en la raiz.

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

PRÓXIMOS PASOS (FRONTEND)

### 🎨 Preparación para el Frontend

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA FUTURA CON FRONTEND                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐         ┌─────────────────┐         ┌───────────────┐ │
│   │   FRONTEND      │         │   BACKEND       │         │   DATABASE    │ │
│   │   (React/Vue)   │◄───────►│   Flask API     │◄───────►│   MySQL       │ │
│   │                 │  HTTP   │                 │  TCP    │               │ │
│   │  - Login Form   │         │  - Auth JWT     │         │               │ │
│   │  - Dashboard    │         │  - Consultas    │         │               │ │
│   │  - Mapas        │         │  - API Externas │         │               │ │
│   │  - Gráficos     │         │                 │         │               │ │
│   └─────────────────┘         └─────────────────┘         └───────────────┘ │
│                                                                              │
│   Comunicación: REST API JSON                                                │
│   Autenticación: Bearer Token JWT                                            │
│   CORS: Habilitado en Flask                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🔧 Configuración CORS para Frontend

```python
# En app/__init__.py, ya está configurado:
from flask_cors import CORS

cors.init_app(app, origins=[
    'http://localhost:3000',      # React dev
    'http://localhost:8080',      # Vue dev
    'https://tu-dominio.com'      # Producción
])
```

### 📦 Endpoints Listos para Frontend

| Funcionalidad Frontend | Endpoint Backend | Método |
|------------------------|------------------|--------|
| Login | `/api/auth/login` | POST |
| Registro | `/api/auth/register` | POST |
| Dashboard datos | `/api/consultas/mis-consultas` | GET |
| Nueva consulta | `/api/consultas/tiempo-real` | POST |
| Ver detalle | `/api/consultas/<id>` | GET |
| Descargar CSV | `/api/consultas/<id>/descargar` | GET |
| Estadísticas | `/api/reportes/estadisticas` | GET |

---

## 📝 Licencia

Este proyecto está bajo la licencia especificada en el archivo [LICENSE](LICENSE).

## 👥 Autores

- **Paradoja Devs*

## 📧 Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.

---

**Última actualización:** Febrero 2026


