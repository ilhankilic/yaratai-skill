"""Tests for ui.react-component skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ui_react_component_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_button_variant(w):
    out = w.run(SkillInput(data={"component_name": "MyButton", "variant": "button", "props": [{"name": "label", "type": "string", "required": True}]}))
    assert out.success and "MyButton" in out.data["component_code"]

def test_form_variant_has_state(w):
    out = w.run(SkillInput(data={"component_name": "LoginForm", "variant": "form"}))
    assert out.data["has_state"] is True and "useState" in out.data["component_code"]

def test_required_props(w):
    out = w.run(SkillInput(data={"component_name": "Card", "props": [{"name": "title", "type": "string", "required": True}]}))
    assert "title: string" in out.data["component_code"]

def test_optional_props_default(w):
    out = w.run(SkillInput(data={"component_name": "Badge", "props": [{"name": "color", "type": "string", "required": False, "default": "blue"}]}))
    assert "color?" in out.data["component_code"]

def test_invalid_variant_error(w):
    out = w.run(SkillInput(data={"component_name": "X", "variant": "nonexistent"}))
    assert out.success is False
