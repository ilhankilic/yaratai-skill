# filepath: skills/ai/lang-detect/worker.py
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
