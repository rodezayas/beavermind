# Requirements — llm_client

> Feature 3 de `settings_files_tasks.json`. Estado: `spec_ready` (esperando aprobación humana).

## R1
The system MUST expose a `GroqClient` class in `src/llm_client.py` with a
`complete(prompt: str) -> str` method that calls the Groq API using the model
GPT-OSS 120B and the `GROQ_API_KEY` from `Settings`.

## R2
IF `GROQ_API_KEY` is missing or empty THEN the system MUST raise a
configuration error whose message names `GROQ_API_KEY` before any network call.

## R3
IF the Groq API returns a non-2xx response THEN the system MUST raise an
error that includes the HTTP status and the response detail.

## R4
IF the caller requests structured output (`complete_json`) and the model
reply is not valid JSON THEN the system MUST raise a parse error that includes
a fragment of the offending reply.

## R5
The client MUST NOT swallow exceptions with a bare `except:`; every error path
must `raise` with context.

## R6
The client MUST accept an injectable transport (callable/session) so tests can
stub responses without network access.
