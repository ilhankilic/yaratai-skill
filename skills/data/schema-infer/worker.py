# filepath: skills/data/schema-infer/worker.py
import json, logging, re
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
URI_RE = re.compile(r"^https?://")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

class Worker(BaseWorker):
    """Infer JSON Schema from sample data."""
    skill_id = "data.schema-infer"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            data = input.data.get("sample_data", None)
            if data is None:
                return SkillOutput(success=False, error="'sample_data' is required.")

            title: str = input.data.get("title", "InferredSchema")
            threshold: float = input.data.get("required_threshold", 1.0)
            detect_fmt: bool = input.data.get("detect_formats", True)

            samples = data if isinstance(data, list) else [data]
            if not samples:
                return SkillOutput(success=False, error="sample_data is empty.")

            formats: dict = {}
            schema = self._infer(samples, threshold, detect_fmt, formats)
            schema["$schema"] = "http://json-schema.org/draft-07/schema#"
            schema["title"] = title

            schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
            field_count = len(schema.get("properties", {}))
            required_count = len(schema.get("required", []))

            return SkillOutput(success=True, data={
                "schema": schema, "schema_json": schema_json,
                "field_count": field_count, "required_count": required_count,
                "detected_formats": formats,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _infer(self, samples: list, threshold: float, detect_fmt: bool, formats: dict) -> dict:
        if not samples:
            return {"type": "object"}
        if isinstance(samples[0], dict):
            props: dict = {}
            field_presence: dict[str, int] = {}
            for s in samples:
                for k, v in s.items():
                    field_presence[k] = field_presence.get(k, 0) + 1
                    if k not in props:
                        props[k] = self._infer_type(v, detect_fmt, formats, k)
            required = [k for k, cnt in field_presence.items() if cnt / len(samples) >= threshold]
            return {"type": "object", "properties": props, "required": required}
        return self._infer_type(samples[0], detect_fmt, formats, "root")

    def _infer_type(self, value, detect_fmt: bool, formats: dict, key: str) -> dict:
        if value is None:
            return {"type": ["string", "null"]}
        if isinstance(value, bool):
            return {"type": "boolean"}
        if isinstance(value, int):
            return {"type": "integer"}
        if isinstance(value, float):
            return {"type": "number"}
        if isinstance(value, str):
            t: dict = {"type": "string"}
            if detect_fmt:
                if EMAIL_RE.match(value):
                    t["format"] = "email"; formats[key] = "email"
                elif DATE_RE.match(value):
                    t["format"] = "date"; formats[key] = "date"
                elif URI_RE.match(value):
                    t["format"] = "uri"; formats[key] = "uri"
                elif UUID_RE.match(value):
                    t["format"] = "uuid"; formats[key] = "uuid"
            return t
        if isinstance(value, list):
            if value:
                return {"type": "array", "items": self._infer_type(value[0], detect_fmt, formats, key)}
            return {"type": "array"}
        if isinstance(value, dict):
            props = {k: self._infer_type(v, detect_fmt, formats, k) for k, v in value.items()}
            return {"type": "object", "properties": props}
        return {"type": "string"}
