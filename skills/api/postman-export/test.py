"""Tests for api.postman-export skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("api_postman_export_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

SCHEMA = {"paths": {"/users": {"get": {"summary": "List users"}}, "/users/{id}": {"get": {"summary": "Get user"}}}}

def test_openapi_conversion(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "TestAPI", "base_url": "https://api.test.com"}))
    assert out.success and out.data["request_count"] == 2

def test_test_scripts(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "T", "base_url": "http://x", "include_tests": True}))
    assert "pm.test" in out.data["collection_json"]

def test_auth_added(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "T", "base_url": "http://x", "include_auth": True}))
    assert "bearer" in out.data["collection_json"]

def test_environment_generated(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "T", "base_url": "http://x"}))
    assert "base_url" in out.data["environment_json"]

def test_missing_fields_error(w):
    out = w.run(SkillInput(data={"source": {}}))
    assert out.success is False
