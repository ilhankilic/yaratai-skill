# SkillForge

**Real code. Standard I/O. No database. Just workers. Docker-ready.**

SkillForge is a stateless AI skill runtime that runs inside Docker. Start the container and instantly get access to **51+ skills** across 10 categories — no setup, no database, no boilerplate. AI agents (Claude Code, Cursor, Codex, Windsurf) discover skills automatically and use them on your behalf.

---

## Why SkillForge?

Every developer keeps re-writing the same utility code — CSV converters, PDF parsers, API wrappers, triage logic. SkillForge packages these as **stateless workers** with an identical `run(input) → output` contract. You don't write them; you *use* them.

1. **Docker-first** — `docker compose up` gives you the full runtime + management dashboard
2. **Standard contract** — every skill: `{success, data, error, metadata}`
3. **Community-driven** — anyone can submit skills; approved ones ship to all users
4. **Agent-friendly** — AI coding assistants auto-discover and execute skills via REST API

---

## Quick Start (Docker — Recommended)

```bash
git clone https://github.com/ilhankilic/yaratai-skill.git
cd yaratai-skill
docker compose up -d
```

Open **http://localhost:9147** — that's it. The modern dashboard lets you:

- 🧩 **Browse** all 51+ skills by category with search
- 📋 **Inspect** input/output schemas for every skill
- ▶️ **Execute** any skill with auto-generated forms or raw JSON
- 🔄 **Sync** community skills from GitHub repos
- 📥 **Import** individual skills by URL

### Quick Start (Local)

```bash
pip install -e ".[all]"
uvicorn skillforge.api.app:app --port 9147   # Dashboard + API
# or CLI:
skillforge list
skillforge run data.json-to-csv --input sample.json
```

---

## Dashboard

The web dashboard at `http://localhost:9147` provides:

| Feature | Description |
|---------|-------------|
| **Category sidebar** | Filter skills by AI, API, Code, CSS, Data, DevOps, JS, Media, Mediscreen, UI |
| **Skill cards** | Every skill with description, version, category badge |
| **Detail modal** | Click any skill → Overview, Input/Output schema tables, Run form |
| **Auto-form** | Input fields generated from `schema.json` — strings, numbers, booleans, arrays |
| **JSON mode** | Toggle to raw JSON for full control |
| **Live results** | Execute and see success/error output inline |
| **Health monitor** | Real-time API health indicator in top bar |
| **Search** | Instant client-side search across all skills |

---

## REST API

Once running (Docker or `uvicorn skillforge.api.app:app --port 9147`):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + stats |
| `/api/skills` | GET | List all skills (with `?category=` and `?search=` filters) |
| `/api/skills/{id}/info` | GET | Full skill details + input/output schema + SKILL.md |
| `/api/skills/{id}/run` | POST | Execute a skill |
| `/api/sync/github` | POST | Sync all skills from a GitHub repo |
| `/api/sync/import` | POST | Import a single skill |
| `/api/sync/validate` | POST | Validate a skill directory |

### Example: Run a skill via API

```bash
curl -X POST http://localhost:9147/api/skills/data.json-to-csv/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"records": [{"name": "Alice", "age": 30}]}}'
```

### Example: Get skill schema

```bash
curl http://localhost:9147/api/skills/data.json-to-csv/info
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

### 💻 Code Gen (8)
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

## For AI Coding Agents

### Universal Workflow (All Agents)

After cloning this repository, any AI agent should:

```
1. docker compose up -d                              # Start runtime
2. GET  http://localhost:9147/health                  # Verify it's running
3. GET  http://localhost:9147/api/skills              # Discover all skills
4. GET  http://localhost:9147/api/skills/{id}/info    # Read skill schema
5. POST http://localhost:9147/api/skills/{id}/run     # Execute with JSON body
```

### Claude Code / Claude Desktop

Read `AGENTS.md` and `skillforge-claude-desktop-prompt.md` for the full session config. The agent reads `SKILL.md` files to understand every skill's purpose and contract.

### Cursor / Windsurf

Add this to your project rules or `.cursorrules`:

```
SkillForge is running at http://localhost:9147.
To use a skill: POST /api/skills/{skill_id}/run with {"data": {...}}.
To discover skills: GET /api/skills.
To see schema: GET /api/skills/{skill_id}/info.
Skills are stateless — input goes in, output comes out.
```

### Codex / GitHub Copilot Agent

The API is self-documenting. Key endpoints:

```bash
# List everything
curl http://localhost:9147/api/skills | python -m json.tool

# Get schema for a specific skill
curl http://localhost:9147/api/skills/data.json-to-csv/info

# Run a skill
curl -X POST http://localhost:9147/api/skills/data.json-to-csv/run \
  -H "Content-Type: application/json" \
  -d '{"data": {"records": [{"name": "Alice", "age": 30}]}}'
```

### Import Community Skills

Through the dashboard (http://localhost:9147 → Sync & Import) or the API:

```bash
# Sync all skills from a community repo
curl -X POST http://localhost:9147/api/sync/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/skillforge-skills"}'

# Import a single skill
curl -X POST http://localhost:9147/api/sync/import \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "skill_path": "skills/data/my-tool"}'
```

---

## Project Structure

```
skillforge/
├── Dockerfile                  # Container image
├── docker-compose.yml          # One-command full runtime
├── pyproject.toml              # Package definition & dependencies
├── AGENTS.md                   # Agent instructions
├── STANDARD.md                 # Skill coding standard
├── skillforge/                 # Core Python package
│   ├── base.py                 # BaseWorker, SkillInput, SkillOutput
│   ├── registry.py             # Auto-discovery & loading (cached)
│   ├── orchestrator.py         # Pipeline execution engine
│   ├── sync.py                 # GitHub sync & skill validation
│   ├── api/                    # FastAPI REST API + web dashboard
│   │   ├── app.py              # Application factory
│   │   ├── routes/             # health, skills, sync, panel
│   │   └── templates/          # Dashboard HTML
│   └── nodes/
│       ├── local_node.py       # Ollama adapter
│       └── cloud_node.py       # RunPod/GCP adapter
├── cli/
│   └── main.py                 # Typer CLI (run, list, test, pipe, create)
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

## CLI Reference

| Command | Description |
|---------|-------------|
| `skillforge run <skill_id> -i <file>` | Run a single skill |
| `skillforge list [--category <cat>]` | List registered skills |
| `skillforge info <skill_id>` | Show skill details & SKILL.md |
| `skillforge test <skill_id>` | Run pytest for a skill |
| `skillforge pipe <pipeline> -i <file>` | Execute a YAML pipeline |
| `skillforge create "<desc>" [--dry-run]` | Auto-generate a skill via Claude |

---

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:4b` | Default LLM model |
| `OLLAMA_TIMEOUT` | `60` | Request timeout (seconds) |
| `RUNPOD_API_KEY` | — | RunPod API key |
| `RUNPOD_ENDPOINT` | — | RunPod endpoint URL |
| `ANTHROPIC_API_KEY` | — | For `skillforge create` |
| `SKILLFORGE_ENV` | — | Set to `docker` in container |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

[Apache 2.0](LICENSE)
