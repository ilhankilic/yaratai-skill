# filepath: skills/ui/dark-mode-patch/worker.py
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

DEFAULT_MAP = {"#ffffff": "#1a1a1a", "#fff": "#1a1a1a", "#000000": "#f5f5f5", "#000": "#f5f5f5",
               "white": "#1a1a1a", "black": "#f5f5f5", "#f8f9fa": "#212529", "#212529": "#f8f9fa"}

class Worker(BaseWorker):
    """Add dark mode to CSS or HTML."""
    skill_id = "ui.dark-mode-patch"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            source: str = input.data.get("source", "")
            if not source.strip():
                return SkillOutput(success=False, error="'source' is required.")
            stype: str = input.data.get("source_type", "css")
            strategy: str = input.data.get("strategy", "media_query")
            custom_map: dict = input.data.get("color_mapping", {})

            cmap = {**DEFAULT_MAP, **custom_map}
            patched = source; count = 0; review = []

            if stype == "css":
                dark_rules = []
                for light, dark_val in cmap.items():
                    if light in source:
                        dark_rules.append(source.replace(light, dark_val))
                        count += 1
                if strategy in ("media_query", "both"):
                    dark_block = "\n@media (prefers-color-scheme: dark) {\n" + "\n".join(dark_rules) + "\n}\n"
                    patched = source + dark_block
                if strategy in ("class", "both"):
                    class_block = "\n.dark {\n"
                    for light, dark_val in cmap.items():
                        if light in source:
                            class_block += f"  /* {light} -> {dark_val} */\n"
                    class_block += "}\n"
                    patched += class_block
            elif stype == "tailwind_html":
                for light, dark_val in cmap.items():
                    if f'"{light}"' in source or f"'{light}'" in source:
                        count += 1
                review.append("Manual Tailwind dark: prefixes may be needed.")
                patched = source

            return SkillOutput(success=True, data={
                "patched_source": patched, "colors_patched": count,
                "manual_review_needed": review,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
