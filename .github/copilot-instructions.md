# Copilot Instructions for SkillForge

SkillForge is a stateless AI skill runtime at `http://localhost:9147` with 51+ skills.

## Start Here

```bash
docker compose up -d
curl http://localhost:9147/health
```

## Use Skills

```bash
GET  /api/skills                          # List all skills
GET  /api/skills/{skill_id}/info          # Read schema (always do this first)
POST /api/skills/{skill_id}/run           # Execute: {"data": {...}}
```

Every response: `{"success": bool, "data": {}, "error": "", "metadata": {}}`

## Key Rules

- Skills are stateless — no database, no global state
- Worker contract: `class Worker(BaseWorker)` with `run(self, input: SkillInput) -> SkillOutput`
- Never raise exceptions — return `SkillOutput(success=False, error="...")`
- Create new skills under `skills/<category>/<name>/` with 4 files: `schema.json`, `worker.py`, `SKILL.md`, `test.py`
- All development on `dev` branch — never push to `master` directly

See `AGENTS.md` for the full reference.

