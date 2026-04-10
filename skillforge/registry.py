"""Skill discovery and registration for SkillForge."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

from skillforge.base import BaseWorker

logger = logging.getLogger("skillforge")

# Root skills directory (relative to repo root)
_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"

# In-memory cache — populated on first call, cleared with force=True.
_registry_cache: dict[str, type[BaseWorker]] | None = None


def discover_skills(
    root: Path | None = None,
    *,
    force: bool = False,
) -> dict[str, type[BaseWorker]]:
    """Walk the skills tree and return a mapping of *skill_id → Worker class*.

    Results are cached in memory after the first call.  Pass ``force=True``
    to rebuild the cache (e.g. after a sync operation).
    """
    global _registry_cache

    if _registry_cache is not None and not force and root is None:
        return _registry_cache

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

    # Store in cache when using the default root
    if root == _SKILLS_ROOT:
        _registry_cache = registry

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
    """Import *worker_file* and return the first BaseWorker subclass found.

    The module is registered in ``sys.modules`` so that
    :meth:`BaseWorker._skill_dir` (which uses ``inspect.getmodule``) can
    resolve back to the file and locate co-located ``schema.json`` / ``SKILL.md``.
    """
    # Build a unique module name from the relative path to avoid collisions
    # e.g. skills/data/json-to-csv/worker.py → skillforge._dyn.data.json_to_csv
    try:
        rel_parts = worker_file.parent.relative_to(_SKILLS_ROOT).parts
    except ValueError:
        rel_parts = (worker_file.parent.name,)
    mod_name = "skillforge._dyn." + ".".join(
        p.replace("-", "_") for p in rel_parts
    )

    spec = importlib.util.spec_from_file_location(mod_name, worker_file)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module  # register so inspect.getmodule() works
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

