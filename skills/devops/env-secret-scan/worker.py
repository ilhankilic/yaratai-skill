# filepath: skills/devops/env-secret-scan/worker.py
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
