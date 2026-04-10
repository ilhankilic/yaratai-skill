"""Tests for media.img-resize-batch skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_img_resize_batch_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_contain_mode(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "width": 100, "fit_mode": "contain"}))
    assert out.success

def test_cover_mode(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "width": 100, "fit_mode": "cover"}))
    assert out.success

def test_width_only(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "width": 200, "fit_mode": "width_only"}))
    assert out.success

def test_batch_count(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}, {"data": "dGVzdA=="}], "width": 100}))
    assert out.data["success_count"] == 2

def test_empty_images_error(w):
    out = w.run(SkillInput(data={"images": []}))
    assert out.success is False
