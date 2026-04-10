# SkillForge Standard

This document defines the rules and conventions for writing SkillForge skills.  
Every skill MUST comply with this standard to be accepted into the repository.

---

## 1. Skill Structure

Every skill lives in `skills/<category>/<skill-name>/` and contains exactly **4 files**:

| File          | Purpose                                       |
|---------------|-----------------------------------------------|
| `schema.json` | Input/output JSON Schema                      |
| `worker.py`   | Python implementation (BaseWorker subclass)   |
| `SKILL.md`    | Human & agent-readable documentation          |
| `test.py`     | Automated tests (pytest)                      |

No other files are required. No additional files should alter the skill's runtime behavior.

---

## 2. BaseWorker Interface

```python
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "category.skill-name"   # unique dot-separated identifier
    version  = "1.0.0"                 # semver

    def run(self, input: SkillInput) -> SkillOutput:
        # Your logic here
        return SkillOutput(success=True, data={...}, metadata={...})
```

### SkillInput

| Field    | Type         | Description                    |
|----------|--------------|--------------------------------|
| data     | `dict`       | Skill-specific input payload   |
| metadata | `dict`       | Optional contextual metadata   |

### SkillOutput

| Field    | Type         | Required | Description                  |
|----------|--------------|----------|------------------------------|
| success  | `bool`       | ✅       | Whether the skill succeeded  |
| data     | `dict`       | ✅       | Result payload               |
| error    | `str`        | ❌       | Error message (on failure)   |
| metadata | `dict`       | ❌       | Timing, model info, etc.     |

**The `run()` signature and output shape must never be changed.**

---

## 3. schema.json Format

```json
{
  "skill_id": "category.skill-name",
  "version": "1.0.0",
  "description": "One-line description.",
  "input": {
    "type": "object",
    "required": ["field_a"],
    "properties": {
      "field_a": { "type": "string", "description": "..." },
      "field_b": { "type": "integer", "description": "...", "default": 10 }
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "result": { "type": "string", "description": "..." }
    }
  }
}
```

- Write `schema.json` **before** `worker.py`.
- Every required field must be listed in `input.required`.
- Use standard JSON Schema types: `string`, `integer`, `number`, `boolean`, `array`, `object`.

---

## 4. SKILL.md Format

```markdown
# category.skill-name

One-paragraph description.

## Usage
(CLI example)

## Input
(table of fields)

## Output
(table of fields)

## Dependencies
(list any extra packages)
```

This file is read by AI agents — keep it concise, factual, and machine-parseable.

---

## 5. Testing Requirements

- At least **3 test cases** per skill:
  1. **Happy path** — valid input produces correct output
  2. **Edge case** — boundary values, empty input, etc.
  3. **Error case** — invalid input returns `success=False`
- Use `pytest` and mock external services (Ollama, RunPod, etc.)
- Tests must run without network access or special hardware

---

## 6. Quality Rules

| Rule                | Detail                                                  |
|---------------------|----------------------------------------------------------|
| Type hints          | Every function parameter and return value must be typed  |
| Docstrings          | Every class and public method                            |
| Error handling      | Never raise exceptions — return `SkillOutput(success=False, error=...)` |
| Dependencies        | Only packages listed in `pyproject.toml`                 |
| No database         | No SQLite, Redis, PostgreSQL, or any persistent storage  |
| No global state     | Workers are stateless; don't write to instance variables  |
| Logging             | Use `logging` module, never `print()`                    |
| No hardcoded values | All config via `schema.json` fields or env variables     |

---

## 7. Naming Conventions

- **skill_id**: `<category>.<kebab-case-name>` — e.g., `data.json-to-csv`
- **Folder**: `skills/<category>/<kebab-case-name>/`
- **Class**: always named `Worker` inside `worker.py`
- **Files**: English only (code, filenames). Communication may be in Turkish.

---

## 8. Minimal Valid Skill Example

### `skills/demo/echo/schema.json`

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

### `skills/demo/echo/worker.py`

```python
from skillforge.base import BaseWorker, SkillInput, SkillOutput

class Worker(BaseWorker):
    skill_id = "demo.echo"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        message = input.data.get("message", "")
        if not message:
            return SkillOutput(success=False, error="'message' is required.")
        return SkillOutput(success=True, data={"echoed": message})
```

---

## Prohibited

- ❌ Database connections of any kind
- ❌ Global mutable state
- ❌ `print()` statements
- ❌ Placeholder code (`TODO`, `...`, `pass` in `run()`)
- ❌ Breaking the `run()` interface signature
- ❌ Hardcoded API keys or URLs

