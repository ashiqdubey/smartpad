"""AI level pipeline — SPEC.md section 6.

Five levels of AI processing depth (0–4). Each level builds on the previous.
Original content is ALWAYS preserved in original_content regardless of level.

Level 0 — Off:      plain save, zero AI calls
Level 1 — Organise: auto-tag, classify type, choose book (metadata only)
Level 2 — Grammar:  Level 1 + silent grammar/typo correction
Level 3 — Tidy:     Level 2 + expand shorthand into full sentences
Level 4 — Enhance:  Level 3 + add detail, structure, link related notes

Phase 09 implements Level 0 and Level 1 fully.
Levels 2-4 are wired (schema in place) but delegate the enhancement prompt
to the active provider — they become meaningful once a provider is configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from smartpad.providers.base import Provider

# ── Result types ──────────────────────────────────────────────────────────────


@dataclass
class Metadata:
    """AI-extracted metadata about a captured item."""

    item_type: str = "note"           # note | task | reminder | snippet
    tags: list[str] = field(default_factory=list)
    book_name: str | None = None
    deadline: str | None = None       # ISO-8601 string if detected
    trigger_time: str | None = None   # ISO-8601 string if detected
    language: str | None = None       # for snippets


@dataclass
class ProcessResult:
    """Result of running an input through the AI level pipeline."""

    original_content: str
    content: str                      # processed (may equal original at level 0)
    metadata: Metadata = field(default_factory=Metadata)
    ai_level_applied: int = 0
    grammar_fixed: bool = False
    enhanced: bool = False


# ── Level 0: plain save ───────────────────────────────────────────────────────

def process_level_0(text: str) -> ProcessResult:
    """Level 0 — save exactly as typed, no AI."""
    return ProcessResult(
        original_content=text,
        content=text,
        ai_level_applied=0,
    )


# ── Level 1: classify + metadata ─────────────────────────────────────────────

_CLASSIFY_PROMPT = """\
You are a fast classifier. Given the user text below, respond with ONLY a
JSON object containing these fields:
  "item_type": one of "note" | "task" | "reminder" | "snippet"
  "tags": array of 1-3 short lowercase tag strings (no # prefix)
  "book_name": a short book/category name or null
  "deadline": ISO-8601 datetime string if a task deadline is mentioned, else null
  "trigger_time": ISO-8601 datetime string if a reminder time is mentioned, else null
  "language": programming language string if snippet, else null

Respond with ONLY the JSON. No prose.

User text:
{text}
"""


async def process_level_1(
    text: str,
    provider: Provider,
    model: str,
) -> ProcessResult:
    """Level 1 — classify type + extract metadata via one fast LLM call."""
    from smartpad.providers.base import ChatMessage  # avoid circular at module level

    prompt = _CLASSIFY_PROMPT.format(text=text)
    response_text = ""

    try:
        async for chunk in await provider.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            model=model,
            temperature=0.0,
            max_tokens=128,
            stream=False,
        ):
            response_text += chunk.delta
    except Exception as exc:
        logger.warning("Level 1 metadata extraction failed: {} — falling back to Level 0", exc)
        return process_level_0(text)

    metadata = _parse_metadata(response_text.strip())
    return ProcessResult(
        original_content=text,
        content=text,   # Level 1 never changes content
        metadata=metadata,
        ai_level_applied=1,
    )


# ── Levels 2-4: content enhancement ──────────────────────────────────────────

_GRAMMAR_PROMPT = """\
Fix grammar and spelling in the text below. Return ONLY the corrected text
with no explanation or additional commentary.

Text:
{text}
"""

_TIDY_PROMPT = """\
Expand the following shorthand note into clear, complete sentences.
Keep the original meaning exactly. Return ONLY the expanded text.

Text:
{text}
"""

_ENHANCE_PROMPT = """\
Enhance the following note by adding relevant structure, detail, and clarity.
Keep the author's intent and do not add information they didn't imply.
Return ONLY the enhanced text.

Text:
{text}
"""


async def process_level_2(
    text: str,
    provider: Provider,
    model: str,
) -> ProcessResult:
    """Level 2 — Level 1 metadata + grammar fix."""
    result = await process_level_1(text, provider, model)
    fixed = await _run_prompt(_GRAMMAR_PROMPT.format(text=text), provider, model)
    if fixed:
        result.content = fixed
        result.grammar_fixed = True
    result.ai_level_applied = 2
    return result


async def process_level_3(
    text: str,
    provider: Provider,
    model: str,
) -> ProcessResult:
    """Level 3 — Level 2 + expand shorthand."""
    result = await process_level_2(text, provider, model)
    tidied = await _run_prompt(_TIDY_PROMPT.format(text=result.content), provider, model)
    if tidied:
        result.content = tidied
    result.ai_level_applied = 3
    return result


async def process_level_4(
    text: str,
    provider: Provider,
    model: str,
) -> ProcessResult:
    """Level 4 — Level 3 + full enhancement."""
    result = await process_level_3(text, provider, model)
    enhanced = await _run_prompt(_ENHANCE_PROMPT.format(text=result.content), provider, model)
    if enhanced:
        result.content = enhanced
        result.enhanced = True
    result.ai_level_applied = 4
    return result


# ── Dispatcher ────────────────────────────────────────────────────────────────

async def process_capture(
    text: str,
    ai_level: int,
    provider: Provider | None,
    model: str = "gpt-3.5-turbo",
) -> ProcessResult:
    """Run the AI pipeline at the configured level.

    Level 0 never calls the provider. Levels 1-4 require a provider;
    if none is configured they silently fall back to Level 0.
    """
    if ai_level == 0 or provider is None:
        return process_level_0(text)

    level = max(0, min(4, ai_level))
    match level:
        case 1:
            return await process_level_1(text, provider, model)
        case 2:
            return await process_level_2(text, provider, model)
        case 3:
            return await process_level_3(text, provider, model)
        case 4:
            return await process_level_4(text, provider, model)
        case _:
            return process_level_0(text)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _run_prompt(prompt: str, provider: Provider, model: str) -> str | None:
    """Run a single prompt and return the response text, or None on failure."""
    from smartpad.providers.base import ChatMessage

    text = ""
    try:
        async for chunk in await provider.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            model=model,
            temperature=0.3,
            max_tokens=512,
            stream=False,
        ):
            text += chunk.delta
        return text.strip() or None
    except Exception as exc:
        logger.warning("AI level enhancement failed: {}", exc)
        return None


def _parse_metadata(json_text: str) -> Metadata:
    """Parse the classification JSON response into a Metadata object."""
    # Strip markdown code fences if the model wrapped the JSON
    cleaned = json_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Could not parse metadata JSON: {!r}", json_text[:120])
        return Metadata()

    return Metadata(
        item_type=data.get("item_type", "note"),
        tags=[str(t) for t in data.get("tags", [])],
        book_name=data.get("book_name"),
        deadline=data.get("deadline"),
        trigger_time=data.get("trigger_time"),
        language=data.get("language"),
    )
