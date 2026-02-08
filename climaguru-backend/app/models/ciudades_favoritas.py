"""
Modelo: CiudadesFavoritas
=========================
Ciudades guardadas por cada usuario
"""
from datetime import datetime
from app.extensions import db


class CiudadesFavoritas(db.Model):
    """Modelo para ciudades favorites de usuarios"""
    
    __tablename__ = 'ciudades_favoritas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    nombre_ciudad = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(50))
    latitud = db.Column(db.Numeric(10, 8), nullable=False)
    longitud = db.Column(db.Numeric(11, 8), nullable=False)
    es_default = db.Column(db.Boolean, default=False)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacion con usuario
    usuario = db.relationship('Usuario', backref='ciudades_favoritas')
    
    # Constraint unica
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'latitud', 'longitud', 
                          name='unique_ciudad_usuario'),
    )
    
    def __init__(self, usuario_id, nombre_ciudad, latitud, longitud, pais=None, es_default=False):
        self.usuario_id = usuario_id
        self.nombre_ciudad = nombre_ciudad
        self.pais = pais
        self.latitud = latitud
        self.longitud = longitud
        self.es_default = es_default
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nombre_ciudad': self.nombre_ciudad,
            'pais': self.pais,
            'latitud': float(self.latitud) if self.latitud else None,
            'longitud': float(self.longitud) if self.longitud else None,
            'es_default': self.es_default,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None
        }
    
    def __repr__(self):
        return f'<CiudadesFavoritas {self.nombre_ciudad} - Usuario {self.usuario_id}>'
