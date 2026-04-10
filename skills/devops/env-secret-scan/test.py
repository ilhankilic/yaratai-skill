"""Tests for devops.env-secret-scan skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("devops_env_secret_scan_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_aws_key_detection(w):
    out = w.run(SkillInput(data={"files": [{"path": "a.py", "content": "key = 'AKIAIOSFODNN7EXAMPLE'"}]}))
    assert out.data["critical_count"] >= 1

def test_jwt_detection(w):
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    out = w.run(SkillInput(data={"files": [{"path": "a.js", "content": f"token = '{jwt}'"}]}))
    assert out.data["high_count"] >= 1

def test_whitelist(w):
    out = w.run(SkillInput(data={"files": [{"path": "a.py", "content": "key = 'AKIAIOSFODNN7EXAMPLE'"}], "whitelist_patterns": ["EXAMPLE"]}))
    assert out.data["critical_count"] == 0

def test_severity_filter(w):
    out = w.run(SkillInput(data={"files": [{"path": "a.py", "content": "key = 'AKIAIOSFODNN7EXAMPLE'"}], "severity_filter": "high"}))
    assert out.data["critical_count"] == 0

def test_clean_file(w):
    out = w.run(SkillInput(data={"files": [{"path": "clean.py", "content": "x = 1 + 2"}]}))
    assert out.data["clean_files"] == 1 and len(out.data["findings"]) == 0
