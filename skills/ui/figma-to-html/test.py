"""Tests for ui.figma-to-html skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ui_figma_to_html_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_text_node(w):
    out = w.run(SkillInput(data={"figma_json": {"type": "TEXT", "name": "title", "characters": "Hello", "style": {"fontSize": 32}}}))
    assert out.success and "<h1>" in out.data["html"]

def test_rectangle(w):
    out = w.run(SkillInput(data={"figma_json": {"type": "RECTANGLE", "name": "box", "style": {"width": 200, "height": 100}}}))
    assert "200px" in out.data["html"]

def test_nested_frame(w):
    figma = {"type": "FRAME", "name": "container", "style": {}, "children": [
        {"type": "TEXT", "name": "t", "characters": "Hi", "style": {"fontSize": 16}}
    ]}
    out = w.run(SkillInput(data={"figma_json": figma}))
    assert out.data["node_count"] == 2

def test_auto_layout(w):
    figma = {"type": "FRAME", "name": "row", "style": {"layoutMode": "HORIZONTAL"}, "children": []}
    out = w.run(SkillInput(data={"figma_json": figma}))
    assert "flex-direction: row" in out.data["css"]

def test_unsupported_node(w):
    out = w.run(SkillInput(data={"figma_json": {"type": "VECTOR", "name": "v", "style": {}}}))
    assert "VECTOR" in out.data["unsupported_nodes"]
