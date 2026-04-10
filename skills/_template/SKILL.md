# Template Skill

A template skill that echoes input back. Copy this folder to `skills/<category>/<skill-name>/` and customise.

## Usage

```bash
skillforge run category.skill-name --input data.json
```

## Input

| Field          | Type   | Required | Description              |
|----------------|--------|----------|--------------------------|
| example_field  | string | ✅       | An example input value   |
| optional_field | int    | ❌       | An optional parameter    |

## Output

| Field  | Type   | Description            |
|--------|--------|------------------------|
| result | string | Echoed input value     |

