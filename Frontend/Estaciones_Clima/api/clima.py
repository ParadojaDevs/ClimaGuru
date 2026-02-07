import sys
import os
from flask_restful import Resource
from models import Estacion

# Asegurar que el directorio raíz del proyecto (donde está main.py) esté en el path
# Desde /Frontend/Estaciones_Clima/api/clima.py, necesitamos subir 3 niveles: api -> Estaciones_Clima -> Frontend -> ClimaGuru
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class ClimaEstacion(Resource):
    # GET /api/clima/<id>
    def get(self, id):
        # 1. Obtener la estación de la base de datos
        estacion = Estacion.query.get_or_404(id)
        
        # 2. Importar el manager de manera lazy (solo cuando se necesite)
        # Esto evita cargar los módulos pesados de radar al iniciar la app
        try:
            import main
            manager = main.ClimAPIManager()
            
            # 3. Consultar datos
            # Usamos consultar_openmeteo primero ya que es gratuito y no requiere API key
            datos_clima = manager.consultar_openmeteo(
                lat=estacion.latitud,
                lon=estacion.longitud,
                location_name=estacion.nombre
            )
            
            if datos_clima:
                return datos_clima, 200
            
            # Si falla OpenMeteo, intentamos OpenWeather como fallback
            datos_fallback = manager.consultar_openweather(
                lat=estacion.latitud,
                lon=estacion.longitud,
                location_name=estacion.nombre
            )
            if datos_fallback:
                return datos_fallback, 200
                
            return {"message": "No se pudieron obtener datos del clima de ninguna fuente"}, 503
            
        except ImportError as e:
            return {"message": f"Error importando módulo de clima: {str(e)}"}, 500
        except Exception as e:
            return {"message": f"Error consultando clima: {str(e)}"}, 500

from . import api
api.add_resource(ClimaEstacion, "/clima/<int:id>", endpoint="clima_estacion")
