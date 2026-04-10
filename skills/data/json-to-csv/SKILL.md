# data.json-to-csv

Convert any JSON array to CSV with nested field support via dot notation.

## Usage

```bash
skillforge run data.json-to-csv --input data.json
```

### Input

| Field     | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| records   | array  | ✅       | List of JSON objects                       |
| fields    | array  | ❌       | Explicit column list (dot notation)        |
| delimiter | string | ❌       | Delimiter char (default `,`)               |
| bom       | bool   | ❌       | Prepend UTF-8 BOM for Excel (default false)|

### Output

| Field     | Type    | Description              |
|-----------|---------|--------------------------|
| csv       | string  | The CSV content          |
| row_count | integer | Number of rows written   |

