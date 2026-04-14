# SkillForge

<p align="center">
  <strong>Open-source, Docker-ready skill library for AI coding agents.</strong><br>
  Real code. Standard I/O. No database. Just workers.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#dashboard">Dashboard</a> •
  <a href="#for-ai-agents-claude-cursor-copilot">AI Agent Setup</a> •
  <a href="#available-skills-51">Skills</a> •
  <a href="#write-your-own-skill">Contribute</a> •
  <a href="#rest-api-reference">API</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white" alt="Docker Ready">
  <img src="https://img.shields.io/badge/skills-51+-6366f1" alt="51+ Skills">
  <img src="https://img.shields.io/badge/license-Apache%202.0-brightgreen" alt="Apache 2.0">
  <img src="https://img.shields.io/badge/API-REST%20%2B%20Dashboard-cyan" alt="REST API">
</p>

---

## What is SkillForge?

SkillForge is a **stateless AI skill runtime** that runs inside Docker. Start the container and instantly get access to **51+ production-ready skills** across 10 categories — no setup, no database, no boilerplate.

**The problem:** Every developer keeps re-writing the same utility code — CSV converters, regex builders, Dockerfile generators, API scaffolders, code analyzers. AI coding agents (Claude, Cursor, Copilot) can help, but they lack standardized, reusable tools.

**The solution:** SkillForge packages common developer tasks as **stateless workers** with an identical contract: `input → output`. You don't write them; you *use* them — from the dashboard, REST API, CLI, or directly from your AI coding agent.

### Key Principles

| Principle | Detail |
|-----------|--------|
| **Docker-first** | `docker compose up` gives you the full runtime + web dashboard on port `9147` |
| **Standard contract** | Every skill returns `{success, data, error, metadata}` — always |
| **Stateless** | No database, no global state, no side effects — pure input→output |
| **Agent-friendly** | AI agents auto-discover and execute skills via REST API |
| **Community-driven** | Anyone can submit skills; approved ones ship to all users automatically |
| **Schema-first** | Every skill has a JSON schema — agents know exactly what to send |

---

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/ilhankilic/yaratai-skill.git
cd yaratai-skill
docker compose up -d
```

Open **http://localhost:9147** — that's it. The dashboard shows all 51+ skills, lets you execute them, and sync community skills.

> **Port `9147`** is SkillForge's standard port. It's chosen to avoid conflicts with common services.

### Local Development

```bash
git clone https://github.com/ilhankilic/yaratai-skill.git
cd yaratai-skill
pip install -e ".[all]"
uvicorn skillforge.api.app:app --port 9147   # Dashboard + API
```

Or use the CLI directly:

```bash
skillforge list                                    # List all skills
skillforge run data.json-to-csv --input sample.json # Run a skill
skillforge info data.json-to-csv                   # Show skill details
```

### Verify It's Working

```bash
# Health check
curl http://localhost:9147/health
# → {"status":"healthy","version":"0.1.0","skills_loaded":51}

# List all skills
curl http://localhost:9147/api/skills

# Run a skill
curl -X POST http://localhost:9147/api/skills/data.json-to-csv/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"records": [{"name": "Alice", "age": 30}]}}'
# → {"success":true,"data":{"csv":"name,age\nAlice,30\n","row_count":1},...}
```

---

## Dashboard

The web dashboard at `http://localhost:9147` provides a modern management interface:

| Feature | Description |
|---------|-------------|
| **Category sidebar** | Filter skills by AI, API, Code, CSS, Data, DevOps, JS, Media, Mediscreen, UI |
| **Skill cards** | Every skill with description, version, and category badge |
| **Detail modal** | Click any skill → Overview, Input/Output schema tables, Run form |
| **Auto-form** | Input fields auto-generated from `schema.json` — strings, numbers, booleans, arrays |
| **JSON mode** | Toggle to raw JSON editor for full control |
| **Live execution** | Execute any skill and see results inline |
| **Health monitor** | Real-time API health indicator in the top bar |
| **Search** | Instant client-side search across all skills |
| **Sync & Import** | Pull community skills from any GitHub repo, or import individual skills |

---

## For AI Agents (Claude, Cursor, Copilot)

SkillForge is designed to be **discovered and used by AI coding agents** automatically. When an agent opens this project, it reads `AGENTS.md` and immediately knows how to use all 51+ skills.

### Claude Code / Claude Desktop

