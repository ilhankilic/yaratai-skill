# SkillForge

**Real code. Standard I/O. No database. Just workers. Docker-ready.**

SkillForge is a stateless AI skill runtime that runs inside Docker. Start the container and instantly get access to every skill — no setup, no database, no boilerplate. AI agents (Claude Code, Cursor, Codex) discover skills automatically and use them on your behalf.

---

## Why SkillForge?

Every developer keeps re-writing the same utility code — CSV converters, PDF parsers, API wrappers, triage logic. SkillForge packages these as **stateless workers** with an identical `run(input) → output` contract. You don't write them; you *use* them.

1. **Docker-first** — `docker compose up` gives you the full runtime + management panel
2. **Standard contract** — every skill: `{success, data, error, metadata}`
3. **Community-driven** — anyone can submit skills; approved ones ship to all users
4. **Agent-friendly** — AI coding assistants auto-discover and execute skills

---

## Quick Start (Docker)

```bash
git clone https://github.com/<your-user>/skillforge.git
cd skillforge
docker compose up -d
```

Open **http://localhost:9147** — that's it. The management panel lets you:

- 🧩 **Browse** all available skills
- ▶️ **Execute** any skill with JSON input
- 🔄 **Sync** community skills from GitHub repos
- 📥 **Import** individual skills by URL

### Quick Start (Local)

```bash
pip install -e ".[dev]"
skillforge list
skillforge run data.json-to-csv --input sample.json
```

---

## REST API

Once running (Docker or local via `uvicorn skillforge.api.app:app --port 9147`):

| Endpoint                              | Method | Description              |
|---------------------------------------|--------|--------------------------|
| `/health`                             | GET    | Health check + stats     |
| `/api/skills`                         | GET    | List all skills          |
| `/api/skills/{id}/info`               | GET    | Skill details + schema   |
| `/api/skills/{id}/run`                | POST   | Execute a skill          |
| `/api/sync/github`                    | POST   | Sync skills from a repo  |
| `/api/sync/import`                    | POST   | Import a single skill    |
| `/api/sync/validate`                  | POST   | Validate a skill dir     |

### Example: Run a skill via API

```bash
curl -X POST http://localhost:9147/api/skills/data.json-to-csv/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"records": [{"name": "Alice", "age": 30}]}}'
```

---

## Available Skills

| Skill ID                  | Category    | Description                              | Dependencies |
|---------------------------|-------------|------------------------------------------|-------------|
| `mediscreen.triage`       | mediscreen  | Patient triage assessment via Ollama LLM | Ollama      |
| `data.json-to-csv`        | data        | JSON array → CSV with nested field support | —          |
| `data.pdf-extract`        | data        | PDF text & table extraction              | pdfplumber  |
| `data.shapefile-convert`  | data        | Shapefile → GeoJSON/KML with CRS transform | geopandas |

### Planned Skills

| Skill ID                     | Category    | Priority   |
|------------------------------|-------------|------------|
| `mediscreen.symptom-parser`  | mediscreen  | 🔴 Critical |
| `mediscreen.report-gen`      | mediscreen  | 🟡 Medium   |
| `ai.ollama-orchestrate`      | ai          | 🟠 High     |
| `ai.prompt-engineer`         | ai          | 🟡 Medium   |
| `web.api-call`               | web         | 🟡 Medium   |
| `ai.fine-tune-prep`          | ai          | 🟢 Low      |

---

## Project Structure

```
skillforge/
├── Dockerfile                  # Container image
├── docker-compose.yml          # One-command full runtime
├── pyproject.toml              # Package definition & dependencies
├── skillforge/                 # Core Python package
│   ├── base.py                 # BaseWorker, SkillInput, SkillOutput
│   ├── registry.py             # Auto-discovery & loading
│   ├── orchestrator.py         # Pipeline execution engine
│   ├── sync.py                 # GitHub sync & skill validation
│   ├── api/                    # FastAPI REST API + web panel
│   │   ├── app.py              # Application factory
│   │   ├── routes/             # health, skills, sync, panel
│   │   └── templates/          # Panel HTML
│   └── nodes/
│       ├── local_node.py       # Ollama adapter
│       └── cloud_node.py       # RunPod/GCP adapter
├── cli/
│   └── main.py                 # Typer CLI (run, list, test, pipe, create)
├── skills/
│   ├── _template/              # Copy this to create a new skill
│   ├── community/              # Auto-synced skills from GitHub
│   ├── mediscreen/triage/      # Patient triage skill
│   └── data/                   # Data processing skills
├── pipelines/                  # YAML pipeline definitions
└── tests/                      # Core, API & integration tests
```

---

## Write Your Own Skill

1. Copy `skills/_template/` to `skills/<category>/<skill-name>/`
2. Edit `schema.json` **first** — define your input/output contract
3. Implement `worker.py` — subclass `BaseWorker`, implement `run()`
4. Write `SKILL.md` — document usage for agents and humans
5. Add `test.py` — at least 3 cases (happy, edge, error)

```python
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "category.my-skill"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        value = input.data.get("my_field", "")
        return SkillOutput(success=True, data={"result": value})
```

See [STANDARD.md](STANDARD.md) for the full specification.

---

## Use with AI Coding Assistants

### Claude Code / Cursor / Codex

When an AI agent clones this repo, it reads `AGENTS.md` and `SKILL.md` files to understand every available skill. The agent can then:

1. Start the runtime: `docker compose up -d`
2. Discover skills: `GET http://localhost:9147/api/skills`
3. Execute any skill: `POST http://localhost:9147/api/skills/{id}/run`

Or use the CLI directly:

```bash
skillforge run data.json-to-csv --input data.json
```

### Import Community Skills

Through the web panel (http://localhost:9147 → Sync & Import) or the API:

```bash
# Import all skills from a community repo
curl -X POST http://localhost:9147/api/sync/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/skillforge-skills"}'

# Import a single skill
curl -X POST http://localhost:9147/api/sync/import \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "skill_path": "skills/data/my-tool"}'
```

### Auto-Generate a Skill

```bash
export ANTHROPIC_API_KEY=sk-...
skillforge create "Convert Excel file to pivot table" --category data
```

---

## CLI Reference

| Command                                   | Description                       |
|-------------------------------------------|-----------------------------------|
| `skillforge run <skill_id> -i <file>`     | Run a single skill                |
| `skillforge list [--category <cat>]`      | List registered skills            |
| `skillforge info <skill_id>`              | Show skill details & SKILL.md     |
| `skillforge test <skill_id>`              | Run pytest for a skill            |
| `skillforge pipe <pipeline> -i <file>`    | Execute a YAML pipeline           |
| `skillforge create "<desc>" [--dry-run]`  | Auto-generate a skill via Claude  |

---

## Configuration

| Env Variable       | Default                    | Description              |
|--------------------|----------------------------|--------------------------|
| `OLLAMA_BASE_URL`  | `http://localhost:11434`   | Ollama server URL        |
| `OLLAMA_MODEL`     | `gemma3:4b`                | Default LLM model        |
| `OLLAMA_TIMEOUT`   | `60`                       | Request timeout (seconds)|
| `RUNPOD_API_KEY`   | —                          | RunPod API key           |
| `RUNPOD_ENDPOINT`  | —                          | RunPod endpoint URL      |
| `ANTHROPIC_API_KEY`| —                          | For `skillforge create`  |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[Apache 2.0](LICENSE)

