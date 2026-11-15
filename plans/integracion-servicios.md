# Guía de Integración de Servicios - ClimaGuru Backend

## 📋 Descripción General

Esta guía detalla cómo integrar los servicios del directorio `climaguru-backend/app/services/` con el sistema existente, utilizando:
- **app.py** como punto de entrada (en lugar de main.py)
- **Base de datos** para autenticación y almacenamiento de API keys
- **Data sources** existentes en `src/data_sources/` para conexión con APIs climáticas

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     Flask App (app.py)                         │
├─────────────────────────────────────────────────────────────────┤
│  Routes (auth.py, consultas.py, api_keys.py)                   │
│        │                    │                    │             │
│        ▼                    ▼                    ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │auth_service  │  │data_processor│  │stats_service │        │
│  │              │  │              │  │              │        │
│  │- login()     │  │- process_csv │  │- calc_avg()  │        │
│  │- register()  │  │- process_json│  │- calc_stats()│        │
│  │- validate()  │  │- transform()│  │- trends()    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────┐          │
│  │           weather_service (CONEXIÓN PRINCIPAL)   │          │
│  │  - get_weather()  - get_forecast()  - get_hist()│          │
│  └──────────────────────────────────────────────────┘          │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Data Sources (src/data_sources/)              │    │
│  │  open_meteo.py │ openweather.py │ meteoblue.py │ etc.  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Servicios Existentes (Data Sources)

### Ubicación y Propósito

| Archivo | Descripción | API Key Requerida |
|---------|-------------|-------------------|
| [`src/data_sources/open_meteo.py`](../../src/data_sources/open_meteo.py) | Pronósticos gratuitos | ❌ No (gratuito) |
| [`src/data_sources/openweather.py`](../../src/data_sources/openweather.py) | Clima actual, pronóstico 5 días, calidad del aire | ✅ Sí |
| [`src/data_sources/meteoblue.py`](../../src/data_sources/meteoblue.py) | Pronósticos detallados y meteogramas | ✅ Sí (key + secret) |
| [`src/data_sources/Meteosource.py`](../../src/data_sources/Meteosource.py) | Datos meteorológicos por place_id | ✅ Sí |
| [`src/data_sources/ideam_radar_downloader.py`](../../src/data_sources/ideam_radar_downloader.py) | Radares meteorológicos IDEAM | ❌ No |
| [`src/data_sources/siata_cliente.py`](../../src/data_sources/siata_cliente.py) | Datos históricos SIATA Medellín | ❌ No |

---

## 2. Modelos de Base de Datos

### Esquema de Relaciones

```
┌──────────────────┐       ┌──────────────────┐
│    Usuario       │       │    APIKey       │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │◄──────│ usuario_id (FK) │
│ username         │       │ id (PK)          │
│ email            │       │ servicio_nombre  │
│ password_hash    │       │ api_key (enc.)   │
│ rol              │       │ activa           │
└──────────────────┘       └──────────────────┘
         │                          │
         │              ┌────────────┴────────────┐
         │              │                         │
         ▼              ▼                         ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│     Sesion       │ │    Consulta       │ │  DatosClima      │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ id (PK)          │ │ id (PK)           │ │ id (PK)           │
│ usuario_id (FK) │ │ usuario_id (FK)   │ │ consulta_id (FK) │
│ token            │ │ tipo_consulta     │ │ temperatura       │
│ activa           │ │ ciudad            │ │ humedad           │
│ fecha_expiracion │ │ latitud/longitud  │ │ presion           │
└──────────────────┘ │ estado            │ │ viento            │
                    │ parametros        │ │ fuentes           │
                    └──────────────────┘ └──────────────────┘
```

---

## 3. Implementación de Servicios

### 3.1 auth_service.py - Autenticación y Autorización

**Ubicación:** `climaguru-backend/app/services/auth_service.py`

