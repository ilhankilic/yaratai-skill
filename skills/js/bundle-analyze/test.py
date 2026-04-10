"""Tests for js.bundle-analyze skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("js_bundle_analyze_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_moment_detection(w):
    pkg = {"dependencies": {"moment": "^2.29.4", "react": "^18"}}
    out = w.run(SkillInput(data={"package_json": pkg}))
    assert out.success and any(h["name"] == "moment" for h in out.data["heavy_packages"])

def test_unused_package(w):
    pkg = {"dependencies": {"react": "^18", "lodash": "^4"}}
    out = w.run(SkillInput(data={"package_json": pkg, "import_list": ["react"]}))
    assert "lodash" in out.data["unused_packages"]

def test_clean_package_high_score(w):
    pkg = {"dependencies": {"react": "^18", "next": "^14"}}
    out = w.run(SkillInput(data={"package_json": pkg}))
    assert out.data["score"] == 100

def test_empty_deps(w):
    out = w.run(SkillInput(data={"package_json": {"dependencies": {}}}))
    assert out.success and out.data["score"] == 100

def test_empty_pkg_error(w):
    out = w.run(SkillInput(data={"package_json": {}}))
    assert out.success is False
