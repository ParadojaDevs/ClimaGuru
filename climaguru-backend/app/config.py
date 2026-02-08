# Configuraciones (dev, prod, test)
"""
Configuración de la aplicación Flask para ClimaGuru
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # Configuración general
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')

    # Configuración de la base de datos
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'climaguru')
    DB_USER = os.getenv('DB_USER', 'user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

    # Construir URL de base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Cambiar a True para ver queries SQL en desarrollo
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    )
        # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Encriptación
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', SECRET_KEY)
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/climaguru.log')


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False
    
    # En producción, asegurar que las claves sean diferentes
    if Config.SECRET_KEY == 'clave-por-defecto-cambiar-en-produccion':
        raise ValueError("Debes establecer SECRET_KEY en producción")


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    DEBUG = True
    # Usar base de datos de prueba
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtener configuración según entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])