```python
"""
Servicio de Autenticación y Autorización
=========================================
Maneja login, registro, validación de tokens y permisos
"""
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models.usuario import Usuario
from app.models.sesion import Sesion
from app.models.logs_actividad import LogsActividad
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
import re


class AuthService:
    """Servicio de autenticación"""
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Validar formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    @staticmethod
    def validar_password(password: str) -> tuple:
        """
        Validar fortaleza de contraseña
        Returns: (es_valida, mensaje)
        """
        if len(password) < 8:
            return False, "Mínimo 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "Al menos una mayúscula"
        if not re.search(r'[a-z]', password):
            return False, "Al menos una minúscula"
        if not re.search(r'\d', password):
            return False, "Al menos un número"
        return True, "Válida"
    
    @staticmethod
    def registrar_usuario(username: str, email: str, password: str, 
                         nombre_completo: str = None) -> tuple:
        """
        Registrar nuevo usuario
        Returns: (usuario, error_message)
        """
        # Validaciones
        if len(username) < 3:
            return None, "Username debe tener al menos 3 caracteres"
        
        if not AuthService.validar_email(email):
            return None, "Email inválido"
        
        valida, mensaje = AuthService.validar_password(password)
        if not valida:
            return None, mensaje
        
        # Verificar existencia
        if Usuario.query.filter_by(username=username).first():
            return None, "Username ya registrado"
        
        if Usuario.query.filter_by(email=email.lower()).first():
            return None, "Email ya registrado"
        
        # Crear usuario
        usuario = Usuario(
            username=username,
            email=email.lower(),
            password=password,
            nombre_completo=nombre_completo
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        return usuario, None
    
    @staticmethod
    def iniciar_sesion(username_or_email: str, password: str) -> tuple:
        """
        Iniciar sesión
        Returns: (usuario, access_token, error)
        """
        usuario = Usuario.query.filter(
            (Usuario.username == username_or_email) |
            (Usuario.email == username_or_email.lower())
        ).first()
        
        if not usuario:
            return None, None, "Credenciales inválidas"
        
        if not usuario.activo:
            return None, None, "Usuario inactivo"
        
        if not usuario.check_password(password):
            return None, None, "Credenciales inválidas"
        
        # Actualizar último acceso
        usuario.actualizar_ultimo_acceso()
        
        # Generar tokens
        access_token = create_access_token(identity=usuario.id)
        refresh_token = create_refresh_token(identity=usuario.id)
        
        return usuario, access_token, None
    
    @staticmethod
    def cerrar_sesion(usuario_id: int, token_jti: str) -> bool:
        """Cerrar sesión del usuario"""
        sesion = Sesion.query.filter_by(
            token=token_jti, 
            usuario_id=usuario_id
        ).first()
        
        if sesion:
            sesion.activa = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def obtener_usuario_actual(usuario_id: int) -> Usuario:
        """Obtener usuario por ID"""
        return Usuario.query.get(usuario_id)


class AuthorizationService:
    """Servicio de autorización basado en roles"""
    
    # Definición de permisos por rol
    PERMISOS = {
        'admin': ['*'],  # Todos los permisos
        'operario': [
            'consulta:crear', 'consulta:leer', 'consulta:actualizar',
            'api_key:crear', 'api_key:leer', 'api_key:actualizar', 'api_key:eliminar',
            'usuario:leer', 'estadisticas:leer'
        ],
        'consultor': [
            'consulta:crear', 'consulta:leer',
            'api_key:crear', 'api_key:lear',
            'estadisticas:leer'
        ]
    }
    
    @staticmethod
    def tiene_permiso(rol: str, permiso: str) -> bool:
        """Verificar si un rol tiene un permiso específico"""
        permisos = AuthorizationService.PERMISOS.get(rol, [])
        return '*' in permisos or permiso in permisos
    
    @staticmethod
    def requiere_permiso(permiso: str):
        """Decorator para requerir permiso específico"""
        def decorator(f):
            @wraps(f)
            @jwt_required()
            def decorated_function(*args, **kwargs):
                usuario_id = get_jwt_identity()
                usuario = Usuario.query.get(usuario_id)
                
                if not usuario or not usuario.activo:
                    return {'error': 'Unauthorized'}, 403
                
                if not AuthorizationService.tiene_permiso(usuario.rol, permiso):
                    return {'error': 'Permiso denegado'}, 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
```

---

### 3.2 weather_service.py - Integración con APIs de Clima

**Ubicación:** `climaguru-backend/app/services/weather_service.py`

```python
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
```

---

### 3.3 data_processor.py - Procesamiento de Datos

**Ubicación:** `climaguru-backend/app/services/data_processor.py`

