# Design — llm_client

> Cómo se construye la feature 3. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/llm_client.py` | create | `GroqClient`, `LLMError`, `LLMAuthError`, `LLMParseError` |
| `tests/test_llm_client.py` | create | Cobertura R2–R6 con stub de transporte |

## New signatures

```python
# src/llm_client.py
class LLMError(RuntimeError): ...        # status + detail (R3)
class LLMAuthError(LLMError): ...        # GROQ_API_KEY ausente (R2)
class LLMParseError(LLMError): ...       # respuesta no-JSON (R4)

class GroqClient:
    MODEL = "openai/gpt-oss-120b"
    def __init__(self, settings: Settings, transport: Transport | None = None): ...
    def complete(self, prompt: str) -> str: ...
    def complete_json(self, prompt: str) -> dict: ...  # parsea JSON, R4
```

`Transport` es un protocolo con `post(url, headers, payload) -> (status, body)`;
por defecto se usa `urllib.request` (stdlib), inyectable en tests (R6).

## Decisions
- **HTTP directo con `urllib` (stdlib)** en vez del SDK `groq`: la superficie
  que usamos es un solo endpoint chat/completions; el SDK añade una dependencia
  y una capa propia de excepciones que duplicaría la nuestra. La URL base y el
  modelo quedan como constantes.
- **`complete_json` separado de `complete`**: el scoring (feature 5) necesita
  JSON estructurado; mantener ambos explícitos evita parseos implícitos.
- **Timeout explícito** en el transporte por defecto para que un run nunca
  quede colgado en `scoring`.

## Alternative discarded
- SDK oficial `groq`: descartado porque solo usamos 1 endpoint; con `urllib` +
  protocolo `Transport` los tests no necesitan red ni mocks del SDK, y evitamos
  una dependencia más en `pyproject.toml` (regla: cada paquete gana su lugar).

## Traceability preview
- R2 → `test_missing_api_key_raises_before_network`
- R3 → `test_api_error_includes_status_and_detail`
- R4 → `test_invalid_json_raises_parse_error`
- R5 → revisión de código (no hay `except:` desnudo) + tests de errores
- R6 → todos los tests usan `FakeTransport` inyectado
