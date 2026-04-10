"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from skillforge import __version__

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return service health and version info."""
    from skillforge.registry import discover_skills

    registry = discover_skills()
    return {
        "status": "healthy",
        "version": __version__,
        "skills_loaded": len(registry),
    }

