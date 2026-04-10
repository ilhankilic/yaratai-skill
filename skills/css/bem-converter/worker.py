# filepath: skills/css/bem-converter/worker.py
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

NESTED_RE = re.compile(r"\.(\w[\w-]*)\s+\.(\w[\w-]*)")
HOVER_RE = re.compile(r"\.(\w[\w-]*):(\w+)")

class Worker(BaseWorker):
    """Convert CSS class names to BEM naming convention."""
    skill_id = "css.bem-converter"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            css: str = input.data.get("css", "")
            if not css.strip():
                return SkillOutput(success=False, error="'css' is required.")
            html: str = input.data.get("html", "")
            dry_run: bool = input.data.get("dry_run", False)

            rename: dict[str, str] = {}
            review: list[str] = []

            # Nested selectors -> BEM element
            for m in NESTED_RE.finditer(css):
                block, element = m.group(1), m.group(2)
                old = f".{block} .{element}"
                new_name = f"{block}__{element}"
                rename[element] = new_name
                if not dry_run:
                    css = css.replace(old, f".{new_name}")

            # Pseudo-classes -> BEM modifier
            for m in HOVER_RE.finditer(css):
                cls, pseudo = m.group(1), m.group(2)
                if pseudo in ("hover", "focus", "active", "disabled"):
                    old = f".{cls}:{pseudo}"
                    new_name = f"{cls}--{pseudo}"
                    rename[f"{cls}:{pseudo}"] = new_name
                    if not dry_run:
                        css = css.replace(old, f".{new_name}")

            converted_html = html
            if html and not dry_run:
                for old_cls, new_cls in rename.items():
                    if ":" not in old_cls:
                        converted_html = converted_html.replace(f'"{old_cls}"', f'"{new_cls}"')
                        converted_html = converted_html.replace(f" {old_cls} ", f" {new_cls} ")

            return SkillOutput(success=True, data={
                "converted_css": css, "converted_html": converted_html,
                "rename_map": rename, "suggestions_count": len(rename),
                "manual_review": review,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
