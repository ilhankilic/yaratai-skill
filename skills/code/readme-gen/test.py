"""Tests for code.readme-gen skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("readme_gen_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

INFO = {"name": "TestProject", "description": "A test project.", "language": "python",
        "features": ["auth", "docker"], "installation_steps": ["pip install -e ."],
        "env_vars": {"SECRET_KEY": "App secret"}, "license": "MIT"}

def test_minimal_style(w) -> None:
    out = w.run(SkillInput(data={"project_info": INFO, "style": "minimal"}))
    assert out.success is True
    assert "# TestProject" in out.data["readme_content"]

def test_detailed_style(w) -> None:
    out = w.run(SkillInput(data={"project_info": INFO, "style": "detailed", "include_contributing": True}))
    assert "Contributing" in out.data["readme_content"]

def test_turkish_language(w) -> None:
    out = w.run(SkillInput(data={"project_info": INFO, "language": "tr"}))
    assert "Kurulum" in out.data["readme_content"]

def test_badge_generation(w) -> None:
    out = w.run(SkillInput(data={"project_info": INFO, "include_badges": True}))
    assert out.data["has_badges"] is True
    assert "shields.io" in out.data["readme_content"]

def test_env_vars_table(w) -> None:
    out = w.run(SkillInput(data={"project_info": INFO, "style": "standard"}))
    assert "SECRET_KEY" in out.data["readme_content"]

def test_empty_info_error(w) -> None:
    out = w.run(SkillInput(data={"project_info": {}}))
    assert out.success is False

