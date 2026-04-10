# filepath: skills/js/eslint-autofix/worker.py
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
