# Modelos de base de datos (SQLAlchemy)
# Importar en orden para evitar dependencias circulares

# Primero importar los modelos base
from app.models.usuario import Usuario

# Luego importar los modelos que dependen de usuario
from app.models.sesion import Sesion
from app.models.api_key import APIKey
from app.models.consulta import Consulta
from app.models.dato_meteorologico import DatosClima
from app.models.logs_actividad import LogsActividad
from app.models.ciudades_favoritas import CiudadesFavoritas

# Exportar todos los modelos
__all__ = [
    'Usuario',
    'Sesion',
    'APIKey', 
    'Consulta',
    'DatosClima',
    'LogsActividad',
    'CiudadesFavoritas'
]
