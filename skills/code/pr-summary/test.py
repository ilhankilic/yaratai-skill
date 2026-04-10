"""Tests for code.pr-summary skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("pr_summary_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

DIFF = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,5 @@
+from fastapi import FastAPI
+
 def hello():
     return "world"
+def new_feature():
+    return True
"""

def test_new_feature_diff(w) -> None:
    out = w.run(SkillInput(data={"diff": DIFF, "branch_name": "feature/add-login"}))
    assert out.success is True
    assert "add login" in out.data["title"]

def test_bug_fix_diff(w) -> None:
    fix_diff = "diff --git a/fix.py b/fix.py\n--- a/fix.py\n+++ b/fix.py\n@@ -1 +1 @@\n-broken\n+fixed\n"
    out = w.run(SkillInput(data={"diff": fix_diff}))
    assert out.success is True

def test_config_change_labels(w) -> None:
    cfg_diff = "diff --git a/.env b/.env\n--- a/.env\n+++ b/.env\n@@ -1 +1 @@\n-OLD\n+NEW\n"
    out = w.run(SkillInput(data={"diff": cfg_diff}))
    assert "config" in out.data["labels"]

def test_breaking_change_detected(w) -> None:
    schema_diff = "diff --git a/schema.json b/schema.json\n--- a/schema.json\n+++ b/schema.json\n@@ -1 +1 @@\n-old\n+new\n"
    out = w.run(SkillInput(data={"diff": schema_diff}))
    assert len(out.data["breaking_changes"]) > 0

def test_empty_diff_error(w) -> None:
    out = w.run(SkillInput(data={"diff": ""}))
    assert out.success is False

