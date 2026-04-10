"""Tests for ui.tailwind-layout skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ui_tailwind_layout_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_margin_padding(w):
    html = '<div style="margin: 0; padding: 0">test</div>'
    out = w.run(SkillInput(data={"html": html}))
    assert out.success and "m-0" in out.data["converted_html"]

def test_flex_layout(w):
    html = '<div style="display: flex; justify-content: center">x</div>'
    out = w.run(SkillInput(data={"html": html}))
    assert "flex" in out.data["converted_html"]

def test_inline_style_removal(w):
    html = '<p style="text-align: center">hi</p>'
    out = w.run(SkillInput(data={"html": html, "remove_inline_styles": True}))
    assert 'style=' not in out.data["converted_html"]

def test_dark_mode(w):
    html = '<div style="display: flex">x</div>'
    out = w.run(SkillInput(data={"html": html, "add_dark_mode": True}))
    assert "dark:flex" in out.data["converted_html"]

def test_empty_html_error(w):
    out = w.run(SkillInput(data={"html": ""}))
    assert out.success is False
