# filepath: skills/devops/github-actions/worker.py
import logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate GitHub Actions workflow YAML."""
    skill_id = "devops.github-actions"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            ptype: str = input.data.get("project_type", "")
            wfs: list = input.data.get("workflows", [])
            if not ptype or not wfs:
                return SkillOutput(success=False, error="'project_type' and 'workflows' required.")
            py_vers: list = input.data.get("python_versions", ["3.11", "3.12"])
            node_vers: list = input.data.get("node_versions", ["20"])
            cache: bool = input.data.get("use_cache", True)

            files: dict[str, str] = {}; jobs = 0; secrets = []

            for wf in wfs:
                if wf == "test":
                    if "python" in ptype:
                        yml = f"name: Test\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python-version: {py_vers}\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: ${{{{ matrix.python-version }}}}\n"
                        if cache:
                            yml += "      - uses: actions/cache@v4\n        with:\n          path: ~/.cache/pip\n          key: pip-${{ hashFiles('requirements.txt') }}\n"
                        yml += "      - run: pip install -e '.[dev]'\n      - run: pytest tests/ -v\n"
                    else:
                        yml = f"name: Test\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-node@v4\n        with:\n          node-version: '{node_vers[0]}'\n      - run: npm ci\n      - run: npm test\n"
                    files[".github/workflows/test.yml"] = yml; jobs += 1
                elif wf == "build":
                    yml = "name: Build\non:\n  push:\n    branches: [main]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: docker/build-push-action@v5\n        with:\n          push: true\n          tags: ${{ secrets.REGISTRY }}/${{ github.repository }}:latest\n"
                    files[".github/workflows/build.yml"] = yml; jobs += 1
                    secrets.append("REGISTRY")
                elif wf == "security":
                    yml = "name: Security\non: [push]\njobs:\n  scan:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install bandit && bandit -r . -ll\n"
                    files[".github/workflows/security.yml"] = yml; jobs += 1

            return SkillOutput(success=True, data={
                "workflows": files, "workflow_count": len(files),
                "jobs_count": jobs, "secrets_required": secrets,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
