"""GitHub sync endpoints — pull and import skills from remote repos."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from skillforge.sync import (
    SyncResult,
    ValidationResult,
    import_skill_from_url,
    sync_from_github,
    validate_skill_directory,
    SKILLS_ROOT,
)

logger = logging.getLogger("skillforge.api.sync")

router = APIRouter()


class SyncRequest(BaseModel):
    """POST body for GitHub repo sync."""
    repo_url: str = Field(..., description="GitHub repo URL to sync skills from")
    branch: str = Field("main", description="Git branch to sync")


class ImportRequest(BaseModel):
    """POST body for single-skill import."""
    repo_url: str = Field(..., description="GitHub repo URL")
    skill_path: str = Field(..., description="Path to skill dir inside repo, e.g. skills/data/my-tool")
    branch: str = Field("main", description="Git branch")


class ValidateRequest(BaseModel):
    """POST body for validating a local skill directory."""
    skill_path: str = Field(..., description="Relative path under skills/, e.g. data/json-to-csv")


@router.post("/github")
async def sync_github(request: SyncRequest) -> dict[str, Any]:
    """Sync all valid skills from a remote GitHub repository."""
    result: SyncResult = sync_from_github(request.repo_url, request.branch)
    return {
        "success": result.success,
        "message": result.message,
        "skills_added": result.skills_added,
        "skills_updated": result.skills_updated,
        "errors": result.errors,
    }


@router.post("/import")
async def import_skill(request: ImportRequest) -> dict[str, Any]:
    """Import a single skill from a GitHub repository path."""
    result: SyncResult = import_skill_from_url(
        request.repo_url, request.skill_path, request.branch
    )
    return {
        "success": result.success,
        "message": result.message,
        "skills_added": result.skills_added,
        "errors": result.errors,
    }


@router.post("/validate")
async def validate_local_skill(request: ValidateRequest) -> dict[str, Any]:
    """Validate a local skill directory against SkillForge standard."""
    skill_dir = SKILLS_ROOT / request.skill_path
    if not skill_dir.exists():
        return {"valid": False, "errors": [f"Directory not found: {request.skill_path}"]}

    result: ValidationResult = validate_skill_directory(skill_dir)
    return {
        "valid": result.valid,
        "skill_id": result.skill_id,
        "errors": result.errors,
        "warnings": result.warnings,
    }

