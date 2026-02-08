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
