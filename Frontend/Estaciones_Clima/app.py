from flask import Flask
from flask_cors import CORS

from extensions import db, migrate, ma
from api import bp as api_bp

# IMPORTANTE: Esto asume que crearás/renombrarás el archivo 'api/empleados.py' a 'api/estaciones.py'
import api.estaciones  # asegura que las rutas de estaciones se registren
import api.clima       # asegura que las rutas de clima se registren
import models  # asegura que los modelos estén visibles para Alembic/Flask-Migrate


def create_app():
    app = Flask(__name__)

    # Ajusta usuario/contraseña/host según tu entorno
    # He cambiado 'recursos_humanos_db' por 'clima_db' para coincidir con el SQL
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:kali@127.0.0.1/clima_db?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_AS_ASCII"] = False

    # Extensiones initialization
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # CORS (abrimos para /api/*)
    # Esto permite que tu React (localhost:5173) hable con este Python (localhost:8080)
    CORS(app, resources={r"/api/*": {"origins": "*"}}) 

    # Blueprints
    app.register_blueprint(api_bp)

    @app.get("/")
    def inicio():
        return "API de Estaciones Climáticas (Flask)"

    return app


if __name__ == "__main__":
    # Puedes mantener el puerto 8080 o cambiarlo al 5000 (default)
    create_app().run(debug=True, port=8080)

