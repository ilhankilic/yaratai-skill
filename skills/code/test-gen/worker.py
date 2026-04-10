"""code.test-gen — Generate pytest test cases from Python source code."""
from __future__ import annotations
import ast, logging, re
from typing import Any
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

EXTERNAL_MODULES = {"httpx", "requests", "aiohttp", "sqlalchemy", "redis", "boto3"}


class Worker(BaseWorker):
    """Generate pytest tests by analyzing Python AST."""
    skill_id = "code.test-gen"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            source: str = input.data.get("source_code", "").strip()
            if not source:
                return SkillOutput(success=False, error="'source_code' is required.")

            coverage: str = input.data.get("coverage_target", "full")
            mock_ext: bool = input.data.get("mock_external", True)
            use_fix: bool = input.data.get("use_fixtures", True)

            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                return SkillOutput(success=False, error=f"Syntax error: {e}")

            functions = self._extract_functions(tree)
            imports = self._extract_imports(tree)
            needs_mock = mock_ext and bool(EXTERNAL_MODULES & set(imports))

            test_lines: list[str] = ['"""Auto-generated tests."""', "import pytest"]
            if needs_mock:
                test_lines.append("from unittest.mock import patch, MagicMock")
            test_lines.append("")

            mock_count = 0
            test_count = 0
            covered: list[str] = []

            for func in functions:
                name = func["name"]
                args = func["args"]
                ret = func["return"]
                covered.append(name)

                # Happy path
                test_lines.append(f"def test_{name}_happy_path():")
                call_args = ", ".join(self._default_value(a["annotation"]) for a in args if a["name"] != "self")
                test_lines.append(f"    result = {name}({call_args})")
                test_lines.append(f"    assert result is not None")
                test_lines.append("")
                test_count += 1

                if coverage in ("edge_cases", "full"):
                    test_lines.append(f"def test_{name}_edge_case():")
                    test_lines.append(f"    # Edge case: empty/minimal input")
                    edge_args = ", ".join(self._edge_value(a["annotation"]) for a in args if a["name"] != "self")
                    test_lines.append(f"    result = {name}({edge_args})")
                    test_lines.append(f"    assert result is not None")
                    test_lines.append("")
                    test_count += 1

                if coverage == "full":
                    if func["raises"]:
                        test_lines.append(f"def test_{name}_raises():")
                        exc = func["raises"][0]
                        test_lines.append(f"    with pytest.raises({exc}):")
                        test_lines.append(f"        {name}(None)")
                        test_lines.append("")
                        test_count += 1

                    if needs_mock:
                        test_lines.append(f"@patch('module.external_call')")
                        test_lines.append(f"def test_{name}_with_mock(mock_call):")
                        test_lines.append(f"    mock_call.return_value = MagicMock()")
                        test_lines.append(f"    result = {name}({call_args})")
                        test_lines.append(f"    assert result is not None")
                        test_lines.append("")
                        test_count += 1
                        mock_count += 1

            test_code = "\n".join(test_lines) + "\n"
            estimate = min(1.0, test_count / max(len(functions) * 3, 1))

            return SkillOutput(success=True, data={
                "test_code": test_code, "test_count": test_count,
                "functions_covered": covered, "mock_count": mock_count,
                "coverage_estimate": round(estimate, 2),
            }, metadata={"skill_id": self.skill_id})
        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    def _extract_functions(self, tree: ast.Module) -> list[dict]:
        """Extract function metadata from AST."""
        funcs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [{"name": a.arg, "annotation": ast.unparse(a.annotation) if a.annotation else ""}
                        for a in node.args.args]
                ret = ast.unparse(node.returns) if node.returns else ""
                raises = [ast.unparse(n.exc) if n.exc else "Exception"
                         for n in ast.walk(node) if isinstance(n, ast.Raise)]
                funcs.append({"name": node.name, "args": args, "return": ret, "raises": raises})
        return funcs

    def _extract_imports(self, tree: ast.Module) -> list[str]:
        """Extract imported module names."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])
        return imports

    def _default_value(self, annotation: str) -> str:
        """Generate a default test value from type annotation."""
        mapping = {"str": '"test"', "int": "1", "float": "1.0", "bool": "True",
                   "list": "[]", "dict": "{}", "": '"test"'}
        return mapping.get(annotation, '"test"')

    def _edge_value(self, annotation: str) -> str:
        """Generate an edge-case test value."""
        mapping = {"str": '""', "int": "0", "float": "0.0", "bool": "False",
                   "list": "[]", "dict": "{}", "": '""'}
        return mapping.get(annotation, '""')

