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
    proveedor = db.Column(db.String(50), nullable=False)
    api_key_encrypted = db.Column(db.Text, nullable=False)
    api_secret_encrypted = db.Column(db.Text, nullable=True)
    descripcion = db.Column(db.String(255), nullable=True)
    activa = db.Column(db.Boolean, default=True)
    limite_consultas_diarias = db.Column(db.Integer, default=1000)
    consultas_realizadas = db.Column(db.Integer, default=0)
    ultimo_uso = db.Column(db.DateTime, nullable=True)
    creada_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único compuesto
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'proveedor', name='unique_proveedor_usuario'),
    )
    
    def __init__(self, usuario_id, proveedor, api_key_texto, api_secret_texto=None, descripcion=None):
        """
        Inicializar API Key
        
        Args:
            usuario_id: ID del usuario propietario
            proveedor: Nombre del servicio (ej: 'openweather', 'meteosource', 'meteoblue')
            api_key_texto: API key en texto plano (se encriptará automáticamente)
            api_secret_texto: API secret en texto plano (opcional)
            descripcion: Descripción de la API key
        """
        self.usuario_id = usuario_id
        self.proveedor = proveedor
        self.set_api_key(api_key_texto)
        if api_secret_texto:
            self.set_api_secret(api_secret_texto)
        self.descripcion = descripcion
    
    def set_api_key(self, api_key_texto):
        """
        Encriptar y guardar API key
        
        Args:
            api_key_texto: API key en texto plano
        """
        cipher = self._get_cipher()
        self.api_key_encrypted = cipher.encrypt(api_key_texto.encode()).decode()
        self.actualizada_en = datetime.utcnow()
    
    def get_api_key(self):
        """
        Desencriptar y obtener API key
        
        Returns:
            str: API key en texto plano
        """
        cipher = self._get_cipher()
        return cipher.decrypt(self.api_key_encrypted.encode()).decode()
    
    def set_api_secret(self, api_secret_texto):
        """Encriptar y guardar API secret"""
        cipher = self._get_cipher()
        self.api_secret_encrypted = cipher.encrypt(api_secret_texto.encode()).decode()
    
    def get_api_secret(self):
        """Desencriptar y obtener API secret"""
        if not self.api_secret_encrypted:
            return None
        cipher = self._get_cipher()
        return cipher.decrypt(self.api_secret_encrypted.encode()).decode()
    
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
            'proveedor': self.proveedor,
            'descripcion': self.descripcion,
            'creada_en': self.creada_en.isoformat() if self.creada_en else None,
            'actualizada_en': self.actualizada_en.isoformat() if self.actualizada_en else None,
            'activa': self.activa,
            'limite_consultas_diarias': self.limite_consultas_diarias,
            'consultas_realizadas': self.consultas_realizadas,
            'ultimo_uso': self.ultimo_uso.isoformat() if self.ultimo_uso else None
        }
        
        if include_key:
            data['api_key'] = self.get_api_key()
            if self.get_api_secret():
                data['api_secret'] = self.get_api_secret()
        else:
            key = self.get_api_key()
            if key and len(key) > 8:
                data['api_key_preview'] = f"{key[:4]}...{key[-4:]}"
            else:
                data['api_key_preview'] = "***"
        
        return data
    
    def __repr__(self):
        return f'<APIKey {self.servicio_nombre} - Usuario {self.usuario_id}>'