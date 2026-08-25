# Requirements — scoring_report

> Feature 5 of `settings_files_tasks.json`. Status: `spec_ready` (awaiting human approval).

## R1
The system MUST expose `build_report(llm_output: dict, rubric: Rubric) ->
Report` in `src/scoring.py` that converts the structured LLM response into a
valid `Report` using the rubric as the source of truth for maxima and bands.

## R2
IF a dimension score exceeds its `max_points`, is negative, or its band label
is not one of the rubric's per-dimension band levels THEN the system MUST
raise `ScoringValidationError` naming the offending dimension.

## R3
IF the LLM output is missing a required section (`one_thing`, `brief`,
`red_flags`, `grade`, or any of the 12 dimensions) THEN the system MUST raise
`ScoringValidationError` naming the missing section.

## R4
WHEN the rubric's optional dimension (coaching D4) is disabled THEN the
system MUST build the report with that `DimensionScore` disabled (score None,
`disabled_reason` present) and `grade.max_possible` equal to
`rubric.max_possible(disabled)` (85).

## R5
The `grade.band` MUST be assigned from the total score using the rubric's
"Scoring Bands Reference" thresholds (ELITE 90–100, STRONG 80–89,
INCONSISTENT 70–79, AT RISK 60–69, FAIL <60) and MUST use the canonical band
names — never invented ones.

## R6
WHEN a dimension entry declares `cap_fired: true` and the rubric declares an
automatic score cap for that dimension THEN the system MUST cap that
dimension's score at the cap value and record which cap fired in the
dimension's `reasoning`. WHEN the entry does not declare `cap_fired` THEN the
system MUST leave the score untouched (the cap conditions are semantic —
evaluating them is the LLM's job; enforcing the maximum is ours).

## R7
The `one_thing` section MUST include the projected score the call would have
reached with the change applied, and the projected score MUST NOT exceed
`grade.max_possible`.

## R8
The prompt used to obtain `llm_output` MUST be built by `build_prompt(
call_type: CallType, transcript: str, rubric: Rubric) -> str` in the same
module, embedding the rubric structure and requiring JSON output with the
report sections.
