# AGENTS.md

## Scope
- **SkillForge** is a Docker-ready, stateless AI skill runtime with standard JSON I/O and no database.
- Primary spec: `skillforge-claude-desktop-prompt.md`. Coding standard: `STANDARD.md`.

## Architecture
- **Core** (`skillforge/`): `base.py` (BaseWorker, SkillInput, SkillOutput), `registry.py` (auto-discovery), `orchestrator.py` (pipeline engine).
- **API** (`skillforge/api/`): FastAPI app with REST endpoints + web management panel at `/`.
- **Sync** (`skillforge/sync.py`): GitHub repo sync, skill validation, community import engine.
- **Nodes** (`skillforge/nodes/`): `local_node.py` (Ollama adapter), `cloud_node.py` (RunPod/GCP adapter).
- **CLI** (`cli/main.py`): Typer app — commands: `run`, `list`, `info`, `test`, `pipe`, `create`.
- **Skills** (`skills/<category>/<name>/`): each has exactly 4 files: `schema.json`, `worker.py`, `SKILL.md`, `test.py`.
- **Community skills** (`skills/community/`): auto-synced from external GitHub repos via panel or API.
- **Pipelines** (`pipelines/*.yaml`): sequential/parallel multi-skill execution definitions.
- **Docker**: `Dockerfile` + `docker-compose.yml` — `docker compose up` starts API (port 9147) + Ollama.

## Key conventions
- Communication in Turkish; code, filenames, and all GitHub-facing docs (README, CONTRIBUTING, STANDARD) in English.
- **Schema first**: write `schema.json` before `worker.py` for every new skill.
- Worker contract is immutable: `run(self, input: SkillInput) -> SkillOutput`.
- Output shape: `{success: bool, data: dict, error: str, metadata: dict}`.
- Skills are stateless — no DB, no global mutable state, no `print()`.
- Errors: never raise — return `SkillOutput(success=False, error=...)`.
- Type hints on every function; docstrings on every class and public method.
- Config via schema fields or env vars — no hardcoded values.

## Docker runtime
- `docker compose up -d` starts SkillForge API + Ollama.
- Web panel: `http://localhost:9147` — browse, execute, sync, import skills.
- REST API: `GET /api/skills`, `POST /api/skills/{id}/run`, `POST /api/sync/github`, `POST /api/sync/import`.
- Community skills persist in a Docker volume (`skills/community/`).

## External integrations
- **Ollama**: `http://ollama:11434` inside Docker, `http://localhost:11434` locally (env: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`).
- **RunPod/GCP**: env `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`.
- **Anthropic** (auto-create): env `ANTHROPIC_API_KEY`.

## Workflow for agents
- **Branch**: Always work on `dev` branch. Never push directly to `master`.
- **Git flow**: `dev` = development, `master` = production (stable releases only via merge from dev).
- When adding a skill: `git checkout dev` → create the 4-file quartet under `skills/<category>/<name>/`.
- When a user pulls this repo, the agent should: (1) `git checkout dev`, (2) `docker compose up -d`, (3) open `http://localhost:9147`, (4) use the API to execute skills.
- When editing the master prompt (`skillforge-claude-desktop-prompt.md`): preserve session block ordering.
- Run tests: `pytest tests/ -v` (core + API), `pytest skills/<cat>/<name>/test.py -v` (per-skill).
- Skill tests mock all external services — they must run offline.
- Skill validation: `POST /api/sync/validate` or `from skillforge.sync import validate_skill_directory`.
- **Commit convention**: `feat(skills): add <category>.<name>`, `fix: <description>`, `docs: <description>`.
- **Before pushing**: always run `pytest` — all 301+ tests must pass.

## Quick API usage
```bash
# Health check
curl http://localhost:9147/health

# List all skills (with optional filters)
curl http://localhost:9147/api/skills
curl http://localhost:9147/api/skills?category=data
curl http://localhost:9147/api/skills?search=csv

# Get full skill info (schema + SKILL.md)
curl http://localhost:9147/api/skills/data.json-to-csv/info

# Execute a skill
curl -X POST http://localhost:9147/api/skills/data.json-to-csv/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"records": [{"name": "Alice", "age": 30}]}}'

# Response shape (always):
# {"success": true/false, "data": {...}, "error": "", "metadata": {...}}
```

## Reference files
| Concept          | File                                | Section               |
|------------------|-------------------------------------|-----------------------|
| Skill standard   | `STANDARD.md`                       | §1-§8                 |
| Worker interface | `skillforge/base.py`                | `BaseWorker`          |
| Auto-discovery   | `skillforge/registry.py`            | `discover_skills()`   |
| Pipeline engine  | `skillforge/orchestrator.py`        | `run_pipeline()`      |
| REST API         | `skillforge/api/app.py`             | `create_app()`        |
| Sync engine      | `skillforge/sync.py`                | `sync_from_github()`  |
| Web panel        | `skillforge/api/templates/index.html` | UI                  |
| CLI commands     | `cli/main.py`                       | all `@app.command()`  |
| Skill template   | `skills/_template/`                 | 4-file example        |
| Docker setup     | `docker-compose.yml`                | services              |
| Quality rules    | `skillforge-claude-desktop-prompt.md` | "KALİTE KURALLARI"  |
