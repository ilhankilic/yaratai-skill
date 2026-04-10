"""Core unit tests for SkillForge base classes and registry."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from skillforge.base import BaseWorker, SkillInput, SkillOutput


# ── SkillInput / SkillOutput ─────────────────────────────────────────

class TestSkillIO:
    def test_input_defaults(self) -> None:
        inp = SkillInput()
        assert inp.data == {}
        assert inp.metadata == {}

    def test_output_success(self) -> None:
        out = SkillOutput(success=True, data={"key": "val"})
        assert out.success is True
        assert out.error == ""

    def test_output_failure(self) -> None:
        out = SkillOutput(success=False, error="something broke")
        assert out.success is False
        assert out.error == "something broke"

    def test_output_json_shape(self) -> None:
        out = SkillOutput(success=True, data={"a": 1}, metadata={"t": 0.5})
        d = out.model_dump()
        assert set(d.keys()) == {"success", "data", "error", "metadata"}


# ── BaseWorker ───────────────────────────────────────────────────────

class _DummyWorker(BaseWorker):
    skill_id = "test.dummy"
    version = "0.1.0"

    def run(self, input: SkillInput) -> SkillOutput:
        return SkillOutput(success=True, data={"echo": input.data})


class TestBaseWorker:
    def test_run(self) -> None:
        w = _DummyWorker()
        out = w.run(SkillInput(data={"x": 1}))
        assert out.success is True
        assert out.data["echo"] == {"x": 1}

    def test_describe(self) -> None:
        w = _DummyWorker()
        desc = w.describe()
        assert desc["skill_id"] == "test.dummy"
        assert desc["version"] == "0.1.0"

    def test_abstract_enforcement(self) -> None:
        with pytest.raises(TypeError):
            BaseWorker()  # type: ignore[abstract]


# ── Registry ─────────────────────────────────────────────────────────

class TestRegistry:
    def test_discover_returns_dict(self, tmp_path: Path) -> None:
        from skillforge.registry import discover_skills

        result = discover_skills(tmp_path)
        assert isinstance(result, dict)
        assert len(result) == 0  # empty dir → no skills

    def test_discover_with_skill(self, tmp_path: Path) -> None:
        from skillforge.registry import discover_skills

        skill_dir = tmp_path / "demo" / "echo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "worker.py").write_text(
            textwrap.dedent("""\
                from skillforge.base import BaseWorker, SkillInput, SkillOutput

                class Worker(BaseWorker):
                    skill_id = "demo.echo"
                    version = "1.0.0"
                    def run(self, input: SkillInput) -> SkillOutput:
                        return SkillOutput(success=True, data=input.data)
            """),
            encoding="utf-8",
        )

        reg = discover_skills(skill_dir.parent.parent)
        assert "demo.echo" in reg

