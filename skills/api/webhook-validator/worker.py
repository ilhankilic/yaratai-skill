# filepath: skills/api/webhook-validator/worker.py
import hashlib, hmac, json, logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Validate webhook payloads and HMAC signatures."""
    skill_id = "api.webhook-validator"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            payload: dict = input.data.get("payload", {})
            if not payload:
                return SkillOutput(success=False, error="'payload' is required.")
            schema: dict = input.data.get("schema", {})
            sig: str = input.data.get("signature", "")
            secret: str = input.data.get("secret", "")
            provider: str = input.data.get("provider", "generic")

            errors = []; warnings = []
            sig_valid = None

            # Basic schema validation (without jsonschema dep)
            if schema:
                req = schema.get("required", [])
                props = schema.get("properties", {})
                for field in req:
                    if field not in payload:
                        errors.append({"path": field, "message": f"Missing required field: {field}", "value": None})
                for field, rules in props.items():
                    if field in payload:
                        exp_type = rules.get("type", "")
                        val = payload[field]
                        if exp_type == "string" and not isinstance(val, str):
                            errors.append({"path": field, "message": f"Expected string, got {type(val).__name__}", "value": val})

            # HMAC validation
            if sig and secret:
                payload_bytes = json.dumps(payload, sort_keys=True).encode()
                expected = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
                sig_valid = hmac.compare_digest(sig, expected)

            # Provider checks
            prov_info: dict = {}
            if provider == "github":
                prov_info["has_action"] = "action" in payload
            elif provider == "stripe":
                prov_info["has_type"] = "type" in payload
                prov_info["livemode"] = payload.get("livemode", None)

            valid = not errors and (sig_valid is not False)

            return SkillOutput(success=True, data={
                "valid": valid, "schema_errors": errors, "signature_valid": sig_valid,
                "provider_specific": prov_info, "warnings": warnings,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
