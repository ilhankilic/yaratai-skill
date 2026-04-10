"""Tests for devops.github-actions skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("devops_github_actions_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_python_test_workflow(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": ["test"]}))
    assert out.success and ".github/workflows/test.yml" in out.data["workflows"]

def test_docker_build(w):
    out = w.run(SkillInput(data={"project_type": "docker", "workflows": ["build"]}))
    assert "REGISTRY" in out.data["secrets_required"]

def test_multi_version_matrix(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": ["test"], "python_versions": ["3.10", "3.11", "3.12"]}))
    assert "3.10" in out.data["workflows"][".github/workflows/test.yml"]

def test_security_workflow(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": ["security"]}))
    assert "bandit" in out.data["workflows"][".github/workflows/security.yml"]

def test_empty_workflows_error(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": []}))
    assert out.success is False
