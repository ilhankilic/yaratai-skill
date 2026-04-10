"""Tests for media.img-to-webp skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_img_to_webp_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_jpeg_to_webp(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA==", "format": "jpeg"}]}))
    assert out.success

def test_lossless(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "lossless": True}))
    assert out.success

def test_quality(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "quality": 90}))
    assert out.success

def test_batch(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}, {"data": "dGVzdA=="}]}))
    assert out.data["total_count"] == 2

def test_empty_error(w):
    out = w.run(SkillInput(data={"images": []}))
    assert out.success is False
