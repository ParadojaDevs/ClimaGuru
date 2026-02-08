"""
Modelo: Consulta
================
Registra cada consulta meteorológica realizada
"""
from datetime import datetime
from app.extensions import db


class Consulta(db.Model):
    """Modelo de consulta meteorológica"""
    
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    tipo_consulta = db.Column(db.Enum('tiempo_real', 'historico', name='tipo_consulta_enum'),
                              nullable=False, index=True)
    ciudad = db.Column(db.String(100), index=True)
    latitud = db.Column(db.Numeric(10, 8), index=True)
    longitud = db.Column(db.Numeric(11, 8), index=True)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    formato_salida = db.Column(db.Enum('json', 'csv', 'txt', 'yaml', name='formato_enum'),
                               default='json')
    parametros_solicitados = db.Column(db.JSON)
    respuesta_api = db.Column(db.JSON)
    estado = db.Column(db.Enum('pendiente', 'procesando', 'completada', 'error', 
                               name='estado_enum'), 
                       default='pendiente', index=True)
    mensaje_error = db.Column(db.Text)
    tiempo_respuesta_ms = db.Column(db.Integer)
    ip_origen = db.Column(db.String(45))
    creada_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completada_en = db.Column(db.DateTime)
    
    # Relación con datos procesados
    datos_clima = db.relationship('DatosClima', backref='consulta', uselist=False,
                                  cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'tipo_consulta': self.tipo_consulta,
            'ciudad': self.ciudad,
            'latitud': float(self.latitud) if self.latitud else None,
            'longitud': float(self.longitud) if self.longitud else None,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'formato_salida': self.formato_salida,
            'parametros_solicitados': self.parametros_solicitados,
            'estado': self.estado,
            'mensaje_error': self.mensaje_error,
            'tiempo_respuesta_ms': self.tiempo_respuesta_ms,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None,
            'completada_en': self.completada_en.isoformat() if self.completada_en else None
        }
    
    def __repr__(self):
        return f'<Consulta {self.id} - {self.tipo_consulta} - {self.estado}>'
