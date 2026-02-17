# Cálculo de estadísticas y promedios
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