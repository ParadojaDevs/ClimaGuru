import os
from flask import Flask, jsonify, request, make_response, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from config import Config
from database import db
from routes import auth_bp, users_bp
from models import User


load_dotenv()

cfg = Config()


# Simple rate limiter using in-memory storage (for production use Flask-Limiter or Redis)
_request_limits = {}


def rate_limit(max_requests=100, window_seconds=900):
    """Decorator to limit requests per IP"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            now = os.times().elapsed if hasattr(os, 'times') else 3600
            # Simple window-based limiting
            if client_ip not in _request_limits:
                _request_limits[client_ip] = []

            # Remove timestamps outside the window
            _request_limits[client_ip] = [
                ts for ts in _request_limits[client_ip]
                if now - ts < window_seconds
            ]

            if len(_request_limits[client_ip]) >= max_requests:
                return jsonify({
                    "error": "demasiadas solicitudes, intenta más tarde",
                    "retry_after": window_seconds
                }), 429

            _request_limits[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(cfg)

    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = cfg.SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = cfg.JWT_ACCESS_TOKEN_EXPIRES
    jwt = JWTManager(app)

    CORS(app, resources={r"/*": {"origins": cfg.CORS_ORIGINS.split(",")}})
    db.init_app(app)

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

    # Apply rate limiting to all routes except health
    @app.before_request
    def apply_rate_limit():
        if request.endpoint not in ['health'] and request.blueprint != 'static':
            rate_limit(max_requests=200, window_seconds=900)(lambda: None)()
        # Note: True rate limiting would be applied per-route in production

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "metodo no permitido"}), 405

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "error interno del servidor"}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")