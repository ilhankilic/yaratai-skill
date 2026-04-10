# code.docstring
Add Google, NumPy, or Sphinx style docstrings to Python functions and classes automatically.

## Input
| Field | Type | Required | Default |
|---|---|---|---|
| source_code | string | ✅ | — |
| style | string | ❌ | `google` |
| overwrite_existing | bool | ❌ | `false` |
| language | string | ❌ | `en` |

## Output
| Field | Type |
|---|---|
| documented_code | string |
| functions_documented | int |
| functions_skipped | int |
| classes_documented | int |

