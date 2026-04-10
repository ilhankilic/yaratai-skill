# filepath: skills/api/rest-scaffold/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate REST API code from OpenAPI schema."""
    skill_id = "api.rest-scaffold"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            schema: dict = input.data.get("openapi_schema", {})
            if not schema:
                return SkillOutput(success=False, error="'openapi_schema' is required.")
            fw: str = input.data.get("framework", "fastapi")
            auth: bool = input.data.get("include_auth", False)

            paths = schema.get("paths", {})
            files: dict[str, str] = {}; ep_count = 0; models = 0

            if fw == "fastapi":
                lines = ["from fastapi import APIRouter, HTTPException", "from pydantic import BaseModel", "", "router = APIRouter()", ""]
                if auth:
                    lines.insert(1, "from fastapi import Depends, Security"); lines.append("# TODO: Add JWT dependency")
                for path, methods in paths.items():
                    for method, detail in methods.items():
                        fn_name = detail.get("operationId", f"{method}_{path.replace('/', '_').strip('_')}")
                        lines.append(f'@router.{method}("{path}")')
                        lines.append(f"async def {fn_name}():")
                        lines.append(f'    return {{"message": "ok"}}')
                        lines.append("")
                        ep_count += 1
                files["routes.py"] = "\n".join(lines)
            else:
                lines = ["const express = require('express');", "const router = express.Router();", ""]
                for path, methods in paths.items():
                    for method, detail in methods.items():
                        lines.append(f"router.{method}('{path}', (req, res) => {{")
                        lines.append(f"  res.json({{ message: 'ok' }});")
                        lines.append("});"); lines.append(""); ep_count += 1
                lines.append("module.exports = router;")
                files["routes.js"] = "\n".join(lines)

            return SkillOutput(success=True, data={
                "files": files, "endpoint_count": ep_count, "model_count": models, "warnings": [],
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
