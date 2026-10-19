from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.extensions import db, migrate, jwt
import os

__all__ = ['db','migrate','jwt']

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV','development')
    from app.config import config
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r'/api/*':{'origins':app.config['CORS_ORIGINS']}})
    with app.app_context():
        from app.database import init_database
        init_database(app)
    register_blueprints(app)
    setup_logging(app)
    register_error_handlers(app)
    os.makedirs('logs', exist_ok=True)
    return app

def register_blueprints(app):
    from app.routes import auth_bp,usuarios_bp,api_keys_bp,consultas_bp,datos_bp,ingestion_bp,spatial_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(api_keys_bp, url_prefix='/api/api-keys')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    app.register_blueprint(datos_bp, url_prefix='/api/datos')
    app.register_blueprint(ingestion_bp, url_prefix='/api/ingestion')
    app.register_blueprint(spatial_bp, url_prefix='/api/spatial')
    @app.route('/health')
    def health(): return {'status':'ok'}, 200

def setup_logging(app):
    import logging
    from logging.handlers import RotatingFileHandler
    if not app.debug and not app.testing:
        h = RotatingFileHandler(app.config['LOG_FILE'], maxBytes=10485760, backupCount=10)
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        h.setLevel(logging.INFO)
        app.logger.addHandler(h)
    app.logger.setLevel(logging.INFO)

def register_error_handlers(app):
    @app.errorhandler(404)
    def nf(e): return {'error':'No encontrado'}, 404
    @app.errorhandler(500)
    def ie(e): db.session.rollback(); return {'error':'Error interno'}, 500
    @app.errorhandler(403)
    def fb(e): return {'error':'Prohibido'}, 403
