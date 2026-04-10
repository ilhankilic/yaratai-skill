"""Base classes for SkillForge workers and standard I/O models."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("skillforge")


# ── Standard I/O Models ─────────────────────────────────────────────

class SkillInput(BaseModel):
    """Standard input envelope for every skill invocation."""

    data: dict[str, Any] = Field(default_factory=dict, description="Skill-specific input payload")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional contextual metadata")


class SkillOutput(BaseModel):
    """Standard output envelope returned by every skill."""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Base Worker ──────────────────────────────────────────────────────

class BaseWorker(ABC):
    """Abstract base class that every SkillForge worker must subclass.

    Subclasses must set ``skill_id`` and ``version`` class attributes and
    implement the :meth:`run` method.
    """

    skill_id: str = ""
    version: str = "0.0.0"

    # ── public API ───────────────────────────────────────────────────

    @abstractmethod
    def run(self, input: SkillInput) -> SkillOutput:
        """Execute the skill logic.  Must be implemented by subclasses."""
        ...

    def validate(self, input: SkillInput) -> list[str]:
        """Validate *input* against the co-located ``schema.json``.

        Returns a list of human-readable validation error strings.
        An empty list means the input is valid.
        """
        schema_path = self._schema_path()
        if schema_path is None or not schema_path.exists():
            logger.warning("schema.json not found for %s – skipping validation", self.skill_id)
            return []

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors: list[str] = []

        required_fields: list[str] = schema.get("input", {}).get("required", [])
        properties: dict[str, Any] = schema.get("input", {}).get("properties", {})

        for field_name in required_fields:
            if field_name not in input.data:
                errors.append(f"Missing required field: {field_name}")

        for field_name, value in input.data.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type and not _type_matches(value, expected_type):
                    errors.append(
                        f"Field '{field_name}' expected type '{expected_type}', "
                        f"got '{type(value).__name__}'"
                    )

        return errors

    def describe(self) -> dict[str, Any]:
        """Return a description dict suitable for ``skillforge list`` and the dashboard.

        Includes ``category`` (parsed from *skill_id*) and ``description``
        (read from the co-located ``schema.json``).
        """
        info: dict[str, Any] = {
            "skill_id": self.skill_id,
            "version": self.version,
            "category": self.skill_id.split(".")[0] if "." in self.skill_id else "",
        }

        # Title from SKILL.md first line
        skill_md = self._skill_md_path()
        if skill_md is not None and skill_md.exists():
            text = skill_md.read_text(encoding="utf-8")
            first_line = text.strip().splitlines()[0] if text.strip() else ""
            info["title"] = first_line.lstrip("# ").strip()

        # Description from schema.json
        schema_path = self._schema_path()
        if schema_path is not None and schema_path.exists():
            try:
                schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
                info["description"] = schema_data.get("description", "")
            except (json.JSONDecodeError, OSError):
                pass

        return info

    # ── private helpers ──────────────────────────────────────────────

    def _skill_dir(self) -> Path | None:
        """Resolve the directory of the concrete worker module."""
        import inspect

        module = inspect.getmodule(type(self))
        if module and module.__file__:
            return Path(module.__file__).resolve().parent
        return None

    def _schema_path(self) -> Path | None:
        d = self._skill_dir()
        return d / "schema.json" if d else None

    def _skill_md_path(self) -> Path | None:
        d = self._skill_dir()
        return d / "SKILL.md" if d else None


# ── helpers ──────────────────────────────────────────────────────────

_JSON_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


def _type_matches(value: Any, json_type: str) -> bool:
    """Check whether *value* conforms to the JSON-Schema *json_type*."""
    expected = _JSON_TYPE_MAP.get(json_type)
    if expected is None:
        return True  # unknown type → allow
    return isinstance(value, expected)

