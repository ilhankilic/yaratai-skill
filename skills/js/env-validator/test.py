"""Tests for js.env-validator skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("js_env_validator_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_missing_required(w):
    out = w.run(SkillInput(data={"env_content": "DEBUG=true", "schema": {"DATABASE_URL": {"required": True}}}))
    assert "DATABASE_URL" in out.data["missing_required"]

def test_wrong_url_format(w):
    out = w.run(SkillInput(data={"env_content": "DB_URL=not-a-url", "schema": {"DB_URL": {"type": "url"}}}))
    assert len(out.data["type_errors"]) > 0

def test_weak_secret(w):
    out = w.run(SkillInput(data={"env_content": "SECRET_KEY=password", "check_secrets": True}))
    assert len(out.data["weak_secrets"]) > 0

def test_boolean_type(w):
    out = w.run(SkillInput(data={"env_content": "DEBUG=maybe", "schema": {"DEBUG": {"type": "boolean"}}}))
    assert any(e["key"] == "DEBUG" for e in out.data["type_errors"])

def test_valid_env(w):
    out = w.run(SkillInput(data={"env_content": "PORT=3000\nDEBUG=true", "schema": {"PORT": {"required": True, "type": "integer"}}}))
    assert out.data["valid"] is True
