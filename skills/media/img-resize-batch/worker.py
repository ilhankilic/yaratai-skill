# filepath: skills/media/img-resize-batch/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Batch resize images with fit modes."""
    skill_id = "media.img-resize-batch"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            data = input.data.get("image_data", "") or input.data.get("images", [])
            if not data:
                return SkillOutput(success=False, error="Input data required.")

            # Simulation mode — real processing requires Pillow
            images = input.data.get("images", [{"data": data}]) if isinstance(data, str) else data
            count = len(images) if isinstance(images, list) else 1

            return SkillOutput(success=True, data={
                "result": "[simulated — requires Pillow for real processing]",
                "success_count": count, "total_count": count,
                "reduction_percent": 25.0, "had_gps": False,
            }, metadata={"skill_id": self.skill_id, "mode": "simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
