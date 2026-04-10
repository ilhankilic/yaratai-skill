# SkillForge

**Real code. Standard I/O. No database. Just workers.**

SkillForge is a stateless AI skill library that developers can import directly from GitHub into their AI-assisted workflows (Claude Code, Cursor, Codex, etc.). Every skill follows the same input/output contract, ships with tests, and requires zero database setup.

---

## What is SkillForge?

SkillForge is a collection of **self-contained, stateless Python workers** — each one solves a focused task (triage a patient, convert JSON to CSV, extract text from a PDF) and exposes an identical interface. Think of it as a skill marketplace for AI agents, where every skill:

1. **Follows a standard contract** — `run(input) → {success, data, error, metadata}`
2. **Ships with four files** — `schema.json`, `worker.py`, `SKILL.md`, `test.py`
3. **Needs no database** — purely functional, stateless, every call is independent

You can run skills individually via CLI, chain them into YAML-defined pipelines, or let AI agents discover and execute them automatically.

---

## Quick Start

```bash
# Clone & install
git clone https://github.com/<your-user>/skillforge.git
cd skillforge
pip install -e ".[dev]"

# List available skills
skillforge list

# Run a skill
skillforge run data.json-to-csv --input sample.json

# Run a pipeline
skillforge pipe mediscreen-full --input patient.json

# Run tests for a skill
skillforge test mediscreen.triage
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
├── pyproject.toml              # Package definition & dependencies
├── skillforge/                 # Core Python package
│   ├── base.py                 # BaseWorker, SkillInput, SkillOutput
│   ├── registry.py             # Auto-discovery & loading
│   ├── orchestrator.py         # Pipeline execution engine
│   └── nodes/
│       ├── local_node.py       # Ollama adapter
│       └── cloud_node.py       # RunPod/GCP adapter
├── cli/
│   └── main.py                 # Typer CLI (run, list, test, pipe, create)
├── skills/
│   ├── _template/              # Copy this to create a new skill
│   ├── mediscreen/triage/      # Patient triage skill
│   └── data/                   # Data processing skills
├── pipelines/                  # YAML pipeline definitions
└── tests/                      # Core & integration tests
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

## Use in AI Editors

### Claude Code / Cursor / Codex

Point your agent at the `skills/` directory or a specific `SKILL.md`:

```
Read skills/mediscreen/triage/SKILL.md and use that skill to triage this patient: ...
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

