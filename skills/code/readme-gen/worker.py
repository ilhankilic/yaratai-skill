"""code.readme-gen — Generate markdown README from project info."""
from __future__ import annotations
import logging
from typing import Any
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

BADGE_TEMPLATES = {
    "python": "![Python](https://img.shields.io/badge/python-{ver}-blue)",
    "node": "![Node](https://img.shields.io/badge/node-%3E%3D{ver}-green)",
    "license": "![License](https://img.shields.io/badge/license-{lic}-brightgreen)",
}


class Worker(BaseWorker):
    """Generate markdown README from project metadata."""
    skill_id = "code.readme-gen"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            info: dict[str, Any] = input.data.get("project_info", {})
            if not info:
                return SkillOutput(success=False, error="'project_info' is required.")

            style: str = input.data.get("style", "standard")
            badges: bool = input.data.get("include_badges", True)
            lang: str = input.data.get("language", "en")
            contrib: bool = input.data.get("include_contributing", False)

            name = info.get("name", "Project")
            desc = info.get("description", "")
            language = info.get("language", "")
            framework = info.get("framework", "")
            features = info.get("features", [])
            install = info.get("installation_steps", [])
            env_vars = info.get("env_vars", {})
            lic = info.get("license", "")

            sections: list[str] = []
            section_count = 0

            # Title
            sections.append(f"# {name}\n")
            if desc:
                sections.append(f"{desc}\n")

            # Badges
            has_badges = False
            if badges and style != "minimal":
                badge_line: list[str] = []
                if language.lower() == "python":
                    badge_line.append(BADGE_TEMPLATES["python"].format(ver=info.get("python_version", "3.11")))
                if language.lower() in ("javascript", "typescript"):
                    badge_line.append(BADGE_TEMPLATES["node"].format(ver=info.get("node_version", "20")))
                if lic:
                    badge_line.append(BADGE_TEMPLATES["license"].format(lic=lic.replace(" ", "_")))
                if badge_line:
                    sections.append(" ".join(badge_line) + "\n")
                    has_badges = True

            # Features
            if features and style != "minimal":
                hdr = "## Özellikler" if lang == "tr" else "## Features"
                sections.append(f"{hdr}\n")
                for f in features:
                    sections.append(f"- {f}")
                sections.append("")
                section_count += 1

            # Installation
            if install:
                hdr = "## Kurulum" if lang == "tr" else "## Installation"
                sections.append(f"{hdr}\n")
                sections.append("```bash")
                for step in install:
                    sections.append(step)
                sections.append("```\n")
                section_count += 1

            # Env vars
            if env_vars and style in ("standard", "detailed"):
                hdr = "## Ortam Değişkenleri" if lang == "tr" else "## Environment Variables"
                sections.append(f"{hdr}\n")
                sections.append("| Variable | Description |")
                sections.append("|----------|-------------|")
                for k, v in env_vars.items():
                    sections.append(f"| `{k}` | {v} |")
                sections.append("")
                section_count += 1

            # Contributing
            if contrib and style == "detailed":
                hdr = "## Katkıda Bulunma" if lang == "tr" else "## Contributing"
                sections.append(f"{hdr}\n")
                sections.append("PRs are welcome. Please follow the coding standards.\n")
                section_count += 1

            # License
            if lic:
                sections.append(f"## License\n\n{lic}\n")
                section_count += 1

            content = "\n".join(sections).strip() + "\n"
            words = len(content.split())

            return SkillOutput(success=True, data={
                "readme_content": content, "section_count": section_count,
                "word_count": words, "has_badges": has_badges,
            }, metadata={"skill_id": self.skill_id})
        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

