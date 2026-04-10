"""Skill auto-generation via Claude API (Anthropic SDK)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

SKILL_CREATOR_PROMPT = """\
You are SkillForge's automatic skill generator.  Given a description, produce EXACTLY 4 files for a new skill.

Rules:
- The worker MUST subclass BaseWorker and implement run(self, input: SkillInput) -> SkillOutput
- Output shape: {success: bool, data: dict, error: str, metadata: dict}
- The skill must be stateless — no database, no global state
- Use Python logging, not print()
- Include type hints on every function
- schema.json must define input.required, input.properties, and output.properties
- test.py must have at least 3 test cases (happy path, edge case, error)
- SKILL.md must describe usage, input, and output tables

Return your response as a JSON object with these exact keys:
{
  "slug": "short-kebab-case-name",
  "schema.json": "...",
  "worker.py": "...",
  "SKILL.md": "...",
  "test.py": "..."
}

Return ONLY valid JSON — no markdown fences, no extra text.
"""


def generate_skill(
    description: str,
    category: str,
    api_key: str,
) -> dict[str, str]:
    """Call Claude API to generate the 4 skill files.

    Returns a dict with keys: ``_slug``, ``schema.json``, ``worker.py``,
    ``SKILL.md``, ``test.py``.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SKILL_CREATOR_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate a SkillForge skill for the following description:\n\n"
                    f"{description}\n\n"
                    f"Category: {category}\n"
                    f"skill_id format: {category}.<slug>"
                ),
            }
        ],
    )

    raw_text = message.content[0].text  # type: ignore[index]
    parsed = _parse_response(raw_text)

    return parsed


def _parse_response(raw: str) -> dict[str, str]:
    """Extract the JSON object from the API response."""
    # Try direct parse
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            obj["_slug"] = obj.pop("slug", "auto-skill")
            return obj
    except json.JSONDecodeError:
        pass

    # Try to find JSON inside markdown fences
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            obj = json.loads(match.group())
            if isinstance(obj, dict):
                obj["_slug"] = obj.pop("slug", "auto-skill")
                return obj
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse skill generation response:\n{raw[:500]}")

