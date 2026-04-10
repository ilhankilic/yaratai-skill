# filepath: skills/ui/bootstrap-scaffold/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)
CDN = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist"

SECTION_TEMPLATES = {
    "hero": '<section class="bg-{theme_bg} text-{theme_fg} py-5"><div class="container text-center"><h1 class="display-4">{title}</h1><p class="lead">{content}</p></div></section>',
    "cards": '<section class="py-4"><div class="container"><h2>{title}</h2><div class="row g-3">{content}</div></div></section>',
    "text": '<section class="py-4"><div class="container"><h2>{title}</h2><p>{content}</p></div></section>',
    "table": '<section class="py-4"><div class="container"><h2>{title}</h2><div class="table-responsive"><table class="table table-striped">{content}</table></div></div></section>',
    "form": '<section class="py-4"><div class="container"><h2>{title}</h2><form>{content}</form></div></section>',
}

class Worker(BaseWorker):
    """Generate Bootstrap 5 HTML page from content structure."""
    skill_id = "ui.bootstrap-scaffold"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            title: str = input.data.get("page_title", "")
            sections: list = input.data.get("sections", [])
            if not title or not sections:
                return SkillOutput(success=False, error="'page_title' and 'sections' are required.")

            navbar: bool = input.data.get("navbar", True)
            theme: str = input.data.get("theme", "light")

            theme_bg = "dark" if theme == "dark" else "light"
            theme_fg = "white" if theme == "dark" else "dark"
            body_cls = f'data-bs-theme="{theme}"' if theme == "dark" else ""

            parts: list[str] = [f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>{title}</title>\n<link rel="stylesheet" href="{CDN}/css/bootstrap.min.css">\n</head>\n<body {body_cls}>']

            if navbar:
                parts.append(f'<nav class="navbar navbar-expand-lg navbar-{theme_bg} bg-{theme_bg}"><div class="container"><a class="navbar-brand" href="#">{title}</a></div></nav>')

            for sec in sections:
                stype = sec.get("type", "text")
                tmpl = SECTION_TEMPLATES.get(stype, SECTION_TEMPLATES["text"])
                parts.append(tmpl.format(title=sec.get("title", ""), content=sec.get("content", ""), theme_bg=theme_bg, theme_fg=theme_fg))

            parts.append(f'<script src="{CDN}/js/bootstrap.bundle.min.js"></script>\n</body>\n</html>')

            html = "\n".join(parts)
            size_kb = round(len(html.encode("utf-8")) / 1024, 2)

            return SkillOutput(success=True, data={
                "html": html, "sections_count": len(sections), "estimated_size_kb": size_kb,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
