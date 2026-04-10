# filepath: skills/ai/prompt-engineer/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

ROLES = {
    "generation": "expert content creator",
    "extraction": "data extraction specialist",
    "classification": "classification and categorization expert",
    "summarization": "concise summarization expert",
    "translation": "professional translator",
    "code": "senior software engineer",
    "analysis": "analytical reasoning expert",
}

class Worker(BaseWorker):
    """Transform raw requests into structured LLM prompts."""
    skill_id = "ai.prompt-engineer"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            raw: str = input.data.get("raw_request", "").strip()
            if not raw:
                return SkillOutput(success=False, error="'raw_request' is required.")

            model: str = input.data.get("target_model", "generic")
            task: str = input.data.get("task_type", "generation")
            fmt: str = input.data.get("output_format", "text")
            lang: str = input.data.get("language", "tr")
            examples: bool = input.data.get("add_examples", True)
            cot: bool = input.data.get("chain_of_thought", False)

            techniques: list[str] = ["role_assignment", "output_constraints"]
            role = ROLES.get(task, "helpful assistant")

            # System prompt
            lang_name = "Türkçe" if lang == "tr" else "English"
            system_parts = [f"Sen bir {role}'sın." if lang == "tr" else f"You are a {role}."]
            system_parts.append(f"Yanıtlarını {lang_name} olarak ver." if lang == "tr" else f"Respond in {lang_name}.")

            if fmt == "json":
                system_parts.append("Çıktını geçerli JSON formatında ver." if lang == "tr" else "Return output as valid JSON.")
                techniques.append("format_constraint")
            elif fmt == "markdown":
                system_parts.append("Markdown formatında yanıtla." if lang == "tr" else "Format your response in Markdown.")

            system_prompt = " ".join(system_parts)

            # User prompt
            user_parts = [raw]
            if cot:
                user_parts.append("\nAdım adım düşün:" if lang == "tr" else "\nThink step by step:")
                techniques.append("chain_of_thought")

            if examples:
                user_parts.append("\nÖrnek:" if lang == "tr" else "\nExample:")
                user_parts.append("Input: [sample] → Output: [sample]")
                techniques.append("few_shot")

            user_prompt = "\n".join(user_parts)
            full = f"[System]\n{system_prompt}\n\n[User]\n{user_prompt}"

            token_est = len(full.split()) * 1.3  # rough token estimate

            suggestions = []
            if not cot and task in ("analysis", "code"):
                suggestions.append("Consider enabling chain_of_thought for better reasoning.")
            if fmt == "text" and task == "extraction":
                suggestions.append("Consider using JSON output_format for structured extraction.")

            return SkillOutput(success=True, data={
                "system_prompt": system_prompt, "user_prompt": user_prompt,
                "full_prompt": full, "techniques_used": techniques,
                "token_estimate": int(token_est), "suggestions": suggestions,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
