"""Tests for data.shapefile-convert skill."""

from __future__ import annotations

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skillforge.base import SkillInput

try:
    import geopandas
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

_worker_path = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("shapefile_convert_worker", _worker_path)
_mod = module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
Worker = _mod.Worker


@pytest.fixture
def worker():
    return Worker()


def test_missing_file_path(worker) -> None:
    out = worker.run(SkillInput(data={}))
    assert out.success is False


@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
def test_unsupported_format(worker) -> None:
    out = worker.run(SkillInput(data={"file_path": "test.shp", "output_format": "xlsx"}))
    assert out.success is False
    assert "unsupported" in out.error.lower()


@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
def test_file_not_found(worker) -> None:
    out = worker.run(SkillInput(data={"file_path": "/nonexistent/test.shp"}))
    assert out.success is False
    assert "not found" in out.error.lower()


@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
def test_geojson_conversion(worker, tmp_path: Path) -> None:
    """Mock geopandas to verify GeoJSON output path."""
    mock_gdf = MagicMock()
    mock_gdf.crs = "EPSG:4326"
    mock_gdf.__len__ = MagicMock(return_value=5)
    mock_gdf.to_json.return_value = '{"type":"FeatureCollection","features":[]}'

    shp_file = tmp_path / "test.shp"
    shp_file.write_text("")  # just needs to exist

    with patch("geopandas.read_file", return_value=mock_gdf):
        out = worker.run(SkillInput(data={
            "file_path": str(shp_file),
            "output_format": "geojson",
        }))

    assert out.success is True
    assert out.data["feature_count"] == 5
    assert "FeatureCollection" in out.data["content"]


def test_geopandas_not_installed() -> None:
    """Graceful error when geopandas is missing."""
    with patch.dict("sys.modules", {"geopandas": None}):
        _spec2 = spec_from_file_location("shp_w2", _worker_path)
        _mod2 = module_from_spec(_spec2)  # type: ignore[arg-type]
        try:
            _spec2.loader.exec_module(_mod2)  # type: ignore[union-attr]
            w = _mod2.Worker()
            out = w.run(SkillInput(data={"file_path": "test.shp"}))
            assert out.success is False
            assert "geopandas" in out.error.lower()
        except ImportError:
            pass  # acceptable

