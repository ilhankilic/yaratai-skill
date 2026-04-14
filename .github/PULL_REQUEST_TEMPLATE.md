---
name: New Skill Submission
about: Submit a new skill for SkillForge
---

## Skill Information

- **Skill ID**: `category.skill-name`
- **Category**: <!-- ai / api / code / css / data / devops / js / media / mediscreen / ui / other -->
- **Version**: `1.0.0`

## Description

<!-- One paragraph: what does this skill do and why is it useful? -->

## Files Included

- [ ] `schema.json` — input/output contract defined
- [ ] `worker.py` — `BaseWorker` subclass with `run()` method
- [ ] `SKILL.md` — documentation for humans and AI agents
- [ ] `test.py` — at least 3 tests (happy path, edge case, error case)

## Input Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
|       |      |          |             |

## Output Fields

| Field | Type | Description |
|-------|------|-------------|
|       |      |             |

## Quality Checklist

- [ ] `skill_id` in `schema.json` and `worker.py` match
- [ ] Never raises exceptions — returns `SkillOutput(success=False, error=...)`
- [ ] Type hints on all function parameters and return values
- [ ] Docstrings on all classes and public methods
- [ ] No database, no global state, no `print()`
- [ ] Tests run offline (all external services mocked)
- [ ] `pytest skills/<category>/<skill-name>/test.py -v` passes
- [ ] Full test suite still passes: `pytest`

## External Dependencies

<!-- Does this need any packages not in pyproject.toml? List them here. -->
<!-- Does this need Ollama or any external API? -->

None / _list dependencies_

## Additional Context

<!-- Screenshots, examples, related skills, or references -->

