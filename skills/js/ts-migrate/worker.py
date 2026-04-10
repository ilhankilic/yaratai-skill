# filepath: skills/js/ts-migrate/worker.py
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
