"""Pipeline orchestration for SkillForge — sequential & parallel skill execution."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from skillforge.base import SkillInput, SkillOutput
from skillforge.registry import load_skill

logger = logging.getLogger("skillforge")


class PipelineMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


@dataclass
class PipelineStep:
    """A single step inside a pipeline definition."""

    skill_id: str
    node: str = "local"          # "local" | "cloud"
    condition: str = ""          # optional condition expression
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineDefinition:
    """A full pipeline parsed from a YAML file."""

    name: str
    mode: PipelineMode = PipelineMode.SEQUENTIAL
    pipe: bool = False           # when True, each step's output feeds the next input
    steps: list[PipelineStep] = field(default_factory=list)


# ── YAML loading ─────────────────────────────────────────────────────

def load_pipeline(path: Path) -> PipelineDefinition:
    """Parse a pipeline YAML file into a :class:`PipelineDefinition`."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    steps = [
        PipelineStep(
            skill_id=s["skill_id"],
            node=s.get("node", "local"),
            condition=s.get("condition", ""),
            params=s.get("params", {}),
        )
        for s in raw.get("steps", [])
    ]
    return PipelineDefinition(
        name=raw.get("name", path.stem),
        mode=PipelineMode(raw.get("mode", "sequential")),
        pipe=raw.get("pipe", False),
        steps=steps,
    )


# ── Execution ────────────────────────────────────────────────────────

def run_pipeline(definition: PipelineDefinition, input: SkillInput) -> list[SkillOutput]:
    """Execute a pipeline synchronously (delegates to async internally)."""
    return asyncio.run(_run_pipeline_async(definition, input))


async def _run_pipeline_async(
    definition: PipelineDefinition,
    input: SkillInput,
) -> list[SkillOutput]:
    if definition.mode == PipelineMode.PARALLEL:
        return await _run_parallel(definition, input)
    return await _run_sequential(definition, input)


async def _run_sequential(
    definition: PipelineDefinition,
    input: SkillInput,
) -> list[SkillOutput]:
    results: list[SkillOutput] = []
    current_input = input

    for step in definition.steps:
        if step.condition and not _evaluate_condition(step.condition, results):
            logger.info("Skipping step %s (condition not met)", step.skill_id)
            continue

        worker = load_skill(step.skill_id)
        logger.info("Running step: %s", step.skill_id)
        output = worker.run(current_input)
        results.append(output)

        # Pipe mode: feed output.data as next input.data
        if definition.pipe and output.success:
            current_input = SkillInput(data=output.data, metadata=output.metadata)

    return results


async def _run_parallel(
    definition: PipelineDefinition,
    input: SkillInput,
) -> list[SkillOutput]:
    async def _exec(step: PipelineStep) -> SkillOutput:
        worker = load_skill(step.skill_id)
        return worker.run(input)

    tasks = [_exec(step) for step in definition.steps if not step.condition]
    return list(await asyncio.gather(*tasks))


def _evaluate_condition(condition: str, previous_results: list[SkillOutput]) -> bool:
    """Very simple condition evaluator.

    Supported patterns:
      - ``"previous.success"`` — last step succeeded
      - ``"previous.data.<key> == <value>"`` — simple equality check
    """
    if not previous_results:
        return False

    last = previous_results[-1]

    if condition.strip() == "previous.success":
        return last.success

    if "==" in condition:
        lhs, rhs = (s.strip().strip('"').strip("'") for s in condition.split("==", 1))
        if lhs.startswith("previous.data."):
            key = lhs.replace("previous.data.", "")
            return str(last.data.get(key, "")) == rhs

    logger.warning("Unrecognised condition: %s — defaulting to True", condition)
    return True

