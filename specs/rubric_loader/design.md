# Design — rubric_loader

> Cómo se construye la feature 2. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/rubrics.py` | create | `Dimension`, `ScoreCap`, `Rubric`, `load_rubric(call_type)` |
| `tests/test_rubrics.py` | create | Cobertura R2–R8 |
| `tests/fixtures/rubrics/` | create | Rúbricas mínimas de prueba (válida, inválida, incompleta) |

## New signatures

```python
# src/rubrics.py
class Dimension(BaseModel):
    id: int; name: str; max_points: int; optional: bool = False

class ScoreCap(BaseModel):
    rule: str; dimension_id: int; max_score: int

class Rubric(BaseModel):
    call_type: CallType
    dimensions: list[Dimension]          # exactamente 12 (R2)
    bands: list[str]                     # nombres exactos (R4)
    score_caps: list[ScoreCap]           # R5
    def max_possible(self, disabled_ids: set[int] = frozenset()) -> int  # R6

def load_rubric(call_type: CallType, rubrics_dir: Path = DEFAULT_DIR) -> Rubric
```

## Parsing strategy
Regex por encabezados del markdown: `### Dimension N — Name (X pts)` para
dimensiones, tabla/bloque "Global Automatic Score Caps" para R5, y el marcador
`Optional dimension` del coaching para `optional: True`. Las bandas se toman de
los nombres de nivel declarados en las tablas (`Elite`, `Strong`, `Mid`/
`Inconsistent`, `At risk`, `Fail`), normalizados a los cinco nombres canónicos.

## Decisions
- **Parsear el markdown existente en runtime** en vez de duplicar los datos en
  Python/JSON: una sola fuente de verdad; si el cliente edita la rúbrica, el
  código no cambia.
- **Fixture de rúbricas mínimas para tests**: los tests no dependen de que el
  markdown real no se edite; los casos de parse-error son controlados.

## Alternative discarded
- Copiar las rúbricas a un `rubrics.json` versionado: descartada porque crea
  una segunda fuente de verdad que puede divergir del markdown que el cliente
  mantiene; el parseo con errores explícitos (R8) cubre el riesgo de formato.

## Traceability preview
- R1, R2, R3 → `test_load_rubric_twelve_dimensions_sum_100`
- R4 → `test_band_names_exact`
- R5 → `test_score_caps_exposed`
- R6 → `test_coaching_optional_d4_max_possible`
- R7 → `test_unknown_call_type_raises`
- R8 → `test_malformed_rubric_raises`
