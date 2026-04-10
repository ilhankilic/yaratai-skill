"""Tests for code.env-template skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("env_template_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

PY_CODE = '''
import os
DB_URL = os.environ["DATABASE_URL"]
SECRET = os.getenv("SECRET_KEY", "changeme")
DEBUG = os.environ.get("DEBUG", "false")
'''

def test_os_getenv_detection(w) -> None:
    out = w.run(SkillInput(data={"source_files": [{"path": "app.py", "content": PY_CODE}]}))
    assert out.success is True
    assert out.data["variable_count"] == 3
    assert any(v["name"] == "SECRET_KEY" for v in out.data["variables"])

def test_default_value_extracted(w) -> None:
    out = w.run(SkillInput(data={"source_files": [{"path": "a.py", "content": PY_CODE}]}))
    sk = next(v for v in out.data["variables"] if v["name"] == "SECRET_KEY")
    assert sk["default"] == "changeme"

def test_grouping(w) -> None:
    out = w.run(SkillInput(data={"source_files": [{"path": "a.py", "content": PY_CODE}]}))
    assert "# Database" in out.data["template"]

def test_merge_existing_env(w) -> None:
    out = w.run(SkillInput(data={
        "source_files": [{"path": "a.py", "content": PY_CODE}],
        "existing_env": "DATABASE_URL=postgres://localhost/db",
    }))
    db = next(v for v in out.data["variables"] if v["name"] == "DATABASE_URL")
    assert db["default"] == "postgres://localhost/db"

def test_yaml_format(w) -> None:
    out = w.run(SkillInput(data={
        "source_files": [{"path": "a.py", "content": PY_CODE}],
        "output_format": "yaml",
    }))
    assert "DATABASE_URL:" in out.data["template"]

def test_empty_files_error(w) -> None:
    out = w.run(SkillInput(data={"source_files": []}))
    assert out.success is False

