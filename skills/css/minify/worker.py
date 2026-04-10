# filepath: skills/css/minify/worker.py
import logging, re, zlib
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Minify CSS content, optionally remove dead rules."""
    skill_id = "css.minify"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            css: str = input.data.get("css", "")
            if not css.strip():
                return SkillOutput(success=False, error="'css' is required.")
            remove_comments: bool = input.data.get("remove_comments", True)
            html_ctx: str = input.data.get("html_context", "")

            original = len(css.encode("utf-8"))
            removed = 0
            out = css

            # Remove comments (keep /*! important */)
            if remove_comments:
                out = re.sub(r"/\*(?!!)[^*]*\*+(?:[^/*][^*]*\*+)*/", "", out)

            # Collapse whitespace
            out = re.sub(r"\s+", " ", out)
            out = re.sub(r"\s*([{};:,>~+])\s*", r"\1", out)
            out = out.strip()

            # Color shorthand
            def shorten_hex(m):
                h = m.group(1)
                if len(h) == 6 and h[0]==h[1] and h[2]==h[3] and h[4]==h[5]:
                    return f"#{h[0]}{h[2]}{h[4]}"
                return m.group(0)
            out = re.sub(r"#([0-9a-fA-F]{6})\b", shorten_hex, out)

            # Shorthand: 0px -> 0
            out = re.sub(r"\b0+(?:px|em|rem|%)\b", "0", out)

            # Dead code removal with html_context
            if html_ctx:
                selectors = re.findall(r"([.#]?[\w-]+)\s*\{", out)
                for sel in selectors:
                    clean = sel.lstrip(".#")
                    if clean not in html_ctx and sel not in html_ctx:
                        out = re.sub(re.escape(sel) + r"\s*\{[^}]*\}", "", out)
                        removed += 1

            minified_bytes = len(out.encode("utf-8"))
            gzip_bytes = len(zlib.compress(out.encode("utf-8"), 9))
            reduction = ((original - minified_bytes) / original * 100) if original > 0 else 0

            return SkillOutput(success=True, data={
                "minified": out, "original_size_bytes": original,
                "minified_size_bytes": minified_bytes, "gzip_size_bytes": gzip_bytes,
                "reduction_percent": round(reduction, 2), "removed_rules_count": removed,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
