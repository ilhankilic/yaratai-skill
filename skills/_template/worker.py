"""Template skill worker — copy this folder to create a new skill."""

from __future__ import annotations

import logging

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class Worker(BaseWorker):
    """Template worker that echoes the input back.

    Replace the contents of :meth:`run` with your own logic.
    """

    skill_id = "category.skill-name"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        """Process the input and return a result."""
        try:
            example_field: str = input.data.get("example_field", "")
            if not example_field:
                return SkillOutput(
                    success=False,
                    error="example_field is required",
                )

            return SkillOutput(
                success=True,
                data={"result": f"echo: {example_field}"},
                metadata={"skill_id": self.skill_id, "version": self.version},
            )

        except Exception as exc:
            logger.exception("Unexpected error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