```python
"""
Procesador de Datos
===================
Manejo de formatos CSV, JSON, XML, transformación y validación
"""
import json
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml


class DataProcessor:
    """Procesador de datos climáticos"""
    
    # Mapeo de campos entre proveedores
    CAMPO_Estandar = {
        'temperatura': ['temperature_2m', 'temp', 'temperatura', 'temp_c'],
        'humedad': ['relative_humidity_2m', 'humidity', 'humedad_relativa', 'humidity_%'],
        'presion': ['pressure', 'presion_atmosferica', 'pressure_hpa'],
        'viento_velocidad': ['wind_speed_10m', 'viento_velocidad', 'wind_speed_kmh'],
        'viento_direccion': ['wind_deg', 'viento_direccion', 'wind_direction'],
        'precipitacion': ['precipitation', 'precipitacion', 'precip_mm'],
        'descripcion': ['weather_description', 'descripcion', 'description', 'weather_main']
    }
    
    @staticmethod
    def procesar_json(data: Dict, normalizar: bool = True) -> Dict[str, Any]:
        """
        Procesar datos JSON
        
        Args:
            data: Datos en formato JSON (dict)
            normalizar: Si True, normaliza nombres de campos
        
        Returns:
            Diccionario procesado
        """
        if not data:
            return {'error': 'Sin datos'}
        
        if normalizar:
            return DataProcessor._normalizar_campos(data)
        
        return data
    
    @staticmethod
    def procesar_csv(csv_data: str, delimiter: str = ',') -> List[Dict]:
        """
        Procesar datos CSV
        
        Args:
            csv_data: Contenido del CSV como string
            delimiter: Delimitador de campos
        
        Returns:
            Lista de diccionarios
        """
        try:
            reader = csv.DictReader(
                io.StringIO(csv_data),
                delimiter=delimiter
            )
            return list(reader)
        except Exception as e:
            return [{'error': str(e)}]
    
    @staticmethod
    def csv_desde_datos(datos: List[Dict], campos: List[str] = None) -> str:
        """
        Convertir datos a formato CSV
        
        Args:
            datos: Lista de diccionarios
            campos: Campos a incluir (opcional)
        
        Returns:
            String en formato CSV
        """
        if not datos:
            return ""
        
        output = io.StringIO()
        
        # Determinar campos
        if campos is None:
            campos = list(datos[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=campos)
        writer.writeheader()
        writer.writerows(datos)
        
        return output.getvalue()
    
    @staticmethod
    def json_desde_datos(datos: Dict, pretty: bool = True) -> str:
        """
        Convertir datos a JSON
        
        Args:
            datos: Diccionario
            pretty: Si True, formato legible
        
        Returns:
            String JSON
        """
        if pretty:
            return json.dumps(datos, indent=2, ensure_ascii=False, 
                           default=str)
        return json.dumps(datos, ensure_ascii=False, default=str)
    
    @staticmethod
    def yaml_desde_datos(datos: Dict) -> str:
        """
        Convertir datos a YAML
        
        Args:
            datos: Diccionario
        
        Returns:
            String YAML
        """
        try:
            return yaml.dump(datos, allow_unicode=True, default_flow_style=False)
        except ImportError:
            return "# PyYAML no está instalado"
    
    @staticmethod
    def texto_desde_datos(datos: Dict, plantilla: str = None) -> str:
        """
        Convertir datos a texto formateado
        
        Args:
            datos: Diccionario con datos
            plantilla: Plantilla personalizada (opcional)
        
        Returns:
            String formateado
        """
        if plantilla:
            return plantilla.format(**datos)
        
        # Plantilla por defecto
        temp = """
╔══════════════════════════════════════════════════════════╗
║              CLIMAGURU - DATOS CLIMÁTICOS                ║
╠══════════════════════════════════════════════════════════╣
║  Fecha/Hora: {timestamp}
║  Proveedor:  {proveedor}
╠══════════════════════════════════════════════════════════╣
║  TEMPERATURA                                            ║
║  ───────────────────────────────────────────────────────║
║  Actual:     {temperatura}°C
║  Mínima:     {temp_min}°C
║  Máxima:     {temp_max}°C
╠══════════════════════════════════════════════════════════╣
║  HUMEDAD:   {humedad}%                                     ║
║  PRESIÓN:   {presion} hPa                                 ║
║  VIENTO:    {viento} km/h                                 ║
╠══════════════════════════════════════════════════════════╣
║  Descripción: {descripcion}                              ║
╚══════════════════════════════════════════════════════════╝
"""
        
        current = datos.get('current', {})
        
        return temp.format(
            timestamp=datos.get('timestamp', datetime.now().isoformat()),
            proveedor=datos.get('proveedor', 'N/A'),
            temperatura=current.get('temperatura', 'N/A'),
            temp_min=current.get('temp_min', 'N/A'),
            temp_max=current.get('temp_max', 'N/A'),
            humedad=current.get('humedad', 'N/A'),
            presion=current.get('presion', 'N/A'),
            viento=current.get('viento', 'N/A'),
            descripcion=current.get('descripcion', 'N/A')
        )
    
    @staticmethod
    def _normalizar_campos(data: Dict) -> Dict:
        """
        Normalizar nombres de campos a estándar interno
        
        Args:
            data: Diccionario con datos originales
        
        Returns:
            Diccionario con campos normalizados
        """
        resultado = {}
        
        for campo_estandar, posibles_campos in DataProcessor.CAMPO_Estandar.items():
            valor_encontrado = None
            
            for campo in posibles_campos:
                if campo in data:
                    valor_encontrado = data[campo]
                    break
            
            if valor_encontrado is not None:
                resultado[campo_estandar] = valor_encontrado
        
        # Copiar otros campos
        for clave, valor in data.items():
            if clave not in [c for campos in DataProcessor.CAMPO_Estandar.values() 
                           for c in campos]:
                resultado[clave] = valor
        
        return resultado
    
    @staticmethod
    def transformar_formato(datos: Dict, formato_destino: str) -> Any:
        """
        Transformar datos a formato específico
        
        Args:
            datos: Diccionario con datos
            formato_destino: json, csv, yaml, txt
        
        Returns:
            Datos en el formato solicitado
        """
        convertidores = {
            'json': DataProcessor.json_desde_datos,
            'csv': lambda d: DataProcessor.csv_desde_datos([d]) if isinstance(d, dict) else '',
            'yaml': DataProcessor.yaml_desde_datos,
            'txt': DataProcessor.texto_desde_datos
        }
        
        convertidor = convertidores.get(formato_destino.lower())
        
        if convertidor:
            return convertidor(datos)
        
        return datos
    
    @staticmethod
    def validar_datos(datos: Dict, esquema: Dict) -> tuple:
        """
        Validar datos contra un esquema
        
        Args:
            datos: Datos a validar
            esquema: Esquema de validación
        
        Returns:
            (es_valido, errores)
        """
        errores = []
        
        for campo, reglas in esquema.items():
            valor = datos.get(campo)
            
            # Validar requerido
            if reglas.get('requerido') and valor is None:
                errores.append(f"Campo requerido: {campo}")
                continue
            
            if valor is None:
                continue
            
            # Validar tipo
            tipo_esperado = reglas.get('tipo')
            if tipo_esperado == 'number':
                try:
                    float(valor)
                except (ValueError, TypeError):
                    errores.append(f"Campo {campo} debe ser numérico")
            
            # Validar rango
            if 'min' in reglas and valor < reglas['min']:
                errores.append(f"Campo {campo} debe ser >= {reglas['min']}")
            
            if 'max' in reglas and valor > reglas['max']:
                errores.append(f"Campo {campo} debe ser <= {reglas['max']}")
        
        return (len(errores) == 0, errores)
```

