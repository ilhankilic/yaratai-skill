# Contributing to SkillForge

Thank you for your interest in contributing! SkillForge is an open-source skill library — **anyone can submit new skills** and, once approved, they ship to every user automatically via Docker.

This guide covers everything: from writing your first skill to getting it merged.

---

## Table of Contents

- [Two Ways to Contribute](#two-ways-to-contribute)
- [Option A: Submit a Skill via Pull Request (Permanent)](#option-a-submit-a-skill-via-pull-request-permanent)
- [Option B: Share via Your Own Repo (Community Sync)](#option-b-share-via-your-own-repo-community-sync)
- [Step-by-Step: Writing a New Skill](#step-by-step-writing-a-new-skill)
- [Available Categories](#available-categories)
- [Review & Approval Process](#review--approval-process)
- [Branch Strategy](#branch-strategy)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Naming Conventions](#naming-conventions)
- [Code Style](#code-style)
- [Running Tests](#running-tests)
- [FAQ](#faq)

---

## Two Ways to Contribute

| Method | Who | Result | Permanent? |
|--------|-----|--------|------------|
| **Pull Request** | Fork → code → PR to `dev` | Skill becomes part of the official repo, ships to all users | ✅ Yes |
| **Community Sync** | Push to your own repo, share URL | Others import via dashboard or API; lives in `skills/community/` | ♻️ Per-user |

Most contributors should use **Option A** (Pull Request) — your skill becomes part of the official distribution.

---

## Option A: Submit a Skill via Pull Request (Permanent)

This is the recommended path. Your skill will be reviewed, tested, and merged into the official SkillForge repo. Once merged, **every user** who runs `docker compose up` gets your skill automatically.

### Quick Overview

```
1. Fork the repo on GitHub
2. Clone your fork locally
3. Create your skill (4 files)
4. Test it
5. Push to your fork
6. Open a PR to the `dev` branch
7. Review → Merge → Your skill ships to everyone 🎉
```

### Detailed Steps

```bash
# 1. Fork on GitHub: click "Fork" at https://github.com/ilhankilic/yaratai-skill

# 2. Clone YOUR fork
git clone https://github.com/YOUR_USERNAME/yaratai-skill.git
cd yaratai-skill
git checkout dev

# 3. Install dependencies
pip install -e ".[all]"

# 4. Copy the template
cp -r skills/_template skills/<category>/<your-skill-name>
# Example: cp -r skills/_template skills/data/xml-to-json

# 5. Write your 4 files (see "Step-by-Step" section below)
#    - schema.json  (FIRST)
#    - worker.py
#    - SKILL.md
#    - test.py

# 6. Test your skill
pytest skills/<category>/<your-skill-name>/test.py -v

# 7. Run ALL tests to make sure nothing is broken
pytest

# 8. Commit and push
git add -A
git commit -m "feat(skills): add <category>.<skill-name>"
git push origin dev

# 9. Open a Pull Request
#    Go to https://github.com/ilhankilic/yaratai-skill/compare
#    Base: dev ← Compare: your-fork/dev
#    Fill in the PR template and submit
```

---

## Option B: Share via Your Own Repo (Community Sync)

You can also host skills in your own GitHub repository. Other SkillForge users can import them via the **dashboard** or **API**. This is useful for:

- Skills that are too niche for the official repo
- Work-in-progress skills you want to share early
- Organization-internal skills

### Requirements

Your repo must follow this structure:

```
your-repo/
└── skills/
    └── <category>/
        └── <skill-name>/
            ├── schema.json
            ├── worker.py
            ├── SKILL.md
            └── test.py
```

### How Users Import Your Skills

**Via Dashboard:**

1. Open `http://localhost:9147`
2. Click **"Sync & Import"** in the sidebar
3. Enter your repo URL: `https://github.com/YOUR_USERNAME/your-repo`
4. Click **Sync Repository**
5. All valid skills are imported into `skills/community/`

**Via API:**

```bash
# Import all skills from a repo
curl -X POST http://localhost:9147/api/sync/github \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/YOUR_USERNAME/your-repo", "branch": "main"}'

# Import a single skill
curl -X POST http://localhost:9147/api/sync/import \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/YOUR_USERNAME/your-repo",
    "skill_path": "skills/data/xml-to-json",
    "branch": "main"
  }'
```

**Via CLI:**

```bash
skillforge import github:YOUR_USERNAME/your-repo/skills/data/xml-to-json
```

> **Note:** Community-imported skills are stored in a Docker volume and persist across container restarts, but they are not part of the official distribution.

---

## Step-by-Step: Writing a New Skill

Every skill is a folder with exactly **4 files**. Write them in this order:

### Step 1: `schema.json` — Define the Contract

This is the most important file. It tells agents and the dashboard what your skill expects and returns.

```json
{
  "skill_id": "data.xml-to-json",
  "version": "1.0.0",
  "description": "Convert XML strings to JSON objects.",
  "input": {
    "type": "object",
    "required": ["xml_content"],
    "properties": {
      "xml_content": {
        "type": "string",
        "description": "Raw XML string to convert."
      },
      "strip_namespaces": {
        "type": "boolean",
        "description": "Remove XML namespace prefixes from keys.",
        "default": false
      }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "json_data": {
        "type": "object",
        "description": "The converted JSON object."
      },
      "element_count": {
        "type": "integer",
        "description": "Number of top-level elements."
      }
    }
  }
}
```

**Rules:**
- `skill_id` must be unique: `<category>.<kebab-case-name>`
- List all required fields in `input.required`
- Use standard JSON Schema types: `string`, `integer`, `number`, `boolean`, `array`, `object`
- Add `description` to every field — AI agents read these

### Step 2: `worker.py` — Implement the Logic

```python
"""data.xml-to-json — Convert XML strings to JSON objects."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class Worker(BaseWorker):
    """Convert XML content to a JSON-compatible dictionary."""

    skill_id = "data.xml-to-json"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        """Parse XML and return as nested dict."""
        try:
            xml_content: str = input.data.get("xml_content", "")
            if not xml_content:
                return SkillOutput(success=False, error="'xml_content' is required.")

            strip_ns: bool = input.data.get("strip_namespaces", False)

            root = ET.fromstring(xml_content)
            json_data = _element_to_dict(root, strip_ns)

            return SkillOutput(
                success=True,
                data={"json_data": json_data, "element_count": len(root)},
                metadata={"skill_id": self.skill_id, "version": self.version},
            )

        except ET.ParseError as exc:
            return SkillOutput(success=False, error=f"Invalid XML: {exc}")
        except Exception as exc:
            logger.exception("Error in %s", self.skill_id)
            return SkillOutput(success=False, error=str(exc))


def _element_to_dict(elem: ET.Element, strip_ns: bool = False) -> dict[str, Any]:
    """Recursively convert an XML element to a dictionary."""
    tag = elem.tag.split("}")[-1] if strip_ns and "}" in elem.tag else elem.tag
    result: dict[str, Any] = {}
    if elem.attrib:
        result["@attributes"] = dict(elem.attrib)
    if elem.text and elem.text.strip():
        result["#text"] = elem.text.strip()
    for child in elem:
        child_dict = _element_to_dict(child, strip_ns)
        child_tag = child.tag.split("}")[-1] if strip_ns and "}" in child.tag else child.tag
        result[child_tag] = child_dict
    return {tag: result} if result else {tag: elem.text or ""}
```

**Rules:**
- Class must be named `Worker` and subclass `BaseWorker`
- `skill_id` and `version` must match `schema.json`
- **Never raise exceptions** — always return `SkillOutput(success=False, error="...")`
- Type hints on every function parameter and return value
- Docstrings on every class and public method
- Use `logging` module, never `print()`
- No database, no global state, no hardcoded values

### Step 3: `SKILL.md` — Document for Humans and Agents

```markdown
# data.xml-to-json

Convert XML strings to JSON-compatible dictionary objects.

## Usage

\```bash
skillforge run data.xml-to-json --input data.json
\```

## Input

| Field             | Type    | Required | Description                         |
|-------------------|---------|----------|-------------------------------------|
| xml_content       | string  | ✅       | Raw XML string to convert           |
| strip_namespaces  | boolean | ❌       | Remove namespace prefixes (default: false) |

## Output

| Field         | Type    | Description                   |
|---------------|---------|-------------------------------|
| json_data     | object  | The converted JSON object     |
| element_count | integer | Number of top-level elements  |

## Dependencies

None (uses Python stdlib `xml.etree.ElementTree`).
```

### Step 4: `test.py` — Minimum 3 Test Cases

```python
"""Tests for data.xml-to-json skill."""

import pytest
from skillforge.base import SkillInput
from skills.data.xml_to_json.worker import Worker  # adjust import path


@pytest.fixture
def worker() -> Worker:
    return Worker()


def test_happy_path(worker: Worker) -> None:
    """Valid XML should be converted to JSON."""
    inp = SkillInput(data={"xml_content": "<root><name>Alice</name></root>"})
    out = worker.run(inp)
    assert out.success is True
    assert "json_data" in out.data


def test_empty_input(worker: Worker) -> None:
    """Missing xml_content should return error."""
    inp = SkillInput(data={})
    out = worker.run(inp)
    assert out.success is False
    assert "required" in out.error.lower()


def test_invalid_xml(worker: Worker) -> None:
    """Malformed XML should return error, not raise."""
    inp = SkillInput(data={"xml_content": "<broken><xml"})
    out = worker.run(inp)
    assert out.success is False
    assert "invalid" in out.error.lower() or "xml" in out.error.lower()
```

**Rules:**
- At least 3 tests: happy path, edge case, error case
- Tests must run **offline** — mock all external services (Ollama, APIs, etc.)
- Use `pytest` fixtures for the worker instance
- Verify both `success` status and actual data content

---

## Available Categories

Use an existing category when possible. To propose a new one, open an issue.

| Category | Prefix | Description | Example |
|----------|--------|-------------|---------|
| **ai** | `ai.` | AI/ML utilities — embeddings, prompts, fine-tuning | `ai.prompt-engineer` |
| **api** | `api.` | API tools — mocking, scaffolding, validation | `api.rest-scaffold` |
| **code** | `code.` | Code generation — boilerplate, tests, docs | `code.test-gen` |
| **css** | `css.` | CSS utilities — minification, conversion | `css.minify` |
| **data** | `data.` | Data processing — conversion, cleaning, extraction | `data.json-to-csv` |
| **devops** | `devops.` | DevOps — Dockerfiles, CI/CD, K8s, secrets | `devops.dockerfile-gen` |
| **js** | `js.` | JavaScript/TypeScript tools | `js.ts-migrate` |
| **media** | `media.` | Image, audio, video processing | `media.img-compress` |
| **mediscreen** | `mediscreen.` | Medical/health domain skills | `mediscreen.triage` |
| **ui** | `ui.` | UI/UX generation — components, layouts | `ui.react-component` |

---

## Review & Approval Process

When you submit a PR, here's what happens:

```
1. Automated CI
   ├── pytest runs on Python 3.11 + 3.12
   ├── All existing tests must still pass
   └── Your skill's test.py must pass

2. Manual Review (maintainer)
   ├── Does the skill follow STANDARD.md?
   ├── Is schema.json complete and accurate?
   ├── Are there at least 3 meaningful tests?
   ├── Is SKILL.md clear for both humans and AI agents?
   ├── No database, no global state, no print()?
   └── Does it solve a real, reusable problem?

3. Merge
   ├── Merged into `dev` branch
   ├── Tested together with all other skills
   └── Released to `master` in the next batch

4. Distribution 🎉
   └── Every user who runs `docker compose up` gets your skill
```

**Review timeline:** We aim to review PRs within 3-5 days.

### What Gets Rejected

- ❌ Skills that duplicate existing functionality without improvement
- ❌ Missing or placeholder files (`TODO`, `pass`, `...` in `run()`)
- ❌ Skills that require database connections or persistent storage
- ❌ Skills with hardcoded API keys or credentials
- ❌ Test files with fewer than 3 real test cases
- ❌ Skills that break existing tests

---

## Branch Strategy

This is a **public open-source repo**. Both branches are visible, but write access is restricted:

| Branch | Visibility | Purpose | Who can push |
|--------|-----------|---------|-------------|
| `master` | 🌍 Public (default) | **Production** — stable, tested, `docker compose up` ready. This is what users clone. | Maintainer only (merge from `dev`) |
| `dev` | 🌍 Public (visible) | **Development** — all new features and fixes land here via PR | Maintainer only (merges PRs) |

> **Both branches are protected.** No one can push directly — all changes go through Pull Requests.

### Workflow for External Contributors

```
1. Fork the repo on GitHub
2. Clone YOUR fork: git clone https://github.com/YOU/yaratai-skill.git
3. git checkout dev
4. git pull origin dev
5. (write your skill, add tests)
6. pytest                        # ALL tests must pass
7. git add -A && git commit -m "feat(skills): add category.skill-name"
8. git push origin dev           # pushes to YOUR fork
9. Open PR: base=ilhankilic/yaratai-skill:dev ← compare=YOU/yaratai-skill:dev
10. Maintainer reviews → merges into dev → later releases to master
```

### Workflow for Maintainer (Release to master)

```bash
# When dev is stable and ready for release:
git checkout master
git merge dev --no-ff -m "release: <description>"
git push origin master
git checkout dev
```

> **Rule**: No direct pushes to `master` or `dev`. All changes go through PRs. External contributors always target `dev`.

---

## Pull Request Guidelines

- **Target branch**: always `dev` (never `master` directly)
- **One skill per PR** (unless tightly coupled)
- **PR title**: `feat(skills): add <category>.<skill-name>`
- **PR body**: Use the template — describe what the skill does, list input/output
- **All CI checks must pass** before merge
- **Keep diffs focused** — don't mix unrelated changes

---

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| skill_id | `<category>.<kebab-case>` | `data.json-to-csv` |
| Folder | `skills/<category>/<kebab-case>/` | `skills/data/json-to-csv/` |
| Class | Always `Worker` | `class Worker(BaseWorker)` |
| Files | English only | `worker.py`, `schema.json` |
| Commit | `feat(skills): add <id>` | `feat(skills): add data.xml-to-json` |

---

## Code Style

- Python 3.11+
- Type hints on every function parameter and return value
- Docstrings on every class and public method
- `logging` module instead of `print()`
- No hardcoded values — use schema fields or env variables
- Only packages already in `pyproject.toml` (propose additions if needed)

---

## Running Tests

```bash
# All tests (must pass before PR)
pytest

# Your specific skill
pytest skills/<category>/<skill-name>/test.py -v

# Core tests only
pytest tests/ -v

# With coverage
pytest --cov=skillforge --cov-report=term-missing
```

---

## Submission Checklist

Before opening a PR, confirm every item:

- [ ] Skill lives in `skills/<category>/<skill-name>/`
- [ ] `schema.json` is present with `skill_id`, `input`, and `output`
- [ ] `worker.py` subclasses `BaseWorker` with a unique `skill_id`
- [ ] `worker.py` never raises exceptions — returns `SkillOutput(success=False, error=...)`
- [ ] `SKILL.md` documents usage, input table, and output table
- [ ] `test.py` has at least 3 test cases (happy path, edge case, error case)
- [ ] All tests pass: `pytest skills/<category>/<skill-name>/test.py -v`
- [ ] Full test suite still passes: `pytest`
- [ ] No database usage, no global state, no `print()`
- [ ] Type hints on all function signatures
- [ ] Docstrings on all classes and public methods

---

## FAQ

**Q: Can I add a new category?**  
A: Open an issue with the proposed category name and at least 2 example skills that would go in it. We'll discuss and approve.

**Q: Can my skill use external packages not in `pyproject.toml`?**  
A: Propose the dependency in your PR. If it's a common, well-maintained package, we'll add it as an optional dependency group.

**Q: Can I submit skills that need Ollama/LLM?**  
A: Yes! Use `OllamaNode` from `skillforge/nodes/local_node.py`. Make sure tests mock the LLM calls and run offline.

**Q: What if my skill idea already exists?**  
A: If you can significantly improve an existing skill, open a PR with improvements. Otherwise, consider a different angle.

**Q: How are community-synced skills different from official skills?**  
A: Official skills (merged via PR) ship with every Docker image. Community-synced skills live in `skills/community/` and are imported per-user via the dashboard or API.

**Q: Can I use the dashboard to validate my skill before submitting?**  
A: Yes! Use `POST /api/sync/validate` with `{"skill_path": "category/skill-name"}` to run the standard validation checks.

---

## Questions?

Open an [issue](https://github.com/ilhankilic/yaratai-skill/issues) or start a discussion. We're happy to help!
