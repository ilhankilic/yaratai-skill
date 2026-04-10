# filepath: skills/ai/fine-tune-prep/worker.py
import json, logging, random
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Convert data into fine-tuning dataset formats."""
    skill_id = "ai.fine-tune-prep"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            raw: list = input.data.get("raw_data", [])
            if not raw:
                return SkillOutput(success=False, error="'raw_data' is required.")

            fmt: str = input.data.get("output_format", "alpaca")
            sys_prompt: str = input.data.get("system_prompt", "")
            split: float = input.data.get("train_split", 0.9)
            shuffle: bool = input.data.get("shuffle", True)

            formatted = []
            for item in raw:
                if fmt == "alpaca":
                    formatted.append({"instruction": item.get("instruction", item.get("question", "")),
                                     "input": item.get("input", ""), "output": item.get("output", item.get("answer", ""))})
                elif fmt == "sharegpt":
                    convs = [{"from": "human", "value": item.get("instruction", item.get("question", ""))},
                             {"from": "gpt", "value": item.get("output", item.get("answer", ""))}]
                    if sys_prompt:
                        convs.insert(0, {"from": "system", "value": sys_prompt})
                    formatted.append({"conversations": convs})
                else:  # chatml / jsonl_chat
                    msgs = []
                    if sys_prompt:
                        msgs.append({"role": "system", "content": sys_prompt})
                    msgs.append({"role": "user", "content": item.get("instruction", item.get("question", ""))})
                    msgs.append({"role": "assistant", "content": item.get("output", item.get("answer", ""))})
                    formatted.append({"messages": msgs})

            if shuffle:
                random.shuffle(formatted)

            split_idx = int(len(formatted) * split)
            train = formatted[:split_idx]
            val = formatted[split_idx:]

            train_jsonl = "\n".join(json.dumps(r, ensure_ascii=False) for r in train)
            val_jsonl = "\n".join(json.dumps(r, ensure_ascii=False) for r in val)

            avg_tokens = sum(len(json.dumps(r).split()) for r in formatted) // max(len(formatted), 1)

            return SkillOutput(success=True, data={
                "train_jsonl": train_jsonl, "val_jsonl": val_jsonl,
                "train_count": len(train), "val_count": len(val),
                "avg_tokens_estimate": int(avg_tokens * 1.3),
                "format_example": formatted[0] if formatted else {},
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
