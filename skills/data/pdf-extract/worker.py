"""data.pdf-extract — Extract text and tables from PDF files."""

from __future__ import annotations

import base64
import io
import logging
import tempfile
from pathlib import Path
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class Worker(BaseWorker):
    """Extract text and tables from a PDF using pdfplumber."""

    skill_id = "data.pdf-extract"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            import pdfplumber
        except ImportError:
            return SkillOutput(
                success=False,
                error="pdfplumber is not installed. Run: pip install 'skillforge[pdf]'",
            )

        try:
            file_path: str = input.data.get("file_path", "")
            b64: str = input.data.get("base64", "")
            page_filter: list[int] = input.data.get("pages", [])

            if not file_path and not b64:
                return SkillOutput(
                    success=False,
                    error="Provide either 'file_path' or 'base64'.",
                )

            # Resolve file handle
            if b64:
                raw_bytes = base64.b64decode(b64)
                file_obj: Any = io.BytesIO(raw_bytes)
            else:
                p = Path(file_path)
                if not p.exists():
                    return SkillOutput(success=False, error=f"File not found: {file_path}")
                file_obj = str(p)

            all_text: list[str] = []
            all_tables: list[list[dict[str, Any]]] = []

            with pdfplumber.open(file_obj) as pdf:
                total_pages = len(pdf.pages)
                target_pages = page_filter if page_filter else range(total_pages)

                for idx in target_pages:
                    if idx >= total_pages:
                        continue
                    page = pdf.pages[idx]

                    text = page.extract_text() or ""
                    all_text.append(text)

                    tables = page.extract_tables() or []
                    for table in tables:
                        if not table:
                            continue
                        headers = table[0]
                        rows = [
                            dict(zip(headers, row))
                            for row in table[1:]
                            if row
                        ]
                        all_tables.append(rows)

            return SkillOutput(
                success=True,
                data={
                    "text": "\n\n".join(all_text),
                    "tables": all_tables,
                    "pages": total_pages,
                },
                metadata={"skill_id": self.skill_id},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

