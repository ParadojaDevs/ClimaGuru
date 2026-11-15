import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from config import Config
from database import db
from database import public_db
from routes import auth_bp, users_bp
from routes.public import public_bp
from models import User


load_dotenv()

cfg = Config()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(cfg)
    app.config["ENV"] = os.getenv("FLASK_ENV", "development")

    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = cfg.SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = cfg.JWT_ACCESS_TOKEN_EXPIRES
    app.config["PWD_HASH_METHOD"] = cfg.PWD_HASH_METHOD
    jwt = JWTManager(app)

    # Rate Limiter Configuration
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    limiter.init_app(app)

    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Remove server header for obscurity
        response.headers.pop("Server", None)
        return response

    CORS(app, resources={r"/*": {"origins": cfg.CORS_ORIGINS.split(",")}})
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(public_bp)

    # Zona publica: su propio SQLite (crea directorio y esquema si faltan).
    try:
        public_db.init_db(cfg.PUBLIC_DB_PATH)
    except Exception as exc:  # pragma: no cover - fallo de disco no debe tumbar auth
        app.logger.error("No se pudo inicializar la base publica: %s", exc)

    @app.errorhandler(429)
    def ratelimit_exceeded(error):
        return jsonify({
            "error": "Límite de tasa excedido",
            "message": "Demasiadas solicitudes desde esta IP",
            "retry_after": error.description if hasattr(error, 'description') else 60
        }), 429

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "metodo no permitido"}), 405

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "error interno del servidor"}), 500

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")