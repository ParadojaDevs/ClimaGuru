"""
Modelo de Usuario para ClimaGuru
"""
from app import db
from datetime import datetime
import bcrypt


class Usuario(db.Model):
    """Modelo de Usuario/Operario"""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(100))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    activo = db.Column(db.Boolean, default=True)
    rol = db.Column(db.Enum('admin', 'operario', 'consultor', name='rol_enum'), default='consultor')
    ultimo_login = db.Column(db.DateTime)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    api_keys = db.relationship('APIKey', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    consultas = db.relationship('Consulta', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    datos_meteorologicos = db.relationship('DatoMeteorologico', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    sesiones = db.relationship('Sesion', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    logs_actividad = db.relationship('LogsActividad', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, nombre_completo=None):
        """
        Inicializar usuario
        
        Args:
            username: Nombre de usuario único
            email: Email único
            password: Contraseña en texto plano (se encriptará)
            nombre_completo: Nombre completo del usuario (opcional)
        """
        self.username = username
        self.email = email
        self.set_password(password)
        self.nombre_completo = nombre_completo
    
    def set_password(self, password):
        """
        Encriptar y establecer contraseña
        
        Args:
            password: Contraseña en texto plano
        """
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        """
        Verificar contraseña
        
        Args:
            password: Contraseña en texto plano a verificar
        
        Returns:
            bool: True si la contraseña es correcta
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def actualizar_ultimo_acceso(self):
        """Actualizar timestamp de último acceso"""
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_stats=False):
        """
        Convertir usuario a diccionario
        
        Args:
            include_stats: Incluir estadísticas de uso
        
        Returns:
            dict: Representación del usuario
        """
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'activo': self.activo
        }
        
        if include_stats:
            data['estadisticas'] = {
                'total_consultas': self.consultas.count(),
                'total_datos': self.datos_meteorologicos.count(),
                'api_keys_registradas': self.api_keys.filter_by(activa=True).count()
            }
        
        return data
    
    def __repr__(self):
        return f'<Usuario {self.username}>'