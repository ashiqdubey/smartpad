"""Tests for intent detector + router — no LLM, pure pattern matching."""

from __future__ import annotations

import pytest

from smartpad.core.intent_detector import (
    ALL_SLASH_COMMANDS,
    IntentKind,
    detect,
    get_slash_completions,
)
from smartpad.core.router import ActionKind, route


# ── detect() — slash commands ─────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected_kind,expected_cmd", [
    ("/note buy milk", IntentKind.NOTE, "/note"),
    ("/task finish report", IntentKind.TASK, "/task"),
    ("/todo write tests", IntentKind.TASK, "/todo"),
    ("/remind call dentist", IntentKind.REMINDER, "/remind"),
    ("/reminder pick up package", IntentKind.REMINDER, "/reminder"),
    ("/snippet git log --oneline", IntentKind.SNIPPET, "/snippet"),
    ("/snip ls -la", IntentKind.SNIPPET, "/snip"),
])
def test_slash_save_commands(text: str, expected_kind: IntentKind, expected_cmd: str) -> None:
    result = detect(text)
    assert result.kind == expected_kind
    assert result.slash_command == expected_cmd


@pytest.mark.parametrize("cmd", [
    "/browse", "/settings", "/help", "/find", "/tasks",
    "/today", "/snippets", "/notes", "/done", "/clear", "/model",
])
def test_slash_app_commands(cmd: str) -> None:
    result = detect(cmd)
    assert result.kind == IntentKind.SLASH
    assert result.slash_command == cmd


def test_slash_command_extracts_body() -> None:
    result = detect("/note this is the note body")
    assert result.body == "this is the note body"


def test_slash_command_no_body() -> None:
    result = detect("/tasks")
    assert result.body == ""


# ── detect() — reminder patterns ─────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "remind me to call the dentist tomorrow",
    "reminder: pick up milk",
    "Remind me to submit the report",
    "alert me when the build finishes",
])
def test_reminder_patterns(text: str) -> None:
    assert detect(text).kind == IntentKind.REMINDER


# ── detect() — task patterns ──────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "todo: write documentation",
    "task: refactor the DB layer",
    "- [ ] add tests for the router",
    "Submit the PR by Friday",
    "need to finish the spec by tomorrow",
])
def test_task_patterns(text: str) -> None:
    assert detect(text).kind == IntentKind.TASK


def test_reminder_takes_priority_over_task() -> None:
    # "remind me to X by Y" should be REMINDER, not TASK
    result = detect("remind me to submit the report by Friday")
    assert result.kind == IntentKind.REMINDER


# ── detect() — snippet patterns ───────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "snippet: git log --oneline",
    "save: kubectl get pods -n default",
    "```python\nprint('hello')\n```",
    "$ git status",
    "> cat /etc/hosts",
])
def test_snippet_patterns(text: str) -> None:
    assert detect(text).kind == IntentKind.SNIPPET


# ── detect() — personal query patterns ───────────────────────────────────────

@pytest.mark.parametrize("text", [
    "what tasks do I have today",
    "do I have any reminders due today",
    "find my git snippet",
    "show my notes",
    "list my tasks",
    "what do I have this week",
    "any tasks due today",
])
def test_personal_query_patterns(text: str) -> None:
    assert detect(text).kind == IntentKind.QUERY


# ── detect() — math ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "2 + 2",
    "100 * 3.14",
    "(5 + 3) * 2",
])
def test_math_goes_to_chat_with_math_flag(text: str) -> None:
    result = detect(text)
    assert result.kind == IntentKind.CHAT
    assert result.metadata.get("math") == "true"


# ── detect() — fallback to CHAT ───────────────────────────────────────────────

@pytest.mark.parametrize("text", [
    "What is the capital of France?",
    "Explain async/await to me",
    "How does SQLAlchemy handle migrations?",
    "Tell me a joke",
])
def test_general_questions_become_chat(text: str) -> None:
    assert detect(text).kind == IntentKind.CHAT


def test_empty_input_is_chat() -> None:
    assert detect("").kind == IntentKind.CHAT
    assert detect("   ").kind == IntentKind.CHAT


# ── get_slash_completions() ───────────────────────────────────────────────────

def test_slash_completions_prefix() -> None:
    completions = get_slash_completions("/ta")
    assert "/task" in completions
    assert "/tasks" in completions
    assert "/note" not in completions


def test_slash_completions_all() -> None:
    all_completions = get_slash_completions("/")
    assert set(all_completions) == ALL_SLASH_COMMANDS


def test_slash_completions_empty() -> None:
    assert get_slash_completions("/zzz") == []


# ── route() — action kinds ────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected_action", [
    ("/note buy apples", ActionKind.SAVE_NOTE),
    ("/task finish report", ActionKind.SAVE_TASK),
    ("/remind call mum at 3pm", ActionKind.SAVE_REMINDER),
    ("/snippet ls -la", ActionKind.SAVE_SNIPPET),
    ("remind me to drink water", ActionKind.SAVE_REMINDER),
    ("todo: refactor config", ActionKind.SAVE_TASK),
    ("what tasks do I have today", ActionKind.QUERY_DB),
    ("What is the speed of light?", ActionKind.CHAT),
    ("2 + 2", ActionKind.CALCULATOR),
])
def test_route_action_kinds(text: str, expected_action: ActionKind) -> None:
    assert route(text).action == expected_action


def test_route_app_command_browse() -> None:
    result = route("/browse")
    assert result.action == ActionKind.APP_COMMAND
    assert result.metadata["app_action"] == "browse"


def test_route_app_command_settings() -> None:
    result = route("/settings")
    assert result.action == ActionKind.APP_COMMAND
    assert result.metadata["app_action"] == "settings"


def test_route_preserves_body() -> None:
    result = route("/note this is my note")
    assert result.body == "this is my note"
    assert result.action == ActionKind.SAVE_NOTE


def test_route_slash_command_stored() -> None:
    result = route("/task write unit tests")
    assert result.slash_command == "/task"
