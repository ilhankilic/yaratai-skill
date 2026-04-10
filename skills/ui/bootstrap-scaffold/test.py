"""Tests for ui.bootstrap-scaffold skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ui_bootstrap_scaffold_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_hero_section(w):
    out = w.run(SkillInput(data={"page_title": "Test", "sections": [{"title": "Hero", "content": "Welcome", "type": "hero"}]}))
    assert out.success and "display-4" in out.data["html"]

def test_dark_theme(w):
    out = w.run(SkillInput(data={"page_title": "Test", "sections": [{"title": "X", "content": "Y", "type": "text"}], "theme": "dark"}))
    assert 'data-bs-theme="dark"' in out.data["html"]

def test_no_navbar(w):
    out = w.run(SkillInput(data={"page_title": "T", "sections": [{"title": "X", "content": "Y", "type": "text"}], "navbar": False}))
    assert "navbar" not in out.data["html"]

def test_multiple_sections(w):
    secs = [{"title": f"S{i}", "content": "c", "type": "text"} for i in range(3)]
    out = w.run(SkillInput(data={"page_title": "T", "sections": secs}))
    assert out.data["sections_count"] == 3

def test_empty_sections_error(w):
    out = w.run(SkillInput(data={"page_title": "T", "sections": []}))
    assert out.success is False
