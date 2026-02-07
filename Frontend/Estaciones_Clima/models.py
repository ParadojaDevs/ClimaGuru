from extensions import db

class Estacion(db.Model):
    __tablename__ = 'estaciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255), nullable=False)
    
    # Campos para la fecha
    dia = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    
    # Coordenadas (Usamos Float para permitir decimales)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    
    def __repr__(self) -> str:
        return f'<Estacion {self.id} - {self.nombre}>'