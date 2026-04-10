"""Tests for css.minify skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("css_minify_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_comment_removal(w):
    out = w.run(SkillInput(data={"css": "/* comment */ body { color: red; }"}))
    assert out.success and "comment" not in out.data["minified"]

def test_whitespace_collapse(w):
    out = w.run(SkillInput(data={"css": "body {\n  color:  red;\n}"}))
    assert "  " not in out.data["minified"]

def test_color_shorthand(w):
    out = w.run(SkillInput(data={"css": "a { color: #ffffff; }"}))
    assert "#fff" in out.data["minified"]

def test_size_calculation(w):
    css = "body { margin: 0px; padding: 0px; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.data["gzip_size_bytes"] > 0
    assert out.data["reduction_percent"] >= 0

def test_empty_css_error(w):
    out = w.run(SkillInput(data={"css": ""}))
    assert out.success is False
