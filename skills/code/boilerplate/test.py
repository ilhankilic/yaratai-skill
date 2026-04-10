"""Tests for code.boilerplate skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("boilerplate_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

def test_fastapi_minimal(w) -> None:
    out = w.run(SkillInput(data={"framework": "fastapi", "project_name": "myapi"}))
    assert out.success is True
    assert "app/main.py" in out.data["files"]
    assert "requirements.txt" in out.data["files"]

def test_fastapi_docker(w) -> None:
    out = w.run(SkillInput(data={"framework": "fastapi", "project_name": "myapi", "features": ["docker"]}))
    assert "Dockerfile" in out.data["files"]

def test_nextjs_minimal(w) -> None:
    out = w.run(SkillInput(data={"framework": "nextjs", "project_name": "mysite"}))
    assert out.success is True
    assert "package.json" in out.data["files"]
    assert "app/page.tsx" in out.data["files"]

def test_react_with_testing(w) -> None:
    out = w.run(SkillInput(data={"framework": "react", "project_name": "myapp", "features": ["testing"]}))
    assert out.success is True
    assert out.data["file_count"] > 0

def test_setup_commands(w) -> None:
    out = w.run(SkillInput(data={"framework": "express", "project_name": "myserver"}))
    assert out.success is True
    assert len(out.data["setup_commands"]) > 0

def test_unknown_framework_error(w) -> None:
    out = w.run(SkillInput(data={"framework": "django", "project_name": "x"}))
    assert out.success is False

