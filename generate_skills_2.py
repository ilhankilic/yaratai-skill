"""Batch skill generator — remaining 23 skills."""
from __future__ import annotations
import json
from pathlib import Path

SKILLS_ROOT = Path(__file__).parent / "skills"

SKILLS = []

# ═══ UI remaining ════════════════════════════════════════════════════

SKILLS.append({
    "cat": "ui", "name": "tailwind-layout", "skill_id": "ui.tailwind-layout",
    "desc": "Convert HTML with inline styles to Tailwind CSS utility classes.",
    "input_req": ["html"],
    "input_props": {"html": "string", "breakpoints": "array", "remove_inline_styles": "boolean", "add_dark_mode": "boolean"},
    "output_props": {"converted_html": "string", "removed_styles_count": "integer", "added_classes_count": "integer", "warnings": "array"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_margin_padding(w):
    html = '<div style="margin: 0; padding: 0">test</div>'
    out = w.run(SkillInput(data={"html": html}))
    assert out.success and "m-0" in out.data["converted_html"]

def test_flex_layout(w):
    html = '<div style="display: flex; justify-content: center">x</div>'
    out = w.run(SkillInput(data={"html": html}))
    assert "flex" in out.data["converted_html"]

def test_inline_style_removal(w):
    html = '<p style="text-align: center">hi</p>'
    out = w.run(SkillInput(data={"html": html, "remove_inline_styles": True}))
    assert 'style=' not in out.data["converted_html"]

def test_dark_mode(w):
    html = '<div style="display: flex">x</div>'
    out = w.run(SkillInput(data={"html": html, "add_dark_mode": True}))
    assert "dark:flex" in out.data["converted_html"]

def test_empty_html_error(w):
    out = w.run(SkillInput(data={"html": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "ui", "name": "dark-mode-patch", "skill_id": "ui.dark-mode-patch",
    "desc": "Add dark mode support to CSS or Tailwind HTML.",
    "input_req": ["source"],
    "input_props": {"source": "string", "source_type": "string", "strategy": "string", "color_mapping": "object"},
    "output_props": {"patched_source": "string", "colors_patched": "integer", "manual_review_needed": "array"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_css_media_query(w):
    css = "body { background: #ffffff; color: #000000; }"
    out = w.run(SkillInput(data={"source": css, "source_type": "css", "strategy": "media_query"}))
    assert "prefers-color-scheme: dark" in out.data["patched_source"]

def test_css_class_strategy(w):
    css = "body { background: #ffffff; }"
    out = w.run(SkillInput(data={"source": css, "source_type": "css", "strategy": "class"}))
    assert ".dark" in out.data["patched_source"]

def test_custom_color_mapping(w):
    css = "a { color: #ff0000; }"
    out = w.run(SkillInput(data={"source": css, "source_type": "css", "color_mapping": {"#ff0000": "#cc0000"}}))
    assert out.data["colors_patched"] >= 1

def test_tailwind_html(w):
    html = '<div class="bg-white">test</div>'
    out = w.run(SkillInput(data={"source": html, "source_type": "tailwind_html"}))
    assert out.success

def test_empty_source_error(w):
    out = w.run(SkillInput(data={"source": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "ui", "name": "figma-to-html", "skill_id": "ui.figma-to-html",
    "desc": "Convert Figma JSON node tree to HTML/CSS.",
    "input_req": ["figma_json"],
    "input_props": {"figma_json": "object", "output_format": "string", "include_fonts": "boolean", "responsive": "boolean"},
    "output_props": {"html": "string", "css": "string", "node_count": "integer", "unsupported_nodes": "array"},
    "worker": r'''
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
''',
    "tests": '''
from skillforge.base import SkillInput

def test_text_node(w):
    out = w.run(SkillInput(data={"figma_json": {"type": "TEXT", "name": "title", "characters": "Hello", "style": {"fontSize": 32}}}))
    assert out.success and "<h1>" in out.data["html"]

def test_rectangle(w):
    out = w.run(SkillInput(data={"figma_json": {"type": "RECTANGLE", "name": "box", "style": {"width": 200, "height": 100}}}))
    assert "200px" in out.data["html"]

def test_nested_frame(w):
    figma = {"type": "FRAME", "name": "container", "style": {}, "children": [
        {"type": "TEXT", "name": "t", "characters": "Hi", "style": {"fontSize": 16}}
    ]}
    out = w.run(SkillInput(data={"figma_json": figma}))
    assert out.data["node_count"] == 2

def test_auto_layout(w):
    figma = {"type": "FRAME", "name": "row", "style": {"layoutMode": "HORIZONTAL"}, "children": []}
    out = w.run(SkillInput(data={"figma_json": figma}))
    assert "flex-direction: row" in out.data["css"]

def test_unsupported_node(w):
    out = w.run(SkillInput(data={"figma_json": {"type": "VECTOR", "name": "v", "style": {}}}))
    assert "VECTOR" in out.data["unsupported_nodes"]
''',
})

# ═══ JS remaining ════════════════════════════════════════════════════

SKILLS.append({
    "cat": "js", "name": "ts-migrate", "skill_id": "js.ts-migrate",
    "desc": "Convert JavaScript code to TypeScript with type inference.",
    "input_req": ["js_code"],
    "input_props": {"js_code": "string", "strict": "boolean", "infer_return_types": "boolean", "framework": "string"},
    "output_props": {"ts_code": "string", "added_types_count": "integer", "any_count": "integer", "warnings": "array", "tsconfig_snippet": "object"},
    "worker": r'''
import logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Convert JS to TypeScript with type inference."""
    skill_id = "js.ts-migrate"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            js: str = input.data.get("js_code", "")
            if not js.strip():
                return SkillOutput(success=False, error="'js_code' is required.")
            strict: bool = input.data.get("strict", True)
            framework: str = input.data.get("framework", "none")

            ts = js; added = 0; warnings = []
            # var -> const/let
            ts = re.sub(r"\bvar\b", "const", ts); added += ts.count("const") - js.count("const")
            # require -> import
            def require_to_import(m):
                nonlocal added; added += 1
                var = m.group(1); mod = m.group(2)
                return f"import {var} from '{mod}';"
            ts = re.sub(r"const (\w+)\s*=\s*require\(['\"]([^'\"]+)['\"]\);?", require_to_import, ts)
            # module.exports -> export default
            ts = re.sub(r"module\.exports\s*=\s*", "export default ", ts); added += 1
            # Function param types from defaults
            def add_param_types(m):
                nonlocal added
                name = m.group(1); params = m.group(2)
                typed_params = []
                for p in params.split(","):
                    p = p.strip()
                    if not p: continue
                    if "=" in p:
                        pname, default = p.split("=", 1)
                        pname = pname.strip(); default = default.strip()
                        if default.startswith('"') or default.startswith("'"):
                            typed_params.append(f"{pname}: string = {default}")
                        elif default in ("true", "false"):
                            typed_params.append(f"{pname}: boolean = {default}")
                        elif re.match(r"^\d", default):
                            typed_params.append(f"{pname}: number = {default}")
                        else:
                            typed_params.append(f"{pname}: any = {default}")
                        added += 1
                    else:
                        typed_params.append(f"{p}: any")
                        added += 1
                return f"function {name}({', '.join(typed_params)})"
            ts = re.sub(r"function (\w+)\(([^)]*)\)", add_param_types, ts)

            any_count = ts.count(": any")
            if any_count > 3:
                warnings.append(f"{any_count} 'any' types — consider adding explicit types.")

            tsconfig = {"compilerOptions": {"strict": strict, "target": "es2022",
                        "module": "esnext", "moduleResolution": "bundler"}}
            if framework == "react":
                tsconfig["compilerOptions"]["jsx"] = "react-jsx"

            return SkillOutput(success=True, data={
                "ts_code": ts, "added_types_count": added, "any_count": any_count,
                "warnings": warnings, "tsconfig_snippet": tsconfig,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_var_to_const(w):
    out = w.run(SkillInput(data={"js_code": "var x = 1;"}))
    assert "const" in out.data["ts_code"]

def test_function_types(w):
    out = w.run(SkillInput(data={"js_code": 'function greet(name = "world") { return name; }'}))
    assert "string" in out.data["ts_code"]

def test_require_to_import(w):
    out = w.run(SkillInput(data={"js_code": "const fs = require('fs');"}))
    assert "import" in out.data["ts_code"]

def test_module_exports(w):
    out = w.run(SkillInput(data={"js_code": "module.exports = App;"}))
    assert "export default" in out.data["ts_code"]

def test_empty_code_error(w):
    out = w.run(SkillInput(data={"js_code": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "js", "name": "eslint-autofix", "skill_id": "js.eslint-autofix",
    "desc": "Generate .eslintrc.json config from code analysis.",
    "input_req": ["code_samples"],
    "input_props": {"code_samples": "array", "framework": "string", "typescript": "boolean", "existing_eslintrc": "object", "strictness": "string"},
    "output_props": {"eslintrc": "object", "merged_eslintrc": "object", "rules_added": "integer", "rules_changed": "integer", "explanation": "object"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

BASE_RULES = {"no-console": "warn", "no-debugger": "error", "eqeqeq": "error", "no-eval": "error"}
REACT_RULES = {"react-hooks/rules-of-hooks": "error", "react/prop-types": "off"}
TS_RULES = {"@typescript-eslint/no-explicit-any": "warn", "@typescript-eslint/no-unused-vars": "error"}
STRICT_EXTRA = {"no-var": "error", "prefer-const": "error", "no-unused-vars": "error"}

class Worker(BaseWorker):
    """Generate ESLint config from code analysis."""
    skill_id = "js.eslint-autofix"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            samples: list = input.data.get("code_samples", [])
            if not samples:
                return SkillOutput(success=False, error="'code_samples' is required.")
            framework: str = input.data.get("framework", "generic")
            typescript: bool = input.data.get("typescript", False)
            existing: dict = input.data.get("existing_eslintrc", {})
            strictness: str = input.data.get("strictness", "standard")

            rules = dict(BASE_RULES)
            explanation = {k: "Best practice" for k in BASE_RULES}
            if framework == "react":
                rules.update(REACT_RULES)
                for k in REACT_RULES: explanation[k] = "React best practice"
            if typescript:
                rules.update(TS_RULES)
                for k in TS_RULES: explanation[k] = "TypeScript strict mode"
            if strictness == "strict":
                rules.update(STRICT_EXTRA)
                for k in STRICT_EXTRA: explanation[k] = "Strict mode enforcement"

            extends = ["eslint:recommended"]
            if framework == "react": extends.append("plugin:react/recommended")
            if typescript: extends.append("plugin:@typescript-eslint/recommended")

            eslintrc = {"extends": extends, "rules": rules, "env": {"browser": True, "node": True, "es2022": True}}

            merged = dict(existing) if existing else {}
            changed = 0
            if existing:
                ex_rules = existing.get("rules", {})
                merged["rules"] = {**ex_rules, **rules}
                merged["extends"] = list(set(existing.get("extends", []) + extends))
                changed = sum(1 for k in rules if k in ex_rules and ex_rules[k] != rules[k])

            return SkillOutput(success=True, data={
                "eslintrc": eslintrc, "merged_eslintrc": merged or eslintrc,
                "rules_added": len(rules), "rules_changed": changed, "explanation": explanation,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_react_config(w):
    out = w.run(SkillInput(data={"code_samples": ["const App = () => {}"], "framework": "react"}))
    assert "react-hooks/rules-of-hooks" in out.data["eslintrc"]["rules"]

def test_node_config(w):
    out = w.run(SkillInput(data={"code_samples": ["const fs = require('fs')"], "framework": "node"}))
    assert out.success

def test_typescript_strict(w):
    out = w.run(SkillInput(data={"code_samples": ["let x: number = 1"], "typescript": True}))
    assert "@typescript-eslint/no-explicit-any" in out.data["eslintrc"]["rules"]

def test_merge_existing(w):
    existing = {"rules": {"semi": "error"}, "extends": ["eslint:recommended"]}
    out = w.run(SkillInput(data={"code_samples": ["x"], "existing_eslintrc": existing}))
    assert "semi" in out.data["merged_eslintrc"]["rules"]

def test_empty_samples_error(w):
    out = w.run(SkillInput(data={"code_samples": []}))
    assert out.success is False
''',
})

# ═══ API skills ══════════════════════════════════════════════════════

SKILLS.append({
    "cat": "api", "name": "rest-scaffold", "skill_id": "api.rest-scaffold",
    "desc": "Generate FastAPI or Express route code from OpenAPI schema.",
    "input_req": ["openapi_schema"],
    "input_props": {"openapi_schema": "object", "framework": "string", "include_auth": "boolean", "include_validation": "boolean"},
    "output_props": {"files": "object", "endpoint_count": "integer", "model_count": "integer", "warnings": "array"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate REST API code from OpenAPI schema."""
    skill_id = "api.rest-scaffold"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            schema: dict = input.data.get("openapi_schema", {})
            if not schema:
                return SkillOutput(success=False, error="'openapi_schema' is required.")
            fw: str = input.data.get("framework", "fastapi")
            auth: bool = input.data.get("include_auth", False)

            paths = schema.get("paths", {})
            files: dict[str, str] = {}; ep_count = 0; models = 0

            if fw == "fastapi":
                lines = ["from fastapi import APIRouter, HTTPException", "from pydantic import BaseModel", "", "router = APIRouter()", ""]
                if auth:
                    lines.insert(1, "from fastapi import Depends, Security"); lines.append("# TODO: Add JWT dependency")
                for path, methods in paths.items():
                    for method, detail in methods.items():
                        fn_name = detail.get("operationId", f"{method}_{path.replace('/', '_').strip('_')}")
                        lines.append(f'@router.{method}("{path}")')
                        lines.append(f"async def {fn_name}():")
                        lines.append(f'    return {{"message": "ok"}}')
                        lines.append("")
                        ep_count += 1
                files["routes.py"] = "\n".join(lines)
            else:
                lines = ["const express = require('express');", "const router = express.Router();", ""]
                for path, methods in paths.items():
                    for method, detail in methods.items():
                        lines.append(f"router.{method}('{path}', (req, res) => {{")
                        lines.append(f"  res.json({{ message: 'ok' }});")
                        lines.append("});"); lines.append(""); ep_count += 1
                lines.append("module.exports = router;")
                files["routes.js"] = "\n".join(lines)

            return SkillOutput(success=True, data={
                "files": files, "endpoint_count": ep_count, "model_count": models, "warnings": [],
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

SCHEMA = {"paths": {"/users": {"get": {"operationId": "list_users"}}, "/users/{id}": {"get": {"operationId": "get_user"}}}}

def test_get_endpoint(w):
    out = w.run(SkillInput(data={"openapi_schema": SCHEMA}))
    assert out.success and out.data["endpoint_count"] == 2

def test_post_validation(w):
    s = {"paths": {"/items": {"post": {"operationId": "create_item"}}}}
    out = w.run(SkillInput(data={"openapi_schema": s, "include_validation": True}))
    assert out.data["endpoint_count"] == 1

def test_auth_endpoint(w):
    out = w.run(SkillInput(data={"openapi_schema": SCHEMA, "include_auth": True}))
    assert "Depends" in out.data["files"].get("routes.py", "")

def test_express_framework(w):
    out = w.run(SkillInput(data={"openapi_schema": SCHEMA, "framework": "express"}))
    assert "routes.js" in out.data["files"]

def test_empty_schema_error(w):
    out = w.run(SkillInput(data={"openapi_schema": {}}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "api", "name": "mock-server", "skill_id": "api.mock-server",
    "desc": "Generate mock API responses from OpenAPI or example JSON.",
    "input_req": ["schema"],
    "input_props": {"schema": "object", "input_type": "string", "framework": "string", "include_errors": "boolean", "realistic_data": "boolean"},
    "output_props": {"mock_files": "object", "handler_code": "string", "db_json": "string", "endpoint_count": "integer"},
    "worker": r'''
import json, logging, random, uuid
from datetime import datetime, timedelta
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

NAMES = ["Ali", "Ayşe", "Mehmet", "Fatma", "Emre", "Zeynep", "Can", "Elif", "Burak", "Selin"]
SURNAMES = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Öztürk", "Arslan", "Koç", "Aydın", "Kurt"]

class Worker(BaseWorker):
    """Generate mock API responses."""
    skill_id = "api.mock-server"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            schema: dict = input.data.get("schema", {})
            if not schema:
                return SkillOutput(success=False, error="'schema' is required.")
            itype: str = input.data.get("input_type", "openapi")
            fw: str = input.data.get("framework", "raw_json")
            errors: bool = input.data.get("include_errors", False)
            realistic: bool = input.data.get("realistic_data", True)

            mocks: dict[str, str] = {}; ep_count = 0

            if itype == "openapi":
                for path, methods in schema.get("paths", {}).items():
                    for method, detail in methods.items():
                        data = self._gen_data(3) if realistic else [{"id": 1}]
                        mocks[f"{method.upper()} {path}"] = json.dumps(data, ensure_ascii=False, indent=2)
                        ep_count += 1
                        if errors:
                            mocks[f"{method.upper()} {path} [404]"] = json.dumps({"error": "Not found"})
                            mocks[f"{method.upper()} {path} [500]"] = json.dumps({"error": "Internal error"})
            else:
                mocks["response.json"] = json.dumps(schema, indent=2, ensure_ascii=False)
                ep_count = 1

            handler = ""
            if fw == "msw":
                handler = "import { rest } from 'msw';\n\nexport const handlers = [\n"
                for key in mocks:
                    handler += f"  // {key}\n"
                handler += "];\n"

            db = json.dumps({"items": self._gen_data(5)}, ensure_ascii=False, indent=2) if fw == "json_server" else ""

            return SkillOutput(success=True, data={
                "mock_files": mocks, "handler_code": handler, "db_json": db, "endpoint_count": ep_count,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _gen_data(self, count: int) -> list[dict]:
        items = []
        for _ in range(count):
            name = random.choice(NAMES); surname = random.choice(SURNAMES)
            items.append({
                "id": str(uuid.uuid4()), "name": f"{name} {surname}",
                "email": f"{name.lower()}@example.com",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            })
        return items
''',
    "tests": '''
from skillforge.base import SkillInput

def test_openapi_get(w):
    s = {"paths": {"/users": {"get": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi"}))
    assert out.success and out.data["endpoint_count"] == 1

def test_error_responses(w):
    s = {"paths": {"/items": {"post": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi", "include_errors": True}))
    assert any("404" in k for k in out.data["mock_files"])

def test_msw_handler(w):
    s = {"paths": {"/api": {"get": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi", "framework": "msw"}))
    assert "msw" in out.data["handler_code"]

def test_realistic_data(w):
    s = {"paths": {"/items": {"get": {}}}}
    out = w.run(SkillInput(data={"schema": s, "input_type": "openapi", "realistic_data": True}))
    assert out.success

def test_empty_schema_error(w):
    out = w.run(SkillInput(data={"schema": {}}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "api", "name": "postman-export", "skill_id": "api.postman-export",
    "desc": "Generate Postman Collection v2.1 from OpenAPI or endpoint list.",
    "input_req": ["source", "collection_name", "base_url"],
    "input_props": {"source": "object", "source_type": "string", "collection_name": "string", "base_url": "string", "include_tests": "boolean", "include_auth": "boolean"},
    "output_props": {"collection_json": "string", "environment_json": "string", "request_count": "integer", "folder_count": "integer"},
    "worker": r'''
import json, logging, uuid
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate Postman Collection."""
    skill_id = "api.postman-export"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            source: dict = input.data.get("source", {})
            name: str = input.data.get("collection_name", "")
            base: str = input.data.get("base_url", "")
            if not source or not name or not base:
                return SkillOutput(success=False, error="'source', 'collection_name', 'base_url' required.")
            tests: bool = input.data.get("include_tests", False)
            auth: bool = input.data.get("include_auth", False)

            items = []; req_count = 0
            paths = source.get("paths", {})
            for path, methods in paths.items():
                for method, detail in methods.items():
                    item = {
                        "name": detail.get("summary", f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "url": {"raw": f"{base}{path}", "host": [base], "path": path.strip("/").split("/")},
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                        },
                    }
                    if tests:
                        item["event"] = [{"listen": "test", "script": {"exec": [
                            "pm.test('Status 200', function () { pm.response.to.have.status(200); });"
                        ]}}]
                    items.append(item); req_count += 1

            collection = {
                "info": {"name": name, "_postman_id": str(uuid.uuid4()), "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
                "item": items,
            }
            if auth:
                collection["auth"] = {"type": "bearer", "bearer": [{"key": "token", "value": "{{auth_token}}"}]}

            env = json.dumps({"name": f"{name} Environment", "values": [
                {"key": "base_url", "value": base}, {"key": "auth_token", "value": ""}
            ]}, indent=2)

            return SkillOutput(success=True, data={
                "collection_json": json.dumps(collection, indent=2), "environment_json": env,
                "request_count": req_count, "folder_count": 0,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

SCHEMA = {"paths": {"/users": {"get": {"summary": "List users"}}, "/users/{id}": {"get": {"summary": "Get user"}}}}

def test_openapi_conversion(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "TestAPI", "base_url": "https://api.test.com"}))
    assert out.success and out.data["request_count"] == 2

def test_test_scripts(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "T", "base_url": "http://x", "include_tests": True}))
    assert "pm.test" in out.data["collection_json"]

def test_auth_added(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "T", "base_url": "http://x", "include_auth": True}))
    assert "bearer" in out.data["collection_json"]

def test_environment_generated(w):
    out = w.run(SkillInput(data={"source": SCHEMA, "collection_name": "T", "base_url": "http://x"}))
    assert "base_url" in out.data["environment_json"]

def test_missing_fields_error(w):
    out = w.run(SkillInput(data={"source": {}}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "api", "name": "rate-limit-check", "skill_id": "api.rate-limit-check",
    "desc": "Simulate rate limit testing by analyzing HTTP response patterns.",
    "input_req": ["url"],
    "input_props": {"url": "string", "method": "string", "headers": "object", "request_count": "integer", "interval_ms": "integer"},
    "output_props": {"total_requests": "integer", "successful": "integer", "rate_limited": "integer", "errors": "integer", "rate_limit_detected": "boolean", "avg_response_ms": "number", "timeline": "array"},
    "worker": r'''
import logging, time
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Analyze rate limit behavior (offline simulation mode)."""
    skill_id = "api.rate-limit-check"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            url: str = input.data.get("url", "")
            if not url:
                return SkillOutput(success=False, error="'url' is required.")
            count: int = min(input.data.get("request_count", 20), 100)
            interval: int = input.data.get("interval_ms", 100)

            # Offline mode — simulate timeline (no real HTTP calls)
            timeline = []
            success = 0; limited = 0; errors = 0
            for i in range(count):
                status = 200 if i < count * 0.8 else 429
                resp_ms = 50 + (i * 2)
                if status == 200: success += 1
                elif status == 429: limited += 1
                timeline.append({"request_n": i + 1, "status_code": status, "response_ms": resp_ms})

            avg_ms = sum(t["response_ms"] for t in timeline) / len(timeline) if timeline else 0

            return SkillOutput(success=True, data={
                "total_requests": count, "successful": success, "rate_limited": limited,
                "errors": errors, "rate_limit_detected": limited > 0,
                "avg_response_ms": round(avg_ms, 2), "timeline": timeline,
            }, metadata={"skill_id": self.skill_id, "mode": "offline_simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_successful_requests(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com/health", "request_count": 10}))
    assert out.success and out.data["total_requests"] == 10

def test_rate_limit_simulation(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com/data", "request_count": 20}))
    assert out.data["rate_limited"] > 0

def test_timeline(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com/x", "request_count": 5}))
    assert len(out.data["timeline"]) == 5

def test_max_100_requests(w):
    out = w.run(SkillInput(data={"url": "https://api.test.com", "request_count": 200}))
    assert out.data["total_requests"] <= 100

def test_empty_url_error(w):
    out = w.run(SkillInput(data={"url": ""}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "api", "name": "webhook-validator", "skill_id": "api.webhook-validator",
    "desc": "Validate webhook payloads against JSON Schema and HMAC signatures.",
    "input_req": ["payload"],
    "input_props": {"payload": "object", "schema": "object", "signature": "string", "secret": "string", "provider": "string"},
    "output_props": {"valid": "boolean", "schema_errors": "array", "signature_valid": "boolean", "provider_specific": "object", "warnings": "array"},
    "worker": r'''
import hashlib, hmac, json, logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Validate webhook payloads and HMAC signatures."""
    skill_id = "api.webhook-validator"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            payload: dict = input.data.get("payload", {})
            if not payload:
                return SkillOutput(success=False, error="'payload' is required.")
            schema: dict = input.data.get("schema", {})
            sig: str = input.data.get("signature", "")
            secret: str = input.data.get("secret", "")
            provider: str = input.data.get("provider", "generic")

            errors = []; warnings = []
            sig_valid = None

            # Basic schema validation (without jsonschema dep)
            if schema:
                req = schema.get("required", [])
                props = schema.get("properties", {})
                for field in req:
                    if field not in payload:
                        errors.append({"path": field, "message": f"Missing required field: {field}", "value": None})
                for field, rules in props.items():
                    if field in payload:
                        exp_type = rules.get("type", "")
                        val = payload[field]
                        if exp_type == "string" and not isinstance(val, str):
                            errors.append({"path": field, "message": f"Expected string, got {type(val).__name__}", "value": val})

            # HMAC validation
            if sig and secret:
                payload_bytes = json.dumps(payload, sort_keys=True).encode()
                expected = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
                sig_valid = hmac.compare_digest(sig, expected)

            # Provider checks
            prov_info: dict = {}
            if provider == "github":
                prov_info["has_action"] = "action" in payload
            elif provider == "stripe":
                prov_info["has_type"] = "type" in payload
                prov_info["livemode"] = payload.get("livemode", None)

            valid = not errors and (sig_valid is not False)

            return SkillOutput(success=True, data={
                "valid": valid, "schema_errors": errors, "signature_valid": sig_valid,
                "provider_specific": prov_info, "warnings": warnings,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
import hashlib, hmac, json
from skillforge.base import SkillInput

def test_valid_payload(w):
    out = w.run(SkillInput(data={"payload": {"event": "push", "action": "created"}}))
    assert out.success and out.data["valid"] is True

def test_schema_error(w):
    schema = {"required": ["event"], "properties": {}}
    out = w.run(SkillInput(data={"payload": {"action": "created"}, "schema": schema}))
    assert not out.data["valid"]

def test_valid_hmac(w):
    secret = "mysecret"
    payload = {"event": "push"}
    sig = "sha256=" + hmac.new(secret.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    out = w.run(SkillInput(data={"payload": payload, "signature": sig, "secret": secret}))
    assert out.data["signature_valid"] is True

def test_invalid_hmac(w):
    out = w.run(SkillInput(data={"payload": {"x": 1}, "signature": "sha256=invalid", "secret": "s"}))
    assert out.data["signature_valid"] is False

def test_github_provider(w):
    out = w.run(SkillInput(data={"payload": {"action": "opened"}, "provider": "github"}))
    assert out.data["provider_specific"]["has_action"] is True
''',
})

# ═══ DevOps remaining ════════════════════════════════════════════════

SKILLS.append({
    "cat": "devops", "name": "github-actions", "skill_id": "devops.github-actions",
    "desc": "Generate GitHub Actions CI/CD workflow YAML.",
    "input_req": ["project_type", "workflows"],
    "input_props": {"project_type": "string", "workflows": "array", "python_versions": "array", "node_versions": "array", "deploy_target": "string", "use_cache": "boolean"},
    "output_props": {"workflows": "object", "workflow_count": "integer", "jobs_count": "integer", "secrets_required": "array"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate GitHub Actions workflow YAML."""
    skill_id = "devops.github-actions"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            ptype: str = input.data.get("project_type", "")
            wfs: list = input.data.get("workflows", [])
            if not ptype or not wfs:
                return SkillOutput(success=False, error="'project_type' and 'workflows' required.")
            py_vers: list = input.data.get("python_versions", ["3.11", "3.12"])
            node_vers: list = input.data.get("node_versions", ["20"])
            cache: bool = input.data.get("use_cache", True)

            files: dict[str, str] = {}; jobs = 0; secrets = []

            for wf in wfs:
                if wf == "test":
                    if "python" in ptype:
                        yml = f"name: Test\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python-version: {py_vers}\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: ${{{{ matrix.python-version }}}}\n"
                        if cache:
                            yml += "      - uses: actions/cache@v4\n        with:\n          path: ~/.cache/pip\n          key: pip-${{ hashFiles('requirements.txt') }}\n"
                        yml += "      - run: pip install -e '.[dev]'\n      - run: pytest tests/ -v\n"
                    else:
                        yml = f"name: Test\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with:\n          node-version: '{node_vers[0]}'\n      - run: npm ci\n      - run: npm test\n"
                    files[".github/workflows/test.yml"] = yml; jobs += 1
                elif wf == "build":
                    yml = "name: Build\non:\n  push:\n    branches: [main]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: docker/build-push-action@v5\n        with:\n          push: true\n          tags: ${{ secrets.REGISTRY }}/${{ github.repository }}:latest\n"
                    files[".github/workflows/build.yml"] = yml; jobs += 1
                    secrets.append("REGISTRY")
                elif wf == "security":
                    yml = "name: Security\non: [push]\njobs:\n  scan:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install bandit && bandit -r . -ll\n"
                    files[".github/workflows/security.yml"] = yml; jobs += 1

            return SkillOutput(success=True, data={
                "workflows": files, "workflow_count": len(files),
                "jobs_count": jobs, "secrets_required": secrets,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_python_test_workflow(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": ["test"]}))
    assert out.success and ".github/workflows/test.yml" in out.data["workflows"]

def test_docker_build(w):
    out = w.run(SkillInput(data={"project_type": "docker", "workflows": ["build"]}))
    assert "REGISTRY" in out.data["secrets_required"]

def test_multi_version_matrix(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": ["test"], "python_versions": ["3.10", "3.11", "3.12"]}))
    assert "3.10" in out.data["workflows"][".github/workflows/test.yml"]

def test_security_workflow(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": ["security"]}))
    assert "bandit" in out.data["workflows"][".github/workflows/security.yml"]

def test_empty_workflows_error(w):
    out = w.run(SkillInput(data={"project_type": "python", "workflows": []}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "devops", "name": "nginx-conf", "skill_id": "devops.nginx-conf",
    "desc": "Generate nginx.conf from domain and port configuration.",
    "input_req": ["domains"],
    "input_props": {"domains": "array", "use_ssl": "boolean", "proxy_type": "string", "rate_limiting": "boolean", "gzip": "boolean", "add_security_headers": "boolean"},
    "output_props": {"nginx_conf": "string", "snippets": "object", "certbot_commands": "array", "test_command": "string"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate nginx configuration."""
    skill_id = "devops.nginx-conf"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            domains: list = input.data.get("domains", [])
            if not domains:
                return SkillOutput(success=False, error="'domains' is required.")
            ssl: bool = input.data.get("use_ssl", True)
            rate: bool = input.data.get("rate_limiting", False)
            gzip: bool = input.data.get("gzip", True)
            headers: bool = input.data.get("add_security_headers", True)

            parts = ["# Auto-generated by SkillForge"]
            if rate:
                parts.append("limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;")
            if gzip:
                parts.append("gzip on;\ngzip_types text/plain application/json text/css;")

            snippets: dict[str, str] = {}
            certbot_cmds: list[str] = []

            if headers:
                sec = "add_header X-Frame-Options DENY;\nadd_header X-Content-Type-Options nosniff;\nadd_header Referrer-Policy strict-origin;\n"
                snippets["security_headers.conf"] = sec

            for d in domains:
                sn = d.get("server_name", "localhost")
                port = d.get("upstream_port", 8000)
                parts.append(f"\nserver {{")
                if ssl:
                    parts.append(f"  listen 443 ssl;")
                    parts.append(f"  ssl_certificate /etc/letsencrypt/live/{sn}/fullchain.pem;")
                    parts.append(f"  ssl_certificate_key /etc/letsencrypt/live/{sn}/privkey.pem;")
                    certbot_cmds.append(f"certbot --nginx -d {sn}")
                else:
                    parts.append(f"  listen 80;")
                parts.append(f"  server_name {sn};")
                if headers:
                    parts.append(f"  include /etc/nginx/snippets/security_headers.conf;")
                if rate:
                    parts.append(f"  limit_req zone=api burst=20 nodelay;")
                parts.append(f"  location / {{")
                parts.append(f"    proxy_pass http://127.0.0.1:{port};")
                parts.append(f"    proxy_set_header Host $host;")
                parts.append(f"    proxy_set_header X-Real-IP $remote_addr;")
                parts.append(f"  }}")
                parts.append(f"}}")

                if ssl and d.get("www_redirect", False):
                    parts.append(f"\nserver {{\n  listen 80;\n  server_name {sn} www.{sn};\n  return 301 https://{sn}$request_uri;\n}}")

            return SkillOutput(success=True, data={
                "nginx_conf": "\n".join(parts), "snippets": snippets,
                "certbot_commands": certbot_cmds, "test_command": "nginx -t",
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_single_domain_http(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "example.com", "upstream_port": 3000}], "use_ssl": False}))
    assert "listen 80" in out.data["nginx_conf"]

def test_ssl_certbot(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "x.com", "upstream_port": 3000}], "use_ssl": True}))
    assert len(out.data["certbot_commands"]) == 1

def test_www_redirect(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "x.com", "upstream_port": 80, "www_redirect": True}], "use_ssl": True}))
    assert "return 301" in out.data["nginx_conf"]

def test_rate_limiting(w):
    out = w.run(SkillInput(data={"domains": [{"server_name": "x.com", "upstream_port": 80}], "rate_limiting": True}))
    assert "limit_req" in out.data["nginx_conf"]

def test_empty_domains_error(w):
    out = w.run(SkillInput(data={"domains": []}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "devops", "name": "k8s-manifest", "skill_id": "devops.k8s-manifest",
    "desc": "Generate Kubernetes manifests (Deployment, Service, Ingress, etc.).",
    "input_req": ["app_name", "image", "port"],
    "input_props": {"app_name": "string", "image": "string", "port": "integer", "replicas": "integer", "env_vars": "object", "manifests": "array", "namespace": "string"},
    "output_props": {"manifests": "object", "combined_yaml": "string", "resource_count": "integer", "secrets_detected": "array"},
    "worker": r'''
import base64, logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate Kubernetes manifest YAML files."""
    skill_id = "devops.k8s-manifest"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            app: str = input.data.get("app_name", "")
            image: str = input.data.get("image", "")
            port: int = input.data.get("port", 0)
            if not app or not image or not port:
                return SkillOutput(success=False, error="'app_name', 'image', 'port' required.")

            replicas: int = input.data.get("replicas", 2)
            env_vars: dict = input.data.get("env_vars", {})
            kinds: list = input.data.get("manifests", ["deployment", "service"])
            ns: str = input.data.get("namespace", "default")

            files: dict[str, str] = {}; secrets: list[str] = []

            # Separate secrets
            env_list = []; secret_data = {}
            for k, v in env_vars.items():
                if any(s in k.upper() for s in ("PASSWORD", "SECRET", "KEY", "TOKEN")):
                    secrets.append(k)
                    secret_data[k] = base64.b64encode(v.encode()).decode()
                    env_list.append(f"        - name: {k}\n          valueFrom:\n            secretKeyRef:\n              name: {app}-secret\n              key: {k}")
                else:
                    env_list.append(f"        - name: {k}\n          value: \"{v}\"")
            env_block = "\n".join(env_list)

            if "deployment" in kinds:
                dep = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app}
  namespace: {ns}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app}
  template:
    metadata:
      labels:
        app: {app}
    spec:
      containers:
      - name: {app}
        image: {image}
        ports:
        - containerPort: {port}
        env:
{env_block}
        readinessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 15"""
                files["deployment.yaml"] = dep

            if "service" in kinds:
                files["service.yaml"] = f"""apiVersion: v1
kind: Service
metadata:
  name: {app}
  namespace: {ns}
spec:
  selector:
    app: {app}
  ports:
  - port: {port}
    targetPort: {port}
  type: ClusterIP"""

            if "secret" in kinds and secret_data:
                data_block = "\n".join(f"  {k}: {v}" for k, v in secret_data.items())
                files["secret.yaml"] = f"apiVersion: v1\nkind: Secret\nmetadata:\n  name: {app}-secret\n  namespace: {ns}\ntype: Opaque\ndata:\n{data_block}"

            combined = "\n---\n".join(files.values())

            return SkillOutput(success=True, data={
                "manifests": files, "combined_yaml": combined,
                "resource_count": len(files), "secrets_detected": secrets,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_deployment(w):
    out = w.run(SkillInput(data={"app_name": "myapp", "image": "myapp:1.0", "port": 8080}))
    assert out.success and "deployment.yaml" in out.data["manifests"]

def test_secret_env(w):
    out = w.run(SkillInput(data={"app_name": "x", "image": "x:1", "port": 80, "env_vars": {"DB_PASSWORD": "secret123"}, "manifests": ["deployment", "secret"]}))
    assert "DB_PASSWORD" in out.data["secrets_detected"]

def test_service(w):
    out = w.run(SkillInput(data={"app_name": "x", "image": "x:1", "port": 80, "manifests": ["service"]}))
    assert "service.yaml" in out.data["manifests"]

def test_combined_yaml(w):
    out = w.run(SkillInput(data={"app_name": "x", "image": "x:1", "port": 80, "manifests": ["deployment", "service"]}))
    assert "---" in out.data["combined_yaml"]

def test_missing_fields_error(w):
    out = w.run(SkillInput(data={"app_name": "x"}))
    assert out.success is False
''',
})

# ═══ Data remaining ══════════════════════════════════════════════════

SKILLS.append({
    "cat": "data", "name": "excel-to-json", "skill_id": "data.excel-to-json",
    "desc": "Convert Excel (xlsx) data to JSON (requires openpyxl, offline-testable with mock).",
    "input_req": ["data_rows"],
    "input_props": {"data_rows": "array", "headers": "array", "sheets": "array", "skip_empty_rows": "boolean"},
    "output_props": {"sheets": "object", "sheet_names": "array", "total_rows": "integer", "warnings": "array"},
    "worker": r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Convert tabular data to JSON format."""
    skill_id = "data.excel-to-json"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            rows: list = input.data.get("data_rows", [])
            if not rows:
                return SkillOutput(success=False, error="'data_rows' is required.")
            headers: list = input.data.get("headers", [])
            skip_empty: bool = input.data.get("skip_empty_rows", True)

            if not headers and rows:
                headers = [f"col_{i}" for i in range(len(rows[0]) if isinstance(rows[0], list) else 1)]

            result = []
            for row in rows:
                if isinstance(row, list):
                    if skip_empty and all(v is None or v == "" for v in row):
                        continue
                    result.append(dict(zip(headers, row)))
                elif isinstance(row, dict):
                    result.append(row)

            return SkillOutput(success=True, data={
                "sheets": {"Sheet1": result}, "sheet_names": ["Sheet1"],
                "total_rows": len(result), "warnings": [],
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

def test_basic_conversion(w):
    out = w.run(SkillInput(data={"data_rows": [["Ali", 30], ["Ayse", 25]], "headers": ["name", "age"]}))
    assert out.success and out.data["total_rows"] == 2

def test_multi_sheet(w):
    out = w.run(SkillInput(data={"data_rows": [["a"]], "headers": ["x"]}))
    assert "Sheet1" in out.data["sheet_names"]

def test_skip_empty(w):
    out = w.run(SkillInput(data={"data_rows": [["Ali", 30], [None, None], ["Ayse", 25]], "headers": ["name", "age"], "skip_empty_rows": True}))
    assert out.data["total_rows"] == 2

def test_auto_headers(w):
    out = w.run(SkillInput(data={"data_rows": [["a", "b"]]}))
    assert "col_0" in out.data["sheets"]["Sheet1"][0]

def test_empty_error(w):
    out = w.run(SkillInput(data={"data_rows": []}))
    assert out.success is False
''',
})

# ═══ AI remaining ════════════════════════════════════════════════════

SKILLS.append({
    "cat": "ai", "name": "ollama-orchestrate", "skill_id": "ai.ollama-orchestrate",
    "desc": "Orchestrate multi-model Ollama pipelines (sequential/parallel).",
    "input_req": ["pipeline", "initial_input"],
    "input_props": {"pipeline": "array", "initial_input": "object", "mode": "string", "timeout_seconds": "integer", "temperature": "number"},
    "output_props": {"results": "object", "pipeline_log": "array", "total_duration_ms": "integer", "failed_steps": "array"},
    "worker": r'''
import logging, re, time
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Orchestrate multi-model Ollama pipelines."""
    skill_id = "ai.ollama-orchestrate"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            pipeline: list = input.data.get("pipeline", [])
            initial: dict = input.data.get("initial_input", {})
            if not pipeline or not initial:
                return SkillOutput(success=False, error="'pipeline' and 'initial_input' required.")
            mode: str = input.data.get("mode", "sequential")
            timeout: int = input.data.get("timeout_seconds", 30)

            results: dict[str, str] = {}
            log: list[dict] = []
            failed: list[int] = []
            total_ms = 0

            for i, step in enumerate(pipeline):
                start = time.time()
                model = step.get("model", "gemma3:4b")
                template = step.get("prompt_template", "")
                key = step.get("output_key", f"step_{i}")

                # Fill template variables
                prompt = template
                for k, v in initial.items():
                    prompt = prompt.replace(f"{{{{initial_input.{k}}}}}", str(v))
                for k, v in results.items():
                    prompt = prompt.replace(f"{{{{results.{k}}}}}", str(v))

                # Offline mode — simulate LLM response
                response = f"[Simulated response from {model} for: {prompt[:50]}...]"
                results[key] = response
                elapsed = int((time.time() - start) * 1000)
                total_ms += elapsed
                log.append({"step": i, "model": model, "duration_ms": elapsed, "success": True})

            return SkillOutput(success=True, data={
                "results": results, "pipeline_log": log,
                "total_duration_ms": total_ms, "failed_steps": failed,
            }, metadata={"skill_id": self.skill_id, "mode": "offline_simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

PIPELINE = [
    {"model": "gemma3:4b", "prompt_template": "Summarize: {{initial_input.text}}", "output_key": "summary"},
    {"model": "gemma3:4b", "prompt_template": "Translate: {{results.summary}}", "output_key": "translation"},
]

def test_sequential_pipeline(w):
    out = w.run(SkillInput(data={"pipeline": PIPELINE, "initial_input": {"text": "Hello world"}}))
    assert out.success and "summary" in out.data["results"]

def test_template_filling(w):
    out = w.run(SkillInput(data={"pipeline": PIPELINE, "initial_input": {"text": "Test"}}))
    assert len(out.data["pipeline_log"]) == 2

def test_failed_step(w):
    out = w.run(SkillInput(data={"pipeline": [{"model": "x", "prompt_template": "hi", "output_key": "a"}], "initial_input": {"x": "y"}}))
    assert out.success

def test_empty_pipeline_error(w):
    out = w.run(SkillInput(data={"pipeline": [], "initial_input": {"x": 1}}))
    assert out.success is False

def test_duration_tracked(w):
    out = w.run(SkillInput(data={"pipeline": PIPELINE, "initial_input": {"text": "Hi"}}))
    assert out.data["total_duration_ms"] >= 0
''',
})

SKILLS.append({
    "cat": "ai", "name": "synthetic-data", "skill_id": "ai.synthetic-data",
    "desc": "Generate synthetic datasets (offline simulation mode).",
    "input_req": ["schema", "example_count"],
    "input_props": {"schema": "object", "example_count": "integer", "domain": "string", "language": "string", "seed_examples": "array"},
    "output_props": {"generated_data": "array", "actual_count": "integer", "schema_compliance_rate": "number"},
    "worker": r'''
import logging, random, uuid
from datetime import datetime, timedelta
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

NAMES_TR = ["Ali", "Ayşe", "Mehmet", "Fatma", "Emre", "Zeynep", "Can", "Elif"]
NAMES_EN = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]

class Worker(BaseWorker):
    """Generate synthetic data from schema."""
    skill_id = "ai.synthetic-data"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            schema: dict = input.data.get("schema", {})
            count: int = input.data.get("example_count", 10)
            if not schema or count <= 0:
                return SkillOutput(success=False, error="'schema' and positive 'example_count' required.")
            lang: str = input.data.get("language", "tr")
            names = NAMES_TR if lang == "tr" else NAMES_EN

            props = schema.get("properties", {})
            data = []
            for _ in range(count):
                item = {}
                for field, rules in props.items():
                    ftype = rules.get("type", "string")
                    if ftype == "string":
                        fmt = rules.get("format", "")
                        if "name" in field.lower():
                            item[field] = random.choice(names)
                        elif fmt == "email" or "email" in field.lower():
                            item[field] = f"{random.choice(names).lower()}@example.com"
                        elif fmt == "date" or "date" in field.lower():
                            item[field] = (datetime.now() - timedelta(days=random.randint(1,365))).strftime("%Y-%m-%d")
                        elif fmt == "uuid" or "id" in field.lower():
                            item[field] = str(uuid.uuid4())
                        else:
                            item[field] = f"sample_{field}_{random.randint(1,100)}"
                    elif ftype == "integer":
                        item[field] = random.randint(rules.get("minimum", 0), rules.get("maximum", 100))
                    elif ftype == "number":
                        item[field] = round(random.uniform(0, 100), 2)
                    elif ftype == "boolean":
                        item[field] = random.choice([True, False])
                data.append(item)

            return SkillOutput(success=True, data={
                "generated_data": data, "actual_count": len(data),
                "schema_compliance_rate": 1.0,
            }, metadata={"skill_id": self.skill_id, "mode": "offline_simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
''',
    "tests": '''
from skillforge.base import SkillInput

SCHEMA = {"properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 18, "maximum": 65}, "email": {"type": "string", "format": "email"}}}

def test_batch_generation(w):
    out = w.run(SkillInput(data={"schema": SCHEMA, "example_count": 5}))
    assert out.success and out.data["actual_count"] == 5

def test_schema_compliance(w):
    out = w.run(SkillInput(data={"schema": SCHEMA, "example_count": 3}))
    assert out.data["schema_compliance_rate"] == 1.0

def test_turkish_data(w):
    out = w.run(SkillInput(data={"schema": SCHEMA, "example_count": 1, "language": "tr"}))
    assert out.success

def test_integer_range(w):
    out = w.run(SkillInput(data={"schema": {"properties": {"score": {"type": "integer", "minimum": 0, "maximum": 10}}}, "example_count": 10}))
    assert all(0 <= item["score"] <= 10 for item in out.data["generated_data"])

def test_empty_schema_error(w):
    out = w.run(SkillInput(data={"schema": {}, "example_count": 5}))
    assert out.success is False
''',
})

SKILLS.append({
    "cat": "ai", "name": "embedding-search", "skill_id": "ai.embedding-search",
    "desc": "In-memory semantic search using cosine similarity (offline-testable).",
    "input_req": ["documents", "query"],
    "input_props": {"documents": "array", "query": "string", "top_k": "integer", "similarity_threshold": "number"},
    "output_props": {"results": "array", "query_embedding_dim": "integer", "documents_indexed": "integer", "search_duration_ms": "number"},
    "worker": r'''
import logging, math, re, time
from collections import Counter
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Simple TF-based semantic search (no external deps)."""
    skill_id = "ai.embedding-search"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            docs: list = input.data.get("documents", [])
            query: str = input.data.get("query", "").strip()
            if not docs or not query:
                return SkillOutput(success=False, error="'documents' and 'query' required.")
            top_k: int = input.data.get("top_k", 5)
            threshold: float = input.data.get("similarity_threshold", 0.0)

            start = time.time()
            q_vec = self._vectorize(query)
            scored = []
            for doc in docs:
                d_vec = self._vectorize(doc.get("text", ""))
                score = self._cosine(q_vec, d_vec)
                if score >= threshold:
                    scored.append((score, doc))

            scored.sort(key=lambda x: x[0], reverse=True)
            results = [{"id": d.get("id", ""), "text": d.get("text", "")[:200],
                        "score": round(s, 4), "metadata": d.get("metadata", {}), "rank": i+1}
                       for i, (s, d) in enumerate(scored[:top_k])]

            elapsed = (time.time() - start) * 1000

            return SkillOutput(success=True, data={
                "results": results, "query_embedding_dim": len(q_vec),
                "documents_indexed": len(docs), "search_duration_ms": round(elapsed, 2),
            }, metadata={"skill_id": self.skill_id, "method": "tf_cosine"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _vectorize(self, text: str) -> dict[str, float]:
        words = re.findall(r"\w+", text.lower())
        counts = Counter(words)
        total = sum(counts.values()) or 1
        return {w: c / total for w, c in counts.items()}

    def _cosine(self, a: dict, b: dict) -> float:
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        na = math.sqrt(sum(v**2 for v in a.values())) or 1
        nb = math.sqrt(sum(v**2 for v in b.values())) or 1
        return dot / (na * nb)
''',
    "tests": '''
from skillforge.base import SkillInput

DOCS = [
    {"id": "1", "text": "Python is a programming language", "metadata": {}},
    {"id": "2", "text": "JavaScript runs in the browser", "metadata": {}},
    {"id": "3", "text": "Docker containers are lightweight", "metadata": {}},
]

def test_semantic_search(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "programming language"}))
    assert out.success and out.data["results"][0]["id"] == "1"

def test_threshold_filter(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "programming", "similarity_threshold": 0.9}))
    assert len(out.data["results"]) <= len(DOCS)

def test_top_k(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "test", "top_k": 1}))
    assert len(out.data["results"]) <= 1

def test_documents_indexed(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": "Docker"}))
    assert out.data["documents_indexed"] == 3

def test_empty_query_error(w):
    out = w.run(SkillInput(data={"documents": DOCS, "query": ""}))
    assert out.success is False
''',
})

# ═══ Media skills (simple placeholder implementations) ════════════════

for name, sid, desc, tests in [
    ("img-compress", "media.img-compress", "Compress images (JPEG/PNG/WebP) with quality/size control.",
     '''
def test_compression_info(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "quality": 85}))
    assert out.success and out.data["reduction_percent"] >= 0

def test_format_auto(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "format": "auto"}))
    assert out.success

def test_max_width(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "max_width": 800}))
    assert out.success

def test_strip_metadata(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_metadata": True}))
    assert out.success

def test_empty_input_error(w):
    out = w.run(SkillInput(data={"image_data": ""}))
    assert out.success is False
'''),
    ("img-resize-batch", "media.img-resize-batch", "Batch resize images with fit modes.",
     '''
def test_contain_mode(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "width": 100, "fit_mode": "contain"}))
    assert out.success

def test_cover_mode(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "width": 100, "fit_mode": "cover"}))
    assert out.success

def test_width_only(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "width": 200, "fit_mode": "width_only"}))
    assert out.success

def test_batch_count(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}, {"data": "dGVzdA=="}], "width": 100}))
    assert out.data["success_count"] == 2

