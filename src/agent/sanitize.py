"""Deterministic transcript sanitization (anti prompt-injection).

The operator pastes arbitrary text that will be embedded in an LLM prompt.
This module makes sure nothing in that text can act as instructions:

- Control, zero-width and bidi-override characters are removed.
- Oversized transcripts are NOT rejected: any length is accepted and the
  prompt layer (`scoring._fit_transcript`) truncates to the provider's token
  budget; `too_long` is kept as an informational audit flag.
- Lines matching known instruction-injection patterns are removed and
  recorded as audit flags.

Everything here is regex/charset based on purpose: a second LLM as sanitizer
would be circular and unauditable.
"""

import re

from pydantic import BaseModel, Field

#: Audit threshold for transcript size (informational only: the prompt layer
#: truncates long transcripts to the LLM token budget instead of failing)
MAX_TRANSCRIPT_CHARS = 60_000

#: Minimum number of speaker turns for a transcript to be scoreable (R5)
MIN_SPEAKER_TURNS = 4

#: Control characters except newline and tab
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

#: Zero-width and bidi-override characters used to hide/flip text
_INVISIBLE_CHARS = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]"
)

#: Speaker turn like `[Dana Whitlock]: ...` (the transcripts' format)
_SPEAKER_TURN = re.compile(r"^\s*\[[^\]]+\]\s*:")

# Verbal instruction patterns — only trusted when they appear at the START of
# a line (or right after a speaker tag), so quoted/mid-sentence speech like
# "my son says 'act as a team'" is not falsely stripped.
_LINE_START_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(please\s+)?ignore\s+(all\s+|any\s+)?(previous|prior|preceding|above)", re.I),
    re.compile(r"(please\s+)?disregard\s+(all\s+|any\s+)?(previous|prior|above|your)", re.I),
    re.compile(r"(system|developer|admin)\s+(prompt|message|instructions)", re.I),
    re.compile(r"you\s+are\s+now\s+(a|an|the)", re.I),
    re.compile(r"new\s+(instructions|rules)\s*:", re.I),
    re.compile(r"(please\s+)?reveal\s+(your\s+)?(system\s+)?(prompt|instructions)", re.I),
    re.compile(r"act\s+as\s+(a|an|the)\b", re.I),
    re.compile(r"print\s+(your|the)\s+(prompt|instructions)", re.I),
)

# Fake role tags are suspicious anywhere in a line.
_ANYWHERE_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"</?\s*(system|assistant|developer)\s*>", re.I),
)

#: Speaker prefix like `[Dana Whitlock]: ` — stripped before start-anchoring
_SPEAKER_PREFIX = re.compile(r"^\s*\[[^\]]+\]\s*:\s*")


class SanitizationResult(BaseModel):
    """Outcome of sanitizing one transcript."""

    text: str  # cleaned transcript, safe to embed in a prompt
    flags: list[str] = Field(default_factory=list)  # audit of removals
    too_long: bool = False  # True when the text exceeds MAX_TRANSCRIPT_CHARS


def _strip_invisible(text: str) -> tuple[str, list[str]]:
    """Remove control/invisible characters; flag when any were found."""
    cleaned = _CONTROL_CHARS.sub("", text)
    cleaned = _INVISIBLE_CHARS.sub("", cleaned)
    flags = []
    if cleaned != text:
        flags.append("removed control/invisible characters")
    return cleaned, flags


def _strip_injection_lines(text: str) -> tuple[str, list[str]]:
    """Drop lines that try to give the model instructions; flag each one.

    Verbal patterns must match at the start of the line (after any speaker
    tag); fake role tags match anywhere.
    """
    kept: list[str] = []
    flags: list[str] = []
    for line in text.splitlines():
        content = _SPEAKER_PREFIX.sub("", line)
        matched = any(p.search(line) for p in _ANYWHERE_INJECTION_PATTERNS) or any(
            p.match(content) or p.match(line) for p in _LINE_START_INJECTION_PATTERNS
        )
        if matched is False:
            kept.append(line)
        else:
            preview = line.strip()[:80]
            flags.append(f"removed injection attempt: {preview!r}")
    return "\n".join(kept), flags


def sanitize_transcript(text: str) -> SanitizationResult:
    """Sanitize a raw transcript for safe embedding in an LLM prompt.

    Args:
        text: Raw transcript as pasted by the operator.

    Returns:
        A `SanitizationResult` with the cleaned text and audit flags.
        `too_long` is informational only: oversized transcripts are accepted
        and truncated later at the prompt layer.
    """
    flags: list[str] = []
    cleaned, strip_flags = _strip_invisible(text)
    flags.extend(strip_flags)
    cleaned, injection_flags = _strip_injection_lines(cleaned)
    flags.extend(injection_flags)
    return SanitizationResult(
        text=cleaned,
        flags=flags,
        too_long=len(cleaned) > MAX_TRANSCRIPT_CHARS,
    )


def count_speaker_turns(text: str) -> int:
    """Count `[Speaker]:` turns, the structural minimum for a scoreable call."""
    return sum(1 for line in text.splitlines() if _SPEAKER_TURN.match(line))


__all__ = [
    "MAX_TRANSCRIPT_CHARS",
    "MIN_SPEAKER_TURNS",
    "SanitizationResult",
    "count_speaker_turns",
    "sanitize_transcript",
]
