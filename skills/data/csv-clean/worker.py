# filepath: skills/data/csv-clean/worker.py
import csv, io, logging, re
from datetime import datetime
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Clean CSV data with configurable operations."""
    skill_id = "data.csv-clean"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            content: str = input.data.get("csv_content", "")
            if not content.strip():
                return SkillOutput(success=False, error="'csv_content' is required.")

            delim: str = input.data.get("delimiter", ",")
            ops: list = input.data.get("operations", ["remove_empty", "trim_whitespace"])
            date_cols: list = input.data.get("date_columns", [])
            date_fmt: str = input.data.get("date_format", "%Y-%m-%d")

            reader = csv.DictReader(io.StringIO(content), delimiter=delim)
            headers = reader.fieldnames or []
            rows = list(reader)
            original_count = len(rows)
            log: list[dict] = []

            if "trim_whitespace" in ops:
                affected = 0
                for row in rows:
                    for k in row:
                        if row[k] and row[k] != row[k].strip():
                            row[k] = row[k].strip()
                            affected += 1
                log.append({"operation": "trim_whitespace", "affected_rows": affected})

            if "remove_empty" in ops:
                before = len(rows)
                rows = [r for r in rows if any(v and v.strip() for v in r.values())]
                log.append({"operation": "remove_empty", "affected_rows": before - len(rows)})

            if "remove_duplicates" in ops:
                before = len(rows)
                seen = set()
                unique = []
                for r in rows:
                    key = tuple(sorted(r.items()))
                    if key not in seen:
                        seen.add(key)
                        unique.append(r)
                rows = unique
                log.append({"operation": "remove_duplicates", "affected_rows": before - len(rows)})

            if "normalize_dates" in ops and date_cols:
                affected = 0
                for row in rows:
                    for col in date_cols:
                        val = row.get(col, "")
                        if val:
                            for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%d.%m.%Y"):
                                try:
                                    dt = datetime.strptime(val, fmt)
                                    row[col] = dt.strftime(date_fmt)
                                    affected += 1
                                    break
                                except ValueError:
                                    continue
                log.append({"operation": "normalize_dates", "affected_rows": affected})

            # Write output
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=headers, delimiter=delim)
            writer.writeheader()
            writer.writerows(rows)

            return SkillOutput(success=True, data={
                "cleaned_csv": out.getvalue(), "original_rows": original_count,
                "cleaned_rows": len(rows), "removed_rows": original_count - len(rows),
                "operations_log": log,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