After cloning this repository, Claude reads `AGENTS.md` and `skillforge-claude-desktop-prompt.md` and can:

1. Start the runtime: `docker compose up -d`
2. Discover all skills: `GET http://localhost:9147/api/skills`
3. Read any skill's schema: `GET http://localhost:9147/api/skills/{id}/info`
4. Execute skills: `POST http://localhost:9147/api/skills/{id}/run`

**Claude Desktop System Prompt** (add to Settings → System Prompt):

```
SkillForge is available at http://localhost:9147.
It provides 51+ stateless skills accessible via REST API.
To discover: GET /api/skills
To inspect:  GET /api/skills/{skill_id}/info
To execute:  POST /api/skills/{skill_id}/run with {"data": {...}}
Every response: {"success": true/false, "data": {...}, "error": "", "metadata": {...}}
Read AGENTS.md for the full reference.
```

### Cursor / Windsurf

Add to your `.cursorrules` or project rules:

```
SkillForge runtime is at http://localhost:9147.
Use POST /api/skills/{skill_id}/run with {"data": {...}} to execute any skill.
Use GET /api/skills to discover available skills.
Use GET /api/skills/{skill_id}/info to read input/output schema before calling.
Skills are stateless — JSON in, JSON out. Always check "success" in the response.
```

### GitHub Copilot / Codex

The API is self-documenting. Key pattern:

```bash
# 1. Discover what's available
curl http://localhost:9147/api/skills | python -m json.tool

# 2. Read a skill's contract
curl http://localhost:9147/api/skills/code.regex-builder/info

# 3. Execute it
curl -X POST http://localhost:9147/api/skills/code.regex-builder/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"description": "match email addresses", "test_strings": ["user@example.com", "not-email"]}}'
```

### Universal Agent Workflow

Any AI agent can follow this pattern:

```
1. docker compose up -d                           # Start runtime
2. GET  http://localhost:9147/health               # Verify it's running
3. GET  http://localhost:9147/api/skills            # Discover all skills
4. GET  http://localhost:9147/api/skills/{id}/info  # Read schema before calling
5. POST http://localhost:9147/api/skills/{id}/run   # Execute with JSON body
```

---

## Available Skills (51)

### 🤖 AI & ML (6)

| Skill ID | Description |
|----------|-------------|
| `ai.embedding-search` | Semantic search over document embeddings |
| `ai.fine-tune-prep` | Prepare datasets for LLM fine-tuning (Alpaca/ShareGPT) |
| `ai.lang-detect` | Language detection with heuristic analysis |
| `ai.ollama-orchestrate` | Multi-step LLM pipeline orchestration via Ollama |
| `ai.prompt-engineer` | Transform raw requests into structured LLM prompts |
| `ai.synthetic-data` | Generate synthetic datasets from schema definitions |

### 🔌 API Tools (5)

| Skill ID | Description |
|----------|-------------|
| `api.mock-server` | Generate mock API servers from OpenAPI specs |
| `api.postman-export` | Convert OpenAPI to Postman collections |
| `api.rate-limit-check` | Simulate and analyze API rate limiting |
| `api.rest-scaffold` | Scaffold REST API endpoints from schema |
| `api.webhook-validator` | Validate webhook payloads and HMAC signatures |

### 💻 Code Generation (8)

| Skill ID | Description |
|----------|-------------|
| `code.boilerplate` | Generate project boilerplate (FastAPI, Next.js, React) |
| `code.changelog` | Generate changelogs from git commit logs |
| `code.docstring` | Auto-generate docstrings for Python functions/classes |
| `code.env-template` | Extract environment variables and generate .env templates |
| `code.pr-summary` | Generate pull request summaries from diffs |
| `code.readme-gen` | Generate README.md from project metadata |
| `code.regex-builder` | Build and test regex patterns from descriptions |
| `code.test-gen` | Generate pytest test cases from source code |

### 🎨 CSS Utils (3)

| Skill ID | Description |
|----------|-------------|
| `css.bem-converter` | Convert CSS selectors to BEM methodology |
| `css.minify` | Minify CSS with comment removal and shorthand optimization |
| `css.var-extract` | Extract repeated CSS values into CSS custom properties |

### 📊 Data Processing (6)

