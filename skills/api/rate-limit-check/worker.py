# filepath: skills/api/rate-limit-check/worker.py
import logging, time
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Analyze rate limit behavior (offline simulation mode)."""
    skill_id = "api.rate-limit-check"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            url: str = input.data.get("url", "")
            if not url:
                return SkillOutput(success=False, error="'url' is required.")
            count: int = min(input.data.get("request_count", 20), 100)
            interval: int = input.data.get("interval_ms", 100)

            # Offline mode — simulate timeline (no real HTTP calls)
            timeline = []
            success = 0; limited = 0; errors = 0
            for i in range(count):
                status = 200 if i < count * 0.8 else 429
                resp_ms = 50 + (i * 2)
                if status == 200: success += 1
                elif status == 429: limited += 1
                timeline.append({"request_n": i + 1, "status_code": status, "response_ms": resp_ms})

            avg_ms = sum(t["response_ms"] for t in timeline) / len(timeline) if timeline else 0

            return SkillOutput(success=True, data={
                "total_requests": count, "successful": success, "rate_limited": limited,
                "errors": errors, "rate_limit_detected": limited > 0,
                "avg_response_ms": round(avg_ms, 2), "timeline": timeline,
            }, metadata={"skill_id": self.skill_id, "mode": "offline_simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
