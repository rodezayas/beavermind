# Design — rubric_loader

> How feature 2 is built. Decisions made before writing code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/rubrics.py` | create | `Dimension`, `ScoreCap`, `Rubric`, `load_rubric(call_type)` |
| `tests/test_rubrics.py` | create | Coverage R2–R8 |
| `tests/fixtures/rubrics/` | create | Minimal test rubrics (valid, invalid, incomplete) |

## New signatures

```python
# src/rubrics.py
class Dimension(BaseModel):
    id: int; name: str; max_points: int; optional: bool = False

class ScoreCap(BaseModel):
    rule: str; dimension_id: int; max_score: int

class Rubric(BaseModel):
    call_type: CallType
    dimensions: list[Dimension]          # exactly 12 (R2)
    bands: list[str]                     # exact names (R4)
    score_caps: list[ScoreCap]           # R5
    def max_possible(self, disabled_ids: set[int] = frozenset()) -> int  # R6

def load_rubric(call_type: CallType, rubrics_dir: Path = DEFAULT_DIR) -> Rubric
```

## Parsing strategy
Regex over the markdown headers: `### Dimension N — Name (X pts)` for
dimensions, the "Global Automatic Score Caps" table/block for R5, and the
`Optional dimension` marker of the coaching rubric for `optional: True`. The bands are taken from
the level names declared in the tables (`Elite`, `Strong`, `Mid`/
`Inconsistent`, `At risk`, `Fail`), normalized to the five canonical names.

## Decisions
- **Parse the existing markdown at runtime** instead of duplicating the data in
  Python/JSON: a single source of truth; if the client edits the rubric, the
  code does not change.
- **Fixture of minimal rubrics for tests**: tests do not depend on the real
  markdown remaining unedited; parse-error cases are controlled.

## Alternative discarded
- Copying the rubrics to a versioned `rubrics.json`: discarded because it creates
  a second source of truth that can diverge from the markdown the client
  maintains; parsing with explicit errors (R8) covers the format risk.

## Traceability preview
- R1, R2, R3 → `test_load_rubric_twelve_dimensions_sum_100`
- R4 → `test_band_names_exact`
- R5 → `test_score_caps_exposed`
- R6 → `test_coaching_optional_d4_max_possible`
- R7 → `test_unknown_call_type_raises`
- R8 → `test_malformed_rubric_raises`