---

### 3.4 stats_service.py - Cálculo de Estadísticas

**Ubicación:** `climaguru-backend/app/services/stats_service.py`

```python
"""
Servicio de Estadísticas
========================
Cálculo de estadísticas, promedios, tendencias y análisis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from app import db
from app.models.consulta import Consulta
from app.models.dato_meteorologico import DatosClima
from sqlalchemy import func


class StatsService:
    """Servicio de estadísticas climáticas"""
    
    @staticmethod
    def calcular_promedios(datos: List[Dict], campo: str) -> float:
        """
        Calcular promedio de un campo específico
        
        Args:
            datos: Lista de diccionarios con datos
            campo: Nombre del campo a promediar
        
        Returns:
            Promedio como float
        """
        valores = [d.get(campo) for d in datos if d.get(campo) is not None]
        
        if not valores:
            return 0.0
        
        return sum(valores) / len(valores)
    
    @staticmethod
    def calcular_estadisticas(datos: List[Dict]) -> Dict[str, Any]:
        """
        Calcular estadísticas completas de un conjunto de datos
        
        Args:
            datos: Lista de diccionarios con datos climáticos
        
        Returns:
            Diccionario con estadísticas
        """
        if not datos:
            return {}
        
        # Extraer campos numéricos
        campos_numericos = ['temperatura', 'humedad', 'presion', 
                          'viento_velocidad', 'precipitacion']
        
        estadisticas = {}
        
        for campo in campos_numericos:
            valores = [d.get(campo) for d in datos 
                      if d.get(campo) is not None]
            
            if valores:
                estadisticas[campo] = {
                    'promedio': sum(valores) / len(valores),
                    'min': min(valores),
                    'max': max(valores),
                    'count': len(valores)
                }
        
        return estadisticas
    
    @staticmethod
    def calcular_tendencias(datos: List[Dict], campo: str,
                           periodo: str = 'diaria') -> Dict[str, Any]:
        """
        Calcular tendencias de un campo a lo largo del tiempo
        
        Args:
            datos: Lista de diccionarios con datos y timestamps
            campo: Campo a analizar
            periodo: Periodo de análisis (diaria, semanal, mensual)
        
        Returns:
            Diccionario con tendencias
        """
        if not datos:
            return {}
        
        # Ordenar por fecha
        datos_ordenados = sorted(
            datos, 
            key=lambda x: x.get('timestamp', '')
        )
        
        valores = [d.get(campo) for d in datos_ordenados if d.get(campo)]
        
        if len(valores) < 2:
            return {'tendencia': 'insuficiente_datos'}
        
        # Calcular pendiente (tendencia)
        n = len(valores)
        sum_x = sum(range(n))
        sum_y = sum(valores)
        sum_xy = sum(i * v for i, v in enumerate(valores))
        sum_x2 = sum(i ** 2 for i in range(n))
        
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        tendencia = 'estable'
        if pendiente > 0.1:
            tendencia = 'ascendente'
        elif pendiente < -0.1:
            tendencia = 'descendente'
        
        return {
            'tendencia': tendencia,
            'pendiente': pendiente,
            'valor_inicial': valores[0],
            'valor_final': valores[-1],
            'variacion': valores[-1] - valores[0],
            'periodo': periodo
        }
    
    @staticmethod
    def obtener_estadisticas_usuario(usuario_id: int) -> Dict[str, Any]:
        """
        Obtener estadísticas de consultas de un usuario
        
        Args:
            usuario_id: ID del usuario
        
        Returns:
            Diccionario con estadísticas
        """
        # Total de consultas
        total_consultas = Consulta.query.filter_by(
            usuario_id=usuario_id
        ).count()
        
        # Consultas por tipo
        consultas_por_tipo = db.session.query(
            Consulta.tipo_consulta,
            func.count(Consulta.id)
        ).filter(Consulta.usuario_id == usuario_id).group_by(
            Consulta.tipo_consulta
        ).all()
        
        # Consultas por estado
        consultas_por_estado = db.session.query(
            Consulta.estado,
            func.count(Consulta.id)
        ).filter(Consulta.usuario_id == usuario_id).group_by(
            Consulta.estado
        ).all()
        
        # Ciudades más consultadas
        ciudades_top = db.session.query(
            Consulta.ciudad,
            func.count(Consulta.id)
        ).filter(
            Consulta.usuario_id == usuario_id,
            Consulta.ciudad.isnot(None)
        ).group_by(
            Consulta.ciudad
        ).order_by(
            func.count(Consulta.id).desc()
        ).limit(5).all()
        
        # Promedio de tiempo de respuesta
        tiempo_promedio = db.session.query(
            func.avg(Consulta.tiempo_respuesta_ms)
        ).filter(
            Consulta.usuario_id == usuario_id,
            Consulta.tiempo_respuesta_ms.isnot(None)
        ).scalar()
        
        return {
            'total_consultas': total_consultas,
            'por_tipo': {t: c for t, c in consultas_por_tipo},
            'por_estado': {e: c for e, c in consultas_por_estado},
            'ciudades_top': [{'ciudad': c, 'consultas': n} for c, n in ciudades_top],
            'tiempo_promedio_ms': float(tiempo_promedio) if tiempo_promedio else 0
        }
    
    @staticmethod
    def obtener_estadisticas_sistema() -> Dict[str, Any]:
        """
        Obtener estadísticas globales del sistema
        
        Returns:
            Diccionario con estadísticas globales
        """
        from app.models.usuario import Usuario
        from app.models.api_key import APIKey
        
        # Total de usuarios
        total_usuarios = Usuario.query.filter_by(activo=True).count()
        
        # Total de consultas
        total_consultas = Consulta.query.count()
        
        # Consultas últimas 24 horas
        hace_24h = datetime.utcnow() - timedelta(hours=24)
        consultas_hoy = Consulta.query.filter(
            Consulta.creada_en >= hace_24h
        ).count()
        
        # Proveedores más usados
        # (requiere almacenar proveedor en DatosClima)
        
        return {
            'total_usuarios': total_usuarios,
            'total_consultas': total_consultas,
            'consultas_ultimas_24h': consultas_hoy,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def analizar_calidad_datos(datos: List[Dict]) -> Dict[str, Any]:
        """
        Analizar calidad de datos recibidos
        
        Args:
            datos: Lista de diccionarios con datos
        
        Returns:
            Reporte de calidad
        """
        if not datos:
            return {'calidad': 'sin        total__datos'}
        
registros = len(datos)
        
        # Contar campos completos
        campos = ['temperatura', 'humedad', 'presion', 'viento']
        campos_completos = defaultdict(int)
        
        for dato in datos:
            for campo in campos:
                if dato.get(campo) is not None:
                    campos_completos[campo] += 1
        
        # Calcular porcentaje de completitud
        completitud = {
            campo: (count / total_registros) * 100 
            for campo, count in campos_completos.items()
        }
        
        # Determinar calidad general
        promedio_completitud = sum(completitud.values()) / len(completitud)
        
        if promedio_completitud >= 90:
            calidad = 'excelente'
        elif promedio_completitud >= 70:
            calidad = 'buena'
        elif promedio_completitud >= 50:
            calidad = 'regular'
        else:
            calidad = 'deficiente'
        
        return {
            'calidad': calidad,
            'completitud_promedio': promedio_completitud,
            'por_campo': completitud,
            'total_registros': total_registros
        }
```

