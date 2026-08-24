# Review — scoring_report

**Verdict: APPROVED**

- R1–R8 cubiertos por tests concretos (trazabilidad en
  `progress/impl_scoring_report.md`); `uv run pytest` verde (78 passed).
- Tareas de `specs/scoring_report/tasks.md` completadas. La enmienda de R6
  (caps condicionales vía `cap_fired` del LLM) está reflejada en requirements
  y design ANTES del código final, con la justificación documentada — el
  comportamiento ingenuo habría anulado D8/D10 en cada reporte coaching.
- R13 (agent_graph) verificada: el prompt enmarca el transcript como dato no
  confiable entre delimitadores (`test_prompt_frames_transcript_as_untrusted`).
- Convenciones: type hints, docstrings, errores explícitos nombrando dimensión
  o sección, sin `except:` desnudo.
- Security review: `build_prompt` no ejecuta nada del transcript (solo lo
  incrusta delimitado); `build_report` valida tipos antes de convertir; el
  total/banda nunca provienen del LLM (superficie de manipulación reducida).
