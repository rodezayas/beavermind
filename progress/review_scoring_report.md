# Review — scoring_report

**Verdict: APPROVED**

- R1–R8 covered by concrete tests (traceability in
  `progress/impl_scoring_report.md`); `uv run pytest` green (78 passed).
- Tasks from `specs/scoring_report/tasks.md` completed. The R6 amendment
  (conditional caps via the LLM's `cap_fired`) is reflected in requirements
  and design BEFORE final code, with documented justification — the
  naive behavior would have nullified D8/D10 in every coaching report.
- R13 (agent_graph) verified: the prompt frames the transcript as untrusted
  data between delimiters (`test_prompt_frames_transcript_as_untrusted`).
- Conventions: type hints, docstrings, explicit errors naming the dimension
  or section, no bare `except:`.
- Security review: `build_prompt` executes nothing from the transcript (it only
  embeds it, delimited); `build_report` validates types before converting; the
  total/band never come from the LLM (reduced manipulation surface).
