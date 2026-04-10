"""code.boilerplate — Generate project scaffolding for FastAPI, Next.js, React, or Express."""

from __future__ import annotations

import logging
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class Worker(BaseWorker):
    """Generate project boilerplate files for popular frameworks."""

    skill_id = "code.boilerplate"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            framework: str = input.data.get("framework", "")
            project_name: str = input.data.get("project_name", "")
            if not framework or not project_name:
                return SkillOutput(success=False, error="'framework' and 'project_name' are required.")

            features: list[str] = input.data.get("features", [])
            py_ver: str = input.data.get("python_version", "3.11")
            node_ver: str = input.data.get("node_version", "20")
            pkg_mgr: str = input.data.get("package_manager", "npm")

            generators = {
                "fastapi": self._fastapi,
                "nextjs": self._nextjs,
                "react": self._react,
                "express": self._express,
            }

            gen = generators.get(framework)
            if gen is None:
                return SkillOutput(
                    success=False,
                    error=f"Unknown framework '{framework}'. Supported: {list(generators.keys())}",
                )

            files, setup_cmds = gen(project_name, features, py_ver, node_ver, pkg_mgr)
            tree = self._build_tree(files)

            readme = f"# {project_name}\n\nGenerated with SkillForge `code.boilerplate` ({framework}).\n\n## Setup\n\n```bash\n"
            readme += "\n".join(setup_cmds) + "\n```\n"

            return SkillOutput(
                success=True,
                data={
                    "files": files,
                    "file_count": len(files),
                    "directory_structure": tree,
                    "setup_commands": setup_cmds,
                    "readme_snippet": readme,
                },
                metadata={"skill_id": self.skill_id, "framework": framework},
            )

        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))

    # ── Generators ───────────────────────────────────────────────────

    def _fastapi(self, name: str, features: list, py_ver: str, *_a) -> tuple[dict, list]:
        files: dict[str, str] = {}
        deps = ["fastapi>=0.110", "uvicorn[standard]>=0.27", "pydantic>=2.0"]
        if "database" in features:
            deps.append("sqlalchemy>=2.0")
        if "auth" in features:
            deps.append("python-jose[cryptography]>=3.3")

        files["requirements.txt"] = "\n".join(deps) + "\n"
        files[".env.example"] = f"# {name}\nDEBUG=true\nPORT=8000\nSECRET_KEY=changeme\n"
        files["app/__init__.py"] = ""
        files["app/main.py"] = (
            f'"""Main entry point for {name}."""\n\n'
            "from fastapi import FastAPI\n\n"
            f'app = FastAPI(title="{name}")\n\n\n'
            '@app.get("/health")\nasync def health():\n    return {"status": "ok"}\n'
        )
        files["app/routers/__init__.py"] = ""
        files["app/schemas/__init__.py"] = ""
        files["app/core/__init__.py"] = ""
        files["app/core/config.py"] = (
            "import os\n\nDEBUG = os.getenv('DEBUG', 'false').lower() == 'true'\n"
            "PORT = int(os.getenv('PORT', '8000'))\n"
        )

        if "docker" in features:
            files["Dockerfile"] = (
                f"FROM python:{py_ver}-slim\nWORKDIR /app\n"
                "COPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\"]\n"
            )

        if "testing" in features:
            files["tests/__init__.py"] = ""
            files["tests/test_health.py"] = (
                "from fastapi.testclient import TestClient\nfrom app.main import app\n\n"
                "client = TestClient(app)\n\ndef test_health():\n    r = client.get('/health')\n    assert r.status_code == 200\n"
            )

        cmds = [f"cd {name}", f"python -m venv .venv", "pip install -r requirements.txt",
                'uvicorn app.main:app --reload']
        return files, cmds

    def _nextjs(self, name: str, features: list, *_a, **_kw) -> tuple[dict, list]:
        files: dict[str, str] = {}
        pkg = {
            "name": name, "version": "0.1.0", "private": True,
            "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
            "dependencies": {"next": "^14", "react": "^18", "react-dom": "^18"},
            "devDependencies": {"typescript": "^5", "@types/react": "^18"},
        }
        import json
        files["package.json"] = json.dumps(pkg, indent=2) + "\n"
        files["tsconfig.json"] = json.dumps({"compilerOptions": {"target": "es2017", "lib": ["dom", "es2017"], "jsx": "preserve", "module": "esnext", "moduleResolution": "bundler", "strict": True}}, indent=2) + "\n"
        files["app/layout.tsx"] = (
            f"export const metadata = {{ title: '{name}' }};\n\n"
            "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
            "  return <html><body>{children}</body></html>;\n}\n"
        )
        files["app/page.tsx"] = f'export default function Home() {{\n  return <h1>{name}</h1>;\n}}\n'

        cmds = [f"cd {name}", "npm install", "npm run dev"]
        return files, cmds

    def _react(self, name: str, features: list, *_a, pkg_mgr: str = "npm", **_kw) -> tuple[dict, list]:
        files: dict[str, str] = {}
        import json
        pkg = {
            "name": name, "version": "0.1.0", "private": True,
            "dependencies": {"react": "^18", "react-dom": "^18"},
            "devDependencies": {"vite": "^5", "@vitejs/plugin-react": "^4", "typescript": "^5"},
            "scripts": {"dev": "vite", "build": "vite build"},
        }
        if "state_management" in features:
            pkg["dependencies"]["zustand"] = "^4"
        files["package.json"] = json.dumps(pkg, indent=2) + "\n"
        files["src/App.tsx"] = f"function App() {{\n  return <h1>{name}</h1>;\n}}\nexport default App;\n"
        files["src/main.tsx"] = "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n"
        files["index.html"] = f'<!DOCTYPE html><html><head><title>{name}</title></head><body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>\n'

        cmds = [f"cd {name}", f"{pkg_mgr} install", f"{pkg_mgr} run dev"]
        return files, cmds

    def _express(self, name: str, features: list, *_a, **_kw) -> tuple[dict, list]:
        files: dict[str, str] = {}
        import json
        pkg = {
            "name": name, "version": "0.1.0",
            "main": "src/index.js",
            "scripts": {"start": "node src/index.js", "dev": "nodemon src/index.js"},
            "dependencies": {"express": "^4"},
            "devDependencies": {"nodemon": "^3"},
        }
        files["package.json"] = json.dumps(pkg, indent=2) + "\n"
        files["src/index.js"] = (
            "const express = require('express');\nconst app = express();\n"
            "const PORT = process.env.PORT || 3000;\n\n"
            "app.get('/health', (req, res) => res.json({ status: 'ok' }));\n\n"
            f"app.listen(PORT, () => console.log(`{name} running on ${{PORT}}`));\n"
        )
        cmds = [f"cd {name}", "npm install", "npm run dev"]
        return files, cmds

    def _build_tree(self, files: dict[str, str]) -> str:
        """Build an ASCII directory tree."""
        paths = sorted(files.keys())
        lines: list[str] = []
        for p in paths:
            depth = p.count("/")
            name = p.rsplit("/", 1)[-1]
            lines.append("  " * depth + "├── " + name)
        return "\n".join(lines)