| Skill ID | Description |
|----------|-------------|
| `data.csv-clean` | Clean CSV data — remove empty rows, duplicates, normalize dates |
| `data.excel-to-json` | Convert Excel spreadsheets to JSON |
| `data.json-to-csv` | Convert JSON arrays to CSV with nested field support |
| `data.pdf-extract` | Extract text and tables from PDF files |
| `data.schema-infer` | Infer JSON Schema from sample data |
| `data.shapefile-convert` | Convert shapefiles to GeoJSON/KML |

### ⚙️ DevOps (5)

| Skill ID | Description |
|----------|-------------|
| `devops.dockerfile-gen` | Generate Dockerfiles for various languages/frameworks |
| `devops.env-secret-scan` | Scan files for exposed secrets and API keys |
| `devops.github-actions` | Generate GitHub Actions workflow files |
| `devops.k8s-manifest` | Generate Kubernetes deployment/service manifests |
| `devops.nginx-conf` | Generate Nginx configuration files |

### 🟨 JavaScript (5)

| Skill ID | Description |
|----------|-------------|
| `js.bundle-analyze` | Analyze npm packages for bundle size issues |
| `js.dead-code` | Detect unused functions and imports |
| `js.env-validator` | Validate environment variable schemas |
| `js.eslint-autofix` | Generate ESLint configurations |
| `js.ts-migrate` | Migrate JavaScript to TypeScript |

### 🖼️ Media (7)

| Skill ID | Description |
|----------|-------------|
| `media.audio-trim` | Trim audio files with fade effects |
| `media.img-compress` | Compress images with format optimization |
| `media.img-meta-strip` | Strip EXIF/GPS metadata from images |
| `media.img-placeholder` | Generate SVG/PNG placeholder images |
| `media.img-resize-batch` | Batch resize images with contain/cover modes |
| `media.img-to-webp` | Convert images to WebP format |
| `media.video-thumbnail` | Extract thumbnails from video files |

### 🏥 Mediscreen (1)

| Skill ID | Description |
|----------|-------------|
| `mediscreen.triage` | Patient triage assessment via Ollama LLM |

### 🎯 UI / UX (5)

| Skill ID | Description |
|----------|-------------|
| `ui.bootstrap-scaffold` | Scaffold Bootstrap page layouts |
| `ui.dark-mode-patch` | Generate dark mode CSS patches |
| `ui.figma-to-html` | Convert Figma node trees to HTML/CSS |
| `ui.react-component` | Generate React component boilerplate |
| `ui.tailwind-layout` | Convert inline styles to Tailwind CSS classes |

---

## REST API Reference

Base URL: `http://localhost:9147`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check — returns status, version, skill count |
| `/api/skills` | GET | List all skills (`?category=data`, `?search=csv`) |
| `/api/skills/{id}/info` | GET | Full skill info — schema, description, SKILL.md |
| `/api/skills/{id}/run` | POST | Execute a skill with `{"data": {...}}` |
| `/api/sync/github` | POST | Sync all skills from a GitHub repo |
| `/api/sync/import` | POST | Import a single skill from a repo path |
| `/api/sync/validate` | POST | Validate a skill directory against standards |

### Response Format (Every Skill)

```json
{
  "success": true,
  "data": { "...skill-specific output..." },
  "error": "",
  "metadata": { "skill_id": "...", "version": "..." }
}
```

### Examples

```bash
# List skills by category
curl "http://localhost:9147/api/skills?category=data"

# Search skills
curl "http://localhost:9147/api/skills?search=regex"

# Get skill schema (always read before calling)
curl http://localhost:9147/api/skills/code.test-gen/info

# Run: Generate a Dockerfile
curl -X POST http://localhost:9147/api/skills/devops.dockerfile-gen/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"language": "python", "framework": "fastapi", "python_version": "3.12"}}'

# Run: Convert JSON to CSV
curl -X POST http://localhost:9147/api/skills/data.json-to-csv/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"records": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}}'

# Run: Build a regex pattern
curl -X POST http://localhost:9147/api/skills/code.regex-builder/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"description": "match IPv4 addresses", "test_strings": ["192.168.1.1", "not-ip"]}}'
```

---

## Community Skills & Sync

SkillForge supports importing skills from any GitHub repository that follows the [SkillForge Standard](STANDARD.md).

### How It Works

