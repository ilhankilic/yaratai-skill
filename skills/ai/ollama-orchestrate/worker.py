# filepath: skills/ai/ollama-orchestrate/worker.py
import logging, re, time
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Orchestrate multi-model Ollama pipelines."""
    skill_id = "ai.ollama-orchestrate"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            pipeline: list = input.data.get("pipeline", [])
            initial: dict = input.data.get("initial_input", {})
            if not pipeline or not initial:
                return SkillOutput(success=False, error="'pipeline' and 'initial_input' required.")
            mode: str = input.data.get("mode", "sequential")
            timeout: int = input.data.get("timeout_seconds", 30)

            results: dict[str, str] = {}
            log: list[dict] = []
            failed: list[int] = []
            total_ms = 0

            for i, step in enumerate(pipeline):
                start = time.time()
                model = step.get("model", "gemma3:4b")
                template = step.get("prompt_template", "")
                key = step.get("output_key", f"step_{i}")

                # Fill template variables
                prompt = template
                for k, v in initial.items():
                    prompt = prompt.replace(f"{{{{initial_input.{k}}}}}", str(v))
                for k, v in results.items():
                    prompt = prompt.replace(f"{{{{results.{k}}}}}", str(v))

                # Offline mode — simulate LLM response
                response = f"[Simulated response from {model} for: {prompt[:50]}...]"
                results[key] = response
                elapsed = int((time.time() - start) * 1000)
                total_ms += elapsed
                log.append({"step": i, "model": model, "duration_ms": elapsed, "success": True})

            return SkillOutput(success=True, data={
                "results": results, "pipeline_log": log,
                "total_duration_ms": total_ms, "failed_steps": failed,
            }, metadata={"skill_id": self.skill_id, "mode": "offline_simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
