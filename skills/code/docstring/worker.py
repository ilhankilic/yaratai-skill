"""code.docstring — Add Google/NumPy/Sphinx style docstrings to Python code."""

from __future__ import annotations

import ast
import logging
import textwrap
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

TYPE_DESCRIPTIONS: dict[str, str] = {
    "str": "A string value.",
    "int": "An integer value.",
    "float": "A floating-point value.",
    "bool": "A boolean flag.",
    "list": "A list of items.",
    "dict": "A dictionary of key-value pairs.",
    "None": "No return value.",
}


class Worker(BaseWorker):
    """Add structured docstrings to Python functions and classes."""

    skill_id = "code.docstring"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            source: str = input.data.get("source_code", "")
            if not source.strip():
                return SkillOutput(success=False, error="'source_code' is required.")

            style: str = input.data.get("style", "google")
            overwrite: bool = input.data.get("overwrite_existing", False)
            language: str = input.data.get("language", "en")

            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                return SkillOutput(success=False, error=f"Python syntax error: {e}")

            lines = source.splitlines(keepends=True)
            insertions: list[tuple[int, str]] = []
            funcs_documented = 0
            funcs_skipped = 0
            classes_documented = 0

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    has_docstring = (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    )
                    if has_docstring and not overwrite:
                        funcs_skipped += 1
                        continue

                    indent = self._get_indent(lines, node)
                    docstring = self._build_func_docstring(node, style, indent, language)

                    if has_docstring and overwrite:
                        # Replace existing docstring node
                        insert_line = node.body[0].end_lineno  # type: ignore[attr-defined]
                        insertions.append((node.body[0].lineno - 1, docstring, insert_line - 1))  # type: ignore[arg-type]
                    else:
                        insert_line = node.body[0].lineno - 1
                        insertions.append((insert_line, docstring, None))  # type: ignore[arg-type]
                    funcs_documented += 1

                elif isinstance(node, ast.ClassDef):
                    has_docstring = (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    )
                    if has_docstring and not overwrite:
                        continue
                    indent = self._get_indent(lines, node)
                    class_doc = f'{indent}    """Class {node.name}."""\n'
                    if not has_docstring:
                        insert_line = node.body[0].lineno - 1
                        insertions.append((insert_line, class_doc, None))  # type: ignore[arg-type]
                    classes_documented += 1

            # Apply insertions from bottom to top
            result_lines = list(lines)
            for item in sorted(insertions, key=lambda x: x[0], reverse=True):
                pos, doc, replace_end = item[0], item[1], item[2] if len(item) > 2 else None
                if replace_end is not None:
                    result_lines[pos:replace_end + 1] = [doc]
                else:
                    result_lines.insert(pos, doc)

            documented_code = "".join(result_lines)

            return SkillOutput(
                success=True,
                data={
                    "documented_code": documented_code,
                    "functions_documented": funcs_documented,
                    "functions_skipped": funcs_skipped,
                    "classes_documented": classes_documented,
                },
                metadata={"skill_id": self.skill_id, "style": style},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    def _get_indent(self, lines: list[str], node: ast.AST) -> str:
        """Return indentation string for the given node."""
        if hasattr(node, "col_offset"):
            return " " * node.col_offset  # type: ignore[attr-defined]
        return ""

    def _build_func_docstring(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, style: str, indent: str, language: str
    ) -> str:
        """Build a docstring for a function node."""
        inner = indent + "    "
        name = node.name
        brief = f"Execute {name} operation." if language == "en" else f"{name} işlemini çalıştır."

        # Collect args
        args_info: list[tuple[str, str, str]] = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            ann = self._annotation_str(arg.annotation)
            desc = TYPE_DESCRIPTIONS.get(ann, f"The {arg.arg} parameter.")
            args_info.append((arg.arg, ann, desc))

        # Return type
        ret_ann = self._annotation_str(node.returns)

        if style == "numpy":
            return self._numpy_docstring(inner, brief, args_info, ret_ann)
        elif style == "sphinx":
            return self._sphinx_docstring(inner, brief, args_info, ret_ann)
        else:
            return self._google_docstring(inner, brief, args_info, ret_ann)

    def _google_docstring(self, indent: str, brief: str, args: list, ret: str) -> str:
        """Build Google-style docstring."""
        parts = [f'{indent}"""{brief}\n']
        if args:
            parts.append(f"\n{indent}Args:\n")
            for name, ann, desc in args:
                type_hint = f" ({ann})" if ann else ""
                parts.append(f"{indent}    {name}{type_hint}: {desc}\n")
        if ret and ret != "None":
            parts.append(f"\n{indent}Returns:\n")
            parts.append(f"{indent}    {ret}: The result.\n")
        parts.append(f'{indent}"""\n')
        return "".join(parts)

    def _numpy_docstring(self, indent: str, brief: str, args: list, ret: str) -> str:
        """Build NumPy-style docstring."""
        parts = [f'{indent}"""{brief}\n']
        if args:
            parts.append(f"\n{indent}Parameters\n{indent}----------\n")
            for name, ann, desc in args:
                parts.append(f"{indent}{name} : {ann or 'Any'}\n{indent}    {desc}\n")
        if ret and ret != "None":
            parts.append(f"\n{indent}Returns\n{indent}-------\n{indent}{ret}\n{indent}    The result.\n")
        parts.append(f'{indent}"""\n')
        return "".join(parts)

    def _sphinx_docstring(self, indent: str, brief: str, args: list, ret: str) -> str:
        """Build Sphinx-style docstring."""
        parts = [f'{indent}"""{brief}\n']
        for name, ann, desc in args:
            parts.append(f"\n{indent}:param {name}: {desc}\n")
            if ann:
                parts.append(f"{indent}:type {name}: {ann}\n")
        if ret and ret != "None":
            parts.append(f"{indent}:return: The result.\n{indent}:rtype: {ret}\n")
        parts.append(f'{indent}"""\n')
        return "".join(parts)

    def _annotation_str(self, annotation: ast.expr | None) -> str:
        """Convert AST annotation to string."""
        if annotation is None:
            return ""
        return ast.unparse(annotation)

