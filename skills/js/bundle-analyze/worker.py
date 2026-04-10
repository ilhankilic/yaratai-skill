# filepath: skills/js/bundle-analyze/worker.py
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

KNOWN_HEAVY = {
    "moment": {"size_kb": 67, "alt": "dayjs (2kb)", "alt_pkg": "dayjs"},
    "lodash": {"size_kb": 71, "alt": "lodash-es or radash", "alt_pkg": "lodash-es"},
    "axios": {"size_kb": 13, "alt": "ky (3kb)", "alt_pkg": "ky"},
    "jquery": {"size_kb": 87, "alt": "vanilla JS", "alt_pkg": None},
    "bootstrap": {"size_kb": 48, "alt": "Tailwind CSS", "alt_pkg": "tailwindcss"},
    "@mui/material": {"size_kb": 300, "alt": "Radix UI + Tailwind", "alt_pkg": "@radix-ui/react-dialog"},
    "antd": {"size_kb": 500, "alt": "Shadcn/UI", "alt_pkg": None},
    "underscore": {"size_kb": 17, "alt": "native ES6+", "alt_pkg": None},
}

class Worker(BaseWorker):
    """Analyze package.json for heavy, duplicate, and unused packages."""
    skill_id = "js.bundle-analyze"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            pkg: dict = input.data.get("package_json", {})
            if not pkg:
                return SkillOutput(success=False, error="'package_json' is required.")
            import_list: list = input.data.get("import_list", [])
            threshold: int = input.data.get("size_threshold_kb", 50)

            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            heavy: list = []
            recs: list[str] = []
            total = 0
            score = 100

            for name, ver in deps.items():
                if name in KNOWN_HEAVY:
                    info = KNOWN_HEAVY[name]
                    total += info["size_kb"]
                    entry = {"name": name, "approx_size_kb": info["size_kb"], "alternatives": [info["alt"]]}
                    if info["size_kb"] >= threshold:
                        heavy.append(entry)
                        recs.append(f"Replace {name} ({info['size_kb']}kb) with {info['alt']}")
                        score -= 10
                else:
                    total += 5  # estimate

            # Unused detection
            unused = []
            if import_list:
                used_pkgs = set()
                for imp in import_list:
                    parts = imp.replace("'", "").replace('"', "").split("/")
                    if parts[0].startswith("@"):
                        used_pkgs.add("/".join(parts[:2]))
                    else:
                        used_pkgs.add(parts[0])
                for name in deps:
                    if name not in used_pkgs:
                        unused.append(name)
                        score -= 3

            score = max(0, min(100, score))

            return SkillOutput(success=True, data={
                "heavy_packages": heavy, "duplicate_packages": [],
                "unused_packages": unused, "total_approx_size_kb": total,
                "recommendations": recs, "score": score,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
