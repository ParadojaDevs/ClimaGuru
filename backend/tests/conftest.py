"""Fixtures compartidas para las suites de la zona autenticada (Backend A).

Ensambla backend/app.py por ruta explicita (mismo patron que
TestRegresionAuth en test_public_endpoints.py) con SQLite en tmp_path,
sin MySQL ni secretos reales.
"""

import importlib.util
import os
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import db  # noqa: E402
from models import User  # noqa: E402


def _load_app_module():
    """Importa backend/app.py como modulo independiente del paquete app_pkg."""
    app_py = os.path.join(BACKEND_DIR, "app.py")
    spec = importlib.util.spec_from_file_location("climaguru_backend_app", app_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def auth_app(monkeypatch, tmp_path):
    """App completa (JWT + SQLAlchemy + blueprint publico) sobre SQLite tmp."""
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_USER", "u")
    monkeypatch.setenv("MYSQL_PASSWORD", "p")
    monkeypatch.setenv("MYSQL_DATABASE", "db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'auth_test.sqlite'}")
    # La zona publica no debe tocar la base real del desarrollador.
    monkeypatch.setenv("PUBLIC_DB_PATH", str(tmp_path / "public_test.sqlite"))

    module = _load_app_module()
    app = module.create_app()
    app.testing = True
    yield app


@pytest.fixture()
def auth_client(auth_app):
    with auth_app.test_client() as test_client:
        yield test_client


@pytest.fixture()
def seeded_user(auth_app):
    """Usuario 'admin' / 'admin123' creado directo por modelo (sin HTTP)."""
    with auth_app.app_context():
        user = User(username="admin", email="admin@climaguru.local")
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()
        return {"id": user.id, "username": user.username}


@pytest.fixture()
def login(auth_client):
    """Callable: login(...) -> body del POST /login (token, refresh_token, user)."""

    def _login(username="admin", password="admin123", expect=200):
        response = auth_client.post(
            "/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == expect
        return response.get_json()

    return _login
