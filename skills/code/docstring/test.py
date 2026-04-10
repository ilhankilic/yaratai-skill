"""Tests for code.docstring skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("docstring_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

SIMPLE_FUNC = "def add(x: int, y: int) -> int:\n    return x + y\n"
CLASS_CODE = "class Foo:\n    def bar(self, x: str) -> None:\n        pass\n"

def test_simple_function_google(w) -> None:
    out = w.run(SkillInput(data={"source_code": SIMPLE_FUNC, "style": "google"}))
    assert out.success is True
    assert "Args:" in out.data["documented_code"]
    assert out.data["functions_documented"] == 1

def test_class_method(w) -> None:
    out = w.run(SkillInput(data={"source_code": CLASS_CODE}))
    assert out.success is True
    assert out.data["classes_documented"] >= 1

def test_existing_docstring_skipped(w) -> None:
    code = 'def foo():\n    """Existing."""\n    pass\n'
    out = w.run(SkillInput(data={"source_code": code, "overwrite_existing": False}))
    assert out.success is True
    assert out.data["functions_skipped"] == 1

def test_numpy_style(w) -> None:
    out = w.run(SkillInput(data={"source_code": SIMPLE_FUNC, "style": "numpy"}))
    assert "Parameters" in out.data["documented_code"]

def test_type_hints_inferred(w) -> None:
    out = w.run(SkillInput(data={"source_code": SIMPLE_FUNC}))
    assert "int" in out.data["documented_code"]

def test_empty_source_error(w) -> None:
    out = w.run(SkillInput(data={"source_code": ""}))
    assert out.success is False

