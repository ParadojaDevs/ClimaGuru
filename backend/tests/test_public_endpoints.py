"""Pruebas de la zona publica (sin auth) y regresion de la zona autenticada.

La app publica se monta en un Flask minimo para no depender de MySQL:
el blueprint public es autocontenido (sqlite3 + requests mockeados).
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask  # noqa: E402

from database import public_db  # noqa: E402
from routes.public import public_bp  # noqa: E402
from services import open_meteo_client as om  # noqa: E402


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "public_test.sqlite")
    public_db.init_db(path)
    return path


@pytest.fixture()
def client(db_path):
    app = Flask(__name__)
    app.config["PUBLIC_DB_PATH"] = db_path
    app.config["PUBLIC_WEATHER_TTL"] = 600
    app.config["SECRET_KEY"] = "test-secret"
    app.register_blueprint(public_bp)
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


def _mock_om_response(payload):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    return response


OM_PAYLOAD = {
    "current": {"temperature_2m": 24.5, "precipitation": 0.0},
    "hourly": {"time": ["2026-11-15T00:00"], "temperature_2m": [24.5]},
    "daily": {"time": ["2026-11-15"], "temperature_2m_max": [28.0]},
    "timezone": "America/Bogota",
    "utc_offset_seconds": -18000,
    "error": False,
}


class TestCities:
    def test_lista_ciudades(self, client):
        response = client.get("/api/public/cities")
        assert response.status_code == 200
        cities = response.get_json()["cities"]
        assert len(cities) >= 5
        assert any(c["name"] == "Bogota" for c in cities)


class TestWeather:
    def test_falta_parametro(self, client):
        assert client.get("/api/public/weather").status_code == 400

    def test_lat_fuera_de_rango(self, client):
        response = client.get("/api/public/weather?lat=50&lon=-74")
        assert response.status_code == 400
        assert "rango" in response.get_json()["error"]

    def test_lon_fuera_de_rango(self, client):
        response = client.get("/api/public/weather?lat=4.7&lon=10")
        assert response.status_code == 400

    def test_consulta_exitosa_con_fuente(self, client):
        with patch.object(om.requests, "get", return_value=_mock_om_response(OM_PAYLOAD)) as mock_get:
            response = client.get("/api/public/weather?lat=4.711&lon=-74.0721")
        assert response.status_code == 200
        body = response.get_json()
        assert body["current"]["temperature_2m"] == 24.5
        assert body["source"]["license"] == "CC BY 4.0"
        assert body["fetched_at"]
        mock_get.assert_called_once()

    def test_cache_evita_segunda_llamada(self, client):
        with patch.object(om.requests, "get", return_value=_mock_om_response(OM_PAYLOAD)) as mock_get:
            client.get("/api/public/weather?lat=4.711&lon=-74.0721")
            client.get("/api/public/weather?lat=4.711&lon=-74.0721")
        assert mock_get.call_count == 1

    def test_upstream_caida_da_502(self, client):
        with patch.object(om.requests, "get", side_effect=om.requests.RequestException("down")):
            response = client.get("/api/public/weather?lat=4.711&lon=-74.0721")
        assert response.status_code == 502


class TestRadar:
    def test_radar_desconocido_400(self, client):
        response = client.get("/api/public/radar/overlay?radar=noexiste")
        assert response.status_code == 400
        assert response.get_json()["valid"]

    def test_stations_estatico(self, client):
        response = client.get("/api/public/radar/stations")
        assert response.status_code == 200
        stations = response.get_json()["stations"]
        assert {s["code"] for s in stations} == {"BAR", "CAR", "GUA", "MUN"}

    def test_latest_con_probe_exitoso(self, client):
        fake = (MagicMock(status_code=200),)
        with patch("services.ideam_radar_client.requests.Session") as session_cls:
            session = session_cls.return_value.__enter__.return_value
            session.head.return_value = MagicMock(status_code=200)
            response = client.get("/api/public/radar/latest")
        assert response.status_code == 200
        body = response.get_json()
        assert body["kind"] == "composite"
        assert len(body["stamp"]) == 10
        assert "_basemap.png" in body["url"]
        assert fake  # noqa: silencia lint del mock auxiliar

    def test_latest_sin_disponibilidad_502(self, client):
        with patch("services.ideam_radar_client.requests.Session") as session_cls:
            session = session_cls.return_value.__enter__.return_value
            session.head.return_value = MagicMock(status_code=404)
            response = client.get("/api/public/radar/latest")
        assert response.status_code == 502

    def test_frames_valida_radar(self, client):
        assert client.get("/api/public/radar/frames?radar=zzz").status_code == 400


class TestThrottle:
    def test_429_al_exceder_ventana(self, client, db_path):
        responses = [client.get("/api/public/cities") for _ in range(11)]
        # limite catalog = 10 / 60 s: la 11va debe ser rechazada
        assert responses[0].status_code == 200
        assert responses[-1].status_code == 429
        # Endpoint distinto mantiene su propio presupuesto
        weather_response = client.get("/api/public/weather")
        assert weather_response.status_code == 400  # 400 por falta de params, no 429


class TestRegresionAuth:
    """La zona autenticada debe seguir intacta: /users exige JWT."""

    def test_users_sin_token_401(self, monkeypatch, tmp_path):
        # create_app exige config MySQL; usamos sqlite en memoria para el test.
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("MYSQL_HOST", "localhost")
        monkeypatch.setenv("MYSQL_PORT", "3306")
        monkeypatch.setenv("MYSQL_USER", "u")
        monkeypatch.setenv("MYSQL_PASSWORD", "p")
        monkeypatch.setenv("MYSQL_DATABASE", "db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'auth_test.sqlite'}")

        # backend tiene app.py (Backend A) y app/ (Backend B): importamos
        # app.py por ruta explicita para no chocar con el paquete.
        import importlib.util

        app_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
        spec = importlib.util.spec_from_file_location("climaguru_backend_app", app_py)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        app = module.create_app()
        app.testing = True
        with app.test_client() as test_client:
            assert test_client.get("/users").status_code == 401
            # La ruta publica nueva vive en la misma app y NO exige token
            assert test_client.get("/api/public/cities").status_code == 200
            assert test_client.get("/health").status_code == 200
