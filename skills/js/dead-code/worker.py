# filepath: skills/js/dead-code/worker.py
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
                matched_text = m.group(0)
                if not check_exports and "export" in matched_text:
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
                matched_text = m.group(0)
                if not check_exports and "export" in matched_text:
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
