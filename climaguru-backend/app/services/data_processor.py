# Procesamiento de datos (CSV, JSON, etc.)

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