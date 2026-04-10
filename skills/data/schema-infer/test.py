"""Tests for data.schema-infer skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("data_schema_infer_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_simple_object(w):
    data = [{"name": "Ali", "age": 30}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert out.success and out.data["field_count"] == 2

def test_nested_object(w):
    data = [{"user": {"name": "Ali"}, "score": 10}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert out.data["schema"]["properties"]["user"]["type"] == "object"

def test_array_items(w):
    data = [{"tags": ["a", "b"]}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert out.data["schema"]["properties"]["tags"]["type"] == "array"

def test_email_format_detected(w):
    data = [{"email": "ali@test.com"}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert "email" in out.data["detected_formats"]

def test_required_threshold(w):
    data = [{"name": "Ali", "age": 30}, {"name": "Ayse"}]
    out = w.run(SkillInput(data={"sample_data": data, "required_threshold": 0.5}))
    assert "name" in out.data["schema"]["required"]
