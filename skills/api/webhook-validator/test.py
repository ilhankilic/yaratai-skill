"""Tests for api.webhook-validator skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("api_webhook_validator_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

import hashlib, hmac, json
from skillforge.base import SkillInput

def test_valid_payload(w):
    out = w.run(SkillInput(data={"payload": {"event": "push", "action": "created"}}))
    assert out.success and out.data["valid"] is True

def test_schema_error(w):
    schema = {"required": ["event"], "properties": {}}
    out = w.run(SkillInput(data={"payload": {"action": "created"}, "schema": schema}))
    assert not out.data["valid"]

def test_valid_hmac(w):
    secret = "mysecret"
    payload = {"event": "push"}
    sig = "sha256=" + hmac.new(secret.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    out = w.run(SkillInput(data={"payload": payload, "signature": sig, "secret": secret}))
    assert out.data["signature_valid"] is True

def test_invalid_hmac(w):
    out = w.run(SkillInput(data={"payload": {"x": 1}, "signature": "sha256=invalid", "secret": "s"}))
    assert out.data["signature_valid"] is False

def test_github_provider(w):
    out = w.run(SkillInput(data={"payload": {"action": "opened"}, "provider": "github"}))
    assert out.data["provider_specific"]["has_action"] is True
