# Rutas/Endpoints de la API

from app.routes.auth import auth_bp
# Por ahora solo tenemos auth, luego agregaremos más

# Para que el __init__.py principal los encuentre
__all__ = ['auth_bp']