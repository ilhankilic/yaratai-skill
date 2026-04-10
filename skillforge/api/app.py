"""SkillForge FastAPI application — serves skills via REST and the management panel."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from skillforge.api.routes import health, skills, sync, panel

logger = logging.getLogger("skillforge.api")

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup / shutdown tasks."""
    logger.info("SkillForge API starting — discovering skills…")
    from skillforge.registry import discover_skills

    registry = discover_skills()
    logger.info("Loaded %d skills", len(registry))
    yield
    logger.info("SkillForge API shutting down.")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="SkillForge",
        description="Stateless AI skill runtime — Docker-ready, agent-friendly.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── Routes ───────────────────────────────────────────────────────
    app.include_router(health.router, tags=["health"])
    app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
    app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
    app.include_router(panel.router, tags=["panel"])

    # ── Static files ─────────────────────────────────────────────────
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()

