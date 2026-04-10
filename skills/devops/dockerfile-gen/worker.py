# filepath: skills/devops/dockerfile-gen/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate multi-stage Dockerfile."""
    skill_id = "devops.dockerfile-gen"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            dep_file: str = input.data.get("dependency_file", "")
            ftype: str = input.data.get("file_type", "")
            if not dep_file or not ftype:
                return SkillOutput(success=False, error="'dependency_file' and 'file_type' required.")

            app_type: str = input.data.get("app_type", "api")
            port: int = input.data.get("expose_port", 0)
            health: bool = input.data.get("health_check", True)
            nonroot: bool = input.data.get("non_root_user", True)

            if ftype == "requirements_txt":
                base = "python:3.11-slim-bookworm"
                lines = [f"FROM {base} AS builder", "WORKDIR /app", "COPY requirements.txt .",
                         "RUN pip install --no-cache-dir -r requirements.txt", "",
                         f"FROM {base}", "WORKDIR /app",
                         "COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages",
                         "COPY . ."]
                est_size = 150
            else:
                base = "node:20-alpine"
                lines = [f"FROM {base} AS builder", "WORKDIR /app", "COPY package*.json ./",
                         "RUN npm ci --only=production", "",
                         f"FROM {base}", "WORKDIR /app",
                         "COPY --from=builder /app/node_modules ./node_modules", "COPY . ."]
                est_size = 120

            sec_notes = []
            if nonroot:
                lines.extend(["RUN addgroup -S appuser && adduser -S appuser -G appuser" if "alpine" in base else "RUN useradd -m appuser",
                              "USER appuser"])
                sec_notes.append("Running as non-root user.")

            if port:
                lines.append(f"EXPOSE {port}")

            if health:
                if ftype == "requirements_txt":
                    lines.append(f'HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen(\'http://localhost:{port or 8000}/health\')"')
                else:
                    lines.append(f'HEALTHCHECK CMD wget -q --spider http://localhost:{port or 3000}/health || exit 1')

            if app_type == "api":
                if ftype == "requirements_txt":
                    lines.append('CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]')
                else:
                    lines.append('CMD ["node", "src/index.js"]')

            dockerfile = "\n".join(lines) + "\n"
            ignore = "__pycache__\n*.pyc\nnode_modules\n.git\n.env\n*.md\n.venv\n"

            return SkillOutput(success=True, data={
                "dockerfile": dockerfile, "dockerignore": ignore,
                "base_image_used": base, "stage_count": 2,
                "estimated_size_mb": est_size, "security_notes": sec_notes,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
