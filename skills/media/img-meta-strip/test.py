"""Tests for media.img-meta-strip skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_img_meta_strip_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_strip_all(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "all"}))
    assert out.success

def test_gps_detection(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "all"}))
    assert "had_gps" in out.data

def test_selective(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "selective", "keep_fields": ["Orientation"]}))
    assert out.success

def test_report(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "all", "report_before": True}))
    assert out.success

def test_empty_error(w):
    out = w.run(SkillInput(data={"image_data": ""}))
    assert out.success is False
