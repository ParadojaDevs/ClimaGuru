import os
import sys
from flask import Flask, jsonify, request, make_response
# from flask_jwt_extended import JWTManager
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
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
    # jwt = JWTManager(app)

    # Rate Limiter Configuration
    # limiter = Limiter(
    #     key_func=get_remote_address,
    #     default_limits=["200 per day", "50 per hour"]
    # )
    # limiter.init_app(app)

    # Security headers middleware
    def add_security_headers(response):
        sys.stderr.write("DEBUG SECURITY: ENTERED\n")
        sys.stderr.flush()
        with open(r"E:\GIT\ClimaGuru\backend\security_debug.txt", "a") as f:
            f.write("Security function ran\n")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Remove server header for obscurity
        response.headers.pop("Server", None)
        sys.stderr.write(f"DEBUG SECURITY: headers={dict(response.headers)}\n")
        sys.stderr.flush()
        return response
    app.after_request(add_security_headers)

    # CORS with manual credentials support - handle everything ourselves
    def add_cors_headers(response):
        sys.stderr.write("DEBUG CORS: ENTERED\n")
        sys.stderr.flush()
        origin = request.headers.get("Origin")
        allowed_origins = cfg.CORS_ORIGINS.split(",")
        sys.stderr.write(f"DEBUG CORS: origin={origin}, allowed={allowed_origins}\n")
        sys.stderr.flush()
        if origin in allowed_origins:
            sys.stderr.write("DEBUG CORS: setting Origin header\n")
            sys.stderr.flush()
            response.headers.add("Access-Control-Allow-Origin", origin)
            sys.stderr.write("DEBUG CORS: Origin header set\n")
            sys.stderr.flush()
            # Write to file to confirm execution
            with open(r"E:\GIT\ClimaGuru\backend\cors_debug.txt", "a") as f:
                f.write(f"CORS function ran, origin={origin}\n")
            sys.stderr.write("DEBUG CORS: setting Credentials header\n")
            sys.stderr.flush()
            try:
                response.headers["Access-Control-Allow-Credentials"] = "true"
                sys.stderr.write("DEBUG CORS: Credentials header set successfully\n")
                sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"DEBUG CORS: ERROR setting Credentials header: {e}\n")
                sys.stderr.flush()
            response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            # Test custom header
            response.headers.add("X-Test-Custom-Header", "test-value")
            sys.stderr.write("DEBUG CORS: all headers added\n")
            sys.stderr.flush()
            sys.stderr.write(f"DEBUG CORS: response.headers={dict(response.headers)}\n")
            sys.stderr.flush()
        else:
            sys.stderr.write("DEBUG CORS: origin not in allowed\n")
            sys.stderr.flush()
        sys.stderr.write("DEBUG CORS: RETURNING\n")
        sys.stderr.flush()
        return response
    app.after_request(add_cors_headers)
    sys.stderr.write("REGISTERED add_cors_headers\n")
    sys.stderr.flush()
    sys.stderr.write(f"AFTER REQUEST FUNCS: {app.after_request_funcs}\n")
    sys.stderr.flush()

    # CORS preflight handling
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin")
            allowed_origins = cfg.CORS_ORIGINS.split(",")
            if origin in allowed_origins:
                response = make_response()
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Max-Age"] = "86400"
                return response
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