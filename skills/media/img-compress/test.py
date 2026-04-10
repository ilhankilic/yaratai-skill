"""Tests for media.img-compress skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_img_compress_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_compression_info(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "quality": 85}))
    assert out.success and out.data["reduction_percent"] >= 0

def test_format_auto(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "format": "auto"}))
    assert out.success

def test_max_width(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "max_width": 800}))
    assert out.success

def test_strip_metadata(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_metadata": True}))
    assert out.success

def test_empty_input_error(w):
    out = w.run(SkillInput(data={"image_data": ""}))
    assert out.success is False