---

## 4. Integración con Rutas Existentes

### 4.1 Modificar consultas.py

Para usar los nuevos servicios, modifica [`climaguru-backend/app/routes/consultas.py`](../../climaguru-backend/app/routes/consultas.py):

```python
# Agregar imports
from app.services.weather_service import WeatherService, ConsultaManager
from app.services.data_processor import DataProcessor

# En el endpoint de tiempo real:
@consultas_bp.route('/tiempo-real', methods=['POST'])
@jwt_required()
def consulta_tiempo_real():
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    # ... validaciones existentes ...
    
    # Iniciar servicio de clima
    weather_service = WeatherService(usuario_id)
    
    # Realizar consulta
    lat = data.get('latitud')
    lon = data.get('longitud')
    ciudad = data.get('ciudad')
    proveedor = data.get('proveedor', 'openmeteo')
    
    # Crear registro en BD
    consulta = ConsultaManager.crear_consulta(
        usuario_id=usuario_id,
        tipo='tiempo_real',
        lat=lat,
        lon=lon,
        ciudad=ciudad,
        parametros=data.get('parametros')
    )
    
    # Obtener datos del proveedor
    datos = weather_service.consultar_tiempo_real(
        lat=lat, lon=lon, ciudad=ciudad, proveedor=proveedor
    )
    
    if 'error' in datos:
        ConsultaManager.completar_consulta(
            consulta.id, 
            estado='error', 
            error=datos['error']
        )
        return jsonify({'error': datos['error']}), 500
    
    # Guardar datos
    datos_clima = ConsultaManager.guardar_datos_clima(
        consulta.id, datos, proveedor
    )
    
    # Completar consulta
    ConsultaManager.completar_consulta(consulta.id, estado='completada')
    
    # Transformar al formato solicitado
    formato = data.get('formato', 'json')
    respuesta = DataProcessor.transformar_formato(
        datos, formato
    )
    
    return jsonify({
        'consulta': consulta.to_dict(),
        'datos': datos_clima.to_dict()
    }), 200
```

