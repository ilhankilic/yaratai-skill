"""Tests for devops.k8s-manifest skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("devops_k8s_manifest_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_deployment(w):
    out = w.run(SkillInput(data={"app_name": "myapp", "image": "myapp:1.0", "port": 8080}))
    assert out.success and "deployment.yaml" in out.data["manifests"]

def test_secret_env(w):
    out = w.run(SkillInput(data={"app_name": "x", "image": "x:1", "port": 80, "env_vars": {"DB_PASSWORD": "secret123"}, "manifests": ["deployment", "secret"]}))
    assert "DB_PASSWORD" in out.data["secrets_detected"]

def test_service(w):
    out = w.run(SkillInput(data={"app_name": "x", "image": "x:1", "port": 80, "manifests": ["service"]}))
    assert "service.yaml" in out.data["manifests"]

def test_combined_yaml(w):
    out = w.run(SkillInput(data={"app_name": "x", "image": "x:1", "port": 80, "manifests": ["deployment", "service"]}))
    assert "---" in out.data["combined_yaml"]

def test_missing_fields_error(w):
    out = w.run(SkillInput(data={"app_name": "x"}))
    assert out.success is False
