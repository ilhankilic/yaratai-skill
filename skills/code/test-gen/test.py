"""Tests for code.test-gen skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("test_gen_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

SOURCE = '''
def add(x: int, y: int) -> int:
    return x + y

def greet(name: str) -> str:
    if not name:
        raise ValueError("empty name")
    return f"Hello {name}"
'''

def test_happy_path_generated(w) -> None:
    out = w.run(SkillInput(data={"source_code": SOURCE}))
    assert out.success is True
    assert out.data["test_count"] >= 4
    assert "add" in out.data["functions_covered"]

def test_edge_case_generated(w) -> None:
    out = w.run(SkillInput(data={"source_code": SOURCE, "coverage_target": "full"}))
    assert "edge_case" in out.data["test_code"]

def test_exception_test(w) -> None:
    out = w.run(SkillInput(data={"source_code": SOURCE, "coverage_target": "full"}))
    assert "pytest.raises" in out.data["test_code"]

def test_mock_generated(w) -> None:
    code = "import httpx\ndef fetch(url: str) -> str:\n    return httpx.get(url).text\n"
    out = w.run(SkillInput(data={"source_code": code, "coverage_target": "full"}))
    assert out.data["mock_count"] >= 1

def test_fixture_usage(w) -> None:
    out = w.run(SkillInput(data={"source_code": SOURCE}))
    assert out.data["coverage_estimate"] > 0

def test_empty_source_error(w) -> None:
    out = w.run(SkillInput(data={"source_code": ""}))
    assert out.success is False