---

## 5. Flujo de Ejecución

### 5.1 Iniciar la aplicación

```bash
# Desde climaguru-backend/
cd climaguru-backend

# Ejecutar con Python
python app.py

# O con Flask CLI
export FLASK_APP=app.py
flask run
```

### 5.2 Flujo de una consulta típica

```
1. Usuario envía POST /api/consultas/tiempo-real
   └─> Headers: Authorization: Bearer {token_jwt}
   └─> Body: {"ciudad": "Medellín", "formato": "json"}

2. Route (consultas.py) valida token JWT
   └─> @jwt_required() extrae usuario_id

3. auth_service verifica permisos
   └─> AuthorizationService.tiene_permiso(rol, 'consulta:crear')

4. weather_service inicializa clientes
   └─> Carga API keys del usuario desde BD
   └─> Instancia clientes de src/data_sources/

5. weather_service consulta proveedor
   └─> open_meteo.get_forecast(lat, lon)
   └─> Respuesta procesada a formato estándar

6. data_processor transforma respuesta
   └─> _normalizar_campos()
   └─> transformar_formato('json')

7. consulta_manager guarda en BD
   └─> Crea Consulta en tabla 'consultas'
   └─> Crea DatosClima en tabla 'datos_clima'

8. Respuesta al cliente
   └─> JSON con datos de consulta y clima
```