1. A community member writes a skill following the 4-file standard (`schema.json`, `worker.py`, `SKILL.md`, `test.py`)
2. They push it to their own GitHub repo under a `skills/<category>/<name>/` structure
3. Any SkillForge user can import it via the dashboard or API
4. After review, approved skills are merged into the official repo and ship to all users

### Import via Dashboard

1. Open `http://localhost:9147`
2. Click **"Sync & Import"** in the sidebar
3. Enter the GitHub repo URL (default: `https://github.com/ilhankilic/yaratai-skill`)
4. Click **Sync** — all valid skills are imported into `skills/community/`

### Import via API

```bash
# Sync all skills from a community repo
curl -X POST http://localhost:9147/api/sync/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/skillforge-skills", "branch": "main"}'

# Import a single skill
curl -X POST http://localhost:9147/api/sync/import \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "skill_path": "skills/data/my-tool", "branch": "main"}'

# Validate before importing
curl -X POST http://localhost:9147/api/sync/validate \
  -H "Content-Type: application/json" \
  -d '{"skill_path": "data/json-to-csv"}'
```

### Submission Process

1. Fork this repository
2. Create your skill under `skills/<category>/<skill-name>/`
3. Ensure all 4 files exist and tests pass
4. Open a PR to the `dev` branch
5. After review and approval, your skill ships to all users

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Write Your Own Skill

Every skill is a folder with exactly **4 files**:

```
skills/<category>/<skill-name>/
├── schema.json    # Input/output contract (write this FIRST)
├── worker.py      # Python implementation (BaseWorker subclass)
├── SKILL.md       # Documentation for humans and AI agents
└── test.py        # Automated tests (minimum 3 cases)
```

### Step-by-Step

1. **Copy the template**: `cp -r skills/_template skills/<category>/<your-skill>/`
2. **Write `schema.json`** — define input fields, types, and required fields
3. **Implement `worker.py`** — subclass `BaseWorker`, implement `run()`
4. **Document in `SKILL.md`** — describe usage, input/output tables
5. **Write `test.py`** — at least 3 tests (happy path, edge case, error)
6. **Test**: `pytest skills/<category>/<your-skill>/test.py -v`

### Minimal Example

**`schema.json`**
```json
{
  "skill_id": "demo.echo",
  "version": "1.0.0",
  "description": "Echo input back as output.",
  "input": {
    "type": "object",
    "required": ["message"],
    "properties": {
      "message": { "type": "string", "description": "Text to echo." }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "echoed": { "type": "string", "description": "The echoed message." }
    }
  }
}
```

**`worker.py`**
```python
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    """Echo the input message back."""
    skill_id = "demo.echo"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        message = input.data.get("message", "")
        if not message:
            return SkillOutput(success=False, error="'message' is required.")
        return SkillOutput(success=True, data={"echoed": message})
```

See [STANDARD.md](STANDARD.md) for the full specification and rules.

---

## Project Structure

```
skillforge/
├── Dockerfile                  # Container image
├── docker-compose.yml          # One-command full runtime (port 9147)
├── pyproject.toml              # Package definition & dependencies
├── AGENTS.md                   # Instructions for AI coding agents
├── STANDARD.md                 # Skill coding standard
├── CONTRIBUTING.md             # Contribution guidelines
├── skillforge/                 # Core Python package
│   ├── base.py                 # BaseWorker, SkillInput, SkillOutput
│   ├── registry.py             # Auto-discovery & cached loading
│   ├── orchestrator.py         # Pipeline execution engine
│   ├── sync.py                 # GitHub sync & skill validation
│   ├── api/                    # FastAPI REST API + web dashboard
│   │   ├── app.py              # Application factory
│   │   ├── routes/             # health, skills, sync, panel
│   │   ├── templates/          # Dashboard HTML (single-page)
│   │   └── static/             # CSS/JS assets
│   └── nodes/
│       ├── local_node.py       # Ollama adapter
│       └── cloud_node.py       # RunPod/GCP adapter
├── cli/
│   ├── main.py                 # Typer CLI (run, list, test, pipe, create)
│   └── _creator.py             # Claude-powered skill generation
├── skills/                     # 51+ skills across 10 categories
│   ├── _template/              # Copy this to create a new skill
│   ├── community/              # Auto-synced skills from GitHub
│   ├── ai/                     # 6 AI/ML skills
│   ├── api/                    # 5 API tool skills
│   ├── code/                   # 8 code generation skills
│   ├── css/                    # 3 CSS utility skills
│   ├── data/                   # 6 data processing skills
│   ├── devops/                 # 5 DevOps skills
│   ├── js/                     # 5 JavaScript skills
│   ├── media/                  # 7 media processing skills
│   ├── mediscreen/             # 1 medical triage skill
│   └── ui/                     # 5 UI/UX skills
├── pipelines/                  # YAML pipeline definitions
├── tests/                      # Core, API, sync & node tests
└── .github/
    ├── workflows/test.yml      # CI: pytest on Python 3.11/3.12
    └── ISSUE_TEMPLATE/         # New skill request template
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `skillforge list [--category <cat>]` | List registered skills |
| `skillforge run <skill_id> -i <file>` | Run a single skill with JSON input |
| `skillforge info <skill_id>` | Show skill details and SKILL.md |
| `skillforge test <skill_id>` | Run pytest for a specific skill |
| `skillforge pipe <pipeline> -i <file>` | Execute a YAML pipeline |
| `skillforge create "<desc>" [--dry-run]` | Auto-generate a skill via Claude API |

---

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL (`http://ollama:11434` in Docker) |
| `OLLAMA_MODEL` | `gemma3:4b` | Default LLM model |
| `OLLAMA_TIMEOUT` | `60` | Request timeout (seconds) |
| `RUNPOD_API_KEY` | — | RunPod API key (optional, for cloud skills) |
| `RUNPOD_ENDPOINT` | — | RunPod endpoint URL |
| `ANTHROPIC_API_KEY` | — | For `skillforge create` command |
| `SKILLFORGE_ENV` | — | Set to `docker` in container |

