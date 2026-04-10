"""Tests for ai.synthetic-data skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("ai_synthetic_data_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

SCHEMA = {"properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 18, "maximum": 65}, "email": {"type": "string", "format": "email"}}}

def test_batch_generation(w):
    out = w.run(SkillInput(data={"schema": SCHEMA, "example_count": 5}))
    assert out.success and out.data["actual_count"] == 5

def test_schema_compliance(w):
    out = w.run(SkillInput(data={"schema": SCHEMA, "example_count": 3}))
    assert out.data["schema_compliance_rate"] == 1.0

def test_turkish_data(w):
    out = w.run(SkillInput(data={"schema": SCHEMA, "example_count": 1, "language": "tr"}))
    assert out.success

def test_integer_range(w):
    out = w.run(SkillInput(data={"schema": {"properties": {"score": {"type": "integer", "minimum": 0, "maximum": 10}}}, "example_count": 10}))
    assert all(0 <= item["score"] <= 10 for item in out.data["generated_data"])

def test_empty_schema_error(w):
    out = w.run(SkillInput(data={"schema": {}, "example_count": 5}))
    assert out.success is False
