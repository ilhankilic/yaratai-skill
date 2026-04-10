# filepath: skills/api/postman-export/worker.py
import json, logging, uuid
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate Postman Collection."""
    skill_id = "api.postman-export"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            source: dict = input.data.get("source", {})
            name: str = input.data.get("collection_name", "")
            base: str = input.data.get("base_url", "")
            if not source or not name or not base:
                return SkillOutput(success=False, error="'source', 'collection_name', 'base_url' required.")
            tests: bool = input.data.get("include_tests", False)
            auth: bool = input.data.get("include_auth", False)

            items = []; req_count = 0
            paths = source.get("paths", {})
            for path, methods in paths.items():
                for method, detail in methods.items():
                    item = {
                        "name": detail.get("summary", f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "url": {"raw": f"{base}{path}", "host": [base], "path": path.strip("/").split("/")},
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                        },
                    }
                    if tests:
                        item["event"] = [{"listen": "test", "script": {"exec": [
                            "pm.test('Status 200', function () { pm.response.to.have.status(200); });"
                        ]}}]
                    items.append(item); req_count += 1

            collection = {
                "info": {"name": name, "_postman_id": str(uuid.uuid4()), "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
                "item": items,
            }
            if auth:
                collection["auth"] = {"type": "bearer", "bearer": [{"key": "token", "value": "{{auth_token}}"}]}

            env = json.dumps({"name": f"{name} Environment", "values": [
                {"key": "base_url", "value": base}, {"key": "auth_token", "value": ""}
            ]}, indent=2)

            return SkillOutput(success=True, data={
                "collection_json": json.dumps(collection, indent=2), "environment_json": env,
                "request_count": req_count, "folder_count": 0,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
