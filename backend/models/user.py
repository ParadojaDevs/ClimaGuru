from datetime import datetime
import bcrypt
from flask import current_app

from database import db


class User(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    activo = db.Column(db.Boolean, default=True)

    def set_password(self, password: str) -> None:
        # Use bcrypt with default rounds (12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "nombre_completo": self.nombre_completo,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "ultimo_acceso": self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            "activo": self.activo,
        }