---

## 6. Proveedores Soportados

| Proveedor | Endpoint Principal | Variables Principales | API Key |
|-----------|-------------------|----------------------|---------|
| **Open-Meteo** | `api.open-meteo.com/v1/forecast` | temp, humidity, wind | ❌ No |
| **OpenWeatherMap** | `api.openweathermap.org/data/2.5/weather` | temp, pressure, humidity | ✅ Requerida |
| **Meteoblue** | `api.meteoblue.com/packages/3d` | temp, precipitation, meteogram | ✅ Key + Secret |
| **Meteosource** | `api.meteosource.com/v1/` | temp, humidity, conditions | ✅ Requerida |

---

## 7. Manejo de Errores

### Códigos de Error

```python
ERRORES = {
    'AUTH_001': 'Token de autenticación inválido',
    'AUTH_002': 'Usuario inactivo o eliminado',
    'AUTH_003': 'Permisos insuficientes',
    'WEATHER_001': 'Proveedor no disponible',
    'WEATHER_002': 'API key inválida o expirada',
    'WEATHER_003': 'Límite de consultas alcanzado',
    'WEATHER_004': 'Coordenadas inválidas',
    'DB_001': 'Error al guardar en base de datos',
    'PROC_001': 'Error al procesar datos'
}
```

---

## 8. Configuración de Variables de Entorno

Crea archivo `.env` en `climaguru-backend/`:

```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=climaguru
DB_USER=usuario
DB_PASSWORD=contraseña

# JWT
SECRET_KEY=tu_secret_key_aqui
JWT_SECRET_KEY=tu_jwt_secret_aqui
JWT_ACCESS_TOKEN_EXPIRES=3600

# Encriptación
ENCRYPTION_KEY=tu_key_de_encriptacion

# APIs externas (para uso global, no requerido)
# METEOBLUE_API_KEY=
# METEOBLUE_SHARED_SECRET=
# OPENWEATHER_API_KEY=
# METEOSOURCE_API_KEY=

# Configuración Flask
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## 9. Próximos Pasos

1. **Completar servicios vacíos** - Implementar el código de esta guía en los archivos de servicios
2. **Integrar con rutas** - Modificar `consultas.py` para usar los servicios
3. **Probar endpoints** - Verificar que las consultas funcionen correctamente
4. **Agregar más proveedores** - Implementar soporte para IDEAM, SIATA
5. **Optimizar caché** - Agregar cacheo de respuestas para reducir latencia
6. **Métricas** - Dashboard de uso por usuario y proveedor

---

## 10. Referencias

- [main.py - Gestor CLI original](../../main.py)
- [app.py - Punto de entrada Flask](../../climaguru-backend/app.py)
- [Modelos de BD](../../climaguru-backend/app/models/)
- [Data Sources](../../src/data_sources/)
- [Documentación API](../../climaguru-backend/docs/API.md)
