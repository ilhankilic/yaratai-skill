"""Tests for media.img-placeholder skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("media_img_placeholder_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_svg_output(w):
    out = w.run(SkillInput(data={"width": 300, "height": 200, "format": "svg"}))
    assert out.success and "<svg" in out.data["content"]

def test_png_output(w):
    out = w.run(SkillInput(data={"width": 100, "height": 100, "format": "png"}))
    assert out.success

def test_custom_text(w):
    out = w.run(SkillInput(data={"width": 200, "height": 100, "text": "Hello", "format": "svg"}))
    assert "Hello" in out.data["content"]

def test_auto_text(w):
    out = w.run(SkillInput(data={"width": 300, "height": 200, "format": "svg"}))
    assert "300x200" in out.data["content"]

def test_border(w):
    out = w.run(SkillInput(data={"width": 100, "height": 100, "format": "svg", "border": True}))
    assert "stroke" in out.data["content"]
