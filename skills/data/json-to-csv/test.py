"""Tests for data.json-to-csv skill."""

from __future__ import annotations

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

import pytest

from skillforge.base import SkillInput

# Load worker directly from co-located file (avoids hyphenated-folder import issues)
_worker_path = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("json_to_csv_worker", _worker_path)
_mod = module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
Worker = _mod.Worker


@pytest.fixture
def worker():
    return Worker()


def test_basic_conversion(worker) -> None:
    inp = SkillInput(data={
        "records": [
            {"name": "Ali", "age": 30},
            {"name": "Ayşe", "age": 25},
        ]
    })
    out = worker.run(inp)
    assert out.success is True
    assert out.data["row_count"] == 2
    lines = out.data["csv"].strip().split("\n")
    assert len(lines) == 3  # header + 2 rows
    assert "Ali" in lines[1]


def test_nested_fields(worker) -> None:
    inp = SkillInput(data={
        "records": [
            {"patient": {"name": "Mehmet", "age": 40}, "status": "active"},
        ]
    })
    out = worker.run(inp)
    assert out.success is True
    assert "patient.name" in out.data["csv"]
    assert "Mehmet" in out.data["csv"]


def test_explicit_fields(worker) -> None:
    inp = SkillInput(data={
        "records": [{"a": 1, "b": 2, "c": 3}],
        "fields": ["a", "c"],
    })
    out = worker.run(inp)
    assert out.success is True
    assert "b" not in out.data["csv"].split("\n")[0]


def test_bom_excel_compat(worker) -> None:
    inp = SkillInput(data={
        "records": [{"x": 1}],
        "bom": True,
    })
    out = worker.run(inp)
    assert out.success is True
    assert out.data["csv"].startswith("\ufeff")


def test_empty_records(worker) -> None:
    inp = SkillInput(data={"records": []})
    out = worker.run(inp)
    assert out.success is False


def test_custom_delimiter(worker) -> None:
    inp = SkillInput(data={
        "records": [{"a": 1, "b": 2}],
        "delimiter": ";",
    })
    out = worker.run(inp)
    assert out.success is True
    assert ";" in out.data["csv"]
