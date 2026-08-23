# Design — scoring_report

> Cómo se construye la feature 5. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/scoring.py` | create | `ScoringValidationError`, `build_prompt()`, `build_report()` |
| `tests/test_scoring.py` | create | cobertura R1–R8 |

## New signatures

```python
# src/scoring.py
class ScoringValidationError(ValueError): ...

def build_prompt(call_type: CallType, transcript: str, rubric: Rubric) -> str
def build_report(llm_output: dict, rubric: Rubric) -> Report
```

## LLM output contract (JSON requerido al modelo)

```json
{
  "one_thing": {"change": "...", "projected_score": 92},
  "brief": "...",
  "red_flags": ["..."],
  "dimensions": [
    {"dimension_id": 1, "score": 8, "reasoning": "quote-first...",
     "transcript_lines": ["[Dana]: ..."], "quick_fix": "..."},
    {"dimension_id": 4, "disabled": true, "disabled_reason": "..."}
  ]
}
```

`grade` no se pide al modelo: se calcula localmente sumando scores y aplicando
las bandas de la "Scoring Bands Reference" (R5) — así el total siempre es
consistente con las dimensiones y no puede ser alucinado.

## Decisions
- **El grade se calcula en código, no lo genera el LLM** (R5): elimina la
  clase entera de alucinaciones en el dato más visible del reporte.
- **Caps aplicados en código** (R6): el LLM puntúa; el motor recorta según la
  tabla de caps y anota en `reasoning` qué cap disparó. Determinista y
  auditable.
- **`projected_score` acotado a `max_possible`** (R7): un "one thing" que
  prometa más de lo posible se rechaza como inválido.
- **Bandas por dimensión**: los labels Elite/Strong/Mid/Fail de las tablas se
  aceptan; cualquier otro label se rechaza (R2).

## Alternative discarded
- Pedirle al LLM el total y la banda directamente: descartado porque el total
  es aritmética determinista; delegarla al modelo introduce errores que el
  coach ve primero (y pdf_format.md exige banda exacta de la rúbrica).

## Traceability preview
- R1, R3 → `test_build_report_valid`
- R2 → `test_score_above_max_rejected`, `test_unknown_dimension_band_rejected`
- R3 → `test_missing_section_rejected`
- R4 → `test_coaching_d4_disabled_max_85`
- R5 → `test_grade_band_from_thresholds`
- R6 → `test_cap_limits_dimension_score`
- R7 → `test_projected_score_capped`
- R8 → `test_prompt_contains_rubric_and_json_contract`
