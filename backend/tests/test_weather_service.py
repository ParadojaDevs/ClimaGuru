"""Pruebas unitarias del cliente Open-Meteo (sin red: requests mockeado)."""

import sys
import os
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import open_meteo_client as om  # noqa: E402


def _mock_response(status_code=200, payload=None, json_exc=None):
    response = MagicMock()
    response.status_code = status_code
    if json_exc is not None:
        response.json.side_effect = json_exc
    else:
        response.json.return_value = payload or {}
    return response


class TestValidateCoords:
    def test_centro_colombia_ok(self):
        lat, lon = om.validate_coords(4.711, -74.0721)
        assert lat == 4.711
        assert lon == -74.0721

    def test_redondeo_a_4_decimales(self):
        lat, lon = om.validate_coords("4.711111", "-74.072199")
        assert lat == 4.7111
        assert lon == -74.0722

    def test_limites_del_bbox_ok(self):
        lat, lon = om.validate_coords(om.COLOMBIA_BBOX["lat_min"], om.COLOMBIA_BBOX["lon_min"])
        assert (lat, lon) == (om.COLOMBIA_BBOX["lat_min"], om.COLOMBIA_BBOX["lon_min"])

    def test_lat_no_numerico_valueerror(self):
        with pytest.raises(ValueError):
            om.validate_coords("abc", -74.0)

    def test_lat_fuera_de_rango(self):
        with pytest.raises(ValueError) as excinfo:
            om.validate_coords(50.0, -74.0)
        assert "lat" in str(excinfo.value)

    def test_lon_fuera_de_rango(self):
        with pytest.raises(ValueError) as excinfo:
            om.validate_coords(4.7, 10.0)
        assert "lon" in str(excinfo.value)


class TestFetchPointForecast:
    def test_parametros_enviados(self):
        with pytest.MonkeyPatch.context() as mp:
            captured = {}

            def fake_get(url, params=None, timeout=None):
                captured["url"] = url
                captured["params"] = params
                captured["timeout"] = timeout
                return _mock_response(200, {"current": {"temperature_2m": 20.0}})

            mp.setattr(om.requests, "get", fake_get)
            om.fetch_point_forecast(4.711, -74.0721)

            assert captured["url"] == om.OPEN_METEO_URL
            assert captured["params"]["latitude"] == 4.711
            assert captured["params"]["longitude"] == -74.0721
            assert captured["params"]["timezone"] == "America/Bogota"
            assert captured["params"]["forecast_days"] == 5
            assert "cloud_cover" in captured["params"]["current"]
            assert "pressure_msl" in captured["params"]["current"]
            assert "is_day" in captured["params"]["current"]
            assert captured["timeout"] == 10

    def test_respuesta_200_devuelve_payload(self):
        payload = {"current": {"temperature_2m": 24.5}, "hourly": {}, "daily": {}}
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                om.requests, "get", lambda *a, **k: _mock_response(200, payload)
            )
            data = om.fetch_point_forecast(4.711, -74.0721)
        assert data == payload

    def test_request_exception_lanza_upstreamerror(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                om.requests,
                "get",
                lambda *a, **k: (_ for _ in ()).throw(om.requests.RequestException("down")),
            )
            with pytest.raises(om.UpstreamError):
                om.fetch_point_forecast(4.711, -74.0721)

    def test_status_no_200_lanza_upstreamerror(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                om.requests, "get", lambda *a, **k: _mock_response(503)
            )
            with pytest.raises(om.UpstreamError) as excinfo:
                om.fetch_point_forecast(4.711, -74.0721)
        assert "503" in str(excinfo.value)

    def test_json_invalido_lanza_upstreamerror(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                om.requests,
                "get",
                lambda *a, **k: _mock_response(200, json_exc=ValueError("bad json")),
            )
            with pytest.raises(om.UpstreamError) as excinfo:
                om.fetch_point_forecast(4.711, -74.0721)
        assert "JSON invalido" in str(excinfo.value)

    def test_error_de_api_lanza_upstreamerror_con_reason(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                om.requests,
                "get",
                lambda *a, **k: _mock_response(200, {"error": True, "reason": "out of quota"}),
            )
            with pytest.raises(om.UpstreamError) as excinfo:
                om.fetch_point_forecast(4.711, -74.0721)
        assert "out of quota" in str(excinfo.value)
