"""Tests for devops.dockerfile-gen skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("devops_dockerfile_gen_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_python_api(w):
    out = w.run(SkillInput(data={"dependency_file": "fastapi\nuvicorn", "file_type": "requirements_txt"}))
    assert out.success and "python" in out.data["base_image_used"]

def test_node_web(w):
    out = w.run(SkillInput(data={"dependency_file": '{"dependencies":{}}', "file_type": "package_json"}))
    assert "node" in out.data["base_image_used"]

def test_port_expose(w):
    out = w.run(SkillInput(data={"dependency_file": "flask", "file_type": "requirements_txt", "expose_port": 5000}))
    assert "EXPOSE 5000" in out.data["dockerfile"]

def test_non_root_user(w):
    out = w.run(SkillInput(data={"dependency_file": "flask", "file_type": "requirements_txt", "non_root_user": True}))
    assert "appuser" in out.data["dockerfile"]

def test_health_check(w):
    out = w.run(SkillInput(data={"dependency_file": "flask", "file_type": "requirements_txt", "health_check": True}))
    assert "HEALTHCHECK" in out.data["dockerfile"]