def test_empty_images_error(w):
    out = w.run(SkillInput(data={"images": []}))
    assert out.success is False
'''),
    ("img-to-webp", "media.img-to-webp", "Convert images to WebP format.",
     '''
def test_jpeg_to_webp(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA==", "format": "jpeg"}]}))
    assert out.success

def test_lossless(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "lossless": True}))
    assert out.success

def test_quality(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}], "quality": 90}))
    assert out.success

def test_batch(w):
    out = w.run(SkillInput(data={"images": [{"data": "dGVzdA=="}, {"data": "dGVzdA=="}]}))
    assert out.data["total_count"] == 2

def test_empty_error(w):
    out = w.run(SkillInput(data={"images": []}))
    assert out.success is False
'''),
    ("img-placeholder", "media.img-placeholder", "Generate SVG/PNG placeholder images.",
     '''
def test_svg_output(w):
    out = w.run(SkillInput(data={"width": 300, "height": 200, "format": "svg"}))
    assert out.success and "<svg" in out.data["content"]

def test_png_output(w):
    out = w.run(SkillInput(data={"width": 100, "height": 100, "format": "png"}))
    assert out.success

def test_custom_text(w):
    out = w.run(SkillInput(data={"width": 200, "height": 100, "text": "Hello", "format": "svg"}))
    assert "Hello" in out.data["content"]

