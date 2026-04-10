"""GitHub sync — pull community skills and validate them against SkillForge standard."""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("skillforge.sync")

# Resolve repo root by looking for pyproject.toml, falling back to __file__ based path
def _find_repo_root() -> Path:
    """Walk up from this file to find the repo root (contains pyproject.toml)."""
    candidate = Path(__file__).resolve().parent
    for _ in range(5):
        if (candidate / "pyproject.toml").exists():
            return candidate
        candidate = candidate.parent
    return Path(__file__).resolve().parent.parent

REPO_ROOT = _find_repo_root()
SKILLS_ROOT = REPO_ROOT / "skills"
COMMUNITY_DIR = SKILLS_ROOT / "community"

REQUIRED_FILES = {"schema.json", "worker.py", "SKILL.md", "test.py"}


@dataclass
class SyncResult:
    """Outcome of a sync or import operation."""
    success: bool
    message: str
    skills_added: list[str] = field(default_factory=list)
    skills_updated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Outcome of validating a skill directory against SkillForge standard."""
    valid: bool
    skill_id: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_skill_directory(skill_dir: Path) -> ValidationResult:
    """Check that *skill_dir* contains the required 4-file quartet and follows conventions.

    This is the gatekeeper — no skill enters the registry without passing this.
    """
    errors: list[str] = []
    warnings: list[str] = []
    skill_id = ""

    # 1. Check required files
    existing = {f.name for f in skill_dir.iterdir() if f.is_file()}
    missing = REQUIRED_FILES - existing
    if missing:
        errors.append(f"Missing required files: {', '.join(sorted(missing))}")

    # 2. Validate schema.json
    schema_path = skill_dir / "schema.json"
    if schema_path.exists():
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            skill_id = schema.get("skill_id", "")
            if not skill_id:
                errors.append("schema.json missing 'skill_id'")
            if "input" not in schema:
                errors.append("schema.json missing 'input' definition")
            if "output" not in schema:
                warnings.append("schema.json missing 'output' definition")
        except json.JSONDecodeError as e:
            errors.append(f"schema.json is not valid JSON: {e}")

    # 3. Validate worker.py basics (static check, no exec)
    worker_path = skill_dir / "worker.py"
    if worker_path.exists():
        code = worker_path.read_text(encoding="utf-8")
        if "BaseWorker" not in code:
            errors.append("worker.py does not reference BaseWorker")
        if "def run(" not in code:
            errors.append("worker.py missing run() method")
        if "print(" in code:
            warnings.append("worker.py uses print() — use logging instead")
        if "sqlite" in code.lower() or "redis" in code.lower():
            errors.append("worker.py references forbidden storage (DB)")

    # 4. Validate test.py basics
    test_path = skill_dir / "test.py"
    if test_path.exists():
        test_code = test_path.read_text(encoding="utf-8")
        test_count = test_code.count("def test_")
        if test_count < 3:
            warnings.append(f"test.py has only {test_count} test(s) — minimum 3 recommended")

    return ValidationResult(
        valid=len(errors) == 0,
        skill_id=skill_id,
        errors=errors,
        warnings=warnings,
    )


def sync_from_github(repo_url: str, branch: str = "main") -> SyncResult:
    """Clone a remote repo, validate skills inside it, and copy valid ones to community/.

    Only skills under ``skills/`` in the remote repo are considered.
    """
    try:
        import git
    except ImportError:
        return SyncResult(
            success=False,
            message="gitpython is not installed.",
        )

    added: list[str] = []
    updated: list[str] = []
    sync_errors: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            logger.info("Cloning %s (branch: %s)…", repo_url, branch)
            repo = git.Repo.clone_from(repo_url, tmpdir, branch=branch, depth=1)
        except Exception as e:
            return SyncResult(success=False, message=f"Clone failed: {e}")

        remote_skills = Path(tmpdir) / "skills"
        if not remote_skills.exists():
            return SyncResult(success=False, message="Remote repo has no skills/ directory.")

        # Walk every potential skill directory (depth 2: category/skill-name)
        for category_dir in sorted(remote_skills.iterdir()):
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue
            for skill_dir in sorted(category_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue

                result = validate_skill_directory(skill_dir)
                if not result.valid:
                    sync_errors.append(
                        f"{skill_dir.name}: {'; '.join(result.errors)}"
                    )
                    continue

                # Copy to community/<category>/<skill-name>
                target = COMMUNITY_DIR / category_dir.name / skill_dir.name
                is_update = target.exists()

                if is_update:
                    shutil.rmtree(target)

                shutil.copytree(skill_dir, target)

                if is_update:
                    updated.append(result.skill_id or skill_dir.name)
                else:
                    added.append(result.skill_id or skill_dir.name)

                logger.info(
                    "%s skill: %s",
                    "Updated" if is_update else "Added",
                    result.skill_id,
                )

    total = len(added) + len(updated)
    return SyncResult(
        success=total > 0 or len(sync_errors) == 0,
        message=f"Synced {total} skill(s) ({len(added)} new, {len(updated)} updated). {len(sync_errors)} error(s).",
        skills_added=added,
        skills_updated=updated,
        errors=sync_errors,
    )


def import_skill_from_url(repo_url: str, skill_path: str, branch: str = "main") -> SyncResult:
    """Import a single skill from a specific path in a GitHub repo.

    Example: import_skill_from_url("https://github.com/user/repo", "skills/data/my-skill")
    """
    try:
        import git
    except ImportError:
        return SyncResult(success=False, message="gitpython is not installed.")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            git.Repo.clone_from(repo_url, tmpdir, branch=branch, depth=1)
        except Exception as e:
            return SyncResult(success=False, message=f"Clone failed: {e}")

        source = Path(tmpdir) / skill_path
        if not source.exists() or not source.is_dir():
            return SyncResult(success=False, message=f"Path '{skill_path}' not found in repo.")

        result = validate_skill_directory(source)
        if not result.valid:
            return SyncResult(
                success=False,
                message=f"Validation failed: {'; '.join(result.errors)}",
                errors=result.errors,
            )

        # Derive target from the last two path components
        parts = Path(skill_path).parts
        if len(parts) >= 2:
            category, name = parts[-2], parts[-1]
        else:
            category, name = "community", parts[-1]

        target = COMMUNITY_DIR / category / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)

        return SyncResult(
            success=True,
            message=f"Imported {result.skill_id or name} to {target.relative_to(REPO_ROOT)}",
            skills_added=[result.skill_id or name],
        )

