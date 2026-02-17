# Autenticación y autorización
"""
Servicio de Autenticación y Autorización
=========================================
Maneja login, registro, validación de tokens y permisos
"""
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from app import db
from app.models.usuario import Usuario
from app.models.sesion import Sesion
from app.models.logs_actividad import LogsActividad
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
import re


class AuthService:
    """Servicio de autenticación"""
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Validar formato de email"""
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(patron, email) is not None
    
    @staticmethod
    def validar_password(password: str) -> tuple:
        """
        Validar fortaleza de contraseña
        Returns: (es_valida, mensaje)
        """
        if len(password) < 8:
            return False, "Mínimo 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "Al menos una mayúscula"
        if not re.search(r'[a-z]', password):
            return False, "Al menos una minúscula"
        if not re.search(r'\d', password):
            return False, "Al menos un número"
        return True, "Válida"
    
    @staticmethod
    def registrar_usuario(username: str, email: str, password: str, 
                         nombre_completo: str = None) -> tuple:
        """
        Registrar nuevo usuario
        Returns: (usuario, error_message)
        """
        # Validaciones
        if len(username) < 3:
            return None, "Username debe tener al menos 3 caracteres"
        
        if not AuthService.validar_email(email):
            return None, "Email inválido"
        
        valida, mensaje = AuthService.validar_password(password)
        if not valida:
            return None, mensaje
        
        # Verificar existencia
        if Usuario.query.filter_by(username=username).first():
            return None, "Username ya registrado"
        
        if Usuario.query.filter_by(email=email.lower()).first():
            return None, "Email ya registrado"
        
        # Crear usuario
        usuario = Usuario(
            username=username,
            email=email.lower(),
            password=password,
            nombre_completo=nombre_completo
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        return usuario, None
    
    @staticmethod
    def iniciar_sesion(username_or_email: str, password: str) -> tuple:
        """
        Iniciar sesión
        Returns: (usuario, access_token, error)
        """
        usuario = Usuario.query.filter(
            (Usuario.username == username_or_email) |
            (Usuario.email == username_or_email.lower())
        ).first()
        
        if not usuario:
            return None, None, "Credenciales inválidas"
        
        if not usuario.activo:
            return None, None, "Usuario inactivo"
        
        if not usuario.check_password(password):
            return None, None, "Credenciales inválidas"
        
        # Actualizar último acceso
        usuario.actualizar_ultimo_acceso()
        
        # Generar tokens
        access_token = create_access_token(identity=usuario.id)
        refresh_token = create_refresh_token(identity=usuario.id)
        
        return usuario, access_token, None
    
    @staticmethod
    def cerrar_sesion(usuario_id: int, token_jti: str) -> bool:
        """Cerrar sesión del usuario"""
        sesion = Sesion.query.filter_by(
            token=token_jti, 
            usuario_id=usuario_id
        ).first()
        
        if sesion:
            sesion.activa = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def obtener_usuario_actual(usuario_id: int) -> Usuario:
        """Obtener usuario por ID"""
        return Usuario.query.get(usuario_id)


class AuthorizationService:
    """Servicio de autorización basado en roles"""
    
    # Definición de permisos por rol
    PERMISOS = {
        'admin': ['*'],  # Todos los permisos
        'operario': [
            'consulta:crear', 'consulta:leer', 'consulta:actualizar',
            'api_key:crear', 'api_key:leer', 'api_key:actualizar', 'api_key:eliminar',
            'usuario:leer', 'estadisticas:leer'
        ],
        'consultor': [
            'consulta:crear', 'consulta:leer',
            'api_key:crear', 'api_key:lear',
            'estadisticas:leer'
        ]
    }
    
    @staticmethod
    def tiene_permiso(rol: str, permiso: str) -> bool:
        """Verificar si un rol tiene un permiso específico"""
        permisos = AuthorizationService.PERMISOS.get(rol, [])
        return '*' in permisos or permiso in permisos
    
    @staticmethod
    def requiere_permiso(permiso: str):
        """Decorator para requerir permiso específico"""
        def decorator(f):
            @wraps(f)
            @jwt_required()
            def decorated_function(*args, **kwargs):
                usuario_id = get_jwt_identity()
                usuario = Usuario.query.get(usuario_id)
                
                if not usuario or not usuario.activo:
                    return {'error': 'Unauthorized'}, 403
                
                if not AuthorizationService.tiene_permiso(usuario.rol, permiso):
                    return {'error': 'Permiso denegado'}, 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator