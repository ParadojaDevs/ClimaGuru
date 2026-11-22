"""Pruebas de georreferenciacion offline de radares IDEAM (F3.1a).

Todo es local: los GeoTIFF se construyen en memoria con la cabecera TIFF
minima necesaria. No se descargan imagenes ni se toca la red.
"""

import json
import math
import os
import struct
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import radar_georef as rg  # noqa: E402

GUA_SCALE = 0.0027060275738625783
GUA_TIE = (-75.3216752210146, 5.234746179819134)
MUN_SCALE = 0.0027070528221321997
MUN_TIE = (-78.97848077616474, 4.548308846227644)

_TIFF_FORMATS = {1: "B", 3: "H", 4: "I", 11: "f", 12: "d"}


def _geokey_directory(raster_type=1, epsg=4326):
    keys = [
        (rg.GEOKEY_MODEL_TYPE, 0, 1, 2),  # geographic
        (rg.GEOKEY_RASTER_TYPE, 0, 1, raster_type),
        (rg.GEOKEY_GEOGRAPHIC_CRS, 0, 1, epsg),
    ]
    values = [1, 1, 0, len(keys)]
    for key in keys:
        values.extend(key)
    return values


def _build_geotiff(
    width=4,
    height=3,
    scale=(1.0, 1.0),
    tiepoint=(10.0, 20.0, 0.0, 0.0),
    raster_type=1,
    epsg=4326,
    transformation=None,
    include_geokeys=True,
    endian="<",
):
    """Construye un TIFF con cabecera geografica valida y pixeles de relleno.

    El parser solo lee tags, no strips, asi que los pixeles son 8 bytes aunque
    las dimensiones declaradas sean 1992x1998.
    """
    entries = [
        (256, 3, [width]),
        (257, 3, [height]),
        (258, 3, [32]),
        (259, 3, [1]),
        (262, 3, [1]),
        (273, 4, [0]),  # StripOffsets, se parchea al final
        (277, 3, [1]),
        (278, 4, [height]),
        (279, 4, [8]),
        (339, 3, [3]),
    ]
    if scale is not None:
        entries.append((rg.TAG_MODEL_PIXEL_SCALE, 12, [scale[0], scale[1], 0.0]))
    if tiepoint is not None:
        entries.append((rg.TAG_MODEL_TIEPOINT, 12, list(tiepoint)))
    if transformation is not None:
        entries.append((rg.TAG_MODEL_TRANSFORMATION, 12, list(transformation)))
    if include_geokeys:
        entries.append(
            (rg.TAG_GEO_KEY_DIRECTORY, 3, _geokey_directory(raster_type, epsg))
        )
    entries.sort(key=lambda item: item[0])

    ifd_size = 2 + 12 * len(entries) + 4
    external_offset = 8 + ifd_size
    if external_offset % 2:
        external_offset += 1

    encoded = []
    for tag, type_id, values in entries:
        if type_id == 2:
            payload = values if isinstance(values, bytes) else values.encode("latin-1")
        else:
            fmt = endian + _TIFF_FORMATS[type_id] * len(values)
            payload = struct.pack(fmt, *values)
        encoded.append([tag, type_id, len(values), payload])

    chunks = []
    for item in encoded:
        payload = item[3]
        if len(payload) <= 4:
            item.append(payload.ljust(4, b"\x00"))
        else:
            align = 8 if item[1] == 12 else 2
            while external_offset % align:
                external_offset += 1
            item.append(struct.pack(endian + "I", external_offset))
            chunks.append((external_offset, payload))
            external_offset += len(payload)

    pixel_offset = external_offset
    for item in encoded:
        if item[0] == 273:
            item[4] = struct.pack(endian + "I", pixel_offset)

    total = pixel_offset + 8
    buffer = bytearray(total)
    buffer[0:2] = b"II" if endian == "<" else b"MM"
    struct.pack_into(endian + "H", buffer, 2, 42)
    struct.pack_into(endian + "I", buffer, 4, 8)
    struct.pack_into(endian + "H", buffer, 8, len(encoded))
    position = 10
    for tag, type_id, count, _payload, value in encoded:
        struct.pack_into(endian + "HHI", buffer, position, tag, type_id, count)
        buffer[position + 8:position + 12] = value
        position += 12
    struct.pack_into(endian + "I", buffer, position, 0)
    for offset, payload in chunks:
        buffer[offset:offset + len(payload)] = payload
    buffer[pixel_offset:pixel_offset + 8] = b"\x00" * 8
    return bytes(buffer)


def _valid_config(**overrides):
    base = {
        "radar_id": "synthetic",
        "name": "Synthetic",
        "code": "SYN",
        "crs": "EPSG:4326",
        "bounds": (-70.0, 2.0, -69.0, 3.0),
        "state": rg.STATE_ASSUMED,
        "source": "synthetic fixture",
        "method": "none",
        "uncertainty": "none",
        "limitations": ["sin calibracion"],
        "evidence": ["fixture de prueba"],
        "station_lat": 2.5,
        "station_lon": -69.5,
        "station_source": "test",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Registro de los cuatro radares
# ---------------------------------------------------------------------------

def test_registry_contains_exactly_the_four_radars():
    assert rg.radar_ids() == (
        "barrancabermeja",
        "carimagua",
        "guaviare",
        "munchique",
    )


def test_every_radar_declares_crs_bounds_state_source_and_limitations():
    for radar_id in rg.radar_ids():
        config = rg.get_radar_georef(radar_id)
        assert config.crs == rg.CRS_WGS84
        assert isinstance(config.bounds, rg.Bounds)
        assert config.state in rg.CONFIDENCE_STATES
        assert config.source and config.method and config.uncertainty
        assert config.limitations
        assert config.evidence
        assert config.overlay_enabled is False


def test_no_radar_is_verified_today():
    # La auditoria F3 no encontro evidencia suficiente para ninguno.
    for radar_id in rg.radar_ids():
        assert rg.get_radar_georef(radar_id).state != rg.STATE_VERIFIED


def test_expected_confidence_per_radar():
    expected = {
        "guaviare": rg.STATE_DERIVED,
        "munchique": rg.STATE_DERIVED,
        "barrancabermeja": rg.STATE_ASSUMED,
        "carimagua": rg.STATE_ASSUMED,
    }
    for radar_id, state in expected.items():
        assert rg.get_radar_georef(radar_id).state == state


def test_require_verified_fails_for_every_registered_radar():
    for radar_id in rg.radar_ids():
        with pytest.raises(rg.UnverifiedGeorefError):
            rg.require_verified(radar_id)


def test_assumed_radars_block_overlay():
    for radar_id in ("barrancabermeja", "carimagua"):
        config = rg.get_radar_georef(radar_id)
        assert config.readiness == rg.OVERLAY_BLOCKED
        assert rg.can_enable_overlay(radar_id) is False


def test_derived_radars_are_only_eligible_with_warning():
    for radar_id in ("guaviare", "munchique"):
        config = rg.get_radar_georef(radar_id)
        assert config.readiness == rg.OVERLAY_ELIGIBLE_WITH_WARNING
        assert rg.can_enable_overlay(radar_id) is True
        # Elegible no significa encendido.
        assert config.overlay_enabled is False


def test_unknown_radar_is_rejected_and_lists_valid_ids():
    with pytest.raises(rg.UnknownRadarError) as excinfo:
        rg.get_radar_georef("no-existe")
    message = str(excinfo.value)
    for radar_id in rg.radar_ids():
        assert radar_id in message


def test_registry_is_immutable():
    with pytest.raises(TypeError):
        rg.RADAR_GEOREF["guaviare"] = rg.RADAR_GEOREF["munchique"]


def test_calibration_report_is_json_serializable_and_ordered():
    report = rg.calibration_report()
    assert [item["radar_id"] for item in report] == list(rg.radar_ids())
    json.dumps(report)  # no debe lanzar


def test_guaviare_bounds_match_its_geotiff_metadata():
    data = _build_geotiff(
        width=1992,
        height=1998,
        scale=(GUA_SCALE, GUA_SCALE),
        tiepoint=(GUA_TIE[0], GUA_TIE[1], 0.0, 0.0, 0.0, 0.0),
    )
    parsed = rg.parse_geotiff_georef(data)
    config = rg.get_radar_georef("guaviare")
    assert parsed.bounds.as_tuple() == pytest.approx(config.bounds.as_tuple(), abs=1e-9)


def test_munchique_bounds_match_its_geotiff_metadata():
    data = _build_geotiff(
        width=1495,
        height=1502,
        scale=(MUN_SCALE, MUN_SCALE),
        tiepoint=(MUN_TIE[0], MUN_TIE[1], 0.0, 0.0, 0.0, 0.0),
    )
    parsed = rg.parse_geotiff_georef(data)
    config = rg.get_radar_georef("munchique")
    assert parsed.bounds.as_tuple() == pytest.approx(config.bounds.as_tuple(), abs=1e-9)


def test_guaviare_and_munchique_do_not_share_extent():
    gua = rg.get_radar_georef("guaviare").bounds
    mun = rg.get_radar_georef("munchique").bounds
    assert gua.as_tuple() != mun.as_tuple()
    assert gua.span_km()[0] == pytest.approx(599.475, abs=0.01)
    assert mun.span_km()[0] == pytest.approx(450.083, abs=0.01)


def test_assumed_bounds_are_exactly_the_documented_hypothesis():
    for radar_id in ("barrancabermeja", "carimagua"):
        config = rg.get_radar_georef(radar_id)
        hypothesis = rg.hypothesis_bounds_from_center(
            config.station_lat, config.station_lon, 300.0
        )
        assert hypothesis.as_tuple() == pytest.approx(config.bounds.as_tuple(), abs=1e-9)


def test_every_radar_bounds_contain_its_station():
    for radar_id in rg.radar_ids():
        config = rg.get_radar_georef(radar_id)
        assert config.bounds.contains(config.station_lat, config.station_lon)


# ---------------------------------------------------------------------------
# Politica de visualizacion (F3.1b)
# ---------------------------------------------------------------------------

def test_visualization_policy_per_radar():
    expected = {
        "guaviare": rg.VISUALIZATION_APPROXIMATE,
        "munchique": rg.VISUALIZATION_APPROXIMATE,
        "barrancabermeja": rg.VISUALIZATION_BLOCKED,
        "carimagua": rg.VISUALIZATION_BLOCKED,
    }
    for radar_id, visualization in expected.items():
        config = rg.get_radar_georef(radar_id)
        assert config.visualization == visualization
        assert rg.can_render_approximate(radar_id) is (visualization != rg.VISUALIZATION_BLOCKED)


def test_derived_radars_have_a_specific_warning():
    gua = rg.get_radar_georef("guaviare")
    mun = rg.get_radar_georef("munchique")
    assert "GeoTIFF histórico" in gua.approximate_warning
    assert "sin validación temporal" in gua.approximate_warning
    assert "10,5 km" in mun.approximate_warning
    assert "estación" in mun.approximate_warning


def test_derived_state_requires_warning():
    with pytest.raises(rg.GeorefError, match="approximate_warning"):
        rg.validate_georef(_valid_config(state=rg.STATE_DERIVED))


def test_assumed_state_cannot_declare_warning():
    with pytest.raises(rg.GeorefError, match="assumed"):
        rg.validate_georef(
            _valid_config(state=rg.STATE_ASSUMED, approximate_warning="no deberia")
        )


def test_require_renderable_blocks_assumed_radars():
    for radar_id in ("barrancabermeja", "carimagua"):
        with pytest.raises(rg.BlockedVisualizationError):
            rg.require_renderable(radar_id)
    for radar_id in ("guaviare", "munchique"):
        assert rg.require_renderable(radar_id).radar_id == radar_id


def test_public_metadata_is_safe_and_json_serializable():
    metadata = {radar_id: rg.public_metadata(radar_id) for radar_id in rg.radar_ids()}
    json.dumps(metadata)
    for radar_id in ("guaviare", "munchique"):
        item = metadata[radar_id]
        assert item["render_allowed"] is True
        assert item["state"] == rg.STATE_DERIVED
        assert item["overlay_enabled"] is False
        assert item["warning"]
        assert set(item["bounds"]) == {"west", "south", "east", "north"}
    for radar_id in ("barrancabermeja", "carimagua"):
        item = metadata[radar_id]
        assert item["render_allowed"] is False
        assert item["state"] == rg.STATE_ASSUMED
        assert item["overlay_enabled"] is False
        assert item["warning"] is None


def test_public_metadata_never_reports_verified_or_enabled():
    for radar_id in rg.radar_ids():
        item = rg.public_metadata(radar_id)
        assert item["state"] != rg.STATE_VERIFIED
        assert item["overlay_enabled"] is False
        assert item["visualization"] != rg.VISUALIZATION_EXACT


# ---------------------------------------------------------------------------
# Parser GeoTIFF
# ---------------------------------------------------------------------------

def test_pixel_is_point_shifts_bounds_by_half_pixel():
    area = rg.bounds_from_pixel_scale(4, 3, 1.0, 1.0, 10.0, 20.0)
    point = rg.bounds_from_pixel_scale(
        4, 3, 1.0, 1.0, 10.0, 20.0, raster_type="PixelIsPoint"
    )
    assert area.as_tuple() == (10.0, 17.0, 14.0, 20.0)
    assert point.as_tuple() == (9.5, 16.5, 14.5, 20.5)


def test_pixel_is_point_geotiff_is_shifted():
    data = _build_geotiff(scale=(1.0, 1.0), tiepoint=(10.0, 20.0, 0.0, 0.0, 0.0, 0.0), raster_type=2)
    parsed = rg.parse_geotiff_georef(data)
    assert parsed.raster_type == "PixelIsPoint"
    assert parsed.bounds.as_tuple() == (9.5, 16.5, 14.5, 20.5)


def test_big_endian_geotiff_is_supported():
    data = _build_geotiff(
        endian=">",
        scale=(2.0, 3.0),
        tiepoint=(-70.0, 5.0, 0.0, 0.0, 0.0, 0.0),
    )
    parsed = rg.parse_geotiff_georef(data)
    assert parsed.bounds.as_tuple() == (-70.0, -4.0, -62.0, 5.0)


def test_model_transformation_is_supported():
    matrix = [
        0.5, 0.0, 0.0, 10.0,
        0.0, -0.5, 0.0, 20.0,
        0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    data = _build_geotiff(width=4, height=2, scale=None, tiepoint=None, transformation=matrix)
    parsed = rg.parse_geotiff_georef(data)
    assert parsed.transformation is not None
    assert parsed.bounds.as_tuple() == (10.0, 19.0, 12.0, 20.0)


def test_geotiff_without_geokeys_is_rejected():
    data = _build_geotiff(include_geokeys=False)
    with pytest.raises(rg.UnsupportedGeoTiffError, match="GeoKeyDirectory"):
        rg.parse_geotiff_georef(data)


def test_geotiff_with_non_wgs84_epsg_is_rejected():
    data = _build_geotiff(epsg=3857)
    with pytest.raises(rg.UnsupportedGeoTiffError, match="EPSG:4326"):
        rg.parse_geotiff_georef(data)


def test_geotiff_without_georeference_tags_is_rejected():
    data = _build_geotiff(scale=None, tiepoint=None)
    with pytest.raises(rg.UnsupportedGeoTiffError, match="ModelPixelScale"):
        rg.parse_geotiff_georef(data)


def test_garbage_truncated_and_bigtiff_are_rejected():
    with pytest.raises(rg.UnsupportedGeoTiffError, match="orden de bytes"):
        rg.parse_geotiff_georef(b"not a tiff at all")
    with pytest.raises(rg.UnsupportedGeoTiffError):
        rg.parse_geotiff_georef(b"II*\x00\xff\xff\xff\x7f")
    with pytest.raises(rg.UnsupportedGeoTiffError, match="BigTIFF"):
        rg.parse_geotiff_georef(b"II+\x00\x08\x00\x00\x00")


def test_parse_is_deterministic():
    data = _build_geotiff(
        width=1992,
        height=1998,
        scale=(GUA_SCALE, GUA_SCALE),
        tiepoint=(GUA_TIE[0], GUA_TIE[1], 0.0, 0.0, 0.0, 0.0),
    )
    first = rg.parse_geotiff_georef(data).to_dict()
    second = rg.parse_geotiff_georef(data).to_dict()
    assert first == second


def test_read_geotiff_georef_roundtrip(tmp_path):
    path = tmp_path / "fixture.tif"
    path.write_bytes(_build_geotiff(scale=(1.0, 1.0), tiepoint=(10.0, 20.0, 0.0, 0.0, 0.0, 0.0)))
    parsed = rg.read_geotiff_georef(str(path))
    assert parsed.source == str(path)
    assert parsed.bounds.as_tuple() == (10.0, 17.0, 14.0, 20.0)


def test_read_geotiff_missing_file(tmp_path):
    with pytest.raises(rg.UnsupportedGeoTiffError, match="no se pudo leer"):
        rg.read_geotiff_georef(str(tmp_path / "nope.tif"))


# ---------------------------------------------------------------------------
# Validacion de bounds y configuracion
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "values",
    [
        (5.0, 0.0, 1.0, 1.0),
        (0.0, 5.0, 1.0, 1.0),
        (-181.0, 0.0, 1.0, 1.0),
        (0.0, -91.0, 1.0, 1.0),
        (float("nan"), 0.0, 1.0, 1.0),
        (float("inf"), 0.0, 1.0, 1.0),
        (True, 0.0, 1.0, 1.0),
    ],
)
def test_invalid_bounds_are_rejected(values):
    with pytest.raises(rg.InvalidBoundsError):
        rg.Bounds(*values)


def test_bounds_outside_colombia_are_rejected():
    with pytest.raises(rg.InvalidBoundsError, match="Colombia"):
        rg.validate_bounds((10.0, 40.0, 11.0, 41.0))
    assert rg.validate_bounds((10.0, 40.0, 11.0, 41.0), require_colombia=False)


def test_bounds_sequence_must_have_four_values():
    with pytest.raises(rg.InvalidBoundsError):
        rg.Bounds.from_sequence((1, 2, 3))
    with pytest.raises(rg.InvalidBoundsError):
        rg.Bounds.from_sequence("abcd")


def test_bounds_contains_and_intersects():
    box = rg.Bounds(-75.0, 0.0, -69.0, 5.0)
    assert box.contains(2.0, -72.0)
    assert not box.contains(2.0, -68.0)
    assert not box.contains(6.0, -72.0)
    assert box.intersects(rg.Bounds(-70.0, 4.0, -68.0, 6.0))
    assert not box.intersects(rg.Bounds(-68.0, 4.0, -67.0, 6.0))
    with pytest.raises(rg.InvalidBoundsError):
        box.contains("2", -72.0)


def test_hypothesis_rejects_invalid_inputs():
    with pytest.raises(rg.InvalidBoundsError):
        rg.hypothesis_bounds_from_center(4.0, -72.0, 0.0)
    with pytest.raises(rg.InvalidBoundsError):
        rg.hypothesis_bounds_from_center(95.0, -72.0)
    with pytest.raises(rg.InvalidBoundsError):
        rg.hypothesis_bounds_from_center(4.0, -72.0, "300")


def test_validate_georef_accepts_valid_config():
    config = rg.validate_georef(_valid_config())
    assert config.state == rg.STATE_ASSUMED
    assert config.readiness == rg.OVERLAY_BLOCKED


def test_validate_georef_accepts_bounds_mapping():
    config = rg.validate_georef(
        _valid_config(bounds={"west": -70.0, "south": 2.0, "east": -69.0, "north": 3.0})
    )
    assert config.bounds.as_tuple() == (-70.0, 2.0, -69.0, 3.0)


def test_validate_georef_rejects_missing_fields():
    bad = _valid_config()
    bad.pop("bounds")
    with pytest.raises(rg.GeorefError, match="faltan bounds"):
        rg.validate_georef(bad)


def test_validate_georef_rejects_unknown_fields():
    with pytest.raises(rg.GeorefError, match="desconocidos"):
        rg.validate_georef(_valid_config(foo="bar"))


def test_validate_georef_rejects_string_sequences():
    with pytest.raises(rg.GeorefError, match="secuencias"):
        rg.validate_georef(_valid_config(limitations="solo una"))


def test_validate_georef_rejects_empty_limitations():
    with pytest.raises(rg.GeorefError, match="limitacion"):
        rg.validate_georef(_valid_config(limitations=[]))


def test_validate_georef_rejects_incomplete_bounds_mapping():
    with pytest.raises(rg.InvalidBoundsError, match="bounds incompletos"):
        rg.validate_georef(
            _valid_config(bounds={"west": -70.0, "south": 2.0, "east": -69.0})
        )


def test_validate_georef_rejects_unknown_state():
    with pytest.raises(rg.GeorefError, match="estado invalido"):
        rg.validate_georef(_valid_config(state="probable"))


def test_overlay_readiness_rejects_unknown_state():
    with pytest.raises(rg.GeorefError):
        rg.overlay_readiness("maybe")


def test_non_verified_cannot_be_enabled():
    with pytest.raises(rg.GeorefError, match="overlay_enabled"):
        rg.validate_georef(
            _valid_config(
                state=rg.STATE_DERIVED,
                approximate_warning="aviso de prueba",
                overlay_enabled=True,
            )
        )


def test_verified_state_is_representable_but_absent_from_registry():
    config = rg.validate_georef(_valid_config(state=rg.STATE_VERIFIED, overlay_enabled=True))
    assert config.readiness == rg.OVERLAY_ELIGIBLE
    assert all(item.state != rg.STATE_VERIFIED for item in rg.RADAR_GEOREF.values())


# ---------------------------------------------------------------------------
# Comparacion de bounds (arnes de calibracion)
# ---------------------------------------------------------------------------

def test_compare_identical_bounds():
    box = rg.Bounds(-75.0, 0.0, -69.0, 5.0)
    result = rg.compare_bounds(box, box)
    assert result["iou"] == 1.0
    assert result["center_offset_km"] == 0.0
    assert all(value == 0.0 for value in result["edge_delta_km"].values())
    assert result["candidate_area_ratio"] == 1.0
    assert result["candidate_contains_reference_center"] is True


def test_compare_disjoint_bounds():
    result = rg.compare_bounds(rg.Bounds(-75.0, 0.0, -69.0, 5.0), rg.Bounds(-68.0, 10.0, -67.0, 11.0))
    assert result["intersection"] is None
    assert result["iou"] == 0.0


def test_compare_guaviare_vs_munchique_shows_no_common_extent():
    gua = rg.get_radar_georef("guaviare").bounds
    mun = rg.get_radar_georef("munchique").bounds
    result = rg.compare_bounds(gua, mun)
    assert 0.0 < result["iou"] < 0.8
    assert result["center_offset_km"] > 100.0


def test_compare_rejects_bounds_outside_colombia():
    with pytest.raises(rg.InvalidBoundsError):
        rg.compare_bounds(rg.Bounds(-75.0, 0.0, -69.0, 5.0), (0.0, 0.0, 1.0, 1.0))


# ---------------------------------------------------------------------------
# Aislamiento: sin red ni dependencias pesadas
# ---------------------------------------------------------------------------

def test_module_has_no_network_or_heavy_dependencies():
    import inspect

    source = inspect.getsource(rg)
    for forbidden in (
        "import requests",
        "import numpy",
        "import PIL",
        "import rasterio",
        "import socket",
        "urllib.request",
    ):
        assert forbidden not in source
    for attribute in ("requests", "numpy", "PIL", "rasterio"):
        assert not hasattr(rg, attribute)


def test_colombia_bbox_matches_open_meteo_client():
    from services import open_meteo_client as om

    assert rg.COLOMBIA_BBOX == om.COLOMBIA_BBOX


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_list_outputs_all_radars(capsys):
    assert rg.main(["--list"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["crs"] == "EPSG:4326"
    assert [item["radar_id"] for item in payload["radars"]] == list(rg.radar_ids())


def test_cli_radar_detail(capsys):
    assert rg.main(["--radar", "munchique"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["state"] == "derived"
    assert payload["readiness"] == "eligible_with_warning"


def test_cli_unknown_radar_returns_2(capsys):
    assert rg.main(["--radar", "nope"]) == 2
    assert "error:" in capsys.readouterr().err


def test_cli_geotiff_with_comparison(tmp_path, capsys):
    path = tmp_path / "gua.tif"
    path.write_bytes(
        _build_geotiff(
            width=1992,
            height=1998,
            scale=(GUA_SCALE, GUA_SCALE),
            tiepoint=(GUA_TIE[0], GUA_TIE[1], 0.0, 0.0, 0.0, 0.0),
        )
    )
    assert rg.main(["--geotiff", str(path), "--compare", "guaviare"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["comparison"]["iou"] == pytest.approx(1.0, abs=1e-6)
    assert payload["comparison"]["center_offset_km"] == pytest.approx(0.0, abs=0.01)


def test_cli_compare_requires_geotiff():
    with pytest.raises(SystemExit) as excinfo:
        rg.main(["--list", "--compare", "guaviare"])
    assert excinfo.value.code == 2
