# Integración con APIs de clima
"""
Servicio de Clima
=================
Integración con APIs climáticas externas
Maneja consultas a múltiples proveedores meteorológicos
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app import db
from app.models.api_key import APIKey
from app.models.consulta import Consulta
from app.models.dato_meteorologico import DatosClima


class WeatherService:
    """Servicio principal para consultas meteorológicas"""
    
    # Proveedores disponibles
    PROVEEDORES = {
        'openweather': {
            'nombre': 'OpenWeatherMap',
            'requiere_key': True,
            'requiere_secret': False,
            'clase': 'OpenWeatherMapClient'
        },
        'openmeteo': {
            'nombre': 'Open-Meteo',
            'requiere_key': False,
            'requiere_secret': False,
            'clase': 'OpenMeteoClient',
            'gratuito': True
        },
        'meteoblue': {
            'nombre': 'Meteoblue',
            'requiere_key': True,
            'requiere_secret': True,
            'clase': 'MeteoblueClient'
        },
        'meteosource': {
            'nombre': 'Meteosource',
            'requiere_key': True,
            'requiere_secret': False,
            'clase': 'MeteosourceAPI'
        }
    }
    
    def __init__(self, usuario_id: int):
        """
        Inicializar servicio para un usuario específico
        
        Args:
            usuario_id: ID del usuario que realiza la consulta
        """
        self.usuario_id = usuario_id
        self._clientes = {}
        self._inicializar_clientes()
    
    def _inicializar_clientes(self):
        """Inicializar clientes según las API keys del usuario"""
        # Obtener API keys activas del usuario
        api_keys = APIKey.query.filter_by(
            usuario_id=self.usuario_id, 
            activa=True
        ).all()
        
        # Importar clientes desde src/data_sources
        from src.data_sources.open_meteo import OpenMeteoClient
        from src.data_sources.openweather import OpenWeatherMapClient
        from src.data_sources.meteoblue import MeteoblueClient
        from src.data_sources.Meteosource import MeteosourceAPI
        
        # Inicializar Open-Meteo (siempre gratuito)
        try:
            self._clientes['openmeteo'] = OpenMeteoClient()
        except Exception as e:
            print(f"Error inicializando Open-Meteo: {e}")
        
        # Inicializar otros proveedores según API keys
        for api_key in api_keys:
            try:
                if api_key.servicio_nombre == 'openweather':
                    key = api_key.get_api_key()
                    self._clientes['openweather'] = OpenWeatherMapClient(key)
                
                elif api_key.servicio_nombre == 'meteoblue':
                    # Meteoblue requiere key y secret
                    # El secret se guarda en un campo adicional o se maneja por separado
                    key = api_key.get_api_key()
                    # Nota: Se necesitaría almacenar el secret también
                    self._clientes['meteoblue'] = MeteoblueClient(key, '')
                
                elif api_key.servicio_nombre == 'meteosource':
                    key = api_key.get_api_key()
                    self._clientes['meteosource'] = MeteosourceAPI(key)
                    
            except Exception as e:
                print(f"Error inicializando {api_key.servicio_nombre}: {e}")
    
    def consultar_tiempo_real(self, lat: float, lon: float, 
                             ciudad: str = None,
                             proveedor: str = 'openmeteo') -> Dict[str, Any]:
        """
        Consultar clima en tiempo real
        
        Args:
            lat: Latitud
            lon: Longitud
            ciudad: Nombre de la ciudad (opcional)
            proveedor: Proveedor a usar (default: openmeteo)
        
        Returns:
            Diccionario con datos del clima
        """
        if proveedor not in self._clientes:
            # Usar proveedor alternativo disponible
            proveedor = self._obtener_proveedor_disponible() or 'openmeteo'
        
        cliente = self._clientes.get(proveedor)
        
        if not cliente:
            return {'error': 'No hay proveedores disponibles'}
        
        try:
            if proveedor == 'openmeteo':
                datos = cliente.get_forecast(lat, lon, ciudad or 'location')
                return self._procesar_openmeteo(datos)
            
            elif proveedor == 'openweather':
                current = cliente.get_current_weather(lat, lon, ciudad or 'location')
                return self._procesar_openweather_current(current)
            
            elif proveedor == 'meteosource':
                # Meteosource usa place_id
                place_id = self._obtener_place_id(ciudad, lat, lon)
                datos = cliente.get_all_data(place_id)
                return self._procesar_meteosource(datos)
            
            else:
                return {'error': f'Proveedor {proveedor} no implementado'}
                
        except Exception as e:
            return {'error': f'Error en consulta: {str(e)}'}
    
    def consultar_pronostico(self, lat: float, lon: float,
                            dias: int = 7,
                            proveedor: str = 'openmeteo') -> Dict[str, Any]:
        """
        Consultar pronóstico de varios días
        """
        if proveedor not in self._clientes:
            proveedor = self._obtener_proveedor_disponible() or 'openmeteo'
        
        cliente = self._clientes.get(proveedor)
        
        if not cliente:
            return {'error': 'No hay proveedores disponibles'}
        
        try:
            if proveedor == 'openmeteo':
                datos = cliente.get_forecast(lat, lon, days=dias)
                return self._procesar_openmeteo_forecast(datos)
            
            elif proveedor == 'openweather':
                datos = cliente.get_forecast_5day(lat, lon)
                return self._procesar_openweather_forecast(datos)
                
        except Exception as e:
            return {'error': f'Error en pronóstico: {str(e)}'}
    
    def consultar_historico(self, lat: float, lon: float,
                           fecha_inicio: str, fecha_fin: str,
                           proveedor: str = 'openmeteo') -> Dict[str, Any]:
        """
        Consultar datos históricos
        Formato fechas: YYYY-MM-DD
        """
        cliente = self._clientes.get(proveedor)
        
        if not cliente:
            return {'error': 'Proveedor no disponible'}
        
        try:
            if proveedor == 'openmeteo':
                datos = cliente.get_historical(lat, lon, fecha_inicio, fecha_fin)
                return self._procesar_openmeteo_historical(datos)
            else:
                return {'error': f'Historico no disponible para {proveedor}'}
                
        except Exception as e:
            return {'error': f'Error en histórico: {str(e)}'}
    
    def _obtener_proveedor_disponible(self) -> Optional[str]:
        """Obtener el primer proveedor disponible"""
        return next((k for k in self._clientes.keys()), None)
    
    def _obtener_place_id(self, ciudad: str, lat: float, lon: float) -> str:
        """Convertir ciudad/coordenadas a place_id para Meteosource"""
        if ciudad:
            return ciudad.lower().replace(' ', '_')
        return f"{lat}_{lon}"
    
    # === Procesadores de respuesta ===
    
    def _procesar_openmeteo(self, datos) -> Dict[str, Any]:
        """Procesar respuesta de Open-Meteo"""
        if not datos:
            return {'error': 'Sin datos'}
        
        # Estructura estándar de respuesta
        return {
            'proveedor': 'open-meteo',
            'timestamp': datetime.utcnow().isoformat(),
            'ubicacion': datos.get('location', {}),
            'current': {
                'temperatura': datos.get('current', {}).get('temperature_2m'),
                'humedad': datos.get('current', {}).get('relative_humidity_2m'),
                'viento': datos.get('current', {}).get('wind_speed_10m')
            },
            'datos': datos
        }
    
    def _procesar_openweather_current(self, datos) -> Dict[str, Any]:
        """Procesar respuesta de OpenWeatherMap actual"""
        if not datos:
            return {'error': 'Sin datos'}
        
        return {
            'proveedor': 'openweathermap',
            'timestamp': datetime.utcnow().isoformat(),
            'current': {
                'temperatura': datos.get('main', {}).get('temp'),
                'humedad': datos.get('main', {}).get('humidity'),
                'presion': datos.get('main', {}).get('pressure'),
                'descripcion': datos.get('weather', [{}])[0].get('description'),
                'viento_velocidad': datos.get('wind', {}).get('speed'),
                'viento_direccion': datos.get('wind', {}).get('deg')
            },
            'datos': datos
        }
    
    def _procesar_openmeteo_forecast(self, datos) -> Dict[str, Any]:
        """Procesar pronóstico de Open-Meteo"""
        return {
            'proveedor': 'open-meteo',
            'tipo': 'forecast',
            'datos': datos
        }
    
    def _procesar_openweather_forecast(self, datos) -> Dict[str, Any]:
        """Procesar pronóstico de OpenWeatherMap"""
        return {
            'proveedor': 'openweathermap',
            'tipo': 'forecast',
            'datos': datos
        }
    
    def _procesar_openmeteo_historical(self, datos) -> Dict[str, Any]:
        """Procesar datos históricos de Open-Meteo"""
        return {
            'proveedor': 'open-meteo',
            'tipo': 'historical',
            'datos': datos
        }
    
    def _procesar_meteosource(self, datos) -> Dict[str, Any]:
        """Procesar respuesta de Meteosource"""
        return {
            'proveedor': 'meteosource',
            'datos': datos
        }


class ConsultaManager:
    """Gestor de consultas con persistencia en BD"""
    
    @staticmethod
    def crear_consulta(usuario_id: int, tipo: str, lat: float, lon: float,
                      ciudad: str = None, parametros: dict = None) -> Consulta:
        """Crear registro de consulta en la base de datos"""
        consulta = Consulta(
            usuario_id=usuario_id,
            tipo_consulta=tipo,
            ciudad=ciudad,
            latitud=lat,
            longitud=lon,
            parametros_solicitados=parametros or {},
            estado='procesando'
        )
        
        db.session.add(consulta)
        db.session.commit()
        
        return consulta
    
    @staticmethod
    def guardar_datos_clima(consulta_id: int, datos: dict, 
                           proveedor: str) -> DatosClima:
        """Guardar datos meteorológicos de una consulta"""
        # Extraer datos principales
        temp = datos.get('current', {}) or datos.get('datos', {}).get('current', {})
        
        datos_clima = DatosClima(
            consulta_id=consulta_id,
            temperatura_promedio=temp.get('temperatura') or temp.get('temperature_2m'),
            humedad_relativa=temp.get('humedad') or temp.get('relative_humidity_2m'),
            presion_atmosferica=temp.get('presion') or temp.get('pressure'),
            velocidad_viento=temp.get('viento_velocidad') or temp.get('viento') or 
                            temp.get('wind_speed_10m'),
            descripcion_clima=temp.get('descripcion'),
            fuentes_utilizadas=[proveedor],
            datos_completos=datos
        )
        
        db.session.add(datos_clima)
        db.session.commit()
        
        return datos_clima
    
    @staticmethod
    def completar_consulta(consulta_id: int, estado: str = 'completada',
                          error: str = None, tiempo_ms: int = None):
        """Marcar consulta como completada o con error"""
        consulta = Consulta.query.get(consulta_id)
        
        if consulta:
            consulta.estado = estado
            consulta.completada_en = datetime.utcnow()
            
            if tiempo_ms:
                consulta.tiempo_respuesta_ms = tiempo_ms
            
            if error:
                consulta.mensaje_error = error
            
            db.session.commit()