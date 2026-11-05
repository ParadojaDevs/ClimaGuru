"""
Modelo: WeatherObservation
==========================
Observaciones meteorologicas normalizadas para multiples fuentes de datos.

Almacena datos procesados de fuentes de ingesta (IDEAM radar, SAB lluvias)
de forma normalizada, independiente de las consultas de API realizadas por usuarios.
"""
from app import db
from datetime import datetime


class WeatherObservation(db.Model):
    """
    Modelo para observaciones meteorologicas normalizadas.

    Permite consolidar datos de diferentes fuentes (ideam_radar, sab_lluvias)
    con estructura flexible mediante metadatos JSON.
    """

    __tablename__ = 'weather_observations'

    id = db.Column(db.Integer, primary_key=True)

    # Identificacion de fuente
    fuente = db.Column(
        db.Enum('ideam_radar', 'sab_lluvias', name='fuente_observacion_enum'),
        nullable=False,
        index=True
    )

    # Identificacion de estacion/ubicacion
    estacion = db.Column(db.String(100))
    ciudad = db.Column(db.String(100), index=True)

    # Coordenadas geograficas
    latitud = db.Column(db.Numeric(10, 8), index=True)
    longitud = db.Column(db.Numeric(11, 8), index=True)

    # Tiempo de observacion
    timestamp_observacion = db.Column(db.DateTime, nullable=False, index=True)

    # Tipo y valor de dato
    tipo_dato = db.Column(db.String(50), nullable=False, index=True)
    valor = db.Column(db.Numeric(12, 4))
    unidad = db.Column(db.String(20))

    # Calidad y estado
    calidad = db.Column(db.String(20), default='unknown')

    # Metadatos flexibles
    metadatos = db.Column(db.JSON)
    datos_crudos = db.Column(db.JSON)

    # Control de registro
    procesado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    actualizado_en = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Convertir a diccionario."""
        return {
            'id': self.id,
            'fuente': self.fuente,
            'estacion': self.estacion,
            'ciudad': self.ciudad,
            'latitud': float(self.latitud) if self.latitud else None,
            'longitud': float(self.longitud) if self.longitud else None,
            'timestamp_observacion': self.timestamp_observacion.isoformat()
            if self.timestamp_observacion else None,
            'tipo_dato': self.tipo_dato,
            'valor': float(self.valor) if self.valor else None,
            'unidad': self.unidad,
            'calidad': self.calidad,
            'metadatos': self.metadatos,
            'procesado_en': self.procesado_en.isoformat()
            if self.procesado_en else None,
            'actualizado_en': self.actualizado_en.isoformat()
            if self.actualizado_en else None
        }

    def __repr__(self):
        return (
            f"<WeatherObservation {self.fuente} - {self.tipo_dato} "
            f"@ {self.timestamp_observacion}>"
        )
