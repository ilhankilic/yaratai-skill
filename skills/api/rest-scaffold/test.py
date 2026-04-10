"""Tests for api.rest-scaffold skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("api_rest_scaffold_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

SCHEMA = {"paths": {"/users": {"get": {"operationId": "list_users"}}, "/users/{id}": {"get": {"operationId": "get_user"}}}}

def test_get_endpoint(w):
    out = w.run(SkillInput(data={"openapi_schema": SCHEMA}))
    assert out.success and out.data["endpoint_count"] == 2

def test_post_validation(w):
    s = {"paths": {"/items": {"post": {"operationId": "create_item"}}}}
    out = w.run(SkillInput(data={"openapi_schema": s, "include_validation": True}))
    assert out.data["endpoint_count"] == 1

def test_auth_endpoint(w):
    out = w.run(SkillInput(data={"openapi_schema": SCHEMA, "include_auth": True}))
    assert "Depends" in out.data["files"].get("routes.py", "")

def test_express_framework(w):
    out = w.run(SkillInput(data={"openapi_schema": SCHEMA, "framework": "express"}))
    assert "routes.js" in out.data["files"]

def test_empty_schema_error(w):
    out = w.run(SkillInput(data={"openapi_schema": {}}))
    assert out.success is False
