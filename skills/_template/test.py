"""Tests for the template skill."""

import pytest

from skillforge.base import SkillInput, SkillOutput

# Import is done lazily so the template doesn't collide with real skills
from skills._template.worker import Worker


@pytest.fixture
def worker() -> Worker:
    return Worker()


def test_happy_path(worker: Worker) -> None:
    """Valid input should return success with echoed data."""
    inp = SkillInput(data={"example_field": "hello"})
    out = worker.run(inp)
    assert out.success is True
    assert out.data["result"] == "echo: hello"


def test_missing_required_field(worker: Worker) -> None:
    """Missing required field should return success=False."""
    inp = SkillInput(data={})
    out = worker.run(inp)
    assert out.success is False
    assert "required" in out.error.lower()


def test_metadata_present(worker: Worker) -> None:
    """Output metadata should include skill_id and version."""
    inp = SkillInput(data={"example_field": "test"})
    out = worker.run(inp)
    assert out.metadata["skill_id"] == "category.skill-name"
    assert out.metadata["version"] == "1.0.0"

