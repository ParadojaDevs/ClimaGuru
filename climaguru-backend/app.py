from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from database.db_connection import db
from config import Config
from app import create_app, db
import os

# Crear aplicación
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Habilitar CORS para futuro frontend
    CORS(app, supports_credentials=True)
    
    # Inicializar base de datos
    db.init_app(app)
    
    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Registrar blueprints (rutas)
    from routes.auth import auth_bp
    from routes.weather import weather_bp
    from routes.queries import queries_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(weather_bp, url_prefix='/api/weather')
    app.register_blueprint(queries_bp, url_prefix='/api/queries')
    
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'ClimaGuru API'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    print("✓ Base de datos inicializada")

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'

    print(f"🚀 ClimaGuru Backend iniciando en http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)