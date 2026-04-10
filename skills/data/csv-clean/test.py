"""Tests for data.csv-clean skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("data_csv_clean_worker", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

from skillforge.base import SkillInput

def test_remove_empty_rows(w):
    csv = "name,age\nAli,30\n,\nAyse,25"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["remove_empty"]}))
    assert out.success and out.data["cleaned_rows"] == 2

def test_remove_duplicates(w):
    csv = "name,age\nAli,30\nAli,30\nAyse,25"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["remove_duplicates"]}))
    assert out.data["cleaned_rows"] == 2

def test_trim_whitespace(w):
    csv = "name,age\n  Ali  ,30\nAyse,25"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["trim_whitespace"]}))
    assert "  Ali  " not in out.data["cleaned_csv"]

def test_normalize_dates(w):
    csv = "name,date\nAli,15/01/2024\nAyse,20/02/2024"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["normalize_dates"], "date_columns": ["date"]}))
    assert "2024-01-15" in out.data["cleaned_csv"]

def test_combined_operations(w):
    csv = "name,age\n  Ali  ,30\n,\nAli,30"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["trim_whitespace", "remove_empty", "remove_duplicates"]}))
    assert out.data["removed_rows"] >= 1
