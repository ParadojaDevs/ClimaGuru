# 🌦️ ClimaGuru - Guía Completa del Backend con Flask y MySQL

> **Proyecto:** Backend API REST para consultas meteorológicas  
> **Tecnologías:** Flask + MySQL + Tailscale VPN  
> **Nivel:** Principiante-Amateur  
> **Fecha:** Febrero 2026

---

## 📋 ÍNDICE

1. [Arquitectura General](#1-arquitectura-general)
2. [Modelo de Base de Datos](#2-modelo-de-base-de-datos)
3. [Estructura del Proyecto Backend](#3-estructura-del-proyecto-backend)
4. [Implementación Paso a Paso](#4-implementación-paso-a-paso)
5. [Despliegue en Máquinas Virtuales](#5-despliegue-en-máquinas-virtuales)
6. [Configuración Tailscale VPN](#6-configuración-tailscale-vpn)
7. [Autenticación GitHub en VM](#7-autenticación-github-en-vm)
8. [API Endpoints Disponibles](#8-api-endpoints-disponibles)
9. [Próximos Pasos (Frontend)](#9-próximos-pasos-frontend)

---

## 1. ARQUITECTURA GENERAL

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

## 2. MODELO DE BASE DE DATOS

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

### 🗄️ Script SQL Completo

```sql
-- =====================================================
-- CLIMAGURU - SCRIPT DE BASE DE DATOS MySQL
-- =====================================================
-- Ejecutar: mysql -u root -p < climaguru_schema.sql

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS climaguru 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE climaguru;

-- =====================================================
-- TABLA: usuarios
-- Almacena los operarios/usuarios del sistema
-- =====================================================
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(100),
    rol ENUM('admin', 'operario', 'consultor') DEFAULT 'operario',
    activo BOOLEAN DEFAULT TRUE,
    ultimo_login DATETIME,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_rol (rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: api_keys
-- Almacena las API keys de cada proveedor por usuario
-- =====================================================
CREATE TABLE api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    proveedor VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT,
    descripcion VARCHAR(255),
    activa BOOLEAN DEFAULT TRUE,
    limite_consultas_diarias INT DEFAULT 1000,
    consultas_realizadas INT DEFAULT 0,
    ultimo_uso DATETIME,
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_proveedor_usuario (usuario_id, proveedor),
    INDEX idx_proveedor (proveedor),
    INDEX idx_activa (activa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: consultas
-- Registra cada consulta realizada por los usuarios
-- =====================================================
CREATE TABLE consultas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo_consulta ENUM('tiempo_real', 'historico') NOT NULL,
    ciudad VARCHAR(100),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    fecha_inicio DATE,
    fecha_fin DATE,
    formato_salida ENUM('json', 'csv', 'txt', 'yaml') DEFAULT 'json',
    parametros_solicitados JSON,
    respuesta_api JSON,
    estado ENUM('pendiente', 'procesando', 'completada', 'error') DEFAULT 'pendiente',
    mensaje_error TEXT,
    tiempo_respuesta_ms INT,
    ip_origen VARCHAR(45),
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completada_en DATETIME,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario (usuario_id),
    INDEX idx_tipo (tipo_consulta),
    INDEX idx_estado (estado),
    INDEX idx_creada (creada_en),
    INDEX idx_ciudad (ciudad),
    INDEX idx_coordenadas (latitud, longitud)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: datos_clima
-- Almacena los datos procesados y promedios
-- =====================================================
CREATE TABLE datos_clima (
    id INT AUTO_INCREMENT PRIMARY KEY,
    consulta_id INT NOT NULL,
    temperatura_promedio DECIMAL(5, 2),
    temperatura_min DECIMAL(5, 2),
    temperatura_max DECIMAL(5, 2),
    presion_atmosferica DECIMAL(8, 2),
    humedad_relativa INT,
    velocidad_viento DECIMAL(5, 2),
    direccion_viento INT,
    precipitacion DECIMAL(6, 2),
    visibilidad INT,
    indice_uv DECIMAL(4, 2),
    calidad_aire INT,
    descripcion_clima VARCHAR(100),
    fuentes_utilizadas JSON,
    datos_completos JSON,
    guardado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (consulta_id) REFERENCES consultas(id) ON DELETE CASCADE,
    UNIQUE KEY unique_consulta (consulta_id),
    INDEX idx_temperatura (temperatura_promedio),
    INDEX idx_fecha (guardado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: logs_actividad
-- Registro de actividad de usuarios (auditoría)
-- =====================================================
CREATE TABLE logs_actividad (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(50) NOT NULL,
    detalle JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX idx_usuario (usuario_id),
    INDEX idx_accion (accion),
    INDEX idx_fecha (creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- TABLA: ciudades_favoritas
-- Ciudades guardadas por cada usuario
-- =====================================================
CREATE TABLE ciudades_favoritas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre_ciudad VARCHAR(100) NOT NULL,
    pais VARCHAR(50),
    latitud DECIMAL(10, 8) NOT NULL,
    longitud DECIMAL(11, 8) NOT NULL,
    es_default BOOLEAN DEFAULT FALSE,
    creada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_ciudad_usuario (usuario_id, latitud, longitud),
    INDEX idx_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- DATOS INICIALES
-- =====================================================

-- Usuario administrador por defecto
-- Contraseña: admin123 (cambiar en producción)
-- Generada con: bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol) VALUES 
('admin', 'admin@climaguru.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1K', 'Administrador', 'admin');

-- Usuario operario de ejemplo
-- Contraseña: operario123
INSERT INTO usuarios (username, email, password_hash, nombre_completo, rol) VALUES 
('operario1', 'operario1@climaguru.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1K', 'Operario Demo', 'operario');

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista de consultas con datos del usuario
CREATE VIEW vista_consultas_completas AS
SELECT 
    c.id,
    c.tipo_consulta,
    c.ciudad,
    c.latitud,
    c.longitud,
    c.estado,
    c.creada_en,
    u.username,
    u.nombre_completo,
    dc.temperatura_promedio,
    dc.presion_atmosferica,
    dc.velocidad_viento
FROM consultas c
JOIN usuarios u ON c.usuario_id = u.id
LEFT JOIN datos_clima dc ON c.id = dc.consulta_id;

-- Vista de estadísticas por usuario
CREATE VIEW vista_estadisticas_usuarios AS
SELECT 
    u.id,
    u.username,
    u.nombre_completo,
    COUNT(c.id) as total_consultas,
    COUNT(CASE WHEN c.estado = 'completada' THEN 1 END) as consultas_exitosas,
    MAX(c.creada_en) as ultima_consulta
FROM usuarios u
LEFT JOIN consultas c ON u.id = c.usuario_id
WHERE u.activo = TRUE
GROUP BY u.id, u.username, u.nombre_completo;
```

---

## 3. ESTRUCTURA DEL PROYECTO BACKEND

### 📁 Árbol de Directorios

```
climaguru-backend/
│
├── 📂 app/                          # Aplicación principal Flask
│   ├── __init__.py                  # Factory de la aplicación
│   ├── config.py                    # Configuraciones
│   ├── extensions.py                # Extensiones (db, jwt, etc.)
│   │
│   ├── 📂 models/                   # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── usuario.py               # Modelo Usuario
│   │   ├── api_key.py               # Modelo ApiKey
│   │   ├── consulta.py              # Modelo Consulta
│   │   ├── datos_clima.py           # Modelo DatosClima
│   │   ├── log_actividad.py         # Modelo LogActividad
│   │   └── ciudad_favorita.py       # Modelo CiudadFavorita
│   │
│   ├── 📂 schemas/                  # Schemas Marshmallow
│   │   ├── __init__.py
│   │   ├── usuario_schema.py
│   │   ├── consulta_schema.py
│   │   └── api_key_schema.py
│   │
│   ├── 📂 routes/                   # Blueprints/Rutas
│   │   ├── __init__.py
│   │   ├── auth.py                  # Login/Register
│   │   ├── consultas.py             # Endpoints de consultas
│   │   ├── usuarios.py              # Gestión de usuarios
│   │   ├── api_keys.py              # Gestión de API keys
│   │   └── reportes.py              # Reportes y estadísticas
│   │
│   ├── 📂 services/                 # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Servicio de autenticación
│   │   ├── clima_service.py         # Servicio de consultas climáticas
│   │   ├── api_key_service.py       # Servicio de API keys
│   │   └── encryption_service.py    # Encriptación de datos sensibles
│   │
│   ├── 📂 utils/                    # Utilidades
│   │   ├── __init__.py
│   │   ├── decorators.py            # Decoradores personalizados
│   │   ├── validators.py            # Validaciones
│   │   └── helpers.py               # Funciones auxiliares
│   │
│   └── 📂 integrations/             # Integraciones con APIs externas
│       ├── __init__.py
│       ├── base_client.py           # Cliente base
│       ├── openweather_client.py
│       ├── openmeteo_client.py
│       ├── meteoblue_client.py
│       ├── meteosource_client.py
│       ├── ideam_client.py
│       └── siata_client.py
│
├── 📂 migrations/                   # Migraciones Flask-Migrate
│   ├── versions/
│   └── alembic.ini
│
├── 📂 tests/                        # Tests
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_consultas.py
│   └── conftest.py
│
├── 📂 scripts/                      # Scripts de utilidad
│   ├── init_db.py                   # Inicializar base de datos
│   ├── create_admin.py              # Crear usuario admin
│   └── backup_db.sh                 # Backup de BD
│
├── 📂 docs/                         # Documentación
│   └── api.md                       # Documentación de API
│
├── .env.example                     # Variables de entorno ejemplo
├── .env                             # Variables de entorno (no subir a git)
├── .gitignore                       # Archivos ignorados por git
├── requirements.txt                 # Dependencias Python
├── run.py                           # Punto de entrada
├── wsgi.py                          # Configuración WSGI
└── README.md                        # Este archivo
```

---

## 4. IMPLEMENTACIÓN PASO A PASO

### 📝 Paso 1: Crear Estructura de Archivos

```bash
# Crear directorio del proyecto
mkdir climaguru-backend
cd climaguru-backend

# Crear estructura de directorios
mkdir -p app/{models,schemas,routes,services,utils,integrations}
mkdir -p migrations tests scripts docs

# Crear archivos iniciales
touch app/__init__.py
touch app/config.py
touch app/extensions.py
touch run.py wsgi.py requirements.txt .env.example .gitignore
```

### 📝 Paso 2: Archivo requirements.txt

```txt
# ============================================
# CLIMAGURU BACKEND - DEPENDENCIAS
# ============================================

# Framework Flask
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
Flask-RESTful==0.3.10

# Base de datos
PyMySQL==1.1.0
cryptography==41.0.7  # Para autenticación MySQL

# Serialización y validación
marshmallow==3.20.1
marshmallow-sqlalchemy==0.29.0

# Seguridad
bcrypt==4.1.2
PyJWT==2.8.0
python-dotenv==1.0.0

# HTTP requests
requests==2.31.0
requests-cache==1.1.1

# Utilidades
python-dateutil==2.8.2
pytz==2023.3

# Testing
pytest==7.4.3
pytest-flask==1.3.0

# Producción
gunicorn==21.2.0
```

### 📝 Paso 3: Configuración (.env.example)

```bash
# ============================================
# CLIMAGURU BACKEND - VARIABLES DE ENTORNO
# ============================================

# ============================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=tu-clave-secreta-super-segura-cambia-en-produccion

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS MySQL
# ============================================
# Para desarrollo local:
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/climaguru

# Para producción con Tailscale (usar IP de la VM MySQL):
DATABASE_URL=mysql+pymysql://climaguru_user:tu_password_seguro@100.x.x.x:3306/climaguru

# Descomponer para configuración manual:
DB_HOST=100.x.x.x
DB_PORT=3306
DB_NAME=climaguru
DB_USER=climaguru_user
DB_PASSWORD=tu_password_seguro

# ============================================
# CONFIGURACIÓN JWT
# ============================================
JWT_SECRET_KEY=otra-clave-super-secreta-para-jwt
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=86400

# ============================================
# ENCRIPTACIÓN DE API KEYS
# ============================================
ENCRYPTION_KEY=tu-clave-de-32-caracteres-para-encriptar!

# ============================================
# APIs EXTERNAS (Keys de ejemplo - se sobreescriben en BD)
# ============================================
OPENWEATHER_API_KEY=tu_api_key_aqui
METEOBLUE_API_KEY=tu_api_key_aqui
METEOBLUE_API_SECRET=tu_api_secret_aqui
METEOSOURCE_API_KEY=tu_api_key_aqui
```

### 📝 Paso 4: Archivo .gitignore

```gitignore
# ============================================
# CLIMAGURU BACKEND - GITIGNORE
# ============================================

# Entorno virtual
venv/
env/
ENV/
.venv/

# Variables de entorno
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Base de datos local
*.sqlite
*.db

# Migraciones (opcional - algunos prefieren versionarlas)
# migrations/versions/*.py
# !migrations/versions/.gitkeep

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Backup
*.bak
*.backup
```

### 📝 Paso 5: Configuración de la App (app/config.py)

```python
"""
Configuración de la aplicación Flask
====================================
"""
import os
from datetime import timedelta


class Config:
    """Configuración base"""
    
    # App
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-cambiar-en-produccion'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:password@localhost:3306/climaguru'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(
        os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
    ))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(
        os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 86400)
    ))
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Encriptación
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # En producción, requerir todas las variables
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

### 📝 Paso 6: Extensiones (app/extensions.py)

```python
"""
Extensiones de Flask
====================
Inicialización de extensiones para evitar importaciones circulares
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restful import Api

# Inicializar extensiones (sin app todavía)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
api = Api()
```

### 📝 Paso 7: Factory Pattern (app/__init__.py)

```python
"""
ClimaGuru Backend - Factory Pattern
====================================
Inicialización de la aplicación Flask
"""
from flask import Flask, jsonify
from app.extensions import db, migrate, jwt, cors, api
from app.config import config


def create_app(config_name='default'):
    """
    Factory pattern para crear la aplicación Flask
    
    Args:
        config_name: Nombre de la configuración (development, production, testing)
    
    Returns:
        app: Instancia de Flask configurada
    """
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', '*'))
    api.init_app(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar manejadores de errores
    register_error_handlers(app)
    
    # Crear tablas si no existen (solo en desarrollo)
    if config_name == 'development':
        with app.app_context():
            db.create_all()
    
    return app


def register_blueprints(app):
    """Registrar todos los blueprints de la aplicación"""
    from app.routes.auth import auth_bp
    from app.routes.consultas import consultas_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.api_keys import api_keys_bp
    from app.routes.reportes import reportes_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(api_keys_bp, url_prefix='/api/api-keys')
    app.register_blueprint(reportes_bp, url_prefix='/api/reportes')


def register_error_handlers(app):
    """Registrar manejadores de errores"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Solicitud incorrecta', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'No autorizado', 'message': str(error)}), 401
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso no encontrado', 'message': str(error)}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor', 'message': str(error)}), 500


# Importar modelos para que Flask-Migrate los detecte
from app.models import usuario, api_key, consulta, datos_clima, log_actividad, ciudad_favorita
```

### 📝 Paso 8: Modelos SQLAlchemy

#### app/models/__init__.py
```python
"""Modelos de la base de datos"""
```

#### app/models/usuario.py
```python
"""
Modelo: Usuario
===============
Representa un operario/usuario del sistema
"""
from datetime import datetime
from app.extensions import db
import bcrypt


class Usuario(db.Model):
    """Modelo de usuario para autenticación"""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(100))
    rol = db.Column(db.Enum('admin', 'operario', 'consultor', name='rol_enum'), 
                    default='operario')
    activo = db.Column(db.Boolean, default=True)
    ultimo_login = db.Column(db.DateTime)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, 
                               onupdate=datetime.utcnow)
    
    # Relaciones
    consultas = db.relationship('Consulta', backref='usuario', lazy='dynamic',
                                cascade='all, delete-orphan')
    api_keys = db.relationship('ApiKey', backref='usuario', lazy='dynamic',
                               cascade='all, delete-orphan')
    ciudades_favoritas = db.relationship('CiudadFavorita', backref='usuario', 
                                         lazy='dynamic', cascade='all, delete-orphan')
    logs = db.relationship('LogActividad', backref='usuario', lazy='dynamic')
    
    def set_password(self, password):
        """Encriptar y guardar contraseña"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Verificar contraseña"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'rol': self.rol,
            'activo': self.activo,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }
    
    def __repr__(self):
        return f'<Usuario {self.username}>'
```

#### app/models/api_key.py
```python
"""
Modelo: ApiKey
==============
Almacena las API keys encriptadas de cada proveedor
"""
from datetime import datetime
from app.extensions import db


class ApiKey(db.Model):
    """Modelo para almacenar API keys de proveedores"""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    proveedor = db.Column(db.String(50), nullable=False, index=True)
    api_key_encrypted = db.Column(db.Text, nullable=False)
    api_secret_encrypted = db.Column(db.Text)
    descripcion = db.Column(db.String(255))
    activa = db.Column(db.Boolean, default=True, index=True)
    limite_consultas_diarias = db.Column(db.Integer, default=1000)
    consultas_realizadas = db.Column(db.Integer, default=0)
    ultimo_uso = db.Column(db.DateTime)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, 
                               onupdate=datetime.utcnow)
    
    # Constraint único: un proveedor por usuario
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'proveedor', name='unique_proveedor_usuario'),
    )
    
    def to_dict(self, include_key=False):
        """Convertir a diccionario"""
        data = {
            'id': self.id,
            'proveedor': self.proveedor,
            'descripcion': self.descripcion,
            'activa': self.activa,
            'limite_consultas_diarias': self.limite_consultas_diarias,
            'consultas_realizadas': self.consultas_realizadas,
            'ultimo_uso': self.ultimo_uso.isoformat() if self.ultimo_uso else None,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None
        }
        if include_key:
            data['api_key'] = self.api_key_encrypted  # Desencriptar antes de enviar
        return data
    
    def __repr__(self):
        return f'<ApiKey {self.proveedor} - Usuario {self.usuario_id}>'
```

#### app/models/consulta.py
```python
"""
Modelo: Consulta
================
Registra cada consulta meteorológica realizada
"""
from datetime import datetime
from app.extensions import db


class Consulta(db.Model):
    """Modelo de consulta meteorológica"""
    
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    tipo_consulta = db.Column(db.Enum('tiempo_real', 'historico', name='tipo_consulta_enum'),
                              nullable=False, index=True)
    ciudad = db.Column(db.String(100), index=True)
    latitud = db.Column(db.Numeric(10, 8), index=True)
    longitud = db.Column(db.Numeric(11, 8), index=True)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    formato_salida = db.Column(db.Enum('json', 'csv', 'txt', 'yaml', name='formato_enum'),
                               default='json')
    parametros_solicitados = db.Column(db.JSON)
    respuesta_api = db.Column(db.JSON)
    estado = db.Column(db.Enum('pendiente', 'procesando', 'completada', 'error', 
                               name='estado_enum'), 
                       default='pendiente', index=True)
    mensaje_error = db.Column(db.Text)
    tiempo_respuesta_ms = db.Column(db.Integer)
    ip_origen = db.Column(db.String(45))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completada_en = db.Column(db.DateTime)
    
    # Relación con datos procesados
    datos_clima = db.relationship('DatosClima', backref='consulta', uselist=False,
                                  cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'tipo_consulta': self.tipo_consulta,
            'ciudad': self.ciudad,
            'latitud': float(self.latitud) if self.latitud else None,
            'longitud': float(self.longitud) if self.longitud else None,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'formato_salida': self.formato_salida,
            'parametros_solicitados': self.parametros_solicitados,
            'estado': self.estado,
            'mensaje_error': self.mensaje_error,
            'tiempo_respuesta_ms': self.tiempo_respuesta_ms,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None,
            'completada_en': self.completada_en.isoformat() if self.completada_en else None
        }
    
    def __repr__(self):
        return f'<Consulta {self.id} - {self.tipo_consulta} - {self.estado}>'
```

#### app/models/datos_clima.py
```python
"""
Modelo: DatosClima
==================
Almacena los datos meteorológicos procesados y promedios
"""
from datetime import datetime
from app.extensions import db


class DatosClima(db.Model):
    """Modelo de datos climáticos procesados"""
    
    __tablename__ = 'datos_clima'
    
    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), 
                            nullable=False, unique=True)
    
    # Temperatura
    temperatura_promedio = db.Column(db.Numeric(5, 2))
    temperatura_min = db.Column(db.Numeric(5, 2))
    temperatura_max = db.Column(db.Numeric(5, 2))
    
    # Presión y humedad
    presion_atmosferica = db.Column(db.Numeric(8, 2))
    humedad_relativa = db.Column(db.Integer)
    
    # Viento
    velocidad_viento = db.Column(db.Numeric(5, 2))
    direccion_viento = db.Column(db.Integer)
    
    # Precipitación y visibilidad
    precipitacion = db.Column(db.Numeric(6, 2))
    visibilidad = db.Column(db.Integer)
    
    # Otros
    indice_uv = db.Column(db.Numeric(4, 2))
    calidad_aire = db.Column(db.Integer)
    descripcion_clima = db.Column(db.String(100))
    
    # Metadatos
    fuentes_utilizadas = db.Column(db.JSON)
    datos_completos = db.Column(db.JSON)  # Todos los datos crudos
    guardado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'consulta_id': self.consulta_id,
            'temperatura': {
                'promedio': float(self.temperatura_promedio) if self.temperatura_promedio else None,
                'min': float(self.temperatura_min) if self.temperatura_min else None,
                'max': float(self.temperatura_max) if self.temperatura_max else None
            },
            'presion_atmosferica': float(self.presion_atmosferica) if self.presion_atmosferica else None,
            'humedad_relativa': self.humedad_relativa,
            'viento': {
                'velocidad': float(self.velocidad_viento) if self.velocidad_viento else None,
                'direccion': self.direccion_viento
            },
            'precipitacion': float(self.precipitacion) if self.precipitacion else None,
            'visibilidad': self.visibilidad,
            'indice_uv': float(self.indice_uv) if self.indice_uv else None,
            'calidad_aire': self.calidad_aire,
            'descripcion_clima': self.descripcion_clima,
            'fuentes_utilizadas': self.fuentes_utilizadas,
            'guardado_en': self.guardado_en.isoformat() if self.guardado_en else None
        }
    
    def __repr__(self):
        return f'<DatosClima Consulta {self.consulta_id}>'
```

#### app/models/log_actividad.py
```python
"""
Modelo: LogActividad
====================
Registro de auditoría de actividad de usuarios
"""
from datetime import datetime
from app.extensions import db


class LogActividad(db.Model):
    """Modelo de log de actividad"""
    
    __tablename__ = 'logs_actividad'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    accion = db.Column(db.String(50), nullable=False, index=True)
    detalle = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'accion': self.accion,
            'detalle': self.detalle,
            'ip_address': self.ip_address,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }
    
    def __repr__(self):
        return f'<LogActividad {self.accion} - Usuario {self.usuario_id}>'
```

#### app/models/ciudad_favorita.py
```python
"""
Modelo: CiudadFavorita
======================
Ciudades guardadas por cada usuario
"""
from datetime import datetime
from app.extensions import db


class CiudadFavorita(db.Model):
    """Modelo de ciudad favorita"""
    
    __tablename__ = 'ciudades_favoritas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre_ciudad = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(50))
    latitud = db.Column(db.Numeric(10, 8), nullable=False)
    longitud = db.Column(db.Numeric(11, 8), nullable=False)
    es_default = db.Column(db.Boolean, default=False)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'latitud', 'longitud', 
                           name='unique_ciudad_usuario'),
    )
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'nombre_ciudad': self.nombre_ciudad,
            'pais': self.pais,
            'latitud': float(self.latitud),
            'longitud': float(self.longitud),
            'es_default': self.es_default,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None
        }
    
    def __repr__(self):
        return f'<CiudadFavorita {self.nombre_ciudad} - Usuario {self.usuario_id}>'
```

### 📝 Paso 9: Blueprint de Autenticación (app/routes/auth.py)

```python
"""
Rutas de Autenticación
======================
Endpoints para login, registro y gestión de tokens
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime
from app.extensions import db
from app.models.usuario import Usuario
from app.models.log_actividad import LogActividad

auth_bp = Blueprint('auth', __name__)

# Blacklist simple para tokens revocados (en producción usar Redis)
blacklist = set()


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registrar nuevo usuario
    
    Body JSON:
        - username: string (requerido)
        - email: string (requerido)
        - password: string (requerido, min 6 caracteres)
        - nombre_completo: string (opcional)
    
    Returns:
        - usuario: datos del usuario creado
        - message: mensaje de éxito
    """
    data = request.get_json()
    
    # Validaciones
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username y password son requeridos'}), 400
    
    if len(data['password']) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    # Verificar si ya existe
    if Usuario.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'El username ya está en uso'}), 409
    
    if Usuario.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'El email ya está registrado'}), 409
    
    # Crear usuario
    usuario = Usuario(
        username=data['username'],
        email=data.get('email', ''),
        nombre_completo=data.get('nombre_completo')
    )
    usuario.set_password(data['password'])
    
    db.session.add(usuario)
    db.session.commit()
    
    # Registrar log
    log = LogActividad(
        usuario_id=usuario.id,
        accion='registro',
        detalle={'username': usuario.username},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Usuario registrado exitosamente',
        'usuario': usuario.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Iniciar sesión y obtener tokens JWT
    
    Body JSON:
        - username: string (requerido)
        - password: string (requerido)
    
    Returns:
        - access_token: token de acceso (1 hora)
        - refresh_token: token de refresco (24 horas)
        - usuario: datos del usuario
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username y password son requeridos'}), 400
    
    # Buscar usuario
    usuario = Usuario.query.filter_by(username=data['username']).first()
    
    if not usuario or not usuario.check_password(data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    if not usuario.activo:
        return jsonify({'error': 'Usuario desactivado'}), 401
    
    # Actualizar último login
    usuario.ultimo_login = datetime.utcnow()
    
    # Crear tokens
    access_token = create_access_token(
        identity=usuario.id,
        additional_claims={
            'username': usuario.username,
            'rol': usuario.rol
        }
    )
    refresh_token = create_refresh_token(identity=usuario.id)
    
    # Registrar log
    log = LogActividad(
        usuario_id=usuario.id,
        accion='login',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'usuario': usuario.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refrescar token de acceso
    
    Header:
        - Authorization: Bearer <refresh_token>
    
    Returns:
        - access_token: nuevo token de acceso
    """
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario or not usuario.activo:
        return jsonify({'error': 'Usuario no válido'}), 401
    
    new_token = create_access_token(
        identity=usuario_id,
        additional_claims={
            'username': usuario.username,
            'rol': usuario.rol
        }
    )
    
    return jsonify({'access_token': new_token}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Cerrar sesión (revocar token)
    
    Header:
        - Authorization: Bearer <access_token>
    
    Returns:
        - message: confirmación de logout
    """
    jti = get_jwt()['jti']
    blacklist.add(jti)
    
    usuario_id = get_jwt_identity()
    
    # Registrar log
    log = LogActividad(
        usuario_id=usuario_id,
        accion='logout',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Obtener información del usuario actual
    
    Header:
        - Authorization: Bearer <access_token>
    
    Returns:
        - usuario: datos del usuario
    """
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(usuario_id)
    
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({'usuario': usuario.to_dict()}), 200


# Callback para verificar si el token está en blacklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blacklist
```

### 📝 Paso 10: Blueprint de Consultas (app/routes/consultas.py)

```python
"""
Rutas de Consultas
==================
Endpoints para realizar consultas meteorológicas
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import db
from app.models.consulta import Consulta
from app.models.datos_clima import DatosClima
from app.models.log_actividad import LogActividad

consultas_bp = Blueprint('consultas', __name__)


@consultas_bp.route('/tiempo-real', methods=['POST'])
@jwt_required()
def consulta_tiempo_real():
    """
    Realizar consulta de clima en tiempo real
    
    Body JSON:
        - ciudad: string (opcional si se envían coordenadas)
        - latitud: float (opcional si se envía ciudad)
        - longitud: float (opcional si se envía ciudad)
        - parametros: array de strings (temperatura, presion, viento, etc.)
        - formato: string (json, csv, txt, yaml) - default: json
    
    Returns:
        - consulta: datos de la consulta registrada
        - datos: datos climáticos procesados
    """
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    # Validar que tenga ciudad o coordenadas
    if not data.get('ciudad') and (not data.get('latitud') or not data.get('longitud')):
        return jsonify({
            'error': 'Debe proporcionar ciudad o coordenadas (latitud, longitud)'
        }), 400
    
    # Crear registro de consulta
    consulta = Consulta(
        usuario_id=usuario_id,
        tipo_consulta='tiempo_real',
        ciudad=data.get('ciudad'),
        latitud=data.get('latitud'),
        longitud=data.get('longitud'),
        formato_salida=data.get('formato', 'json'),
        parametros_solicitados=data.get('parametros', ['temperatura', 'humedad', 'viento']),
        estado='procesando',
        ip_origen=request.remote_addr
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    # TODO: Aquí se integrarían los clientes de las APIs externas
    # Por ahora, simulamos una respuesta
    
    try:
        # Simular consulta a APIs externas
        # En producción: climapi = ClimaAPIManager()
        # datos = climapi.get_current_weather(lat, lon)
        
        datos_simulados = {
            'temperatura': 24.5,
            'humedad': 65,
            'presion': 1013,
            'viento_velocidad': 12,
            'viento_direccion': 180,
            'descripcion': 'Parcialmente nublado'
        }
        
        # Guardar datos procesados
        datos_clima = DatosClima(
            consulta_id=consulta.id,
            temperatura_promedio=datos_simulados['temperatura'],
            humedad_relativa=datos_simulados['humedad'],
            presion_atmosferica=datos_simulados['presion'],
            velocidad_viento=datos_simulados['viento_velocidad'],
            direccion_viento=datos_simulados['viento_direccion'],
            descripcion_clima=datos_simulados['descripcion'],
            fuentes_utilizadas=['openweather', 'openmeteo'],
            datos_completos=datos_simulados
        )
        
        db.session.add(datos_clima)
        
        # Actualizar consulta
        consulta.estado = 'completada'
        consulta.completada_en = datetime.utcnow()
        consulta.tiempo_respuesta_ms = 500  # Simulado
        
        db.session.commit()
        
        # Registrar log
        log = LogActividad(
            usuario_id=usuario_id,
            accion='consulta_tiempo_real',
            detalle={
                'consulta_id': consulta.id,
                'ciudad': consulta.ciudad,
                'coordenadas': f"{consulta.latitud}, {consulta.longitud}"
            },
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'consulta': consulta.to_dict(),
            'datos': datos_clima.to_dict()
        }), 200
        
    except Exception as e:
        consulta.estado = 'error'
        consulta.mensaje_error = str(e)
        db.session.commit()
        
        return jsonify({
            'error': 'Error al procesar la consulta',
            'message': str(e)
        }), 500


@consultas_bp.route('/historico', methods=['POST'])
@jwt_required()
def consulta_historico():
    """
    Realizar consulta de datos históricos
    
    Body JSON:
        - ciudad: string (opcional si se envían coordenadas)
        - latitud: float (opcional si se envía ciudad)
        - longitud: float (opcional si se envía ciudad)
        - fecha_inicio: string (YYYY-MM-DD)
        - fecha_fin: string (YYYY-MM-DD)
        - parametros: array de strings
        - formato: string (json, csv, txt, yaml)
    
    Returns:
        - consulta: datos de la consulta
        - datos: datos históricos procesados
    """
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    # Validaciones
    if not data.get('ciudad') and (not data.get('latitud') or not data.get('longitud')):
        return jsonify({
            'error': 'Debe proporcionar ciudad o coordenadas'
        }), 400
    
    if not data.get('fecha_inicio') or not data.get('fecha_fin'):
        return jsonify({
            'error': 'Debe proporcionar fecha_inicio y fecha_fin'
        }), 400
    
    # Crear consulta
    consulta = Consulta(
        usuario_id=usuario_id,
        tipo_consulta='historico',
        ciudad=data.get('ciudad'),
        latitud=data.get('latitud'),
        longitud=data.get('longitud'),
        fecha_inicio=data.get('fecha_inicio'),
        fecha_fin=data.get('fecha_fin'),
        formato_salida=data.get('formato', 'json'),
        parametros_solicitados=data.get('parametros'),
        estado='procesando',
        ip_origen=request.remote_addr
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    # TODO: Integrar con APIs históricas
    # Por ahora, simulamos
    
    consulta.estado = 'completada'
    consulta.completada_en = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Consulta histórica registrada',
        'consulta': consulta.to_dict()
    }), 200


@consultas_bp.route('/mis-consultas', methods=['GET'])
@jwt_required()
def get_mis_consultas():
    """
    Obtener historial de consultas del usuario
    
    Query params:
        - page: int (default: 1)
        - per_page: int (default: 10, max: 100)
        - tipo: string (tiempo_real, historico)
        - estado: string (pendiente, procesando, completada, error)
    
    Returns:
        - consultas: lista de consultas
        - total: total de consultas
        - pages: total de páginas
    """
    usuario_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    
    query = Consulta.query.filter_by(usuario_id=usuario_id)
    
    if tipo:
        query = query.filter_by(tipo_consulta=tipo)
    if estado:
        query = query.filter_by(estado=estado)
    
    pagination = query.order_by(Consulta.creada_en.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'consultas': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@consultas_bp.route('/<int:consulta_id>', methods=['GET'])
@jwt_required()
def get_consulta(consulta_id):
    """
    Obtener detalle de una consulta específica
    
    Args:
        consulta_id: ID de la consulta
    
    Returns:
        - consulta: datos de la consulta
        - datos_clima: datos climáticos asociados (si existen)
    """
    usuario_id = get_jwt_identity()
    
    consulta = Consulta.query.filter_by(id=consulta_id, usuario_id=usuario_id).first()
    
    if not consulta:
        return jsonify({'error': 'Consulta no encontrada'}), 404
    
    response = {'consulta': consulta.to_dict()}
    
    if consulta.datos_clima:
        response['datos_clima'] = consulta.datos_clima.to_dict()
    
    return jsonify(response), 200


@consultas_bp.route('/<int:consulta_id>/descargar', methods=['GET'])
@jwt_required()
def descargar_consulta(consulta_id):
    """
    Descargar datos de una consulta en el formato solicitado
    
    Args:
        consulta_id: ID de la consulta
    
    Returns:
        - Archivo en formato JSON, CSV, TXT o YAML
    """
    usuario_id = get_jwt_identity()
    
    consulta = Consulta.query.filter_by(id=consulta_id, usuario_id=usuario_id).first()
    
    if not consulta:
        return jsonify({'error': 'Consulta no encontrada'}), 404
    
    if consulta.estado != 'completada':
        return jsonify({'error': 'La consulta no está completada'}), 400
    
    if not consulta.datos_clima:
        return jsonify({'error': 'No hay datos disponibles'}), 404
    
    formato = consulta.formato_salida
    datos = consulta.datos_clima.to_dict()
    
    if formato == 'json':
        return jsonify(datos), 200
    
    elif formato == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(['Parametro', 'Valor'])
        
        # Escribir datos
        writer.writerow(['Temperatura Promedio', datos['temperatura']['promedio']])
        writer.writerow(['Temperatura Min', datos['temperatura']['min']])
        writer.writerow(['Temperatura Max', datos['temperatura']['max']])
        writer.writerow(['Presion', datos['presion_atmosferica']])
        writer.writerow(['Humedad', datos['humedad_relativa']])
        writer.writerow(['Viento Velocidad', datos['viento']['velocidad']])
        writer.writerow(['Viento Direccion', datos['viento']['direccion']])
        
        output.seek(0)
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=consulta_{consulta_id}.csv'
        }
    
    elif formato == 'txt':
        texto = f"""
CONSULTA CLIMÁTICA - ClimaGuru
==============================
ID Consulta: {consulta_id}
Fecha: {consulta.creada_en}

DATOS OBTENIDOS:
----------------
Temperatura: {datos['temperatura']['promedio']}°C
  - Mínima: {datos['temperatura']['min']}°C
  - Máxima: {datos['temperatura']['max']}°C
Presión Atmosférica: {datos['presion_atmosferica']} hPa
Humedad: {datos['humedad_relativa']}%
Viento: {datos['viento']['velocidad']} km/h, dirección {datos['viento']['direccion']}°
Descripción: {datos['descripcion_clima']}

Fuentes: {', '.join(datos['fuentes_utilizadas'] or [])}
"""
        return texto, 200, {'Content-Type': 'text/plain'}
    
    elif formato == 'yaml':
        try:
            import yaml
            return yaml.dump(datos), 200, {'Content-Type': 'text/yaml'}
        except ImportError:
            return jsonify({'error': 'Formato YAML no disponible'}), 500
    
    return jsonify({'error': 'Formato no soportado'}), 400
```

### 📝 Paso 11: Punto de Entrada (run.py)

```python
"""
Punto de entrada de la aplicación
==================================
Ejecutar: python run.py
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from app import create_app

# Crear app con configuración según entorno
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🌦️  CLIMAGURU BACKEND                     ║
╠══════════════════════════════════════════════════════════════╣
║  Entorno: {config_name:<15}                                  ║
║  Host: {host:<20}                                   ║
║  Puerto: {port:<15}                                    ║
║  Debug: {str(debug):<15}                                    ║
╚══════════════════════════════════════════════════════════════╝

Endpoints disponibles:
  - POST   /api/auth/register      → Registrar usuario
  - POST   /api/auth/login         → Iniciar sesión
  - POST   /api/auth/refresh       → Refrescar token
  - POST   /api/auth/logout        → Cerrar sesión
  - GET    /api/auth/me            → Datos del usuario
  - POST   /api/consultas/tiempo-real  → Consulta tiempo real
  - POST   /api/consultas/historico    → Consulta histórica
  - GET    /api/consultas/mis-consultas → Historial
  
Documentación completa: /api/docs (próximamente)
    """)
    
    app.run(host=host, port=port, debug=debug)
```

---

## 5. DESPLIEGUE EN MÁQUINAS VIRTUALES

### 🖥️ VM 1: MySQL Database Server

```bash
# ============================================
# CONFIGURACIÓN VM 1 - MySQL SERVER
# ============================================

# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar MySQL Server
sudo apt install mysql-server -y

# 3. Iniciar y habilitar MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 4. Configurar seguridad básica
sudo mysql_secure_installation

# 5. Crear base de datos y usuario
sudo mysql -u root -p

# Dentro de MySQL:
CREATE DATABASE climaguru CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'climaguru_user'@'%' IDENTIFIED BY 'tu_password_seguro_aqui';
GRANT ALL PRIVILEGES ON climaguru.* TO 'climaguru_user'@'%';
FLUSH PRIVILEGES;
EXIT;

# 6. Configurar MySQL para aceptar conexiones remotas
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# Modificar estas líneas:
# bind-address = 0.0.0.0
# mysqlx-bind-address = 0.0.0.0

# 7. Reiniciar MySQL
sudo systemctl restart mysql

# 8. Verificar estado
sudo systemctl status mysql
sudo netstat -tlnp | grep mysql
```

### 🖥️ VM 2: Ubuntu Server (Flask Backend)

```bash
# ============================================
# CONFIGURACIÓN VM 2 - FLASK SERVER
# ============================================

# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv git nginx

# 3. Crear usuario para la aplicación
sudo useradd -m -s /bin/bash climaguru
sudo usermod -aG sudo climaguru

# 4. Cambiar al usuario
sudo su - climaguru

# 5. Crear directorio de la aplicación
mkdir -p ~/climaguru-backend
cd ~/climaguru-backend

# 6. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 7. Instalar dependencias (ver sección de requirements.txt)
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended flask-cors pymysql cryptography bcrypt marshmallow python-dotenv requests gunicorn

# 8. Crear archivo .env
nano .env

# Contenido del .env:
# ============================================
FLASK_APP=run.py
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria

# Base de datos (IP de la VM MySQL vía Tailscale)
DATABASE_URL=mysql+pymysql://climaguru_user:tu_password_seguro@100.x.x.x:3306/climaguru

# JWT
JWT_SECRET_KEY=otra-clave-super-secreta-para-jwt
JWT_ACCESS_TOKEN_EXPIRES=3600

# Encriptación
ENCRYPTION_KEY=tu-clave-de-32-caracteres-para-encriptar!
# ============================================

# 9. Copiar archivos del proyecto (ver sección de Git)
# git clone ... o scp ...

# 10. Inicializar base de datos
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 11. Crear usuario admin
python scripts/create_admin.py

# 12. Probar aplicación
python run.py
```

### 🔧 Configuración Gunicorn + Systemd

```bash
# ============================================
# CONFIGURAR GUNICORN COMO SERVICIO
# ============================================

# 1. Crear archivo de servicio systemd
sudo nano /etc/systemd/system/climaguru.service

# Contenido:
# ============================================
[Unit]
Description=ClimaGuru Flask Backend
After=network.target

[Service]
User=climaguru
Group=climaguru
WorkingDirectory=/home/climaguru/climaguru-backend
Environment="PATH=/home/climaguru/climaguru-backend/venv/bin"
EnvironmentFile=/home/climaguru/climaguru-backend/.env
ExecStart=/home/climaguru/climaguru-backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
# ============================================

# 2. Recargar systemd y habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable climaguru
sudo systemctl start climaguru

# 3. Verificar estado
sudo systemctl status climaguru
sudo journalctl -u climaguru -f
```

### 🔧 Configuración Nginx (Reverse Proxy)

```bash
# ============================================
# CONFIGURAR NGINX COMO REVERSE PROXY
# ============================================

# 1. Crear configuración
sudo nano /etc/nginx/sites-available/climaguru

# Contenido:
# ============================================
server {
    listen 80;
    server_name tu-dominio-o-ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/climaguru/climaguru-backend/app/static;
        expires 30d;
    }
}
# ============================================

# 2. Habilitar sitio
sudo ln -s /etc/nginx/sites-available/climaguru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. CONFIGURACIÓN TAILSCALE VPN

### 📡 ¿Qué es Tailscale?

Tailscale crea una **red privada virtual (VPN)** mesh entre tus dispositivos usando el protocolo WireGuard. Te da IPs privadas estables (100.x.x.x) para conectar tus VMs de forma segura, como si estuvieran en la misma red local.

### 🔧 Instalación en Ambas VMs

```bash
# ============================================
# INSTALAR TAILSCALE EN CADA VM
# ============================================

# 1. Instalar Tailscale (Ubuntu/Debian)
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Iniciar Tailscale
sudo tailscale up

# 3. Autenticar (te dará un link para abrir en navegador)
# Abre el link y loguéate con tu cuenta de GitHub/Google/Microsoft

# 4. Verificar conexión
sudo tailscale status

# 5. Ver tu IP de Tailscale
sudo tailscale ip -4
# Devuelve algo como: 100.x.y.z
```

### 🔗 Conectar las VMs

```bash
# ============================================
# VERIFICAR CONECTIVIDAD ENTRE VMs
# ============================================

# En VM Flask (con IP de Tailscale 100.100.1.1)
# Probar conexión a MySQL VM (con IP 100.100.1.2)
ping 100.100.1.2

# Probar conexión a MySQL
telnet 100.100.1.2 3306

# O desde MySQL client
mysql -h 100.100.1.2 -u climaguru_user -p
```

### 🔒 ACLs de Tailscale (Opcional - Seguridad)

```json
// En https://login.tailscale.com/admin/acls
// Configurar para que solo la VM Flask pueda acceder a MySQL

{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:flask-backend"],
      "dst": ["tag:mysql-db:3306"]
    },
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["*:80", "*:443", "*:22"]
    }
  ],
  "tagOwners": {
    "tag:flask-backend": ["tu-usuario@github"],
    "tag:mysql-db": ["tu-usuario@github"]
  }
}
```

---

## 7. AUTENTICACIÓN GITHUB EN VM

### 🔑 Opción 1: SSH Key (Recomendado)

```bash
# ============================================
# CONFIGURAR SSH KEY PARA GITHUB
# ============================================

# 1. Generar nueva clave SSH (en la VM)
ssh-keygen -t ed25519 -C "tu-email@ejemplo.com"

# 2. Ver la clave pública
cat ~/.ssh/id_ed25519.pub

# 3. Copiar el contenido y agregarlo en GitHub:
#    GitHub → Settings → SSH and GPG keys → New SSH key

# 4. Probar conexión
ssh -T git@github.com
# Debe decir: "Hi username! You've successfully authenticated..."

# 5. Clonar repositorio
git clone git@github.com:xtatikmel/ClimaGuru.git
```

### 🔑 Opción 2: GitHub CLI (gh)

```bash
# ============================================
# USAR GITHUB CLI
# ============================================

# 1. Instalar GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# 2. Autenticar
gh auth login

# 3. Seguir el wizard:
#    - GitHub.com
#    - HTTPS
#    - Login with a web browser
#    - Copiar código y abrir navegador

# 4. Clonar repositorio
gh repo clone xtatikmel/ClimaGuru
```

### 🔑 Opción 3: Personal Access Token (PAT)

```bash
# ============================================
# USAR PERSONAL ACCESS TOKEN
# ============================================

# 1. Crear token en GitHub:
#    GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
#    → Generate new token
#    Scopes necesarios: repo

# 2. Clonar usando el token
git clone https://TU_TOKEN@github.com/xtatikmel/ClimaGuru.git

# 3. O configurar git para usar el token
git config --global credential.helper store
# Al hacer push/pull, ingresar username: tu-usuario, password: el token
```

### 👥 Colaboradores

```bash
# ============================================
# AGREGAR COLABORADORES AL REPOSITORIO
# ============================================

# Esto se hace desde GitHub web:
# 1. Ir al repositorio
# 2. Settings → Manage access → Invite a collaborator
# 3. Agregar username o email de GitHub de cada colaborador

# Cada colaborador debe:
# 1. Aceptar la invitación (llega por email)
# 2. Clonar el repo con su propia autenticación
# 3. Crear su propia rama: git checkout -b feature/nombre-feature
# 4. Hacer push y crear Pull Request
```

---

## 8. API ENDPOINTS DISPONIBLES

### 📋 Resumen de Endpoints

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Registrar nuevo usuario | No |
| POST | `/api/auth/login` | Iniciar sesión | No |
| POST | `/api/auth/refresh` | Refrescar token JWT | Refresh |
| POST | `/api/auth/logout` | Cerrar sesión | Sí |
| GET | `/api/auth/me` | Datos del usuario actual | Sí |
| POST | `/api/consultas/tiempo-real` | Consulta tiempo real | Sí |
| POST | `/api/consultas/historico` | Consulta histórica | Sí |
| GET | `/api/consultas/mis-consultas` | Listar consultas | Sí |
| GET | `/api/consultas/<id>` | Ver consulta | Sí |
| GET | `/api/consultas/<id>/descargar` | Descargar datos | Sí |
| GET | `/api/usuarios` | Listar usuarios (admin) | Admin |
| GET | `/api/reportes/estadisticas` | Estadísticas | Sí |

### 🧪 Ejemplos de Uso con curl

```bash
# ============================================
# EJEMPLOS DE USO DE LA API
# ============================================

# 1. Registrar usuario
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operario1",
    "email": "operario1@ejemplo.com",
    "password": "password123",
    "nombre_completo": "Operario Uno"
  }'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operario1",
    "password": "password123"
  }'
# Guardar el access_token que devuelve

# 3. Consulta tiempo real
curl -X POST http://localhost:5000/api/consultas/tiempo-real \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -d '{
    "ciudad": "Bogotá",
    "latitud": 4.6097,
    "longitud": -74.0817,
    "parametros": ["temperatura", "humedad", "viento"],
    "formato": "json"
  }'

# 4. Ver mis consultas
curl -X GET "http://localhost:5000/api/consultas/mis-consultas?page=1&per_page=10" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"

# 5. Descargar consulta en CSV
curl -X GET http://localhost:5000/api/consultas/1/descargar \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -o consulta_1.csv
```

---

## 9. PRÓXIMOS PASOS (FRONTEND)

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

## 📚 COMANDOS RÁPIDOS DE REFERENCIA

```bash
# ============================================
# COMANDOS ÚTILES - GUÍA RÁPIDA
# ============================================

# --- FLASK ---
flask run                          # Iniciar servidor de desarrollo
flask db init                      # Inicializar migraciones
flask db migrate -m "mensaje"      # Crear migración
flask db upgrade                   # Aplicar migraciones
flask db downgrade                 # Revertir última migración
flask shell                        # Shell interactivo con app context

# --- GUNICORN ---
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app    # 4 workers
gunicorn -w 4 -b 0.0.0.0:8000 --reload wsgi:app  # Con auto-reload

# --- SYSTEMD ---
sudo systemctl start climaguru     # Iniciar servicio
sudo systemctl stop climaguru      # Detener servicio
sudo systemctl restart climaguru   # Reiniciar servicio
sudo systemctl status climaguru    # Ver estado
sudo journalctl -u climaguru -f    # Ver logs en tiempo real

# --- MYSQL ---
sudo mysql -u root -p              # Login como root
mysql -h IP -u user -p             # Login remoto
SHOW DATABASES;                    # Listar bases de datos
USE climaguru; SHOW TABLES;        # Ver tablas

# --- TAILSCALE ---
sudo tailscale up                  # Iniciar Tailscale
sudo tailscale down                # Detener Tailscale
sudo tailscale status              # Ver estado
sudo tailscale ip -4               # Ver mi IP

# --- GIT ---
git clone git@github.com:xtatikmel/ClimaGuru.git
git status
git add .
git commit -m "mensaje"
git push origin main
git pull origin main
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Crear estructura de archivos del backend
- [ ] Instalar dependencias en entorno virtual
- [ ] Configurar archivo .env con credenciales
- [ ] Crear modelos SQLAlchemy
- [ ] Implementar blueprints de autenticación
- [ ] Implementar blueprints de consultas
- [ ] Probar localmente con Flask dev server
- [ ] Configurar VM MySQL e instalar MySQL Server
- [ ] Crear base de datos y usuario en MySQL
- [ ] Configurar VM Ubuntu Server para Flask
- [ ] Instalar Tailscale en ambas VMs
- [ ] Conectar VMs con Tailscale y verificar ping
- [ ] Configurar Gunicorn como servicio systemd
- [ ] Configurar Nginx como reverse proxy
- [ ] Clonar repositorio con autenticación SSH
- [ ] Ejecutar migraciones de base de datos
- [ ] Crear usuario administrador inicial
- [ ] Probar endpoints con curl/Postman
- [ ] Verificar logs y monitoreo

---

**¡Listo!** Con esta guía tienes todo lo necesario para implementar tu backend Flask con MySQL, desplegarlo en VMs y conectarlo mediante Tailscale VPN. Cualquier duda, revisa los logs con `journalctl` y `flask shell` para debugging.
