"""Tests for js.dead-code skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("js_dead_code_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_unused_function(w):
    code = "function unused() { return 1; }\nfunction used() { return unused(); }\nconsole.log(used());"
    out = w.run(SkillInput(data={"code": code}))
    assert out.success

def test_unused_import(w):
    code = "import { useState } from 'react';\nimport { useEffect } from 'react';\nconst App = () => useState();"
    out = w.run(SkillInput(data={"code": code}))
    assert out.success
    assert any(i["name"] == "useEffect" for i in out.data["unused_imports"])

def test_exported_function_skipped(w):
    code = "export function helper() { return 1; }"
    out = w.run(SkillInput(data={"code": code}))
    assert len(out.data["unused_functions"]) == 0

def test_underscore_prefix_skipped(w):
    code = "function _internal() { return 1; }"
    out = w.run(SkillInput(data={"code": code}))
    assert len(out.data["unused_functions"]) == 0

def test_clean_code_output(w):
    code = "import { unused } from 'lib';\nconsole.log('hello');"
    out = w.run(SkillInput(data={"code": code}))
    assert "import" not in out.data["clean_code"] or "unused" not in out.data["clean_code"]