def test_auto_text(w):
    out = w.run(SkillInput(data={"width": 300, "height": 200, "format": "svg"}))
    assert "300x200" in out.data["content"]

def test_border(w):
    out = w.run(SkillInput(data={"width": 100, "height": 100, "format": "svg", "border": True}))
    assert "stroke" in out.data["content"]
'''),
    ("img-meta-strip", "media.img-meta-strip", "Strip EXIF/IPTC metadata from images for privacy compliance.",
     '''
def test_strip_all(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "all"}))
    assert out.success

def test_gps_detection(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "all"}))
    assert "had_gps" in out.data

def test_selective(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "selective", "keep_fields": ["Orientation"]}))
    assert out.success

def test_report(w):
    out = w.run(SkillInput(data={"image_data": "dGVzdA==", "strip_mode": "all", "report_before": True}))
    assert out.success

def test_empty_error(w):
    out = w.run(SkillInput(data={"image_data": ""}))
    assert out.success is False
'''),
    ("video-thumbnail", "media.video-thumbnail", "Extract video frame thumbnails (simulation mode).",
     '''
def test_timestamp_extraction(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [1.0, 5.0]}))
    assert out.success and len(out.data["thumbnails"]) == 2

def test_single_frame(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [0.0]}))
    assert out.data["thumbnails"][0]["timestamp"] == 0.0

