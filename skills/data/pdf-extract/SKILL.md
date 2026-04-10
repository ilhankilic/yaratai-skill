# data.pdf-extract

Extract text and tables from PDF files using `pdfplumber`.

## Usage

```bash
skillforge run data.pdf-extract --input input.json
```

### Input

| Field     | Type   | Required | Description                           |
|-----------|--------|----------|---------------------------------------|
| file_path | string | ❌*      | Path to the PDF file on disk          |
| base64    | string | ❌*      | Base64-encoded PDF content            |
| pages     | array  | ❌       | Page indices to extract (default: all)|

\* Provide at least one of `file_path` or `base64`.

### Output

| Field  | Type    | Description                         |
|--------|---------|-------------------------------------|
| text   | string  | Concatenated extracted text         |
| tables | array   | List of tables (each: list of dicts)|
| pages  | integer | Total page count                    |

## Dependencies

- `pdfplumber` — install via `pip install 'skillforge[pdf]'`

