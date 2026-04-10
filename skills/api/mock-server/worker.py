# filepath: skills/api/mock-server/worker.py
import json, logging, random, uuid
from datetime import datetime, timedelta
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

NAMES = ["Ali", "Ayşe", "Mehmet", "Fatma", "Emre", "Zeynep", "Can", "Elif", "Burak", "Selin"]
SURNAMES = ["Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Öztürk", "Arslan", "Koç", "Aydın", "Kurt"]

class Worker(BaseWorker):
    """Generate mock API responses."""
    skill_id = "api.mock-server"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            schema: dict = input.data.get("schema", {})
            if not schema:
                return SkillOutput(success=False, error="'schema' is required.")
            itype: str = input.data.get("input_type", "openapi")
            fw: str = input.data.get("framework", "raw_json")
            errors: bool = input.data.get("include_errors", False)
            realistic: bool = input.data.get("realistic_data", True)

            mocks: dict[str, str] = {}; ep_count = 0

            if itype == "openapi":
                for path, methods in schema.get("paths", {}).items():
                    for method, detail in methods.items():
                        data = self._gen_data(3) if realistic else [{"id": 1}]
                        mocks[f"{method.upper()} {path}"] = json.dumps(data, ensure_ascii=False, indent=2)
                        ep_count += 1
                        if errors:
                            mocks[f"{method.upper()} {path} [404]"] = json.dumps({"error": "Not found"})
                            mocks[f"{method.upper()} {path} [500]"] = json.dumps({"error": "Internal error"})
            else:
                mocks["response.json"] = json.dumps(schema, indent=2, ensure_ascii=False)
                ep_count = 1

            handler = ""
            if fw == "msw":
                handler = "import { rest } from 'msw';\n\nexport const handlers = [\n"
                for key in mocks:
                    handler += f"  // {key}\n"
                handler += "];\n"

            db = json.dumps({"items": self._gen_data(5)}, ensure_ascii=False, indent=2) if fw == "json_server" else ""

            return SkillOutput(success=True, data={
                "mock_files": mocks, "handler_code": handler, "db_json": db, "endpoint_count": ep_count,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))

    def _gen_data(self, count: int) -> list[dict]:
        items = []
        for _ in range(count):
            name = random.choice(NAMES); surname = random.choice(SURNAMES)
            items.append({
                "id": str(uuid.uuid4()), "name": f"{name} {surname}",
                "email": f"{name.lower()}@example.com",
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            })
        return items