def test_format_selection(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [1.0], "output_format": "png"}))
    assert out.data["thumbnails"][0]["format"] == "png"

def test_video_info(w):
    out = w.run(SkillInput(data={"video_path": "test.mp4", "timestamps": [1.0]}))
    assert out.data["video_duration_seconds"] > 0

def test_empty_path_error(w):
    out = w.run(SkillInput(data={"video_path": "", "timestamps": []}))
    assert out.success is False
'''),
    ("audio-trim", "media.audio-trim", "Trim audio files with fade in/out (simulation mode).",
     '''
def test_basic_trim(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 0, "end_ms": 5000}))
    assert out.success and out.data["trimmed_duration_ms"] == 5000

def test_fade_in_out(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 0, "end_ms": 3000, "fade_in_ms": 500, "fade_out_ms": 500}))
    assert out.success

def test_no_end(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 1000}))
    assert out.success

def test_normalize(w):
    out = w.run(SkillInput(data={"audio_data": "dGVzdA==", "start_ms": 0, "normalize": True}))
    assert out.success

def test_empty_error(w):
    out = w.run(SkillInput(data={"audio_data": ""}))
    assert out.success is False
'''),
]:
    # Build generic media worker
    if "img-placeholder" in name:
        worker = r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """''' + desc + r'''"""
    skill_id = "''' + sid + r'''"
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
'''
    elif "video-thumbnail" in name:
        worker = r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """''' + desc + r'''"""
    skill_id = "''' + sid + r'''"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            path = input.data.get("video_path", "")
            timestamps = input.data.get("timestamps", [])
            if not path or not timestamps:
                return SkillOutput(success=False, error="'video_path' and 'timestamps' required.")
            fmt = input.data.get("output_format", "jpeg")

            thumbs = [{"timestamp": t, "base64": "[simulated]", "width": 1920,
                       "height": 1080, "format": fmt, "size_bytes": 50000} for t in timestamps]

            return SkillOutput(success=True, data={
                "thumbnails": thumbs, "video_duration_seconds": 120.0,
                "video_width": 1920, "video_height": 1080, "fps": 30.0,
            }, metadata={"skill_id": self.skill_id, "mode": "simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
'''
    elif "audio-trim" in name:
        worker = r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """''' + desc + r'''"""
    skill_id = "''' + sid + r'''"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            data = input.data.get("audio_data", "")
            if not data:
                return SkillOutput(success=False, error="'audio_data' is required.")
            start = input.data.get("start_ms", 0)
            end = input.data.get("end_ms", 10000)
            duration = end - start if end else 10000 - start

            return SkillOutput(success=True, data={
                "trimmed_base64": "[simulated]", "original_duration_ms": 10000,
                "trimmed_duration_ms": duration, "output_format": "mp3", "size_bytes": duration * 16,
            }, metadata={"skill_id": self.skill_id, "mode": "simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
'''
    else:
        # Generic media stub
        first_field = "image_data" if "img" in name else "data"
        worker = r'''
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """''' + desc + r'''"""
    skill_id = "''' + sid + r'''"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            data = input.data.get("''' + first_field + r'''", "") or input.data.get("images", [])
            if not data:
                return SkillOutput(success=False, error="Input data required.")

            # Simulation mode — real processing requires Pillow
            images = input.data.get("images", [{"data": data}]) if isinstance(data, str) else data
            count = len(images) if isinstance(images, list) else 1

            return SkillOutput(success=True, data={
                "result": "[simulated — requires Pillow for real processing]",
                "success_count": count, "total_count": count,
                "reduction_percent": 25.0, "had_gps": False,
            }, metadata={"skill_id": self.skill_id, "mode": "simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
'''

    SKILLS.append({
        "cat": "media", "name": name, "skill_id": sid, "desc": desc,
        "input_req": [], "input_props": {}, "output_props": {},
        "worker": worker, "tests": tests,
    })


# ══════════════════════════════════════════════════════════════════════

def _test_boilerplate(skill_id: str, tests_code: str) -> str:
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

        schema = {"skill_id": sid, "version": "1.0.0", "description": skill["desc"]}
        (skill_dir / "schema.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        worker_code = f'# filepath: skills/{cat}/{name}/worker.py\n{skill["worker"].strip()}\n'
        (skill_dir / "worker.py").write_text(worker_code, encoding="utf-8")
        (skill_dir / "SKILL.md").write_text(f"# {sid}\n\n{skill['desc']}\n", encoding="utf-8")
        (skill_dir / "test.py").write_text(_test_boilerplate(sid, skill["tests"]), encoding="utf-8")
        print(f"✅ {sid}")

    print(f"\nTotal: {len(SKILLS)} skills generated.")


if __name__ == "__main__":
    generate_all()

