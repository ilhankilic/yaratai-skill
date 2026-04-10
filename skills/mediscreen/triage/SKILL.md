# mediscreen.triage

Emergency department triage assessment powered by a local Ollama LLM.

## What It Does

Evaluates patient information (age, gender, chief complaint, duration, vitals) and returns a structured triage recommendation including priority level, department, warning signs, and estimated wait time.

## Usage

```bash
skillforge run mediscreen.triage --input patient.json
```

### Example Input (`patient.json`)

```json
{
  "data": {
    "age": 45,
    "gender": "erkek",
    "complaint": "Göğüs ağrısı, sol kola yayılıyor",
    "duration": "1 saat",
    "vitals": {
      "blood_pressure": "160/95",
      "heart_rate": 110,
      "temperature": 36.8,
      "spo2": 96
    }
  }
}
```

### Example Output

```json
{
  "success": true,
  "data": {
    "priority": "KIRMIZI",
    "department": "Kardiyoloji / Acil",
    "warning_signs": ["göğüs ağrısı", "sol kola yayılım", "taşikardi"],
    "estimated_wait_minutes": 0,
    "reasoning": "Sol kola yayılan göğüs ağrısı akut koroner sendrom açısından değerlendirilmeli."
  }
}
```

## Priority Levels

| Level    | Meaning        | Wait |
|----------|----------------|------|
| KIRMIZI  | Life-threat    | 0 min |
| TURUNCU  | Urgent         | 10 min |
| SARI     | Semi-urgent    | 30 min |
| YESIL    | Non-urgent     | 60 min |

## Dependencies

- Ollama running at `http://localhost:11434` (override with `OLLAMA_BASE_URL`)
- Model: `gemma3:4b` (override with `OLLAMA_MODEL`)

