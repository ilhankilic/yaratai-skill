"""Skill listing, execution, and info endpoints."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from skillforge.base import SkillInput, SkillOutput
from skillforge.registry import load_skill, list_skills

logger = logging.getLogger("skillforge.api")

router = APIRouter()


# ── Request / Response models ────────────────────────────────────────

class RunRequest(BaseModel):
    """POST body for /api/skills/{skill_id}/run."""
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillInfo(BaseModel):
    """Detailed skill information."""
    skill_id: str
    version: str
    title: str = ""
    description: str = ""
    schema_input: dict[str, Any] = Field(default_factory=dict)
    schema_output: dict[str, Any] = Field(default_factory=dict)
    skill_md: str = ""


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("")
async def get_skills(
    category: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List all registered skills, optionally filtered by category or search term."""
    results = list_skills(category=category)
    if search:
        q = search.lower()
        results = [
            s for s in results
            if q in s.get("skill_id", "").lower()
            or q in s.get("title", "").lower()
            or q in s.get("description", "").lower()
        ]
    return results


@router.get("/{skill_id:path}/info")
async def get_skill_info(skill_id: str) -> SkillInfo:
    """Return detailed info for a skill including schema and SKILL.md."""
    try:
        worker = load_skill(skill_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found.")

    desc = worker.describe()

    # Read schema.json
    schema_data: dict[str, Any] = {}
    schema_path = worker._schema_path()
    if schema_path and schema_path.exists():
        schema_data = json.loads(schema_path.read_text(encoding="utf-8"))

    # Read SKILL.md
    skill_md_text = ""
    skill_md_path = worker._skill_md_path()
    if skill_md_path and skill_md_path.exists():
        skill_md_text = skill_md_path.read_text(encoding="utf-8")

    return SkillInfo(
        skill_id=desc.get("skill_id", skill_id),
        version=desc.get("version", "0.0.0"),
        title=desc.get("title", ""),
        description=schema_data.get("description", ""),
        schema_input=schema_data.get("input", {}),
        schema_output=schema_data.get("output", {}),
        skill_md=skill_md_text,
    )


@router.post("/{skill_id:path}/run")
async def run_skill(skill_id: str, request: RunRequest) -> dict[str, Any]:
    """Execute a skill and return the result."""
    try:
        worker = load_skill(skill_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found.")

    skill_input = SkillInput(data=request.data, metadata=request.metadata)

    # Validate
    errors = worker.validate(skill_input)

    # Execute
    result: SkillOutput = worker.run(skill_input)

    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "metadata": result.metadata,
        "validation_warnings": errors,
    }

