"""code.pr-summary — Generate PR title and description from git diff."""
from __future__ import annotations
import logging, re
from typing import Any
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

FILE_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)
FUNC_RE = re.compile(r"^[+-]\s*(?:def |function |const |class )\s*(\w+)", re.MULTILINE)
LABEL_MAP = {".py": "python", ".ts": "typescript", ".tsx": "react", ".js": "javascript",
             ".yml": "ci/cd", ".yaml": "config", ".md": "docs", ".css": "styles",
             "Dockerfile": "docker", ".env": "config"}


class Worker(BaseWorker):
    """Generate PR title and description from a git diff."""
    skill_id = "code.pr-summary"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            diff: str = input.data.get("diff", "").strip()
            if not diff:
                return SkillOutput(success=False, error="'diff' is required.")

            template: str = input.data.get("template", "github")
            lang: str = input.data.get("language", "en")
            ticket: str = input.data.get("ticket_id", "")
            branch: str = input.data.get("branch_name", "")

            files = FILE_RE.findall(diff)
            changed_files = list({b for _, b in files})
            added = diff.count("\n+") - diff.count("\n+++")
            removed = diff.count("\n-") - diff.count("\n---")
            funcs = FUNC_RE.findall(diff)

            # Labels
            labels: list[str] = []
            for f in changed_files:
                for ext, label in LABEL_MAP.items():
                    if f.endswith(ext) or ext in f:
                        if label not in labels:
                            labels.append(label)
            has_tests = any("test" in f.lower() for f in changed_files)
            if has_tests:
                labels.append("tested")

            # Breaking changes
            breaking: list[str] = []
            if any("schema" in f.lower() for f in changed_files):
                breaking.append("Schema files changed — check backward compatibility.")
            if re.search(r"^-.*@app\.(get|post|put|delete)", diff, re.MULTILINE):
                breaking.append("API endpoint(s) may have been removed.")

            # Title
            prefix = "feat" if added > removed else "fix" if removed > added else "refactor"
            if branch:
                slug = branch.split("/")[-1].replace("-", " ").replace("_", " ")
                title = f"{prefix}: {slug}"
            else:
                title = f"{prefix}: update {len(changed_files)} file(s)"
            if ticket:
                title = f"[{ticket}] {title}"

            # Body
            body = self._build_body(template, lang, changed_files, added, removed, funcs, has_tests, ticket)

            return SkillOutput(success=True, data={
                "title": title, "body": body, "labels": labels,
                "reviewers_hint": list(set(labels) - {"tested", "docs"}),
                "breaking_changes": breaking,
            }, metadata={"skill_id": self.skill_id})
        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    def _build_body(self, tmpl: str, lang: str, files: list, added: int, removed: int,
                    funcs: list, has_tests: bool, ticket: str) -> str:
        lines: list[str] = []
        if tmpl == "github":
            lines.append("## Summary\n")
            if ticket:
                lines.append(f"Resolves {ticket}\n")
            lines.append("## Changes\n")
            lines.append(f"- **{len(files)}** file(s) changed (+{added} / -{removed})")
            if funcs:
                lines.append(f"- Modified functions/classes: {', '.join(set(funcs[:10]))}")
            lines.append("\n## Testing\n")
            lines.append("- [x] Tests included" if has_tests else "- [ ] Tests needed")
        elif tmpl == "gitlab":
            lines.append("## What\n")
            for f in files[:15]:
                lines.append(f"- `{f}`")
            lines.append("\n## Why\n\n_(fill in)_\n\n## Testing\n")
            lines.append("Tests updated." if has_tests else "No test changes.")
        else:
            lines.append("## Changes\n")
            for f in files[:15]:
                lines.append(f"- `{f}`")
        return "\n".join(lines) + "\n"

