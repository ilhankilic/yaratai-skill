"""Tests for the skill validation and sync engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillforge.sync import validate_skill_directory, ValidationResult


@pytest.fixture
def valid_skill(tmp_path: Path) -> Path:
    """Create a minimal valid skill directory."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()

    (skill_dir / "schema.json").write_text(json.dumps({
        "skill_id": "test.valid-skill",
        "version": "1.0.0",
        "input": {"type": "object", "required": ["msg"], "properties": {"msg": {"type": "string"}}},
        "output": {"type": "object", "properties": {"echo": {"type": "string"}}},
    }), encoding="utf-8")

    (skill_dir / "worker.py").write_text("""
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "test.valid-skill"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        return SkillOutput(success=True, data={"echo": input.data.get("msg", "")})
""", encoding="utf-8")

    (skill_dir / "SKILL.md").write_text("# test.valid-skill\nA test skill.\n", encoding="utf-8")

    (skill_dir / "test.py").write_text("""
import pytest
from skillforge.base import SkillInput

def test_happy():
    from importlib.util import spec_from_file_location, module_from_spec
    from pathlib import Path
    assert True

def test_edge():
    assert True

def test_error():
    assert True
""", encoding="utf-8")

    return skill_dir


@pytest.fixture
def invalid_skill(tmp_path: Path) -> Path:
    """Create a skill directory missing required files."""
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir()
    (skill_dir / "worker.py").write_text("print('hello')", encoding="utf-8")
    return skill_dir


def test_valid_skill_passes(valid_skill: Path) -> None:
    result = validate_skill_directory(valid_skill)
    assert result.valid is True
    assert result.skill_id == "test.valid-skill"
    assert len(result.errors) == 0


def test_missing_files_detected(invalid_skill: Path) -> None:
    result = validate_skill_directory(invalid_skill)
    assert result.valid is False
    assert any("Missing required files" in e for e in result.errors)


def test_db_usage_detected(tmp_path: Path) -> None:
    """worker.py referencing sqlite should fail validation."""
    skill_dir = tmp_path / "db-skill"
    skill_dir.mkdir()

    (skill_dir / "schema.json").write_text(json.dumps({
        "skill_id": "test.db-skill",
        "input": {"type": "object", "required": [], "properties": {}},
        "output": {"type": "object", "properties": {}},
    }), encoding="utf-8")

    (skill_dir / "worker.py").write_text("""
import sqlite3
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "test.db-skill"
    version = "1.0.0"
    def run(self, input: SkillInput) -> SkillOutput:
        conn = sqlite3.connect(':memory:')
        return SkillOutput(success=True)
""", encoding="utf-8")

    (skill_dir / "SKILL.md").write_text("# db-skill\n", encoding="utf-8")
    (skill_dir / "test.py").write_text("def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n", encoding="utf-8")

    result = validate_skill_directory(skill_dir)
    assert result.valid is False
    assert any("DB" in e or "storage" in e.lower() for e in result.errors)


def test_missing_schema_skill_id(tmp_path: Path) -> None:
    skill_dir = tmp_path / "no-id"
    skill_dir.mkdir()

    (skill_dir / "schema.json").write_text(json.dumps({
        "input": {"type": "object", "required": [], "properties": {}},
    }), encoding="utf-8")
    (skill_dir / "worker.py").write_text("""
from skillforge.base import BaseWorker, SkillInput, SkillOutput
class Worker(BaseWorker):
    skill_id = ""
    version = "1.0.0"
    def run(self, input: SkillInput) -> SkillOutput:
        return SkillOutput(success=True)
""", encoding="utf-8")
    (skill_dir / "SKILL.md").write_text("# no-id\n", encoding="utf-8")
    (skill_dir / "test.py").write_text("def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n", encoding="utf-8")

    result = validate_skill_directory(skill_dir)
    assert result.valid is False
    assert any("skill_id" in e for e in result.errors)


def test_print_usage_warned(valid_skill: Path) -> None:
    """Rewrite worker.py with print() → should produce warning, not error."""
    (valid_skill / "worker.py").write_text("""
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "test.print-skill"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        print("debug")
        return SkillOutput(success=True, data={})
""", encoding="utf-8")

    result = validate_skill_directory(valid_skill)
    assert result.valid is True  # print is a warning, not an error
    assert any("print" in w for w in result.warnings)

