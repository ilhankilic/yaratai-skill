"""Tests for api.mock-server skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("api_mock_server_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_openapi_get(w):
    s = {"paths": {"/users": {"get": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi"}))
    assert out.success and out.data["endpoint_count"] == 1

def test_error_responses(w):
    s = {"paths": {"/items": {"post": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi", "include_errors": True}))
    assert any("404" in k for k in out.data["mock_files"])

def test_msw_handler(w):
    s = {"paths": {"/api": {"get": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi", "framework": "msw"}))
    assert "msw" in out.data["handler_code"]

def test_realistic_data(w):
    s = {"paths": {"/items": {"get": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi", "realistic_data": True}))
    assert out.success

def test_empty_schema_error(w):
    out = w.run(SkillInput(data={"schema": {}}))
    assert out.success is False
