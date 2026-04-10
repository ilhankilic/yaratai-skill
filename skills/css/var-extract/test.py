"""Tests for css.var-extract skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("css_var_extract_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_color_extraction(w):
    css = "a { color: #ff0000; } b { color: #ff0000; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.success and out.data["extracted_count"] >= 1
    assert "var(" in out.data["converted_css"]

def test_size_extraction(w):
    css = "a { padding: 16px; } b { margin: 16px; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.data["extracted_count"] >= 1

def test_min_occurrences_3(w):
    css = "a { color: #abc; } b { color: #abc; }"
    out = w.run(SkillInput(data={"css": css, "min_occurrences": 3}))
    assert out.data["extracted_count"] == 0

def test_custom_prefix(w):
    css = "a { color: #000; } b { color: #000; }"
    out = w.run(SkillInput(data={"css": css, "prefix": "--my"}))
    assert "--my" in out.data["variables_css"]

def test_empty_css_error(w):
    out = w.run(SkillInput(data={"css": ""}))
    assert out.success is False
