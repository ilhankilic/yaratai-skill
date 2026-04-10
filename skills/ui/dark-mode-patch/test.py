"""Tests for ui.dark-mode-patch skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ui_dark_mode_patch_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_css_media_query(w):
    css = "body { background: #ffffff; color: #000000; }"
    out = w.run(SkillInput(data={"source": css, "source_type": "css", "strategy": "media_query"}))
    assert "prefers-color-scheme: dark" in out.data["patched_source"]

def test_css_class_strategy(w):
    css = "body { background: #ffffff; }"
    out = w.run(SkillInput(data={"source": css, "source_type": "css", "strategy": "class"}))
    assert ".dark" in out.data["patched_source"]

def test_custom_color_mapping(w):
    css = "a { color: #ff0000; }"
    out = w.run(SkillInput(data={"source": css, "source_type": "css", "color_mapping": {"#ff0000": "#cc0000"}}))
    assert out.data["colors_patched"] >= 1

def test_tailwind_html(w):
    html = '<div class="bg-white">test</div>'
    out = w.run(SkillInput(data={"source": html, "source_type": "tailwind_html"}))
    assert out.success

def test_empty_source_error(w):
    out = w.run(SkillInput(data={"source": ""}))
    assert out.success is False
