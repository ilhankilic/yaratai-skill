"""Tests for css.bem-converter skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("css_bem_converter_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_nested_selector(w):
    css = ".card .title { font-size: 16px; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.success and "card__title" in out.data["converted_css"]

def test_hover_state(w):
    css = ".btn:hover { opacity: 0.8; }"
    out = w.run(SkillInput(data={"css": css}))
    assert "btn--hover" in out.data["converted_css"]

def test_html_conversion(w):
    css = ".card .title { color: red; }"
    html = '<div class="card"><h2 class="title">Hi</h2></div>'
    out = w.run(SkillInput(data={"css": css, "html": html}))
    assert "card__title" in out.data["converted_html"]

def test_dry_run(w):
    css = ".card .title { color: red; }"
    out = w.run(SkillInput(data={"css": css, "dry_run": True}))
    assert out.data["suggestions_count"] > 0
    assert ".card .title" in out.data["converted_css"]  # unchanged

def test_empty_css_error(w):
    out = w.run(SkillInput(data={"css": ""}))
    assert out.success is False
