from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database import db
from routes import auth_bp, users_bp
from models import User


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS.split(",")}})
    db.init_app(app)

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

        # Seeder minimo para facilitar pruebas con Postman.
        if User.query.count() == 0:
            admin = User(username="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
