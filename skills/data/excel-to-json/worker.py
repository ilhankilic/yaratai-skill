# filepath: skills/data/excel-to-json/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Convert tabular data to JSON format."""
    skill_id = "data.excel-to-json"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            rows: list = input.data.get("data_rows", [])
            if not rows:
                return SkillOutput(success=False, error="'data_rows' is required.")
            headers: list = input.data.get("headers", [])
            skip_empty: bool = input.data.get("skip_empty_rows", True)

            if not headers and rows:
                headers = [f"col_{i}" for i in range(len(rows[0]) if isinstance(rows[0], list) else 1)]

            result = []
            for row in rows:
                if isinstance(row, list):
                    if skip_empty and all(v is None or v == "" for v in row):
                        continue
                    result.append(dict(zip(headers, row)))
                elif isinstance(row, dict):
                    result.append(row)

            return SkillOutput(success=True, data={
                "sheets": {"Sheet1": result}, "sheet_names": ["Sheet1"],
                "total_rows": len(result), "warnings": [],
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
