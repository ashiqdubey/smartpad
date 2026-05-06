"""Intent detector — SPEC.md section 7.

Classifies user input without an LLM call (slash commands + regex patterns).
LLM-based classification (step 4 of spec section 7) is wired in Phase 9.

Classification priority order (matches spec exactly):
  1. Slash command  → SlashIntent
  2. Regex pattern  → typed Intent (NOTE/TASK/REMINDER/SNIPPET)
  3. Personal query → QUERY intent (DB-first mode)
  4. Fallback       → CHAT (LLM handles it — wired Phase 9)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum, auto


class IntentKind(StrEnum):
    SLASH = auto()    # /command detected
    NOTE = auto()
    TASK = auto()
    REMINDER = auto()
    SNIPPET = auto()
    QUERY = auto()    # personal-data query → DB-first
    CHAT = auto()     # fallback


# ── Slash command tables ──────────────────────────────────────────────────────

# Save-type commands
SAVE_COMMANDS: dict[str, IntentKind] = {
    "/note": IntentKind.NOTE,
    "/task": IntentKind.TASK,
    "/todo": IntentKind.TASK,
    "/remind": IntentKind.REMINDER,
    "/reminder": IntentKind.REMINDER,
    "/snippet": IntentKind.SNIPPET,
    "/snip": IntentKind.SNIPPET,
}

# Query/action commands (handled by router, not intent-typed)
ACTION_COMMANDS: frozenset[str] = frozenset({
    "/find",
    "/search",
    "/tasks",
    "/today",
    "/snippets",
    "/notes",
    "/done",
    "/remove",
    "/delete",
    "/clear",
    "/settings",
    "/browse",
    "/model",
    "/help",
    "/ai",
    "/level",
})

ALL_SLASH_COMMANDS: frozenset[str] = (
    frozenset(SAVE_COMMANDS.keys()) | ACTION_COMMANDS
)


# ── Pattern tables ────────────────────────────────────────────────────────────

_REMINDER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^remind\s+me\s+to\b", re.I),
    re.compile(r"^remind\s+me\b", re.I),
    re.compile(r"^reminder\s*[:\-–—]\s*", re.I),
    re.compile(r"^alert\s+me\b", re.I),
    re.compile(r"^set\s+(a\s+)?reminder\b", re.I),
]

_TASK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^todo\s*[:\-–—]\s*", re.I),
    re.compile(r"^task\s*[:\-–—]\s*", re.I),
    re.compile(r"^\s*-\s+\[\s*\]"),          # markdown checkbox
    re.compile(r"^add\s+(a\s+|the\s+)?task\b", re.I),
    re.compile(r"^new\s+task\b", re.I),
    re.compile(r"\b(by|due|deadline)\s+\w+", re.I),
    re.compile(r"\bneed\s+to\b.{0,60}\bby\b", re.I),
]

# LITERAL note patterns — the user is providing the body directly.
# Permissive about polite prefixes ("hey,", "can you", "please") and
# accepts content on the same line OR after a newline. We slice the body
# from the match end so newlines inside the user's content are preserved.
# Generative phrasings ("make/write a note about X") are intentionally
# NOT here: those go to CHAT → AI generates → compound-intent saves.
_NOTE_PATTERNS: list[re.Pattern[str]] = [
    # "[hey,] [can you] [please|just|kindly] (note|remember|store|jot|save)
    #   (this|that|it|down) [:|-]" — polite/conversational forms.
    re.compile(
        r"^(?:hey[,!\s]+)?"
        r"(?:can\s+you\s+(?:please\s+)?)?"
        r"(?:please\s+|just\s+|kindly\s+)?"
        r"(?:note|remember|store|jot|save)"
        r"\s+(?:this|that|it|down)\b\s*[:\-–—]?\s*",
        re.I,
    ),
    # Direct colon forms — "note: foo", "remember: foo"
    re.compile(r"^note\s*[:\-–—]\s*", re.I),
    re.compile(r"^remember\s*[:\-–—]\s*", re.I),
    # "jot down: foo" / "note down: foo"
    re.compile(r"^(?:jot|note)\s+down\s*[:\-–—]?\s*", re.I),
    # "save this/it as a note" / "save this/it to notes"
    re.compile(r"^save\s+(?:this|it)\s+(?:as\s+)?(?:a\s+)?note\s*[:\-–—]?\s*", re.I),
    re.compile(r"^save\s+(?:this|it)\s+to\s+notes?\s*[:\-–—]?\s*", re.I),
]

_SNIPPET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^snippet\s*[:\-–—]\s*", re.I),
    re.compile(r"^save\s+(this\s+)?(as\s+)?(a\s+)?snippet\b", re.I),
    re.compile(r"^`{1,3}"),                   # starts with backtick(s)
    re.compile(r"^\$\s"),                      # shell command
    re.compile(r"^>\s"),                       # blockquote (often pasted cmd)
]

_MATH_PATTERN: re.Pattern[str] = re.compile(
    r"^[\d\s\+\-\*\/\(\)\.\^%]+$"
)

_PERSONAL_QUERY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(my|i have|do i have)\b.{0,40}\b(task|note|reminder|snippet|todo)\b", re.I),
    re.compile(r"\b(what|any)\b.{0,30}\b(today|due|deadline|pending|overdue)\b", re.I),
    re.compile(r"\bfind\s+my\b", re.I),
    re.compile(r"\bshow\s+(my|me\s+my)\b", re.I),
    re.compile(r"\blist\s+my\b", re.I),
    re.compile(r"\bwhat\s+do\s+i\s+have\b", re.I),
    re.compile(r"\bany\s+(tasks?|reminders?|notes?)\b.{0,30}\b(today|this week|due)\b", re.I),
]


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class DetectionResult:
    kind: IntentKind
    body: str              # text after slash command / the full text
    slash_command: str | None = None   # e.g. "/note"
    metadata: dict[str, str] = field(default_factory=dict)


# ── Public API ────────────────────────────────────────────────────────────────

def detect(text: str) -> DetectionResult:
    """Classify user input without an LLM call.

    Returns DetectionResult with the best-guess intent and cleaned body text.
    Falls through to CHAT if no pattern matches (LLM handles CHAT in Phase 9).
    """
    stripped = text.strip()
    if not stripped:
        return DetectionResult(kind=IntentKind.CHAT, body="")

    # ── 1. Slash command ──────────────────────────────────────────────────────
    if stripped.startswith("/"):
        return _detect_slash(stripped)

    # ── 2. Math expression ────────────────────────────────────────────────────
    if _MATH_PATTERN.match(stripped):
        return DetectionResult(kind=IntentKind.CHAT, body=stripped, metadata={"math": "true"})

    # ── 3. Personal-data query — check BEFORE task/snippet because phrases like
    #       "any tasks due today" contain "due" which would match task patterns.
    #       Queries are always about retrieving existing data, never creating.
    for pat in _PERSONAL_QUERY_PATTERNS:
        if pat.search(stripped):
            return DetectionResult(kind=IntentKind.QUERY, body=stripped)

    # ── 2. Reminder patterns (check before task — "remind me to buy milk by 5pm"
    #       must be REMINDER not TASK) ──────────────────────────────────────────
    for pat in _REMINDER_PATTERNS:
        m = pat.search(stripped)
        if m:
            body = _strip_prefix(stripped, m)
            return DetectionResult(kind=IntentKind.REMINDER, body=body)

    # ── 2. Note patterns ("note: foo", "write the note: foo", etc.) ─────────
    for pat in _NOTE_PATTERNS:
        m = pat.match(stripped)
        if m:
            body = _strip_prefix(stripped, m)
            if body:  # ignore bare "note:" with no content
                return DetectionResult(kind=IntentKind.NOTE, body=body)

    # ── 2. Task patterns ──────────────────────────────────────────────────────
    for pat in _TASK_PATTERNS:
        m = pat.search(stripped)
        if m:
            body = _strip_prefix(stripped, m)
            return DetectionResult(kind=IntentKind.TASK, body=body)

    # ── 2. Snippet patterns ───────────────────────────────────────────────────
    for pat in _SNIPPET_PATTERNS:
        m = pat.search(stripped)
        if m:
            body = _strip_prefix(stripped, m)
            return DetectionResult(kind=IntentKind.SNIPPET, body=body)

    # ── 4. Fallback → CHAT (LLM routing added in Phase 9) ────────────────────
    return DetectionResult(kind=IntentKind.CHAT, body=stripped)


def _strip_prefix(text: str, match: re.Match[str]) -> str:
    """Return text with the matched prefix removed (only when match was at start)."""
    if match.start() == 0:
        return text[match.end():].strip()
    return text.strip()


def get_slash_completions(prefix: str) -> list[str]:
    """Return slash commands that start with prefix (for slash menu)."""
    p = prefix.lower()
    return sorted(cmd for cmd in ALL_SLASH_COMMANDS if cmd.startswith(p))


# ── Private helpers ───────────────────────────────────────────────────────────

def _detect_slash(text: str) -> DetectionResult:
    """Parse a slash-command input and return the appropriate DetectionResult."""
    parts = text.split(None, 1)
    cmd = parts[0].lower()
    body = parts[1].strip() if len(parts) > 1 else ""

    # Save-type slash → convert to save intent
    if cmd in SAVE_COMMANDS:
        return DetectionResult(
            kind=SAVE_COMMANDS[cmd],
            body=body,
            slash_command=cmd,
        )

    # Action / app commands → SLASH intent, router dispatches
    return DetectionResult(
        kind=IntentKind.SLASH,
        body=body,
        slash_command=cmd,
    )
