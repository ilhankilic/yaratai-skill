# filepath: skills/ui/tailwind-layout/worker.py
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

CSS_TO_TW = {
    "margin: 0": "m-0", "margin: auto": "m-auto", "padding: 0": "p-0",
    "display: flex": "flex", "display: grid": "grid", "display: block": "block",
    "display: none": "hidden", "display: inline": "inline",
    "text-align: center": "text-center", "text-align: left": "text-left", "text-align: right": "text-right",
    "font-weight: bold": "font-bold", "font-weight: normal": "font-normal",
    "position: relative": "relative", "position: absolute": "absolute", "position: fixed": "fixed",
    "overflow: hidden": "overflow-hidden", "overflow: auto": "overflow-auto",
    "width: 100%": "w-full", "height: 100%": "h-full",
    "cursor: pointer": "cursor-pointer",
    "flex-direction: column": "flex-col", "flex-direction: row": "flex-row",
    "justify-content: center": "justify-center", "align-items: center": "items-center",
    "flex-wrap: wrap": "flex-wrap",
}
STYLE_RE = re.compile(r'style="([^"]*)"')

class Worker(BaseWorker):
    """Convert inline CSS to Tailwind utility classes."""
    skill_id = "ui.tailwind-layout"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            html: str = input.data.get("html", "")
            if not html.strip():
                return SkillOutput(success=False, error="'html' is required.")
            remove: bool = input.data.get("remove_inline_styles", True)
            dark: bool = input.data.get("add_dark_mode", False)

            added = 0; removed = 0; warnings = []
            def replace_style(m):
                nonlocal added, removed
                style = m.group(1)
                tw_classes = []
                props = [p.strip() for p in style.split(";") if p.strip()]
                for prop in props:
                    prop_clean = re.sub(r"\s+", " ", prop).strip()
                    matched = False
                    for css, tw in CSS_TO_TW.items():
                        if css in prop_clean:
                            tw_classes.append(tw)
                            if dark:
                                tw_classes.append(f"dark:{tw}")
                            matched = True; added += 1; break
                    if not matched:
                        warnings.append(f"Could not convert: {prop_clean}")
                removed += len(props)
                if remove:
                    return f'class="{" ".join(tw_classes)}"' if tw_classes else ""
                return f'class="{" ".join(tw_classes)}" style="{style}"'

            result = STYLE_RE.sub(replace_style, html)
            return SkillOutput(success=True, data={
                "converted_html": result, "removed_styles_count": removed,
                "added_classes_count": added, "warnings": warnings,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
