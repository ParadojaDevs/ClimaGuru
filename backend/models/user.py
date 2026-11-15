from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
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
        method = current_app.config.get("PWD_HASH_METHOD", "bcrypt")
        self.password_hash = generate_password_hash(password, method=method)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

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
