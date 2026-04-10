# code.regex-builder

Generate regex patterns from natural language descriptions with built-in test validation.

## Usage

```bash
skillforge run code.regex-builder --input input.json
```

### Input

| Field            | Type   | Required | Description                                |
|------------------|--------|----------|--------------------------------------------|
| description      | string | ✅       | What the regex should match                |
| examples_match   | array  | ❌       | Strings that SHOULD match                  |
| examples_no_match| array  | ❌       | Strings that should NOT match              |
| language         | string | ❌       | Target: `python` / `javascript` / `go`     |
| flags            | array  | ❌       | `IGNORECASE`, `MULTILINE`, `DOTALL`        |
| named_groups     | bool   | ❌       | Use named capture groups                   |

### Output

| Field         | Type   | Description                       |
|---------------|--------|-----------------------------------|
| pattern       | string | Generated regex pattern           |
| flags_used    | array  | Active flags                      |
| explanation   | string | Human-readable explanation        |
| test_results  | array  | Validation against examples       |
| usage_example | string | Code snippet in target language   |
| alternatives  | array  | Alternative patterns              |

## Built-in Pattern Library

Email, Turkish phone, TC Kimlik, URL, IPv4, ISO date, hex color, UUID, semver, IBAN, credit card, Turkish postal code.

