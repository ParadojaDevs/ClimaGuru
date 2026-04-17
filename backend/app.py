"""
Run script for ClimaGuru Backend
================================
Punto de entrada para ejecutar el servidor Flask
"""
from app import create_app
from app.config import config
import os

# Cargar configuracion segun entorno
env = os.getenv('FLASK_ENV', 'development')
app_config = config[env]

# Crear aplicacion
app = create_app(env)

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"CLIMAGURU BACKEND")
    print(f"{'='*60}")
    print(f"Entorno: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Debug: {app_config.DEBUG}")
    print(f"Base de datos: {app_config.DB_NAME}")
    print(f"{'='*60}\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app_config.DEBUG
    )
