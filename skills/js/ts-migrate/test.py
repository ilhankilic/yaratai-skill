"""Tests for js.ts-migrate skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("js_ts_migrate_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_var_to_const(w):
    out = w.run(SkillInput(data={"js_code": "var x = 1;"}))
    assert "const" in out.data["ts_code"]

def test_function_types(w):
    out = w.run(SkillInput(data={"js_code": 'function greet(name = "world") { return name; }'}))
    assert "string" in out.data["ts_code"]

def test_require_to_import(w):
    out = w.run(SkillInput(data={"js_code": "const fs = require('fs');"}))
    assert "import" in out.data["ts_code"]

def test_module_exports(w):
    out = w.run(SkillInput(data={"js_code": "module.exports = App;"}))
    assert "export default" in out.data["ts_code"]

def test_empty_code_error(w):
    out = w.run(SkillInput(data={"js_code": ""}))
    assert out.success is False
