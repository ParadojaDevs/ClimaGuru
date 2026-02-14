"""WSGI entrypoint for deployment."""
import os

from app import create_app

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True") == "True"

    print(f"ClimaGuru Backend iniciando en http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)