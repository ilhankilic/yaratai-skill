# filepath: skills/ui/figma-to-html/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Convert Figma node tree to HTML/CSS."""
    skill_id = "ui.figma-to-html"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            figma: dict = input.data.get("figma_json", {})
            if not figma:
                return SkillOutput(success=False, error="'figma_json' is required.")
            fmt: str = input.data.get("output_format", "plain_html")

            html_parts: list[str] = []; css_parts: list[str] = []
            count = [0]; unsupported: list[str] = []

            def traverse(node: dict, depth: int = 0):
                ntype = node.get("type", "")
                name = node.get("name", "element")
                style = node.get("style", {})
                children = node.get("children", [])
                count[0] += 1
                indent = "  " * depth

                if ntype == "TEXT":
                    fs = style.get("fontSize", 16)
                    tag = "h1" if fs >= 32 else "h2" if fs >= 24 else "p"
                    html_parts.append(f"{indent}<{tag}>{node.get('characters', name)}</{tag}>")
                elif ntype in ("FRAME", "GROUP", "COMPONENT", "INSTANCE"):
                    cls = name.lower().replace(" ", "-")
                    layout = style.get("layoutMode", "")
                    css_rule = f".{cls} {{ "
                    if layout == "HORIZONTAL":
                        css_rule += "display: flex; flex-direction: row; "
                    elif layout == "VERTICAL":
                        css_rule += "display: flex; flex-direction: column; "
                    css_rule += "}"
                    css_parts.append(css_rule)
                    html_parts.append(f'{indent}<div class="{cls}">')
                    for child in children:
                        traverse(child, depth + 1)
                    html_parts.append(f"{indent}</div>")
                elif ntype == "RECTANGLE":
                    w = style.get("width", 100); h = style.get("height", 100)
                    html_parts.append(f'{indent}<div style="width:{w}px;height:{h}px;background:#ccc;"></div>')
                elif ntype == "ELLIPSE":
                    html_parts.append(f'{indent}<div style="border-radius:50%;width:50px;height:50px;background:#ccc;"></div>')
                else:
                    unsupported.append(ntype)

            traverse(figma)
            html = "\n".join(html_parts)
            css = "\n".join(css_parts)

            return SkillOutput(success=True, data={
                "html": html, "css": css, "node_count": count[0],
                "unsupported_nodes": list(set(unsupported)),
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
