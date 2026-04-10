"""code.env-template — Detect env variables from source code and generate .env.example."""
from __future__ import annotations
import json, logging, re
from typing import Any
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

PATTERNS = [
    (r'os\.environ\.get\(["\'](\w+)["\'](?:,\s*["\']([^"\']*)["\'])?\)', "python"),
    (r'os\.getenv\(["\'](\w+)["\'](?:,\s*["\']([^"\']*)["\'])?\)', "python"),
    (r'os\.environ\[["\'](\w+)["\']\]', "python_required"),
    (r'process\.env\.(\w+)', "node"),
    (r'env\(["\'](\w+)["\'](?:,\s*["\']([^"\']*)["\'])?\)', "generic"),
    (r'config\(["\'](\w+)["\'](?:,\s*["\']([^"\']*)["\'])?\)', "generic"),
]

GROUPS = {
    "DATABASE": "# Database", "DB_": "# Database", "REDIS": "# Cache",
    "JWT": "# Security", "SECRET": "# Security", "SMTP": "# Email",
    "EMAIL": "# Email", "S3_": "# Storage", "AWS": "# Storage",
    "OLLAMA": "# AI/LLM", "ANTHROPIC": "# AI/LLM", "RUNPOD": "# AI/LLM",
    "PORT": "# Server", "HOST": "# Server", "DEBUG": "# Server",
}


class Worker(BaseWorker):
    """Detect environment variables from source and generate .env.example."""
    skill_id = "code.env-template"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            files: list[dict] = input.data.get("source_files", [])
            if not files:
                return SkillOutput(success=False, error="'source_files' is required.")

            existing: str = input.data.get("existing_env", "")
            add_comments: bool = input.data.get("add_comments", True)
            add_defaults: bool = input.data.get("add_defaults", True)
            group_by: bool = input.data.get("group_by_service", True)
            fmt: str = input.data.get("output_format", "env")

            vars_found: dict[str, dict[str, Any]] = {}

            for f in files:
                content = f.get("content", "")
                path = f.get("path", "")
                for pat, kind in PATTERNS:
                    for m in re.finditer(pat, content):
                        name = m.group(1)
                        default = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
                        required = kind == "python_required"
                        if name not in vars_found:
                            vars_found[name] = {
                                "name": name, "default": default or "",
                                "required": required, "detected_in_files": [],
                                "service_group": self._group(name),
                            }
                        vars_found[name]["detected_in_files"].append(path)
                        if required:
                            vars_found[name]["required"] = True

            # Merge existing
            if existing:
                for line in existing.strip().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        if k in vars_found and not vars_found[k]["default"]:
                            vars_found[k]["default"] = v.strip()

            variables = sorted(vars_found.values(), key=lambda x: x["name"])
            template = self._format(variables, fmt, add_comments, add_defaults, group_by)

            return SkillOutput(success=True, data={
                "template": template,
                "variables": variables,
                "variable_count": len(variables),
                "required_count": sum(1 for v in variables if v["required"]),
            }, metadata={"skill_id": self.skill_id})
        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    def _group(self, name: str) -> str:
        for prefix, group in GROUPS.items():
            if name.upper().startswith(prefix):
                return group
        return "# Application"

    def _format(self, variables: list, fmt: str, comments: bool, defaults: bool, group: bool) -> str:
        if fmt == "json":
            return json.dumps({v["name"]: v["default"] for v in variables}, indent=2) + "\n"
        if fmt == "yaml":
            lines = []
            for v in variables:
                lines.append(f"{v['name']}: \"{v['default']}\"")
            return "\n".join(lines) + "\n"

        # .env format
        lines: list[str] = []
        current_group = ""
        for v in variables:
            if group and v["service_group"] != current_group:
                if current_group:
                    lines.append("")
                current_group = v["service_group"]
                lines.append(current_group)
            val = v["default"] if defaults else ""
            req = " (required)" if v["required"] else ""
            if comments:
                lines.append(f"# {v['name']}{req}")
            lines.append(f"{v['name']}={val}")
        return "\n".join(lines) + "\n"

