# AGENTS.md

> Instructions for AI coding agents (Claude, Cursor, Copilot, Codex, Windsurf) working with SkillForge.

## What is SkillForge?

SkillForge is a **Docker-ready, stateless AI skill runtime** with 51+ production skills. It exposes a REST API + web dashboard at `http://localhost:9147`. Skills are pure functions: JSON in → JSON out, no database, no state. Every skill follows the same contract and is auto-discovered at startup.

## First Steps (Mandatory)

When a user clones this repo, execute these steps **immediately**:

```bash
cd yaratai-skill          # or wherever the repo was cloned
docker compose up -d       # Starts SkillForge API (port 9147) + Ollama (port 11434)
# Wait ~10s for startup, then verify:
curl http://localhost:9147/health
# → {"status":"healthy","version":"0.1.0","skills_loaded":51}
```

Once running, the user has access to **all 51+ skills** via:
- **Dashboard**: `http://localhost:9147` — browse, search, execute, sync skills
- **REST API**: `http://localhost:9147/api/skills` — programmatic access
- **CLI**: `skillforge list`, `skillforge run <id> -i input.json`

## Architecture (Key Files)

```
skillforge/base.py          → BaseWorker, SkillInput, SkillOutput (immutable contract)
skillforge/registry.py      → discover_skills() auto-loads all worker.py files
skillforge/orchestrator.py  → run_pipeline() for multi-skill YAML pipelines
skillforge/sync.py          → sync_from_github(), validate_skill_directory()
skillforge/api/app.py       → FastAPI factory, creates the REST API + dashboard
skillforge/api/routes/      → health.py, skills.py, sync.py, panel.py
skillforge/nodes/           → local_node.py (Ollama), cloud_node.py (RunPod/GCP)
cli/main.py                 → Typer CLI: run, list, info, test, pipe, create
skills/<category>/<name>/   → Each skill: schema.json, worker.py, SKILL.md, test.py
skills/_template/           → Copy this to create a new skill
skills/community/           → Auto-synced from external GitHub repos
pipelines/*.yaml            → Multi-skill pipeline definitions
```

## Using Skills (API Reference)

```bash
# List all skills (with optional filters)
GET  /api/skills
GET  /api/skills?category=data
GET  /api/skills?search=csv

# Get full skill schema + SKILL.md (ALWAYS read this before calling a skill)
GET  /api/skills/{skill_id}/info

# Execute a skill
POST /api/skills/{skill_id}/run
Content-Type: application/json
{"data": {"field": "value"}}

# Response shape (ALWAYS this format):
{"success": true/false, "data": {...}, "error": "", "metadata": {...}}
```

### Common Skill Examples

```bash
# Convert JSON to CSV
POST /api/skills/data.json-to-csv/run
{"data": {"records": [{"name": "Alice", "age": 30}]}}

# Generate a Dockerfile
POST /api/skills/devops.dockerfile-gen/run
{"data": {"language": "python", "framework": "fastapi"}}

# Build a regex pattern
POST /api/skills/code.regex-builder/run
{"data": {"description": "match email addresses", "test_strings": ["user@example.com"]}}

# Generate pytest test cases
POST /api/skills/code.test-gen/run
{"data": {"source_code": "def add(a, b): return a + b", "language": "python"}}

# Sync community skills from GitHub
POST /api/sync/github
{"repo_url": "https://github.com/ilhankilic/yaratai-skill", "branch": "main"}
```

## Skill Contract (Immutable)

Every skill is a `BaseWorker` subclass with this exact interface — **never change it**:

```python
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "category.skill-name"   # unique, dot-separated
    version  = "1.0.0"                 # semver

    def run(self, input: SkillInput) -> SkillOutput:
        # input.data is a dict with skill-specific fields
        # MUST return SkillOutput, NEVER raise exceptions
        return SkillOutput(success=True, data={...}, metadata={...})
```

- **SkillInput**: `{data: dict, metadata: dict}`
- **SkillOutput**: `{success: bool, data: dict, error: str, metadata: dict}`

## Creating a New Skill

**Order matters**: schema.json → worker.py → SKILL.md → test.py

Each skill is a folder `skills/<category>/<kebab-name>/` with exactly 4 files:

| File | Purpose |
|------|---------|
| `schema.json` | JSON Schema for input/output — write this FIRST |
| `worker.py` | Python worker — `class Worker(BaseWorker)` with `run()` method |
| `SKILL.md` | Documentation — agents and humans read this |
| `test.py` | Pytest tests — minimum 3: happy path, edge case, error case |

Copy `skills/_template/` as a starting point. See `STANDARD.md` for all rules.

## Rules (Non-Negotiable)

- **No database**: no SQLite, Redis, PostgreSQL — skills are pure functions
- **No global state**: no mutable class/module variables, no `print()`
- **No exceptions**: return `SkillOutput(success=False, error="...")` instead
- **Type hints**: every function parameter and return value
- **Docstrings**: every class and public method
- **Config**: via `schema.json` fields or env vars — no hardcoded values
- **Tests**: must run offline, mock all external services (Ollama, APIs)

## Git Workflow

- **`master` branch**: production/stable, default branch for users — **protected, merge from `dev` only**
- **`dev` branch**: all development — **protected, changes via PR only**
- External contributors: fork → code on `dev` → PR to `dev` → maintainer reviews and merges
- **Commit messages**: `feat(skills): add category.skill-name`, `fix: description`, `docs: description`
- **Before pushing**: `pytest` — all 301+ tests must pass

```bash
git checkout dev
# make changes...
pytest
git add -A && git commit -m "feat(skills): add data.new-skill"
git push origin dev
```

## Environment Variables

| Variable | Default | Used by |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` (Docker) / `http://localhost:11434` (local) | AI skills |
| `OLLAMA_MODEL` | `gemma3:4b` | AI skills |
| `OLLAMA_TIMEOUT` | `120` | AI skills |
| `RUNPOD_API_KEY` | — | Cloud node |
| `ANTHROPIC_API_KEY` | — | `skillforge create` |
| `SKILLFORGE_ENV` | `docker` (in container) | Runtime detection |

## Testing

```bash
pytest                                          # All tests
pytest tests/ -v                                # Core + API tests
pytest skills/data/json-to-csv/test.py -v       # Single skill
pytest --cov=skillforge --cov-report=term-missing  # With coverage
```

## Reference

| Concept | File | Key symbol |
|---------|------|------------|
| Worker contract | `skillforge/base.py` | `BaseWorker`, `SkillInput`, `SkillOutput` |
| Skill discovery | `skillforge/registry.py` | `discover_skills()`, `load_skill()` |
| Pipeline engine | `skillforge/orchestrator.py` | `run_pipeline()`, `PipelineDefinition` |
| REST API | `skillforge/api/app.py` | `create_app()` |
| Sync engine | `skillforge/sync.py` | `sync_from_github()`, `validate_skill_directory()` |
| Dashboard | `skillforge/api/templates/index.html` | Single-page web UI |
| CLI | `cli/main.py` | `run`, `list`, `info`, `test`, `pipe`, `create` |
| Skill standard | `STANDARD.md` | §1-§8: all rules |
| Skill template | `skills/_template/` | Copy to create new skills |
| Docker setup | `docker-compose.yml` | `skillforge:9147` + `ollama:11434` |
