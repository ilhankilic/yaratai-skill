# filepath: skills/js/env-validator/worker.py
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
