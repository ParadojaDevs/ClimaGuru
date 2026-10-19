# Rutas de la API
from flask import Blueprint

# Importar blueprints
from app.routes.auth import auth_bp
from app.routes.usuarios import usuarios_bp
from app.routes.api_keys import api_keys_bp
from app.routes.consultas import consultas_bp
from app.routes.datos import datos_bp
from app.routes.ingestion import ingestion_bp

__all__ = [
    'auth_bp',
    'usuarios_bp',
    'api_keys_bp',
    'consultas_bp',
    'datos_bp',
    'ingestion_bp'
]
