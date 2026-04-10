"""Tests for code.regex-builder skill."""

from __future__ import annotations

from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

import pytest

from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("regex_builder_worker", _wp)
_mod = module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
Worker = _mod.Worker


@pytest.fixture
def w():
    return Worker()


def test_email_regex(w) -> None:
    out = w.run(SkillInput(data={
        "description": "email address",
        "examples_match": ["ali@test.com", "user.name+tag@domain.co"],
        "examples_no_match": ["not-an-email", "@no-user.com"],
    }))
    assert out.success is True
    assert all(r["passed"] for r in out.data["test_results"])
    assert "email" in out.data["explanation"].lower()


def test_turkish_phone(w) -> None:
    out = w.run(SkillInput(data={
        "description": "Türkçe telefon numarası",
        "examples_match": ["+90 532 123 45 67", "05321234567"],
        "examples_no_match": ["12345", "abc"],
    }))
    assert out.success is True
    assert all(r["passed"] for r in out.data["test_results"])


def test_date_pattern(w) -> None:
    out = w.run(SkillInput(data={
        "description": "ISO date format",
        "examples_match": ["2024-01-15", "2023-12-31"],
        "examples_no_match": ["15-01-2024", "2024/01/15"],
    }))
    assert out.success is True
    assert all(r["passed"] for r in out.data["test_results"])


def test_named_groups(w) -> None:
    out = w.run(SkillInput(data={
        "description": "email",
        "named_groups": True,
    }))
    assert out.success is True
    assert "?P<" in out.data["pattern"]


def test_match_no_match_validation(w) -> None:
    out = w.run(SkillInput(data={
        "description": "hex color",
        "examples_match": ["#fff", "#aabbcc"],
        "examples_no_match": ["#gggggg", "red"],
    }))
    assert out.success is True
    for r in out.data["test_results"]:
        assert r["passed"] is True


def test_javascript_usage(w) -> None:
    out = w.run(SkillInput(data={
        "description": "uuid",
        "language": "javascript",
    }))
    assert out.success is True
    assert "const regex" in out.data["usage_example"]


def test_empty_description_error(w) -> None:
    out = w.run(SkillInput(data={"description": ""}))
    assert out.success is False
    assert "description" in out.error.lower()

