"""Pruebas de F3.1b: manifiesto IDEAM, politica geografica y cache radar.

Todo local: requests y los probes se mockean; no hay red.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask  # noqa: E402

from database import public_db  # noqa: E402
from routes.public import public_bp  # noqa: E402
from services import ideam_radar_client as ideam  # noqa: E402
from services import radar_georef as rg  # noqa: E402

NOW_UTC = datetime(2026, 11, 15, 18, 35, tzinfo=timezone.utc)


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "public_f31b.sqlite")
    public_db.init_db(path)
    return path


@pytest.fixture()
def client(db_path):
    app = Flask(__name__)
    app.config["PUBLIC_DB_PATH"] = db_path
    app.config["PUBLIC_WEATHER_TTL"] = 600
    app.config["RADAR_DISCOVERY_TTL"] = 300
    app.config["SECRET_KEY"] = "test-secret"
    app.register_blueprint(public_bp)
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


def _token(stamp="2611151320", code="GUA", folder="Guaviare"):
    return (
        f"/radares/interno/radarcol/transparent/{folder}/z/2026/11/15/"
        f"{code}{stamp}_z_Transp.png"
    )


def _manifest_response(text, status=200):
    return MagicMock(status_code=status, text=text)


def _manifest_patch(text, status=200):
    return patch(
        "services.ideam_radar_client.requests.get",
        return_value=_manifest_response(text, status),
    )


def _stamps(count=30, start=datetime(2026, 11, 15, 10, 0, tzinfo=ideam.COT_TZ)):
    return [(start + timedelta(minutes=5 * index)).strftime("%y%m%d%H%M") for index in range(count)]


# ---------------------------------------------------------------------------
# Manifiesto IDEAM
# ---------------------------------------------------------------------------

def test_manifest_single_line_space_separated_is_parsed():
    text = " ".join(_token(stamp) for stamp in ("2611151310", "2611151320", "2611151330"))
    with _manifest_patch(text):
        frames = ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)

    assert [frame["stamp"] for frame in frames] == ["2611151310", "2611151320", "2611151330"]
    assert all(frame["url"].startswith("https://bart.ideam.gov.co/ospa/") for frame in frames)
    assert frames[0]["timestamp"] == "2026-11-15T13:10:00-05:00"
    assert frames[0]["age_minutes"] == 25
    assert frames[-1]["age_minutes"] == 5


def test_manifest_deduplicates_stamps():
    text = f"{_token('2611151320')} {_token('2611151320')}\n{_token('2611151330')}"
    with _manifest_patch(text):
        frames = ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)
    assert [frame["stamp"] for frame in frames] == ["2611151320", "2611151330"]


def test_manifest_is_sorted_ascending_regardless_of_input_order():
    stamps = ["2611151330", "2611151310", "2611151320"]
    text = " ".join(_token(stamp) for stamp in stamps)
    with _manifest_patch(text):
        frames = ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)
    assert [frame["stamp"] for frame in frames] == sorted(stamps)


def test_manifest_keeps_only_the_24_most_recent_frames():
    stamps = _stamps(30)
    shuffled = stamps[::2] + stamps[1::2]
    text = " ".join(_token(stamp) for stamp in shuffled)
    with _manifest_patch(text):
        frames = ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)

    assert len(frames) == ideam.MANIFEST_MAX_FRAMES == 24
    assert [frame["stamp"] for frame in frames] == stamps[-24:]
    assert frames == sorted(frames, key=lambda frame: frame["timestamp"])


def test_manifest_limit_is_clamped_to_24():
    text = " ".join(_token(stamp) for stamp in _stamps(30))
    with _manifest_patch(text):
        frames = ideam.latest_transparent_manifest("guaviare", limit=999, now_utc=NOW_UTC)
    assert len(frames) == 24


def test_manifest_rejects_foreign_origins_and_traversal():
    bad_tokens = [
        "https://evil.example/x/GUA2611151320_z_Transp.png",
        "http://bart.ideam.gov.co/ospa/x/GUA2611151320_z_Transp.png",
        "https://bart.ideam.gov.co.evil/x/GUA2611151320_z_Transp.png",
        "https://bart.ideam.gov.co/ospa/x/GUA2611151320_z_Transp.png?next=evil",
        "/ospa/../GUA2611151320_z_Transp.png",
        "//evil.example/GUA2611151320_z_Transp.png",
        "C:\\temp\\GUA2611151320_z_Transp.png",
    ]
    with _manifest_patch(" ".join(bad_tokens)):
        with pytest.raises(ideam.RadarUnavailable):
            ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)


def test_manifest_rejects_frames_from_another_radar():
    text = _token("2611151320", code="MUN", folder="Munchique")
    with _manifest_patch(text):
        with pytest.raises(ideam.RadarUnavailable):
            ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)


def test_manifest_rejects_tokens_without_verifiable_stamp():
    text = "/radares/interno/radarcol/transparent/Guaviare/z/2026/11/15/GUA_z_Transp.png"
    with _manifest_patch(text):
        with pytest.raises(ideam.RadarUnavailable):
            ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)


@pytest.mark.parametrize("text", ["", "   ", "sin frames aqui", "GUA2611151320_z_Transp.png"])
def test_manifest_empty_or_malformed_raises(text):
    with _manifest_patch(text):
        with pytest.raises(ideam.RadarUnavailable):
            ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)


def test_manifest_http_error_raises():
    with _manifest_patch("", status=404):
        with pytest.raises(ideam.RadarUnavailable):
            ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)


def test_manifest_network_error_raises():
    with patch(
        "services.ideam_radar_client.requests.get",
        side_effect=ideam.requests.RequestException("boom"),
    ):
        with pytest.raises(ideam.RadarUnavailable):
            ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)


def test_manifest_age_is_never_negative():
    future_stamp = "2611151900"  # 19:00 COT = 00:00 UTC del dia siguiente
    with _manifest_patch(_token(future_stamp)):
        frames = ideam.latest_transparent_manifest("guaviare", now_utc=NOW_UTC)
    assert frames[0]["age_minutes"] == 0


# ---------------------------------------------------------------------------
# Politica geografica
# ---------------------------------------------------------------------------

def test_public_metadata_matches_approved_policy():
    expected = {
        "guaviare": True,
        "munchique": True,
        "barrancabermeja": False,
        "carimagua": False,
    }
    for radar_id, allowed in expected.items():
        metadata = rg.public_metadata(radar_id)
        assert metadata["render_allowed"] is allowed
        assert metadata["overlay_enabled"] is False
        assert metadata["state"] != rg.STATE_VERIFIED


def test_munchique_warning_mentions_the_10_5_km_discrepancy():
    warning = rg.public_metadata("munchique")["warning"]
    assert "10,5 km" in warning
    assert "estación" in warning


def test_blocked_radars_have_no_warning_and_are_not_renderable():
    for radar_id in ("barrancabermeja", "carimagua"):
        metadata = rg.public_metadata(radar_id)
        assert metadata["visualization"] == rg.VISUALIZATION_BLOCKED
        assert metadata["warning"] is None
        with pytest.raises(rg.BlockedVisualizationError):
            rg.require_renderable(radar_id)


# ---------------------------------------------------------------------------
# Endpoints publicos: metadatos y compatibilidad
# ---------------------------------------------------------------------------

def test_stations_include_georef_for_the_four_radars(client):
    response = client.get("/api/public/radar/stations")
    assert response.status_code == 200
    stations = {station["code"]: station for station in response.get_json()["stations"]}
    assert set(stations) == {"BAR", "CAR", "GUA", "MUN"}
    assert stations["GUA"]["georef"]["render_allowed"] is True
    assert stations["MUN"]["georef"]["render_allowed"] is True
    assert stations["BAR"]["georef"]["render_allowed"] is False
    assert stations["CAR"]["georef"]["render_allowed"] is False
    assert stations["GUA"]["georef"]["overlay_enabled"] is False


def test_overlay_keeps_contract_and_adds_georef(client):
    with patch(
        "services.ideam_radar_client.probe_transparent_z",
        return_value=("2611151320", "https://bart.ideam.gov.co/ospa/GUA.png"),
    ):
        response = client.get("/api/public/radar/overlay?radar=guaviare")

    assert response.status_code == 200
    body = response.get_json()
    assert body["kind"] == "overlay:guaviare"
    assert body["stamp"] == "2611151320"
    assert body["url"].endswith("GUA.png")
    assert body["station"]["code"] == "GUA"
    assert body["source"]["license"] == "CC BY 4.0"
    assert body["georef"]["render_allowed"] is True
    assert body["georef"]["state"] == "derived"


def test_overlay_unknown_radar_still_400(client):
    response = client.get("/api/public/radar/overlay?radar=noexiste")
    assert response.status_code == 400
    assert response.get_json()["valid"]


def test_overlay_unavailable_still_502_and_not_cached(client):
    with patch(
        "services.ideam_radar_client.probe_transparent_z",
        side_effect=ideam.RadarUnavailable("sin frames"),
    ) as probe:
        first = client.get("/api/public/radar/overlay?radar=guaviare")
        second = client.get("/api/public/radar/overlay?radar=guaviare")

    assert first.status_code == second.status_code == 502
    assert probe.call_count == 2  # el error no se cachea


def test_overlay_success_is_cached_until_ttl(client, db_path):
    with patch(
        "services.ideam_radar_client.probe_transparent_z",
        return_value=("2611151320", "https://bart.ideam.gov.co/ospa/GUA.png"),
    ) as probe:
        first = client.get("/api/public/radar/overlay?radar=guaviare")
        second = client.get("/api/public/radar/overlay?radar=guaviare")

    assert first.status_code == second.status_code == 200
    assert probe.call_count == 1
    assert first.get_json() == second.get_json()

    # Expiracion: la siguiente peticion vuelve a consultar IDEAM.
    public_db.cache_put(db_path, "radar:v1:overlay:guaviare", {}, -1)
    with patch(
        "services.ideam_radar_client.probe_transparent_z",
        return_value=("2611151325", "https://bart.ideam.gov.co/ospa/GUA2.png"),
    ) as probe_again:
        third = client.get("/api/public/radar/overlay?radar=guaviare")

    assert third.status_code == 200
    assert probe_again.call_count == 1
    assert third.get_json()["stamp"] == "2611151325"


def test_latest_success_is_cached(client):
    with patch(
        "services.ideam_radar_client.probe_composite",
        return_value=("2611151320", "https://bart.ideam.gov.co/ospa/Composite.png"),
    ) as probe:
        first = client.get("/api/public/radar/latest")
        second = client.get("/api/public/radar/latest")

    assert first.status_code == second.status_code == 200
    assert probe.call_count == 1
    assert first.get_json()["kind"] == "composite"


def test_frames_success_is_cached_and_preserves_order(client):
    frames = [
        {"stamp": "2611151310", "url": "https://x/GUA1.png", "timestamp": "t1", "age_minutes": 25},
        {"stamp": "2611151320", "url": "https://x/GUA2.png", "timestamp": "t2", "age_minutes": 15},
    ]
    with patch(
        "services.ideam_radar_client.latest_transparent_manifest",
        return_value=frames,
    ) as manifest:
        first = client.get("/api/public/radar/frames?radar=guaviare")
        second = client.get("/api/public/radar/frames?radar=guaviare")

    assert first.status_code == second.status_code == 200
    assert manifest.call_count == 1
    assert [frame["stamp"] for frame in first.get_json()["frames"]] == ["2611151310", "2611151320"]


def test_frames_unavailable_still_502_and_not_cached(client):
    with patch(
        "services.ideam_radar_client.latest_transparent_manifest",
        side_effect=ideam.RadarUnavailable("sin manifiesto"),
    ) as manifest:
        first = client.get("/api/public/radar/frames?radar=guaviare")
        second = client.get("/api/public/radar/frames?radar=guaviare")

    assert first.status_code == second.status_code == 502
    assert manifest.call_count == 2
