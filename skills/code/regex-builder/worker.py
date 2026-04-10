"""code.regex-builder — Generate regex patterns from natural language descriptions."""

from __future__ import annotations

import logging
import re
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

# ── Known pattern library ────────────────────────────────────────────

KNOWN_PATTERNS: dict[str, dict[str, Any]] = {
    "email": {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "named": r"(?P<user>[a-zA-Z0-9._%+-]+)@(?P<domain>[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        "explanation": "Matches standard email addresses: user@domain.tld",
        "keywords": ["email", "e-posta", "mail", "e-mail"],
    },
    "turkish_phone": {
        "pattern": r"(?:\+90|0)?[- ]?5\d{2}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}",
        "named": r"(?:\+90|0)?[- ]?(?P<area>5\d{2})[- ]?(?P<first>\d{3})[- ]?(?P<second>\d{2})[- ]?(?P<third>\d{2})",
        "explanation": "Matches Turkish mobile numbers: +90 5XX XXX XX XX",
        "keywords": ["telefon", "phone", "cep", "gsm", "turkish phone", "türk telefon"],
    },
    "tc_kimlik": {
        "pattern": r"[1-9]\d{10}",
        "named": r"(?P<tc>[1-9]\d{10})",
        "explanation": "Matches Turkish national ID (11 digits, first non-zero).",
        "keywords": ["tc", "kimlik", "tc kimlik", "national id", "tckn"],
    },
    "url": {
        "pattern": r"https?://[^\s<>\"']+",
        "named": r"(?P<scheme>https?)://(?P<rest>[^\s<>\"']+)",
        "explanation": "Matches HTTP/HTTPS URLs.",
        "keywords": ["url", "link", "web adresi", "website"],
    },
    "ipv4": {
        "pattern": r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
        "named": r"\b(?P<ip>(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))\b",
        "explanation": "Matches IPv4 addresses (0.0.0.0 – 255.255.255.255).",
        "keywords": ["ip", "ipv4", "ip address", "ip adresi"],
    },
    "iso_date": {
        "pattern": r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])",
        "named": r"(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12]\d|3[01])",
        "explanation": "Matches ISO 8601 dates: YYYY-MM-DD.",
        "keywords": ["date", "tarih", "iso date", "iso tarih"],
    },
    "hex_color": {
        "pattern": r"#(?:[0-9a-fA-F]{3}){1,2}\b",
        "named": r"(?P<color>#(?:[0-9a-fA-F]{3}){1,2})\b",
        "explanation": "Matches hex color codes: #RGB or #RRGGBB.",
        "keywords": ["hex", "color", "renk", "hex color", "colour"],
    },
    "uuid": {
        "pattern": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        "named": r"(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
        "explanation": "Matches UUIDs (8-4-4-4-12 hex digits).",
        "keywords": ["uuid", "guid"],
    },
    "semver": {
        "pattern": r"\bv?(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[\w.]+)?(?:\+[\w.]+)?\b",
        "named": r"\bv?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<pre>[\w.]+))?(?:\+(?P<build>[\w.]+))?\b",
        "explanation": "Matches semantic version strings: major.minor.patch[-pre][+build].",
        "keywords": ["semver", "version", "versiyon", "semantic version"],
    },
    "iban": {
        "pattern": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}[A-Z0-9]{0,16}\b",
        "named": r"\b(?P<country>[A-Z]{2})(?P<check>\d{2})(?P<bban>[A-Z0-9]{4}\d{7}[A-Z0-9]{0,16})\b",
        "explanation": "Matches IBAN numbers (2 letter country + 2 check + up to 30 alphanumeric).",
        "keywords": ["iban", "banka", "bank account"],
    },
    "credit_card": {
        "pattern": r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "named": r"\b(?P<card>(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})\b",
        "explanation": "Matches Visa/MC/Amex/Discover card numbers.",
        "keywords": ["credit card", "kredi kartı", "kart", "card number"],
    },
    "turkish_postal": {
        "pattern": r"\b\d{5}\b",
        "named": r"\b(?P<postal>\d{5})\b",
        "explanation": "Matches Turkish postal codes (5 digits).",
        "keywords": ["posta kodu", "postal", "zip", "zip code"],
    },
}

FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


class Worker(BaseWorker):
    """Generate regex patterns from natural language descriptions."""

    skill_id = "code.regex-builder"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            description: str = input.data.get("description", "").strip()
            if not description:
                return SkillOutput(success=False, error="'description' is required.")

            examples_match: list[str] = input.data.get("examples_match", [])
            examples_no_match: list[str] = input.data.get("examples_no_match", [])
            language: str = input.data.get("language", "python")
            flags_list: list[str] = input.data.get("flags", [])
            named_groups: bool = input.data.get("named_groups", False)

            # Resolve flags
            combined_flags = 0
            flags_used: list[str] = []
            for f in flags_list:
                if f in FLAG_MAP:
                    combined_flags |= FLAG_MAP[f]
                    flags_used.append(f)

            # Try to match known patterns
            pattern, explanation, alternatives = self._find_pattern(
                description, named_groups
            )

            # Validate against examples
            test_results = self._test_pattern(
                pattern, examples_match, examples_no_match, combined_flags
            )

            # If examples fail, try alternatives
            if not all(r["passed"] for r in test_results) and alternatives:
                for alt in alternatives:
                    alt_results = self._test_pattern(
                        alt, examples_match, examples_no_match, combined_flags
                    )
                    if all(r["passed"] for r in alt_results):
                        pattern = alt
                        test_results = alt_results
                        break

            usage = self._usage_example(pattern, language, flags_used)

            return SkillOutput(
                success=True,
                data={
                    "pattern": pattern,
                    "flags_used": flags_used,
                    "explanation": explanation,
                    "test_results": test_results,
                    "usage_example": usage,
                    "alternatives": alternatives,
                },
                metadata={"skill_id": self.skill_id},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    def _find_pattern(
        self, description: str, named: bool
    ) -> tuple[str, str, list[str]]:
        """Match description against known pattern library."""
        desc_lower = description.lower()

        for _key, info in KNOWN_PATTERNS.items():
            for kw in info["keywords"]:
                if kw in desc_lower:
                    pat = info["named"] if named else info["pattern"]
                    alt_key = "pattern" if named else "named"
                    alternatives = [info[alt_key]] if info.get(alt_key) else []
                    return pat, info["explanation"], alternatives

        # Fallback: build from examples or return wildcard
        return r".*", f"No known pattern found for: {description}", []

    def _test_pattern(
        self,
        pattern: str,
        should_match: list[str],
        should_not_match: list[str],
        flags: int,
    ) -> list[dict[str, Any]]:
        """Run pattern against examples."""
        results: list[dict[str, Any]] = []
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            return [{"input": "", "expected": True, "actual": False, "passed": False, "error": str(e)}]

        for s in should_match:
            match = compiled.search(s) is not None
            results.append({"input": s, "expected": True, "actual": match, "passed": match})

        for s in should_not_match:
            match = compiled.search(s) is not None
            results.append({"input": s, "expected": False, "actual": match, "passed": not match})

        return results

    def _usage_example(self, pattern: str, language: str, flags: list[str]) -> str:
        """Return a code snippet showing how to use the regex."""
        escaped = pattern.replace("\\", "\\\\").replace('"', '\\"')

        if language == "javascript":
            js_flags = ""
            if "IGNORECASE" in flags:
                js_flags += "i"
            if "MULTILINE" in flags:
                js_flags += "m"
            if "DOTALL" in flags:
                js_flags += "s"
            return f'const regex = /{pattern}/{js_flags};\nconst match = regex.test(text);'

        if language == "go":
            return f're := regexp.MustCompile(`{pattern}`)\nmatch := re.MatchString(text)'

        # Python (default)
        flag_str = ""
        if flags:
            flag_str = " | ".join(f"re.{f}" for f in flags)
            return f'import re\npattern = re.compile(r"{escaped}", {flag_str})\nmatch = pattern.search(text)'
        return f'import re\npattern = re.compile(r"{escaped}")\nmatch = pattern.search(text)'

