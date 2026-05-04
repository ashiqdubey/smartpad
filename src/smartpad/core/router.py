"""Router — SPEC.md section 7.

Decides what to do with user input and returns a RouteResult the UI can act on.
LLM-based routing (step 4) is wired in Phase 9; this phase covers steps 1-3.

Pipeline:
  detect(text)     → DetectionResult (intent_detector)
  route(result)    → RouteResult     (this module)

The UI calls route(text) and renders the appropriate bubble.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto

from smartpad.core.intent_detector import DetectionResult, IntentKind, detect


class ActionKind(StrEnum):
    SAVE_NOTE = auto()
    SAVE_TASK = auto()
    SAVE_REMINDER = auto()
    SAVE_SNIPPET = auto()
    QUERY_DB = auto()        # personal-data query → search local DB
    CHAT = auto()            # forward to LLM chat
    APP_COMMAND = auto()     # /browse /settings /help etc.
    CALCULATOR = auto()      # math expression


@dataclass
class RouteResult:
    action: ActionKind
    body: str                               # cleaned text to act on
    slash_command: str | None = None        # original slash cmd if any
    metadata: dict[str, str] = field(default_factory=dict)


# ── App command dispatch table ────────────────────────────────────────────────
# Maps slash commands to a stable string the UI can switch on.

_APP_COMMANDS: dict[str, str] = {
    "/browse": "browse",
    "/settings": "settings",
    "/model": "model",
    "/help": "help",
    "/find": "search",
    "/search": "search",
    "/tasks": "list_tasks",
    "/today": "today",
    "/snippets": "list_snippets",
    "/notes": "list_notes",
    "/done": "mark_done",
    "/remove": "soft_delete",
    "/delete": "soft_delete",
    "/clear": "clear_chat",
    "/ai": "ai_settings",
    "/level": "ai_settings",
}


def route(text: str) -> RouteResult:
    """Classify and route user input.

    Returns a RouteResult the UI renders immediately. Heavy work (DB writes,
    LLM calls) is submitted to the worker pool by the panel, not here.
    """
    result = detect(text)
    return _dispatch(result)


def route_from_detection(result: DetectionResult) -> RouteResult:
    """Route from an already-computed DetectionResult (for testing)."""
    return _dispatch(result)


# ── Private ───────────────────────────────────────────────────────────────────

def _dispatch(result: DetectionResult) -> RouteResult:
    match result.kind:
        case IntentKind.NOTE:
            return RouteResult(
                action=ActionKind.SAVE_NOTE,
                body=result.body,
                slash_command=result.slash_command,
            )
        case IntentKind.TASK:
            return RouteResult(
                action=ActionKind.SAVE_TASK,
                body=result.body,
                slash_command=result.slash_command,
            )
        case IntentKind.REMINDER:
            return RouteResult(
                action=ActionKind.SAVE_REMINDER,
                body=result.body,
                slash_command=result.slash_command,
            )
        case IntentKind.SNIPPET:
            return RouteResult(
                action=ActionKind.SAVE_SNIPPET,
                body=result.body,
                slash_command=result.slash_command,
            )
        case IntentKind.QUERY:
            return RouteResult(
                action=ActionKind.QUERY_DB,
                body=result.body,
            )
        case IntentKind.SLASH:
            cmd = result.slash_command or ""
            app_action = _APP_COMMANDS.get(cmd, "unknown")
            return RouteResult(
                action=ActionKind.APP_COMMAND,
                body=result.body,
                slash_command=cmd,
                metadata={"app_action": app_action},
            )
        case IntentKind.CHAT:
            # Math expressions get a special marker so the UI can show the
            # calculator tool result instead of a full chat bubble.
            if result.metadata.get("math") == "true":
                return RouteResult(
                    action=ActionKind.CALCULATOR,
                    body=result.body,
                )
            return RouteResult(
                action=ActionKind.CHAT,
                body=result.body,
            )
        case _:
            return RouteResult(action=ActionKind.CHAT, body=result.body)
