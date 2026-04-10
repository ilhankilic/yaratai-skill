# Contributing to SkillForge

Thank you for your interest in contributing! This guide covers the essentials.

---

## Getting Started

```bash
git clone https://github.com/ilhankilic/yaratai-skill.git
cd yaratai-skill
git checkout dev              # always work on dev branch
pip install -e ".[all]"       # install all optional dependencies
pytest                         # run all tests (301 should pass)
```

---

## Branch Strategy

| Branch | Purpose | Who pushes |
|--------|---------|------------|
| `master` | **Production** — stable, tested, ready for `docker compose up` | Merge from `dev` only |
| `dev` | **Development** — all new features and fixes land here first | Everyone |

### Workflow

```
1. git checkout dev
2. git pull origin dev
3. (make changes, add tests)
4. pytest                       # all tests must pass
5. git add -A && git commit -m "feat(skills): add category.skill-name"
6. git push origin dev
7. When dev is stable → merge dev into master (release)
```

### Release to master

```bash
git checkout master
git merge dev --no-ff -m "release: <description>"
git push origin master
git checkout dev               # go back to dev
```

> **Rule**: Never push directly to `master`. Always develop on `dev` and merge when ready.

---

## Adding a New Skill

### Checklist

Before submitting a PR for a new skill, confirm every item:

- [ ] Skill lives in `skills/<category>/<skill-name>/`
- [ ] `schema.json` is present and defines input/output
- [ ] `worker.py` subclasses `BaseWorker` with a unique `skill_id`
- [ ] `SKILL.md` documents usage, input table, and output table
- [ ] `test.py` has at least 3 test cases (happy, edge, error)
- [ ] All tests pass: `pytest skills/<category>/<skill-name>/test.py -v`
- [ ] No database usage, no global state, no `print()`
- [ ] Type hints on all function signatures

### Workflow

1. **Schema first** — write `schema.json` before any code
2. **Implement** — create `worker.py` following the BaseWorker contract
3. **Document** — write `SKILL.md` for human and agent readers
4. **Test** — write `test.py` and mock all external services
5. **Verify** — run `pytest` and `skillforge test <skill_id>` locally

---

## Pull Request Guidelines

- **Target branch**: always `dev` (never `master` directly)
- One skill per PR (unless tightly coupled)
- PR title: `feat(skills): add <category>.<skill-name>`
- Include a brief description of what the skill does
- All CI checks must pass before merge
- Keep diffs focused — don't mix unrelated changes

---

## Naming Conventions

| Item      | Convention                          | Example                  |
|-----------|-------------------------------------|--------------------------|
| skill_id  | `<category>.<kebab-case>`           | `data.json-to-csv`       |
| Folder    | `skills/<category>/<kebab-case>/`   | `skills/data/json-to-csv/` |
| Class     | Always `Worker`                     | `class Worker(BaseWorker)` |
| Files     | English only                        | `worker.py`, `schema.json` |

---

## Code Style

- Python 3.11+
- Type hints on every function
- Docstrings on every class and public method
- `logging` module instead of `print()`
- No hardcoded values — use schema fields or env variables

---

## Running Tests

```bash
# All tests
pytest

# Specific skill
pytest skills/mediscreen/triage/test.py -v

# Core tests only
pytest tests/ -v

# With coverage
pytest --cov=skillforge --cov-report=term-missing
```

---

## Questions?

Open an issue or start a discussion. We're happy to help!

