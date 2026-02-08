"""
Modelo: LogsActividad
=====================
Registro de actividad de usuarios para auditoría
"""
from datetime import datetime
from app.extensions import db


class LogsActividad(db.Model):
    """Modelo para logs de actividad de usuarios"""
    
    __tablename__ = 'logs_actividad'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    accion = db.Column(db.String(50), nullable=False, index=True)
    detalle = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __init__(self, usuario_id=None, accion=None, detalle=None, ip_address=None, user_agent=None):
        self.usuario_id = usuario_id
        self.accion = accion
        self.detalle = detalle
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'accion': self.accion,
            'detalle': self.detalle,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }
    
    def __repr__(self):
        return f'<LogsActividad {self.accion} - Usuario {self.usuario_id}>'
