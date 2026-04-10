"""Tests for js.eslint-autofix skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("js_eslint_autofix_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_react_config(w):
    out = w.run(SkillInput(data={"code_samples": ["const App = () => {}"], "framework": "react"}))
    assert "react-hooks/rules-of-hooks" in out.data["eslintrc"]["rules"]

def test_node_config(w):
    out = w.run(SkillInput(data={"code_samples": ["const fs = require('fs')"], "framework": "node"}))
    assert out.success

def test_typescript_strict(w):
    out = w.run(SkillInput(data={"code_samples": ["let x: number = 1"], "typescript": True}))
    assert "@typescript-eslint/no-explicit-any" in out.data["eslintrc"]["rules"]

def test_merge_existing(w):
    existing = {"rules": {"semi": "error"}, "extends": ["eslint:recommended"]}
    out = w.run(SkillInput(data={"code_samples": ["x"], "existing_eslintrc": existing}))
    assert "semi" in out.data["merged_eslintrc"]["rules"]

def test_empty_samples_error(w):
    out = w.run(SkillInput(data={"code_samples": []}))
    assert out.success is False
