"""code.changelog — Generate CHANGELOG.md from git log using Conventional Commits."""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

CATEGORIES: dict[str, str] = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "chore": "Maintenance",
    "refactor": "Refactoring",
    "perf": "Performance",
    "test": "Tests",
    "ci": "CI/CD",
    "style": "Style",
    "build": "Build",
}

COMMIT_RE = re.compile(
    r"^(?P<hash>[0-9a-fA-F]+)\|(?P<msg>.+?)(?:\|(?P<author>[^|]*))?(?:\|(?P<date>.*))?$"
)
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>\w+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)


class Worker(BaseWorker):
    """Generate CHANGELOG.md from git log using Conventional Commits."""

    skill_id = "code.changelog"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            git_log: str = input.data.get("git_log", "").strip()
            version: str = input.data.get("version", "")
            if not git_log:
                return SkillOutput(success=False, error="'git_log' is required.")
            if not version:
                return SkillOutput(success=False, error="'version' is required.")

            repo_url: str = input.data.get("repo_url", "")
            release_date: str = input.data.get("date", "") or date.today().isoformat()
            include_authors: bool = input.data.get("include_authors", False)

            grouped: dict[str, list[dict[str, str]]] = {}
            breaking_list: list[str] = []
            total = 0

            for line in git_log.strip().splitlines():
                line = line.strip().strip("'\"")
                if not line:
                    continue
                total += 1
                m = COMMIT_RE.match(line)
                if not m:
                    grouped.setdefault("other", []).append({"desc": line, "hash": "", "author": ""})
                    continue

                commit_hash = m.group("hash")[:7]
                msg = m.group("msg").strip()
                author = (m.group("author") or "").strip()

                cm = CONVENTIONAL_RE.match(msg)
                if not cm:
                    grouped.setdefault("other", []).append({"desc": msg, "hash": commit_hash, "author": author})
                    continue

                ctype = cm.group("type")
                desc = cm.group("desc").strip()
                scope = cm.group("scope") or ""
                is_breaking = bool(cm.group("breaking")) or "BREAKING CHANGE" in msg

                entry: dict[str, str] = {"desc": desc, "hash": commit_hash, "author": author, "scope": scope}
                grouped.setdefault(ctype, []).append(entry)

                if is_breaking:
                    breaking_list.append(desc)

            # Build markdown
            lines: list[str] = [f"## [{version}] - {release_date}", ""]

            if breaking_list:
                lines.append("### ⚠ Breaking Changes")
                lines.append("")
                for b in breaking_list:
                    lines.append(f"- {b}")
                lines.append("")

            for ctype, heading in CATEGORIES.items():
                entries = grouped.get(ctype, [])
                if not entries:
                    continue
                lines.append(f"### {heading}")
                lines.append("")
                for e in entries:
                    parts = [f"- {e['desc']}"]
                    if e.get("scope"):
                        parts = [f"- **{e['scope']}:** {e['desc']}"]
                    if repo_url and e.get("hash"):
                        parts.append(f" ([{e['hash']}]({repo_url}/commit/{e['hash']}))")
                    if include_authors and e.get("author"):
                        parts.append(f" — {e['author']}")
                    lines.append("".join(parts))
                lines.append("")

            # Other uncategorized
            others = grouped.get("other", [])
            if others:
                lines.append("### Other")
                lines.append("")
                for e in others:
                    lines.append(f"- {e['desc']}")
                lines.append("")

            changelog_md = "\n".join(lines).rstrip() + "\n"

            return SkillOutput(
                success=True,
                data={
                    "changelog_md": changelog_md,
                    "feat_count": len(grouped.get("feat", [])),
                    "fix_count": len(grouped.get("fix", [])),
                    "breaking_count": len(breaking_list),
                    "total_commits": total,
                },
                metadata={"skill_id": self.skill_id},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