---

## Docker Architecture

```
┌─────────────────────────────────────────────────┐
│  docker compose up -d                           │
│                                                 │
│  ┌──────────────────────┐  ┌─────────────────┐  │
│  │  skillforge:9147     │  │  ollama:11434   │  │
│  │  ┌────────────────┐  │  │                 │  │
│  │  │ FastAPI + UI   │  │  │  gemma3:4b      │  │
│  │  │ 51+ Skills     │──│──│  LLM inference  │  │
│  │  │ Sync Engine    │  │  │                 │  │
│  │  └────────────────┘  │  └─────────────────┘  │
│  │  volume: community/  │  │  volume: models  │  │
│  └──────────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────┘
```

- **SkillForge container** (port 9147): FastAPI API + Dashboard + all skills
- **Ollama container** (port 11434): Local LLM for AI-powered skills
- Community skills persist across restarts via Docker volume
- Ollama models are cached in a separate volume

---

## Running Tests

```bash
# All tests (core + skills)
pytest

# Core tests only
pytest tests/ -v

# Specific skill
pytest skills/data/json-to-csv/test.py -v

# With coverage
pytest --cov=skillforge --cov-report=term-missing
```

> All 301+ tests must pass. 6 tests may skip if optional dependencies (pdfplumber, geopandas) are not installed.

---

## Contributing

We welcome contributions! Whether it's a new skill, a bug fix, or documentation improvement:

1. **Fork** this repository
2. **Clone** your fork and switch to `dev` branch
3. **Create** your skill following [STANDARD.md](STANDARD.md) (4 files: schema.json → worker.py → SKILL.md → test.py)
4. **Test** everything: `pytest`
5. **Push** to your fork and open a **PR targeting `dev`**
6. After review & merge → your skill ships to all users via `docker compose up` 🎉

> Both `master` and `dev` are protected. `master` is the stable release branch (default for users). All development flows through `dev` via Pull Requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full step-by-step guide, submission checklist, and naming conventions.

---

## Roadmap

- [ ] Skill marketplace with ratings and reviews
- [ ] WebSocket support for long-running skills
- [ ] Skill dependency chains (skill A requires skill B)
- [ ] Plugin system for custom node types
- [ ] Multi-language workers (TypeScript, Go)
- [ ] Skill versioning and rollback

---

## License

[Apache 2.0](LICENSE) — use it, extend it, contribute back.

---

<p align="center">
  <strong>SkillForge</strong> — Real code. Standard I/O. No database. Just workers.<br>
  <a href="https://github.com/ilhankilic/yaratai-skill">GitHub</a> •
  <a href="http://localhost:9147">Dashboard</a> •
  <a href="STANDARD.md">Standard</a> •
  <a href="CONTRIBUTING.md">Contributing</a>
</p>
