# filepath: skills/media/audio-trim/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Trim audio files with fade in/out (simulation mode)."""
    skill_id = "media.audio-trim"
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
