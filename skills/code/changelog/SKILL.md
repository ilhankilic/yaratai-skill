# code.changelog

Generate CHANGELOG.md from git log output using Conventional Commits standard.

## Usage
```bash
git log --oneline --pretty=format:'%H|%s|%an|%ad' > log.txt
skillforge run code.changelog --input input.json
```

### Input
| Field            | Type   | Required | Description                     |
|------------------|--------|----------|---------------------------------|
| git_log          | string | ✅       | Git log output (hash|msg|author|date) |
| version          | string | ✅       | New version (e.g. `1.2.0`)     |
| repo_url         | string | ❌       | Repo URL for commit links       |
| date             | string | ❌       | Release date (default: today)   |
| include_authors  | bool   | ❌       | Include author names            |

### Output
| Field          | Type    | Description               |
|----------------|---------|---------------------------|
| changelog_md   | string  | Full CHANGELOG.md content |
| feat_count     | integer | Feature commit count      |
| fix_count      | integer | Bug fix count             |
| breaking_count | integer | Breaking change count     |
| total_commits  | integer | Total commits processed   |

