# filepath: skills/media/img-placeholder/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate SVG/PNG placeholder images."""
    skill_id = "media.img-placeholder"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            w = input.data.get("width", 0)
            h = input.data.get("height", 0)
            fmt = input.data.get("format", "svg")
            if not w or not h:
                return SkillOutput(success=False, error="'width' and 'height' required.")
            text = input.data.get("text", f"{w}x{h}")
            bg = input.data.get("bg_color", "#cccccc")
            tc = input.data.get("text_color", "#666666")
            border = input.data.get("border", False)

            if fmt == "svg":
                svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                svg += f'<rect width="{w}" height="{h}" fill="{bg}"'
                if border:
                    svg += f' stroke="{input.data.get("border_color", "#999")}" stroke-width="2"'
                svg += '/>'
                svg += f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="{tc}" font-family="system-ui,sans-serif">{text}</text>'
                svg += '</svg>'
                content = svg
            else:
                content = f"[PNG placeholder {w}x{h} — requires Pillow]"

            return SkillOutput(success=True, data={
                "content": content, "width": w, "height": h,
                "format": fmt, "size_bytes": len(content.encode()),
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
