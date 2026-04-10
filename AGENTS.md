# AGENTS.md

## Scope
- **SkillForge** is a stateless AI skill library with standard JSON I/O and no database.
- Primary spec: `skillforge-claude-desktop-prompt.md`. Coding standard: `STANDARD.md`.

## Architecture
- **Core** (`skillforge/`): `base.py` (BaseWorker, SkillInput, SkillOutput), `registry.py` (auto-discovery), `orchestrator.py` (pipeline engine).
- **Nodes** (`skillforge/nodes/`): `local_node.py` (Ollama adapter), `cloud_node.py` (RunPod/GCP adapter).
- **CLI** (`cli/main.py`): Typer app — commands: `run`, `list`, `info`, `test`, `pipe`, `create`.
- **Skills** (`skills/<category>/<name>/`): each has exactly 4 files: `schema.json`, `worker.py`, `SKILL.md`, `test.py`.
- **Pipelines** (`pipelines/*.yaml`): sequential/parallel multi-skill execution definitions.

## Key conventions
- Communication in Turkish; code and filenames in English.
- **Schema first**: write `schema.json` before `worker.py` for every new skill.
- Worker contract is immutable: `run(self, input: SkillInput) -> SkillOutput`.
- Output shape: `{success: bool, data: dict, error: str, metadata: dict}`.
- Skills are stateless — no DB, no global mutable state, no `print()`.
- Errors: never raise — return `SkillOutput(success=False, error=...)`.
- Type hints on every function; docstrings on every class and public method.
- Config via schema fields or env vars — no hardcoded values.

## External integrations
- **Ollama**: `http://localhost:11434` (env: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`).
- **RunPod/GCP**: env `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT`.
- **Anthropic** (auto-create): env `ANTHROPIC_API_KEY`.

## Workflow for agents
- When adding a skill: create the 4-file quartet under `skills/<category>/<name>/`.
- When editing the master prompt (`skillforge-claude-desktop-prompt.md`): preserve session block ordering.
- Run tests: `pytest tests/ -v` (core), `pytest skills/<cat>/<name>/test.py -v` (per-skill).
- Skill tests mock all external services — they must run offline.

## Reference files
| Concept          | File                                | Section               |
|------------------|-------------------------------------|-----------------------|
| Skill standard   | `STANDARD.md`                       | §1-§8                 |
| Worker interface | `skillforge/base.py`                | `BaseWorker`          |
| Auto-discovery   | `skillforge/registry.py`            | `discover_skills()`   |
| Pipeline engine  | `skillforge/orchestrator.py`        | `run_pipeline()`      |
| CLI commands     | `cli/main.py`                       | all `@app.command()`  |
| Skill template   | `skills/_template/`                 | 4-file example        |
| Quality rules    | `skillforge-claude-desktop-prompt.md` | "KALİTE KURALLARI"  |
