"""Batch skill generator — creates all remaining SkillForge skills."""

from __future__ import annotations

import json
from pathlib import Path

SKILLS_ROOT = Path(__file__).parent / "skills"

# ──────────────────────────────────────────────────────────────────────
# Each skill: (category, name, skill_id, description, deps_note,
#              input_fields, output_fields, worker_code, test_code)
# ──────────────────────────────────────────────────────────────────────

SKILLS = []

# ═══ CSS SKILLS ══════════════════════════════════════════════════════

SKILLS.append({
    "cat": "css", "name": "minify", "skill_id": "css.minify",
    "desc": "Minify CSS, remove dead code, calculate gzip size.",
    "input_req": ["css"],
    "input_props": {"css": "string", "remove_comments": "boolean", "remove_unused_vars": "boolean", "html_context": "string"},
    "output_props": {"minified": "string", "original_size_bytes": "integer", "minified_size_bytes": "integer", "gzip_size_bytes": "integer", "reduction_percent": "number", "removed_rules_count": "integer"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_comment_removal(w):
    out = w.run(SkillInput(data={"css": "/* comment */ body { color: red; }"}))
    assert out.success and "comment" not in out.data["minified"]

def test_whitespace_collapse(w):
    out = w.run(SkillInput(data={"css": "body {\\n  color:  red;\\n}"}))
    assert "  " not in out.data["minified"]

def test_color_shorthand(w):
    out = w.run(SkillInput(data={"css": "a { color: #ffffff; }"}))
    assert "#fff" in out.data["minified"]

def test_size_calculation(w):
    css = "body { margin: 0px; padding: 0px; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.data["gzip_size_bytes"] > 0
    assert out.data["reduction_percent"] >= 0

def test_empty_css_error(w):
    out = w.run(SkillInput(data={"css": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "css", "name": "var-extract", "skill_id": "css.var-extract",
    "desc": "Extract repeated CSS values into custom properties (--var).",
    "input_req": ["css"],
    "input_props": {"css": "string", "min_occurrences": "integer", "prefix": "string", "categories": "array"},
    "output_props": {"converted_css": "string", "variables_css": "string", "full_css": "string", "extracted_count": "integer", "variable_map": "object"},
    "worker": r'''
import logging, re
from collections import Counter
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\)|hsla?\([^)]+\)")
SIZE_RE = re.compile(r"\b\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw)\b")
NAMED_COLORS = {"#ff0000": "red", "#00ff00": "green", "#0000ff": "blue",
                "#ffffff": "white", "#000000": "black", "#fff": "white", "#000": "black"}

class Worker(BaseWorker):
    """Extract repeated CSS values into custom properties."""
    skill_id = "css.var-extract"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            css: str = input.data.get("css", "")
            if not css.strip():
                return SkillOutput(success=False, error="'css' is required.")
            min_occ: int = input.data.get("min_occurrences", 2)
            prefix: str = input.data.get("prefix", "--sf")
            cats: list = input.data.get("categories", ["color", "size"])

            values: list[str] = []
            if "color" in cats:
                values.extend(COLOR_RE.findall(css))
            if "size" in cats:
                values.extend(SIZE_RE.findall(css))

            counts = Counter(values)
            var_map: dict[str, str] = {}
            idx = {"color": 0, "size": 0}

            for val, cnt in counts.most_common():
                if cnt < min_occ:
                    continue
                lv = val.lower()
                if lv in NAMED_COLORS:
                    name = f"{prefix}-{NAMED_COLORS[lv]}"
                elif COLOR_RE.match(val):
                    idx["color"] += 1
                    name = f"{prefix}-color-{idx['color']}"
                else:
                    idx["size"] += 1
                    name = f"{prefix}-size-{idx['size']}"
                var_map[val] = name

            converted = css
            for val, name in var_map.items():
                converted = converted.replace(val, f"var({name})")

            var_block = ":root {\n" + "".join(f"  {name}: {val};\n" for val, name in var_map.items()) + "}\n"
            full = var_block + "\n" + converted

            return SkillOutput(success=True, data={
                "converted_css": converted, "variables_css": var_block,
                "full_css": full, "extracted_count": len(var_map), "variable_map": var_map,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_color_extraction(w):
    css = "a { color: #ff0000; } b { color: #ff0000; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.success and out.data["extracted_count"] >= 1
    assert "var(" in out.data["converted_css"]

def test_size_extraction(w):
    css = "a { padding: 16px; } b { margin: 16px; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.data["extracted_count"] >= 1

def test_min_occurrences_3(w):
    css = "a { color: #abc; } b { color: #abc; }"
    out = w.run(SkillInput(data={"css": css, "min_occurrences": 3}))
    assert out.data["extracted_count"] == 0

def test_custom_prefix(w):
    css = "a { color: #000; } b { color: #000; }"
    out = w.run(SkillInput(data={"css": css, "prefix": "--my"}))
    assert "--my" in out.data["variables_css"]

def test_empty_css_error(w):
    out = w.run(SkillInput(data={"css": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "css", "name": "bem-converter", "skill_id": "css.bem-converter",
    "desc": "Convert traditional CSS class names to BEM naming convention.",
    "input_req": ["css"],
    "input_props": {"css": "string", "html": "string", "block_prefix": "string", "dry_run": "boolean"},
    "output_props": {"converted_css": "string", "converted_html": "string", "rename_map": "object", "suggestions_count": "integer", "manual_review": "array"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_nested_selector(w):
    css = ".card .title { font-size: 16px; }"
    out = w.run(SkillInput(data={"css": css}))
    assert out.success and "card__title" in out.data["converted_css"]

def test_hover_state(w):
    css = ".btn:hover { opacity: 0.8; }"
    out = w.run(SkillInput(data={"css": css}))
    assert "btn--hover" in out.data["converted_css"]

def test_html_conversion(w):
    css = ".card .title { color: red; }"
    html = '<div class="card"><h2 class="title">Hi</h2></div>'
    out = w.run(SkillInput(data={"css": css, "html": html}))
    assert "card__title" in out.data["converted_html"]

def test_dry_run(w):
    css = ".card .title { color: red; }"
    out = w.run(SkillInput(data={"css": css, "dry_run": True}))
    assert out.data["suggestions_count"] > 0
    assert ".card .title" in out.data["converted_css"]  # unchanged

def test_empty_css_error(w):
    out = w.run(SkillInput(data={"css": ""}))
    assert out.success is False
''',
})

# ═══ UI SKILLS ═══════════════════════════════════════════════════════

SKILLS.append({
    "cat": "ui", "name": "bootstrap-scaffold", "skill_id": "ui.bootstrap-scaffold",
    "desc": "Generate Bootstrap 5 HTML page from content structure.",
    "input_req": ["page_title", "sections"],
    "input_props": {"page_title": "string", "sections": "array", "navbar": "boolean", "theme": "string", "extra_classes": "string"},
    "output_props": {"html": "string", "sections_count": "integer", "estimated_size_kb": "number"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_hero_section(w):
    out = w.run(SkillInput(data={"page_title": "Test", "sections": [{"title": "Hero", "content": "Welcome", "type": "hero"}]}))
    assert out.success and "display-4" in out.data["html"]

def test_dark_theme(w):
    out = w.run(SkillInput(data={"page_title": "Test", "sections": [{"title": "X", "content": "Y", "type": "text"}], "theme": "dark"}))
    assert 'data-bs-theme="dark"' in out.data["html"]

def test_no_navbar(w):
    out = w.run(SkillInput(data={"page_title": "T", "sections": [{"title": "X", "content": "Y", "type": "text"}], "navbar": False}))
    assert "navbar" not in out.data["html"]

def test_multiple_sections(w):
    secs = [{"title": f"S{i}", "content": "c", "type": "text"} for i in range(3)]
    out = w.run(SkillInput(data={"page_title": "T", "sections": secs}))
    assert out.data["sections_count"] == 3

def test_empty_sections_error(w):
    out = w.run(SkillInput(data={"page_title": "T", "sections": []}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "ui", "name": "react-component", "skill_id": "ui.react-component",
    "desc": "Generate TypeScript React component with Tailwind CSS.",
    "input_req": ["component_name"],
    "input_props": {"component_name": "string", "description": "string", "props": "array", "variant": "string", "with_storybook": "boolean"},
    "output_props": {"component_code": "string", "story_code": "string", "prop_count": "integer", "has_state": "boolean"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

VARIANT_CLASSES = {
    "button": "inline-flex items-center justify-center rounded-md px-4 py-2 font-medium",
    "card": "rounded-lg border bg-white p-6 shadow-sm",
    "form": "space-y-4",
    "list": "divide-y divide-gray-200",
    "modal": "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
    "generic": "",
}

class Worker(BaseWorker):
    """Generate TypeScript React component."""
    skill_id = "ui.react-component"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            name: str = input.data.get("component_name", "")
            if not name:
                return SkillOutput(success=False, error="'component_name' is required.")

            desc: str = input.data.get("description", f"A {name} component.")
            props: list = input.data.get("props", [])
            variant: str = input.data.get("variant", "generic")
            storybook: bool = input.data.get("with_storybook", False)

            if variant not in VARIANT_CLASSES:
                return SkillOutput(success=False, error=f"Unknown variant '{variant}'. Use: {list(VARIANT_CLASSES)}")

            # Props interface
            iface_lines = [f"export interface {name}Props {{"]
            for p in props:
                req = "" if p.get("required", True) else "?"
                iface_lines.append(f"  /** {p.get('description', '')} */")
                iface_lines.append(f"  {p['name']}{req}: {p.get('type', 'string')};")
            iface_lines.append("}")

            # Destructure
            destructure = ", ".join(p["name"] for p in props) if props else ""
            defaults = []
            for p in props:
                if "default" in p:
                    defaults.append(f"{p['name']} = {repr(p['default'])}")
                else:
                    defaults.append(p["name"])

            has_state = variant in ("form", "modal")
            state_line = '  const [open, setOpen] = useState(false);' if has_state else ""
            import_line = "import React, { useState } from 'react';" if has_state else "import React from 'react';"

            tw = VARIANT_CLASSES[variant]
            body = f'    <div className="{tw}">\n      {{/* {desc} */}}\n    </div>'

            comp = f"""{import_line}

{chr(10).join(iface_lines)}

/**
 * {desc}
 */
export default function {name}({{ {', '.join(defaults)} }}: {name}Props) {{
{state_line}
  return (
{body}
  );
}}
"""
            story = ""
            if storybook:
                story = f"""import type {{ Meta, StoryObj }} from '@storybook/react';
import {name} from './{name}';

const meta: Meta<typeof {name}> = {{ component: {name}, title: '{name}' }};
export default meta;
type Story = StoryObj<typeof {name}>;

export const Default: Story = {{ args: {{}} }};
"""

            return SkillOutput(success=True, data={
                "component_code": comp, "story_code": story,
                "prop_count": len(props), "has_state": has_state,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_button_variant(w):
    out = w.run(SkillInput(data={"component_name": "MyButton", "variant": "button", "props": [{"name": "label", "type": "string", "required": True}]}))
    assert out.success and "MyButton" in out.data["component_code"]

def test_form_variant_has_state(w):
    out = w.run(SkillInput(data={"component_name": "LoginForm", "variant": "form"}))
    assert out.data["has_state"] is True and "useState" in out.data["component_code"]

def test_required_props(w):
    out = w.run(SkillInput(data={"component_name": "Card", "props": [{"name": "title", "type": "string", "required": True}]}))
    assert "title: string" in out.data["component_code"]

def test_optional_props_default(w):
    out = w.run(SkillInput(data={"component_name": "Badge", "props": [{"name": "color", "type": "string", "required": False, "default": "blue"}]}))
    assert "color?" in out.data["component_code"]

def test_invalid_variant_error(w):
    out = w.run(SkillInput(data={"component_name": "X", "variant": "nonexistent"}))
    assert out.success is False
''',
})

# ═══ JS SKILLS ═══════════════════════════════════════════════════════

SKILLS.append({
    "cat": "js", "name": "bundle-analyze", "skill_id": "js.bundle-analyze",
    "desc": "Analyze package.json for heavy/duplicate/unused dependencies.",
    "input_req": ["package_json"],
    "input_props": {"package_json": "object", "import_list": "array", "size_threshold_kb": "integer"},
    "output_props": {"heavy_packages": "array", "duplicate_packages": "array", "unused_packages": "array", "total_approx_size_kb": "number", "recommendations": "array", "score": "integer"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_moment_detection(w):
    pkg = {"dependencies": {"moment": "^2.29.4", "react": "^18"}}
    out = w.run(SkillInput(data={"package_json": pkg}))
    assert out.success and any(h["name"] == "moment" for h in out.data["heavy_packages"])

def test_unused_package(w):
    pkg = {"dependencies": {"react": "^18", "lodash": "^4"}}
    out = w.run(SkillInput(data={"package_json": pkg, "import_list": ["react"]}))
    assert "lodash" in out.data["unused_packages"]

def test_clean_package_high_score(w):
    pkg = {"dependencies": {"react": "^18", "next": "^14"}}
    out = w.run(SkillInput(data={"package_json": pkg}))
    assert out.data["score"] == 100

def test_empty_deps(w):
    out = w.run(SkillInput(data={"package_json": {"dependencies": {}}}))
    assert out.success and out.data["score"] == 100

def test_empty_pkg_error(w):
    out = w.run(SkillInput(data={"package_json": {}}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "js", "name": "dead-code", "skill_id": "js.dead-code",
    "desc": "Detect unused functions, variables, and imports in JS/TS code.",
    "input_req": ["code"],
    "input_props": {"code": "string", "language": "string", "check_exports": "boolean", "ignore_patterns": "array"},
    "output_props": {"unused_functions": "array", "unused_variables": "array", "unused_imports": "array", "total_dead_lines": "integer", "clean_code": "string", "confidence": "number"},
    "worker": r'''
import logging, re
from collections import Counter
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

FUNC_DEF = re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)")
CONST_FUNC = re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=")
IMPORT_RE = re.compile(r"import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]")

class Worker(BaseWorker):
    """Detect unused functions, variables, and imports in JS/TS."""
    skill_id = "js.dead-code"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            code: str = input.data.get("code", "")
            if not code.strip():
                return SkillOutput(success=False, error="'code' is required.")
            check_exports: bool = input.data.get("check_exports", False)
            ignore: list = input.data.get("ignore_patterns", [])

            lines = code.splitlines()
            words = re.findall(r"\b\w+\b", code)
            word_counts = Counter(words)

            # Functions
            unused_funcs = []
            for m in FUNC_DEF.finditer(code):
                name = m.group(1)
                if name.startswith("_") or any(re.match(p, name) for p in ignore):
                    continue
                if not check_exports and "export" in code[max(0,m.start()-10):m.start()]:
                    continue
                if word_counts.get(name, 0) <= 1:
                    line = code[:m.start()].count("\n") + 1
                    unused_funcs.append({"name": name, "line": line, "reason": "defined but never called"})

            # Variables
            unused_vars = []
            for m in CONST_FUNC.finditer(code):
                name = m.group(1)
                if name.startswith("_") or any(re.match(p, name) for p in ignore):
                    continue
                if not check_exports and "export" in code[max(0,m.start()-10):m.start()]:
                    continue
                if word_counts.get(name, 0) <= 1:
                    line = code[:m.start()].count("\n") + 1
                    unused_vars.append({"name": name, "line": line, "reason": "defined but never used"})

            # Imports
            unused_imports = []
            for m in IMPORT_RE.finditer(code):
                names = (m.group(1) or m.group(2) or "").split(",")
                source = m.group(3)
                for n in names:
                    n = n.strip().split(" as ")[-1].strip()
                    if not n:
                        continue
                    if word_counts.get(n, 0) <= 1:
                        line = code[:m.start()].count("\n") + 1
                        unused_imports.append({"name": n, "source": source, "line": line})

            dead_lines = len(unused_funcs) * 3 + len(unused_vars) + len(unused_imports)

            # Clean code
            clean = code
            for item in unused_imports:
                clean = re.sub(r"import\s+.*" + re.escape(item["source"]) + r".*\n?", "", clean, count=1)

            confidence = 0.7 if not check_exports else 0.85

            return SkillOutput(success=True, data={
                "unused_functions": unused_funcs, "unused_variables": unused_vars,
                "unused_imports": unused_imports, "total_dead_lines": dead_lines,
                "clean_code": clean, "confidence": confidence,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_unused_function(w):
    code = "function unused() { return 1; }\\nfunction used() { return unused(); }\\nconsole.log(used());"
    out = w.run(SkillInput(data={"code": code}))
    assert out.success

def test_unused_import(w):
    code = "import { useState } from 'react';\\nimport { useEffect } from 'react';\\nconst App = () => useState();"
    out = w.run(SkillInput(data={"code": code}))
    assert out.success
    assert any(i["name"] == "useEffect" for i in out.data["unused_imports"])

def test_exported_function_skipped(w):
    code = "export function helper() { return 1; }"
    out = w.run(SkillInput(data={"code": code}))
    assert len(out.data["unused_functions"]) == 0

def test_underscore_prefix_skipped(w):
    code = "function _internal() { return 1; }"
    out = w.run(SkillInput(data={"code": code}))
    assert len(out.data["unused_functions"]) == 0

def test_clean_code_output(w):
    code = "import { unused } from 'lib';\\nconsole.log('hello');"
    out = w.run(SkillInput(data={"code": code}))
    assert "import" not in out.data["clean_code"] or "unused" not in out.data["clean_code"]
''',
})

SKILLS.append({
    "cat": "js", "name": "env-validator", "skill_id": "js.env-validator",
    "desc": "Validate .env files for missing, malformed, and weak values.",
    "input_req": ["env_content"],
    "input_props": {"env_content": "string", "schema": "object", "check_secrets": "boolean"},
    "output_props": {"valid": "boolean", "missing_required": "array", "type_errors": "array", "weak_secrets": "array", "exposed_defaults": "array", "parsed": "object"},
    "worker": r'''
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)
WEAK_VALUES = {"test", "secret", "password", "changeme", "123456", "admin", "test123", "default"}
URL_RE = re.compile(r"^https?://\S+")
BOOL_VALUES = {"true", "false", "1", "0", "yes", "no"}

class Worker(BaseWorker):
    """Validate .env file content."""
    skill_id = "js.env-validator"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            content: str = input.data.get("env_content", "")
            if not content.strip():
                return SkillOutput(success=False, error="'env_content' is required.")

            schema: dict = input.data.get("schema", {})
            check_secrets: bool = input.data.get("check_secrets", True)

            parsed: dict[str, str] = {}
            for line in content.strip().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                parsed[k.strip()] = v.strip().strip('"').strip("'")

            missing = []
            type_errors = []
            weak = []
            exposed = []

            for key, rules in schema.items():
                if rules.get("required") and key not in parsed:
                    missing.append(key)
                    continue
                if key not in parsed:
                    continue
                val = parsed[key]
                exp_type = rules.get("type", "")
                if exp_type == "url" and not URL_RE.match(val):
                    type_errors.append({"key": key, "expected": "url", "got": val[:30]})
                elif exp_type == "boolean" and val.lower() not in BOOL_VALUES:
                    type_errors.append({"key": key, "expected": "boolean", "got": val})
                elif exp_type == "integer":
                    try:
                        int(val)
                    except ValueError:
                        type_errors.append({"key": key, "expected": "integer", "got": val})

            if check_secrets:
                for k, v in parsed.items():
                    vl = v.lower()
                    if any(w == vl for w in WEAK_VALUES):
                        weak.append({"key": k, "reason": f"Weak value: '{v}'"})
                    if any(w in k.upper() for w in ("KEY", "SECRET", "TOKEN", "PASSWORD")):
                        if len(v) < 8:
                            weak.append({"key": k, "reason": "Secret too short (<8 chars)"})

            valid = not missing and not type_errors

            return SkillOutput(success=True, data={
                "valid": valid, "missing_required": missing, "type_errors": type_errors,
                "weak_secrets": weak, "exposed_defaults": exposed, "parsed": parsed,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_missing_required(w):
    out = w.run(SkillInput(data={"env_content": "DEBUG=true", "schema": {"DATABASE_URL": {"required": True}}}))
    assert "DATABASE_URL" in out.data["missing_required"]

def test_wrong_url_format(w):
    out = w.run(SkillInput(data={"env_content": "DB_URL=not-a-url", "schema": {"DB_URL": {"type": "url"}}}))
    assert len(out.data["type_errors"]) > 0

def test_weak_secret(w):
    out = w.run(SkillInput(data={"env_content": "SECRET_KEY=password", "check_secrets": True}))
    assert len(out.data["weak_secrets"]) > 0

def test_boolean_type(w):
    out = w.run(SkillInput(data={"env_content": "DEBUG=maybe", "schema": {"DEBUG": {"type": "boolean"}}}))
    assert any(e["key"] == "DEBUG" for e in out.data["type_errors"])

def test_valid_env(w):
    out = w.run(SkillInput(data={"env_content": "PORT=3000\\nDEBUG=true", "schema": {"PORT": {"required": True, "type": "integer"}}}))
    assert out.data["valid"] is True
''',
})

# ═══ DEVOPS SKILLS ═══════════════════════════════════════════════════

SKILLS.append({
    "cat": "devops", "name": "dockerfile-gen", "skill_id": "devops.dockerfile-gen",
    "desc": "Generate optimized multi-stage Dockerfile from dependency files.",
    "input_req": ["dependency_file", "file_type"],
    "input_props": {"dependency_file": "string", "file_type": "string", "app_type": "string", "expose_port": "integer", "health_check": "boolean", "non_root_user": "boolean"},
    "output_props": {"dockerfile": "string", "dockerignore": "string", "base_image_used": "string", "stage_count": "integer", "estimated_size_mb": "integer", "security_notes": "array"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_python_api(w):
    out = w.run(SkillInput(data={"dependency_file": "fastapi\\nuvicorn", "file_type": "requirements_txt"}))
    assert out.success and "python" in out.data["base_image_used"]

def test_node_web(w):
    out = w.run(SkillInput(data={"dependency_file": '{"dependencies":{}}', "file_type": "package_json"}))
    assert "node" in out.data["base_image_used"]

def test_port_expose(w):
    out = w.run(SkillInput(data={"dependency_file": "flask", "file_type": "requirements_txt", "expose_port": 5000}))
    assert "EXPOSE 5000" in out.data["dockerfile"]

def test_non_root_user(w):
    out = w.run(SkillInput(data={"dependency_file": "flask", "file_type": "requirements_txt", "non_root_user": True}))
    assert "appuser" in out.data["dockerfile"]

def test_health_check(w):
    out = w.run(SkillInput(data={"dependency_file": "flask", "file_type": "requirements_txt", "health_check": True}))
    assert "HEALTHCHECK" in out.data["dockerfile"]
''',
})

SKILLS.append({
    "cat": "devops", "name": "env-secret-scan", "skill_id": "devops.env-secret-scan",
    "desc": "Scan source code for hardcoded API keys, secrets, and credentials.",
    "input_req": ["files"],
    "input_props": {"files": "array", "scan_types": "array", "severity_filter": "string", "whitelist_patterns": "array"},
    "output_props": {"findings": "array", "critical_count": "integer", "high_count": "integer", "medium_count": "integer", "clean_files": "integer", "summary": "string"},
    "worker": r'''
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

PATTERNS = [
    {"name": "AWS Access Key", "regex": r"AKIA[0-9A-Z]{16}", "severity": "critical", "type": "api_keys"},
    {"name": "GitHub Token", "regex": r"ghp_[a-zA-Z0-9]{36}", "severity": "critical", "type": "tokens"},
    {"name": "Stripe Secret", "regex": r"sk_live_[a-zA-Z0-9]{24,}", "severity": "critical", "type": "api_keys"},
    {"name": "JWT Token", "regex": r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "severity": "high", "type": "jwt"},
    {"name": "Private Key", "regex": r"-----BEGIN[A-Z ]*PRIVATE KEY-----", "severity": "critical", "type": "private_keys"},
    {"name": "Generic Password", "regex": r"""password\s*[=:]\s*['"][^'"]{8,}['"]""", "severity": "high", "type": "passwords"},
    {"name": "DB Connection String", "regex": r"(?:postgres|mysql|mongodb)://\w+:\w+@", "severity": "critical", "type": "connection_strings"},
]

class Worker(BaseWorker):
    """Scan code for hardcoded secrets."""
    skill_id = "devops.env-secret-scan"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            files: list = input.data.get("files", [])
            if not files:
                return SkillOutput(success=False, error="'files' is required.")
            severity_filter: str = input.data.get("severity_filter", "all")
            whitelist: list = input.data.get("whitelist_patterns", [])

            findings = []
            dirty_files = set()

            for f in files:
                path = f.get("path", "")
                content = f.get("content", "")
                lines = content.splitlines()

                for pat in PATTERNS:
                    if severity_filter != "all" and pat["severity"] != severity_filter:
                        continue
                    for i, line in enumerate(lines, 1):
                        for m in re.finditer(pat["regex"], line, re.IGNORECASE):
                            val = m.group(0)
                            if any(re.search(wp, val) for wp in whitelist):
                                continue
                            masked = val[:4] + "***" + val[-4:] if len(val) > 8 else "***"
                            findings.append({
                                "file": path, "line": i, "severity": pat["severity"],
                                "type": pat["type"], "matched_value_masked": masked,
                                "context": line.strip()[:100],
                                "recommendation": f"Move to environment variable or secret manager.",
                            })
                            dirty_files.add(path)

            crit = sum(1 for f in findings if f["severity"] == "critical")
            high = sum(1 for f in findings if f["severity"] == "high")
            med = sum(1 for f in findings if f["severity"] == "medium")
            clean = len(files) - len(dirty_files)

            return SkillOutput(success=True, data={
                "findings": findings, "critical_count": crit, "high_count": high,
                "medium_count": med, "clean_files": clean,
                "summary": f"Found {len(findings)} secret(s) in {len(dirty_files)} file(s). {clean} file(s) clean.",
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_aws_key_detection(w):
    out = w.run(SkillInput(data={"files": [{"path": "a.py", "content": "key = 'AKIAIOSFODNN7EXAMPLE'"}]}))
    assert out.data["critical_count"] >= 1

def test_jwt_detection(w):
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    out = w.run(SkillInput(data={"files": [{"path": "a.js", "content": f"token = '{jwt}'"}]}))
    assert out.data["high_count"] >= 1

def test_whitelist(w):
    out = w.run(SkillInput(data={"files": [{"path": "a.py", "content": "key = 'AKIAIOSFODNN7EXAMPLE'"}], "whitelist_patterns": ["EXAMPLE"]}))
    assert out.data["critical_count"] == 0

def test_severity_filter(w):
    out = w.run(SkillInput(data={"files": [{"path": "a.py", "content": "key = 'AKIAIOSFODNN7EXAMPLE'"}], "severity_filter": "high"}))
    assert out.data["critical_count"] == 0

def test_clean_file(w):
    out = w.run(SkillInput(data={"files": [{"path": "clean.py", "content": "x = 1 + 2"}]}))
    assert out.data["clean_files"] == 1 and len(out.data["findings"]) == 0
''',
})

# ═══ AI SKILLS ═══════════════════════════════════════════════════════

SKILLS.append({
    "cat": "ai", "name": "prompt-engineer", "skill_id": "ai.prompt-engineer",
    "desc": "Transform raw requests into structured, effective LLM prompts.",
    "input_req": ["raw_request"],
    "input_props": {"raw_request": "string", "target_model": "string", "task_type": "string", "output_format": "string", "language": "string", "add_examples": "boolean", "chain_of_thought": "boolean"},
    "output_props": {"system_prompt": "string", "user_prompt": "string", "full_prompt": "string", "techniques_used": "array", "token_estimate": "integer", "suggestions": "array"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

ROLES = {
    "generation": "expert content creator",
    "extraction": "data extraction specialist",
    "classification": "classification and categorization expert",
    "summarization": "concise summarization expert",
    "translation": "professional translator",
    "code": "senior software engineer",
    "analysis": "analytical reasoning expert",
}

class Worker(BaseWorker):
    """Transform raw requests into structured LLM prompts."""
    skill_id = "ai.prompt-engineer"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            raw: str = input.data.get("raw_request", "").strip()
            if not raw:
                return SkillOutput(success=False, error="'raw_request' is required.")

            model: str = input.data.get("target_model", "generic")
            task: str = input.data.get("task_type", "generation")
            fmt: str = input.data.get("output_format", "text")
            lang: str = input.data.get("language", "tr")
            examples: bool = input.data.get("add_examples", True)
            cot: bool = input.data.get("chain_of_thought", False)

            techniques: list[str] = ["role_assignment", "output_constraints"]
            role = ROLES.get(task, "helpful assistant")

            # System prompt
            lang_name = "Türkçe" if lang == "tr" else "English"
            system_parts = [f"Sen bir {role}'sın." if lang == "tr" else f"You are a {role}."]
            system_parts.append(f"Yanıtlarını {lang_name} olarak ver." if lang == "tr" else f"Respond in {lang_name}.")

            if fmt == "json":
                system_parts.append("Çıktını geçerli JSON formatında ver." if lang == "tr" else "Return output as valid JSON.")
                techniques.append("format_constraint")
            elif fmt == "markdown":
                system_parts.append("Markdown formatında yanıtla." if lang == "tr" else "Format your response in Markdown.")

            system_prompt = " ".join(system_parts)

            # User prompt
            user_parts = [raw]
            if cot:
                user_parts.append("\nAdım adım düşün:" if lang == "tr" else "\nThink step by step:")
                techniques.append("chain_of_thought")

            if examples:
                user_parts.append("\nÖrnek:" if lang == "tr" else "\nExample:")
                user_parts.append("Input: [sample] → Output: [sample]")
                techniques.append("few_shot")

            user_prompt = "\n".join(user_parts)
            full = f"[System]\n{system_prompt}\n\n[User]\n{user_prompt}"

            token_est = len(full.split()) * 1.3  # rough token estimate

            suggestions = []
            if not cot and task in ("analysis", "code"):
                suggestions.append("Consider enabling chain_of_thought for better reasoning.")
            if fmt == "text" and task == "extraction":
                suggestions.append("Consider using JSON output_format for structured extraction.")

            return SkillOutput(success=True, data={
                "system_prompt": system_prompt, "user_prompt": user_prompt,
                "full_prompt": full, "techniques_used": techniques,
                "token_estimate": int(token_est), "suggestions": suggestions,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_code_generation(w):
    out = w.run(SkillInput(data={"raw_request": "Write a sorting function", "task_type": "code"}))
    assert out.success and "engineer" in out.data["system_prompt"]

def test_data_extraction(w):
    out = w.run(SkillInput(data={"raw_request": "Extract names from text", "task_type": "extraction"}))
    assert "extraction" in out.data["system_prompt"]

def test_json_format(w):
    out = w.run(SkillInput(data={"raw_request": "List items", "output_format": "json"}))
    assert "JSON" in out.data["system_prompt"]

def test_chain_of_thought(w):
    out = w.run(SkillInput(data={"raw_request": "Analyze this", "chain_of_thought": True}))
    assert "chain_of_thought" in out.data["techniques_used"]

def test_turkish_prompt(w):
    out = w.run(SkillInput(data={"raw_request": "Metin özetle", "language": "tr"}))
    assert "Türkçe" in out.data["system_prompt"]

def test_empty_request_error(w):
    out = w.run(SkillInput(data={"raw_request": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "ai", "name": "lang-detect", "skill_id": "ai.lang-detect",
    "desc": "Detect text language using heuristics, optionally translate via Ollama.",
    "input_req": ["text"],
    "input_props": {"text": "string", "task": "string", "target_language": "string", "confidence_threshold": "number", "use_heuristics": "boolean"},
    "output_props": {"detected_language": "string", "detection_confidence": "number", "translated_text": "string", "detection_method": "string", "processing_ms": "number"},
    "worker": r'''
import logging, re, time
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

CHAR_PATTERNS = {
    "tr": re.compile(r"[şğüöıçŞĞÜÖİÇ]"),
    "de": re.compile(r"[äöüßÄÖÜ]"),
    "fr": re.compile(r"[éèêëàâùûçîïôœæ]", re.IGNORECASE),
    "ar": re.compile(r"[\u0600-\u06FF]"),
    "ja": re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"),
    "zh": re.compile(r"[\u4e00-\u9fff]"),
    "ko": re.compile(r"[\uac00-\ud7af]"),
    "ru": re.compile(r"[\u0400-\u04FF]"),
}

class Worker(BaseWorker):
    """Detect text language using character heuristics."""
    skill_id = "ai.lang-detect"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            text: str = input.data.get("text", "").strip()
            if not text:
                return SkillOutput(success=False, error="'text' is required.")

            task: str = input.data.get("task", "detect")
            threshold: float = input.data.get("confidence_threshold", 0.7)

            start = time.time()
            lang, conf, method = self._detect(text)
            elapsed = (time.time() - start) * 1000

            translated = ""
            if task in ("translate", "both"):
                target = input.data.get("target_language", "en")
                translated = f"[Translation to {target} requires Ollama — not available in offline mode]"

            if len(text) < 10:
                conf = min(conf, 0.5)

            return SkillOutput(success=True, data={
                "detected_language": lang, "detection_confidence": round(conf, 2),
                "translated_text": translated, "detection_method": method,
                "processing_ms": round(elapsed, 2),
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _detect(self, text: str) -> tuple[str, float, str]:
        scores: dict[str, int] = {}
        for lang, pattern in CHAR_PATTERNS.items():
            count = len(pattern.findall(text))
            if count > 0:
                scores[lang] = count

        if scores:
            best = max(scores, key=scores.get)  # type: ignore
            total = len(text)
            conf = min(1.0, scores[best] / max(total * 0.1, 1))
            return best, conf, "heuristic"

        # Default to English if ASCII-only
        if all(ord(c) < 128 for c in text):
            return "en", 0.6, "heuristic"

        return "unknown", 0.0, "heuristic"
''',
    "tests": '''
from skillforge.base import SkillInput

def test_turkish_heuristic(w):
    out = w.run(SkillInput(data={"text": "Merhaba dünya, bu güzel bir gün."}))
    assert out.success and out.data["detected_language"] == "tr"

def test_english_detection(w):
    out = w.run(SkillInput(data={"text": "Hello world, this is a test."}))
    assert out.data["detected_language"] == "en"

def test_short_text_low_confidence(w):
    out = w.run(SkillInput(data={"text": "Hi"}))
    assert out.data["detection_confidence"] <= 0.5

def test_translate_task(w):
    out = w.run(SkillInput(data={"text": "Merhaba", "task": "translate", "target_language": "en"}))
    assert out.data["translated_text"] != ""

def test_mixed_language(w):
    out = w.run(SkillInput(data={"text": "This is mixed içerik with Türkçe."}))
    assert out.success

def test_empty_text_error(w):
    out = w.run(SkillInput(data={"text": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "ai", "name": "fine-tune-prep", "skill_id": "ai.fine-tune-prep",
    "desc": "Convert raw data into fine-tuning formats (Alpaca, ShareGPT, ChatML).",
    "input_req": ["raw_data"],
    "input_props": {"raw_data": "array", "input_type": "string", "output_format": "string", "system_prompt": "string", "train_split": "number", "shuffle": "boolean"},
    "output_props": {"train_jsonl": "string", "val_jsonl": "string", "train_count": "integer", "val_count": "integer", "avg_tokens_estimate": "integer", "format_example": "object"},
    "worker": r'''
import json, logging, random
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Convert data into fine-tuning dataset formats."""
    skill_id = "ai.fine-tune-prep"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            raw: list = input.data.get("raw_data", [])
            if not raw:
                return SkillOutput(success=False, error="'raw_data' is required.")

            fmt: str = input.data.get("output_format", "alpaca")
            sys_prompt: str = input.data.get("system_prompt", "")
            split: float = input.data.get("train_split", 0.9)
            shuffle: bool = input.data.get("shuffle", True)

            formatted = []
            for item in raw:
                if fmt == "alpaca":
                    formatted.append({"instruction": item.get("instruction", item.get("question", "")),
                                     "input": item.get("input", ""), "output": item.get("output", item.get("answer", ""))})
                elif fmt == "sharegpt":
                    convs = [{"from": "human", "value": item.get("instruction", item.get("question", ""))},
                             {"from": "gpt", "value": item.get("output", item.get("answer", ""))}]
                    if sys_prompt:
                        convs.insert(0, {"from": "system", "value": sys_prompt})
                    formatted.append({"conversations": convs})
                else:  # chatml / jsonl_chat
                    msgs = []
                    if sys_prompt:
                        msgs.append({"role": "system", "content": sys_prompt})
                    msgs.append({"role": "user", "content": item.get("instruction", item.get("question", ""))})
                    msgs.append({"role": "assistant", "content": item.get("output", item.get("answer", ""))})
                    formatted.append({"messages": msgs})

            if shuffle:
                random.shuffle(formatted)

            split_idx = int(len(formatted) * split)
            train = formatted[:split_idx]
            val = formatted[split_idx:]

            train_jsonl = "\n".join(json.dumps(r, ensure_ascii=False) for r in train)
            val_jsonl = "\n".join(json.dumps(r, ensure_ascii=False) for r in val)

            avg_tokens = sum(len(json.dumps(r).split()) for r in formatted) // max(len(formatted), 1)

            return SkillOutput(success=True, data={
                "train_jsonl": train_jsonl, "val_jsonl": val_jsonl,
                "train_count": len(train), "val_count": len(val),
                "avg_tokens_estimate": int(avg_tokens * 1.3),
                "format_example": formatted[0] if formatted else {},
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

DATA = [{"question": "What is 1+1?", "answer": "2"}, {"question": "Capital of Turkey?", "answer": "Ankara"},
        {"question": "Python creator?", "answer": "Guido"}, {"question": "HTTP port?", "answer": "80"}]

def test_alpaca_format(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "output_format": "alpaca", "shuffle": False}))
    assert out.success and "instruction" in out.data["format_example"]

def test_sharegpt_format(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "output_format": "sharegpt", "shuffle": False}))
    assert "conversations" in out.data["format_example"]

def test_train_val_split(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "train_split": 0.75, "shuffle": False}))
    assert out.data["train_count"] == 3 and out.data["val_count"] == 1

def test_system_prompt(w):
    out = w.run(SkillInput(data={"raw_data": DATA, "output_format": "chatml", "system_prompt": "Be helpful", "shuffle": False}))
    assert "system" in out.data["train_jsonl"]

def test_empty_data_error(w):
    out = w.run(SkillInput(data={"raw_data": []}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "data", "name": "csv-clean", "skill_id": "data.csv-clean",
    "desc": "Clean CSV: remove empty rows, duplicates, normalize dates, fix types.",
    "input_req": ["csv_content"],
    "input_props": {"csv_content": "string", "delimiter": "string", "operations": "array", "date_columns": "array", "date_format": "string"},
    "output_props": {"cleaned_csv": "string", "original_rows": "integer", "cleaned_rows": "integer", "removed_rows": "integer", "operations_log": "array"},
    "worker": r'''
import csv, io, logging, re
from datetime import datetime
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Clean CSV data with configurable operations."""
    skill_id = "data.csv-clean"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            content: str = input.data.get("csv_content", "")
            if not content.strip():
                return SkillOutput(success=False, error="'csv_content' is required.")

            delim: str = input.data.get("delimiter", ",")
            ops: list = input.data.get("operations", ["remove_empty", "trim_whitespace"])
            date_cols: list = input.data.get("date_columns", [])
            date_fmt: str = input.data.get("date_format", "%Y-%m-%d")

            reader = csv.DictReader(io.StringIO(content), delimiter=delim)
            headers = reader.fieldnames or []
            rows = list(reader)
            original_count = len(rows)
            log: list[dict] = []

            if "trim_whitespace" in ops:
                affected = 0
                for row in rows:
                    for k in row:
                        if row[k] and row[k] != row[k].strip():
                            row[k] = row[k].strip()
                            affected += 1
                log.append({"operation": "trim_whitespace", "affected_rows": affected})

            if "remove_empty" in ops:
                before = len(rows)
                rows = [r for r in rows if any(v and v.strip() for v in r.values())]
                log.append({"operation": "remove_empty", "affected_rows": before - len(rows)})

            if "remove_duplicates" in ops:
                before = len(rows)
                seen = set()
                unique = []
                for r in rows:
                    key = tuple(sorted(r.items()))
                    if key not in seen:
                        seen.add(key)
                        unique.append(r)
                rows = unique
                log.append({"operation": "remove_duplicates", "affected_rows": before - len(rows)})

            if "normalize_dates" in ops and date_cols:
                affected = 0
                for row in rows:
                    for col in date_cols:
                        val = row.get(col, "")
                        if val:
                            for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%d.%m.%Y"):
                                try:
                                    dt = datetime.strptime(val, fmt)
                                    row[col] = dt.strftime(date_fmt)
                                    affected += 1
                                    break
                                except ValueError:
                                    continue
                log.append({"operation": "normalize_dates", "affected_rows": affected})

            # Write output
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=headers, delimiter=delim)
            writer.writeheader()
            writer.writerows(rows)

            return SkillOutput(success=True, data={
                "cleaned_csv": out.getvalue(), "original_rows": original_count,
                "cleaned_rows": len(rows), "removed_rows": original_count - len(rows),
                "operations_log": log,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_remove_empty_rows(w):
    csv = "name,age\\nAli,30\\n,\\nAyse,25"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["remove_empty"]}))
    assert out.success and out.data["cleaned_rows"] == 2

def test_remove_duplicates(w):
    csv = "name,age\\nAli,30\\nAli,30\\nAyse,25"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["remove_duplicates"]}))
    assert out.data["cleaned_rows"] == 2

def test_trim_whitespace(w):
    csv = "name,age\\n  Ali  ,30\\nAyse,25"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["trim_whitespace"]}))
    assert "  Ali  " not in out.data["cleaned_csv"]

def test_normalize_dates(w):
    csv = "name,date\\nAli,15/01/2024\\nAyse,20/02/2024"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["normalize_dates"], "date_columns": ["date"]}))
    assert "2024-01-15" in out.data["cleaned_csv"]

def test_combined_operations(w):
    csv = "name,age\\n  Ali  ,30\\n,\\nAli,30"
    out = w.run(SkillInput(data={"csv_content": csv, "operations": ["trim_whitespace", "remove_empty", "remove_duplicates"]}))
    assert out.data["removed_rows"] >= 1
''',
})

SKILLS.append({
    "cat": "data", "name": "schema-infer", "skill_id": "data.schema-infer",
    "desc": "Infer JSON Schema (draft-7) from sample data.",
    "input_req": ["sample_data"],
    "input_props": {"sample_data": "object", "title": "string", "required_threshold": "number", "additional_properties": "boolean", "detect_formats": "boolean"},
    "output_props": {"schema": "object", "schema_json": "string", "field_count": "integer", "required_count": "integer", "detected_formats": "object"},
    "worker": r'''
import json, logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
URI_RE = re.compile(r"^https?://")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

class Worker(BaseWorker):
    """Infer JSON Schema from sample data."""
    skill_id = "data.schema-infer"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            data = input.data.get("sample_data", None)
            if data is None:
                return SkillOutput(success=False, error="'sample_data' is required.")

            title: str = input.data.get("title", "InferredSchema")
            threshold: float = input.data.get("required_threshold", 1.0)
            detect_fmt: bool = input.data.get("detect_formats", True)

            samples = data if isinstance(data, list) else [data]
            if not samples:
                return SkillOutput(success=False, error="sample_data is empty.")

            formats: dict = {}
            schema = self._infer(samples, threshold, detect_fmt, formats)
            schema["$schema"] = "http://json-schema.org/draft-07/schema#"
            schema["title"] = title

            schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
            field_count = len(schema.get("properties", {}))
            required_count = len(schema.get("required", []))

            return SkillOutput(success=True, data={
                "schema": schema, "schema_json": schema_json,
                "field_count": field_count, "required_count": required_count,
                "detected_formats": formats,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _infer(self, samples: list, threshold: float, detect_fmt: bool, formats: dict) -> dict:
        if not samples:
            return {"type": "object"}
        if isinstance(samples[0], dict):
            props: dict = {}
            field_presence: dict[str, int] = {}
            for s in samples:
                for k, v in s.items():
                    field_presence[k] = field_presence.get(k, 0) + 1
                    if k not in props:
                        props[k] = self._infer_type(v, detect_fmt, formats, k)
            required = [k for k, cnt in field_presence.items() if cnt / len(samples) >= threshold]
            return {"type": "object", "properties": props, "required": required}
        return self._infer_type(samples[0], detect_fmt, formats, "root")

    def _infer_type(self, value, detect_fmt: bool, formats: dict, key: str) -> dict:
        if value is None:
            return {"type": ["string", "null"]}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer"}
        if isinstance(value, float):
            return {"type": "number"}
        if isinstance(value, str):
            t: dict = {"type": "string"}
            if detect_fmt:
                if EMAIL_RE.match(value):
                    t["format"] = "email"; formats[key] = "email"
                elif DATE_RE.match(value):
                    t["format"] = "date"; formats[key] = "date"
                elif URI_RE.match(value):
                    t["format"] = "uri"; formats[key] = "uri"
                elif UUID_RE.match(value):
                    t["format"] = "uuid"; formats[key] = "uuid"
            return t
        if isinstance(value, list):
            if value:
                return {"type": "array", "items": self._infer_type(value[0], detect_fmt, formats, key)}
            return {"type": "array"}
        if isinstance(value, dict):
            props = {k: self._infer_type(v, detect_fmt, formats, k) for k, v in value.items()}
            return {"type": "object", "properties": props}
        return {"type": "string"}
''',
    "tests": '''
from skillforge.base import SkillInput

def test_simple_object(w):
    data = [{"name": "Ali", "age": 30}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert out.success and out.data["field_count"] == 2

def test_nested_object(w):
    data = [{"user": {"name": "Ali"}, "score": 10}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert out.data["schema"]["properties"]["user"]["type"] == "object"

def test_array_items(w):
    data = [{"tags": ["a", "b"]}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert out.data["schema"]["properties"]["tags"]["type"] == "array"

def test_email_format_detected(w):
    data = [{"email": "ali@test.com"}]
    out = w.run(SkillInput(data={"sample_data": data}))
    assert "email" in out.data["detected_formats"]

def test_required_threshold(w):
    data = [{"name": "Ali", "age": 30}, {"name": "Ayse"}]
    out = w.run(SkillInput(data={"sample_data": data, "required_threshold": 0.5}))
    assert "name" in out.data["schema"]["required"]
''',
})


# ══════════════════════════════════════════════════════════════════════
# GENERATOR
# ══════════════════════════════════════════════════════════════════════

def _test_boilerplate(skill_id: str, tests_code: str) -> str:
    """Wrap test functions with standard boilerplate."""
    mod_name = skill_id.replace(".", "_").replace("-", "_") + "_worker"
    return f'''"""Tests for {skill_id} skill."""
from __future__ import annotations
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import pytest
from skillforge.base import SkillInput

_wp = Path(__file__).parent / "worker.py"
_spec = spec_from_file_location("{mod_name}", _wp)
_mod = module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
Worker = _mod.Worker

@pytest.fixture
def w(): return Worker()

{tests_code.strip()}
'''


def generate_all():
    for skill in SKILLS:
        cat = skill["cat"]
        name = skill["name"]
        sid = skill["skill_id"]
        skill_dir = SKILLS_ROOT / cat / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # schema.json
        schema = {
            "skill_id": sid, "version": "1.0.0",
            "description": skill["desc"],
            "input": {
                "type": "object",
                "required": skill.get("input_req", []),
                "properties": {k: {"type": v} for k, v in skill.get("input_props", {}).items()},
            },
            "output": {
                "type": "object",
                "properties": {k: {"type": v} for k, v in skill.get("output_props", {}).items()},
            },
        }
        (skill_dir / "schema.json").write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        # worker.py
        worker_code = f'# filepath: skills/{cat}/{name}/worker.py\n{skill["worker"].strip()}\n'
        (skill_dir / "worker.py").write_text(worker_code, encoding="utf-8")

        # SKILL.md
        skill_md = f"# {sid}\n\n{skill['desc']}\n"
        (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

        # test.py
        test_code = _test_boilerplate(sid, skill["tests"])
        (skill_dir / "test.py").write_text(test_code, encoding="utf-8")

        print(f"✅ {sid}")

    print(f"\nTotal: {len(SKILLS)} skills generated.")


if __name__ == "__main__":
    generate_all()

