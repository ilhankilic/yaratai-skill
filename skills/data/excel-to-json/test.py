"""Tests for data.excel-to-json skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("data_excel_to_json_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_basic_conversion(w):
    out = w.run(SkillInput(data={"data_rows": [["Ali", 30], ["Ayse", 25]], "headers": ["name", "age"]}))
    assert out.success and out.data["total_rows"] == 2

def test_multi_sheet(w):
    out = w.run(SkillInput(data={"data_rows": [["a"]], "headers": ["x"]}))
    assert "Sheet1" in out.data["sheet_names"]

def test_skip_empty(w):
    out = w.run(SkillInput(data={"data_rows": [["Ali", 30], [None, None], ["Ayse", 25]], "headers": ["name", "age"], "skip_empty_rows": True}))
    assert out.data["total_rows"] == 2

def test_auto_headers(w):
    out = w.run(SkillInput(data={"data_rows": [["a", "b"]]}))
    assert "col_0" in out.data["sheets"]["Sheet1"][0]

def test_empty_error(w):
    out = w.run(SkillInput(data={"data_rows": []}))
    assert out.success is False
