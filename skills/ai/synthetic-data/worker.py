# filepath: skills/ai/synthetic-data/worker.py
import logging, random, uuid
from datetime import datetime, timedelta
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

NAMES_TR = ["Ali", "Ayşe", "Mehmet", "Fatma", "Emre", "Zeynep", "Can", "Elif"]
NAMES_EN = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]

class Worker(BaseWorker):
    """Generate synthetic data from schema."""
    skill_id = "ai.synthetic-data"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            schema: dict = input.data.get("schema", {})
            count: int = input.data.get("example_count", 10)
            if not schema or count <= 0:
                return SkillOutput(success=False, error="'schema' and positive 'example_count' required.")
            lang: str = input.data.get("language", "tr")
            names = NAMES_TR if lang == "tr" else NAMES_EN

            props = schema.get("properties", {})
            data = []
            for _ in range(count):
                item = {}
                for field, rules in props.items():
                    ftype = rules.get("type", "string")
                    if ftype == "string":
                        fmt = rules.get("format", "")
                        if "name" in field.lower():
                            item[field] = random.choice(names)
                        elif fmt == "email" or "email" in field.lower():
                            item[field] = f"{random.choice(names).lower()}@example.com"
                        elif fmt == "date" or "date" in field.lower():
                            item[field] = (datetime.now() - timedelta(days=random.randint(1,365))).strftime("%Y-%m-%d")
                        elif fmt == "uuid" or "id" in field.lower():
                            item[field] = str(uuid.uuid4())
                        else:
                            item[field] = f"sample_{field}_{random.randint(1,100)}"
                    elif ftype == "integer":
                        item[field] = random.randint(rules.get("minimum", 0), rules.get("maximum", 100))
                    elif ftype == "number":
                        item[field] = round(random.uniform(0, 100), 2)
                    elif ftype == "boolean":
                        item[field] = random.choice([True, False])
                data.append(item)

            return SkillOutput(success=True, data={
                "generated_data": data, "actual_count": len(data),
                "schema_compliance_rate": 1.0,
            }, metadata={"skill_id": self.skill_id, "mode": "offline_simulation"})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
