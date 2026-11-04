"""
Modelo de API Keys para ClimaGuru
"""
from app import db
from datetime import datetime
from cryptography.fernet import Fernet
import os


class APIKey(db.Model):
    """Modelo para almacenar API Keys de servicios meteorológicos"""
    
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    servicio_nombre = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)  # Se guarda encriptada
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)
    
    # Índice único compuesto
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'servicio_nombre', name='unique_user_service'),
    )
    
    def __init__(self, usuario_id, servicio_nombre, api_key_texto):
        """
        Inicializar API Key
        
        Args:
            usuario_id: ID del usuario propietario
            servicio_nombre: Nombre del servicio (ej: 'OpenWeatherMap', 'WeatherAPI')
            api_key_texto: API key en texto plano (se encriptará automáticamente)
        """
        self.usuario_id = usuario_id
        self.servicio_nombre = servicio_nombre
        self.set_api_key(api_key_texto)
    
    def set_api_key(self, api_key_texto):
        """
        Encriptar y guardar API key
        
        Args:
            api_key_texto: API key en texto plano
        """
        cipher = self._get_cipher()
        self.api_key = cipher.encrypt(api_key_texto.encode()).decode()
        self.fecha_actualizacion = datetime.utcnow()
    
    def get_api_key(self):
        """
        Desencriptar y obtener API key
        
        Returns:
            str: API key en texto plano
        """
        cipher = self._get_cipher()
        return cipher.decrypt(self.api_key.encode()).decode()
    
    @staticmethod
    def _get_cipher():
        """
        Obtener objeto cipher para encriptación
        
        Returns:
            Fernet: Objeto para encriptar/desencriptar
        """
        # Obtener clave de encriptación desde variables de entorno
        encryption_key = os.getenv('ENCRYPTION_KEY', '').encode()
        
        # Si no hay clave o es muy corta, usar una por defecto (NO SEGURO EN PRODUCCIÓN)
        if len(encryption_key) < 32:
            # Generar una clave base64 válida
            encryption_key = Fernet.generate_key()
        
        return Fernet(encryption_key)
    
    def to_dict(self, include_key=False):
        """
        Convertir a diccionario
        
        Args:
            include_key: Si es True, incluye la API key desencriptada (usar con cuidado)
        
        Returns:
            dict: Representación de la API key
        """
        data = {
            'id': self.id,
            'servicio_nombre': self.servicio_nombre,
            'fecha_registro': self.fecha_registro.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'activa': self.activa
        }
        
        if include_key:
            # Solo incluir si explícitamente se solicita
            data['api_key'] = self.get_api_key()
        else:
            # Mostrar versión parcialmente oculta
            key = self.get_api_key()
            if len(key) > 8:
                data['api_key_preview'] = f"{key[:4]}...{key[-4:]}"
            else:
                data['api_key_preview'] = "***"
        
        return data
    
    def __repr__(self):
        return f'<APIKey {self.servicio_nombre} - Usuario {self.usuario_id}>'