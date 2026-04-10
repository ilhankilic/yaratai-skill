"""Skill discovery and registration for SkillForge."""

from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any

from skillforge.base import BaseWorker

logger = logging.getLogger("skillforge")

# Root skills directory (relative to repo root)
_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"


def discover_skills(root: Path | None = None) -> dict[str, type[BaseWorker]]:
    """Walk the skills tree and return a mapping of *skill_id → Worker class*.

    Each valid skill directory must contain a ``worker.py`` that defines
    a class inheriting from :class:`BaseWorker` with a non-empty ``skill_id``.
    """
    root = root or _SKILLS_ROOT
    registry: dict[str, type[BaseWorker]] = {}

    if not root.exists():
        logger.warning("Skills root not found: %s", root)
        return registry

    for worker_file in sorted(root.rglob("worker.py")):
        if worker_file.parent.name.startswith("_"):
            continue  # skip _template and similar
        try:
            cls = _load_worker_class(worker_file)
            if cls and cls.skill_id:
                registry[cls.skill_id] = cls
                logger.debug("Registered skill: %s", cls.skill_id)
        except Exception:
            logger.exception("Failed to load worker: %s", worker_file)

    return registry


def load_skill(skill_id: str, root: Path | None = None) -> BaseWorker:
    """Return an *instantiated* worker for *skill_id*.

    Raises ``KeyError`` if the skill is not found.
    """
    registry = discover_skills(root)
    if skill_id not in registry:
        available = ", ".join(sorted(registry)) or "(none)"
        raise KeyError(f"Skill '{skill_id}' not found. Available: {available}")
    return registry[skill_id]()


def list_skills(category: str | None = None, root: Path | None = None) -> list[dict[str, Any]]:
    """Return a list of skill description dicts, optionally filtered by *category*."""
    registry = discover_skills(root)
    results: list[dict[str, Any]] = []
    for sid, cls in sorted(registry.items()):
        if category and not sid.startswith(f"{category}."):
            continue
        worker = cls()
        results.append(worker.describe())
    return results


# ── private helpers ──────────────────────────────────────────────────

def _load_worker_class(worker_file: Path) -> type[BaseWorker] | None:
    """Import *worker_file* and return the first BaseWorker subclass found."""
    spec = importlib.util.spec_from_file_location(
        f"skillforge._dyn.{worker_file.parent.name}",
        worker_file,
    )
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseWorker)
            and obj is not BaseWorker
        ):
            return obj
    return None

