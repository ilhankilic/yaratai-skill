"""data.json-to-csv — Convert a JSON array to CSV text."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class Worker(BaseWorker):
    """Convert JSON records to CSV with nested field (dot notation) support."""

    skill_id = "data.json-to-csv"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            records: list[dict[str, Any]] = input.data.get("records", [])
            if not records:
                return SkillOutput(success=False, error="'records' must be a non-empty array.")

            fields: list[str] = input.data.get("fields", [])
            delimiter: str = input.data.get("delimiter", ",")
            bom: bool = input.data.get("bom", False)

            # Flatten records
            flat_records = [_flatten(r) for r in records]

            # Determine columns
            if not fields:
                seen: dict[str, None] = {}
                for rec in flat_records:
                    for k in rec:
                        seen.setdefault(k, None)
                fields = list(seen)

            # Write CSV
            buf = io.StringIO()
            if bom:
                buf.write("\ufeff")
            writer = csv.DictWriter(
                buf,
                fieldnames=fields,
                delimiter=delimiter,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            for rec in flat_records:
                writer.writerow(rec)

            csv_text = buf.getvalue()

            return SkillOutput(
                success=True,
                data={"csv": csv_text, "row_count": len(flat_records)},
                metadata={"skill_id": self.skill_id, "fields": fields},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))


def _flatten(obj: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten nested dict using dot notation keys."""
    items: dict[str, Any] = {}
    for key, val in obj.items():
        new_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(val, dict):
            items.update(_flatten(val, new_key))
        else:
            items[new_key] = val
    return items

