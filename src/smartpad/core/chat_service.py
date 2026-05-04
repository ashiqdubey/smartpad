"""ChatService — integrates router + AI levels + worker pool + repos.

Bridges the UI (floating panel) and the backend layers. The panel calls
submit_message() with the raw user text; ChatService routes it, runs the
AI level pipeline, persists to the DB, and signals results back via the
worker pool's existing signals.

This module has no PyQt imports — it is pure business logic.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from loguru import logger

from smartpad.core.ai_levels import ProcessResult, process_capture
from smartpad.core.router import ActionKind, RouteResult, route
from smartpad.db.models import Message, Note, Reminder, Snippet, Task

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from smartpad.providers.base import Provider


async def handle_capture(
    text: str,
    ai_level: int,
    provider: Provider | None,
    model: str,
    session: AsyncSession,
    device_id: str = "",
) -> dict[str, object]:
    """Route user input, apply AI pipeline, persist to DB.

    Returns a dict with keys:
      route_result  — RouteResult from the router
      process_result — ProcessResult from AI levels pipeline
      saved_id       — UUID of the saved entity (or None for chat)
    """
    route_result: RouteResult = route(text)
    logger.debug("ChatService handle_capture: action={}", route_result.action)

    process_result: ProcessResult = await process_capture(
        text=route_result.body or text,
        ai_level=ai_level,
        provider=provider,
        model=model,
    )

    saved_id: str | None = None

    match route_result.action:
        case ActionKind.SAVE_NOTE:
            saved_id = await _save_note(process_result, session, device_id)
        case ActionKind.SAVE_TASK:
            saved_id = await _save_task(process_result, session, device_id)
        case ActionKind.SAVE_REMINDER:
            saved_id = await _save_reminder(process_result, session, device_id)
        case ActionKind.SAVE_SNIPPET:
            saved_id = await _save_snippet(process_result, session, device_id)
        case _:
            # Chat / query / app commands — caller handles the LLM side
            pass

    # Always persist the user message in the messages table
    await _save_message(
        role="user",
        content=text,
        kind=_action_to_kind(route_result.action),
        session=session,
        device_id=device_id,
    )

    return {
        "route_result": route_result,
        "process_result": process_result,
        "saved_id": saved_id,
    }


# ── Entity savers ─────────────────────────────────────────────────────────────

async def _save_note(result: ProcessResult, session: AsyncSession, device_id: str) -> str:
    from smartpad.db.repositories.notes import NotesRepo

    note_id = str(uuid.uuid4())
    note = Note(
        id=note_id,
        content=result.content,
        original_content=result.original_content,
        tags=",".join(result.metadata.tags) if result.metadata.tags else None,
        ai_level_applied=result.ai_level_applied,
        grammar_fixed=result.grammar_fixed,
        enhanced=result.enhanced,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        device_id=device_id or None,
        sync_version=0,
    )
    repo = NotesRepo(session)
    await repo.save(note)
    return note_id


async def _save_task(result: ProcessResult, session: AsyncSession, device_id: str) -> str:
    from smartpad.db.repositories.tasks import TasksRepo

    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        content=result.content,
        tags=",".join(result.metadata.tags) if result.metadata.tags else None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        device_id=device_id or None,
        sync_version=0,
    )
    repo = TasksRepo(session)
    await repo.save(task)
    return task_id


async def _save_reminder(result: ProcessResult, session: AsyncSession, device_id: str) -> str:
    from smartpad.db.repositories.reminders import RemindersRepo

    reminder_id = str(uuid.uuid4())
    # trigger_time from metadata is an ISO string; default to 1 hour from now
    trigger_at = datetime.now(UTC).replace(hour=datetime.now(UTC).hour + 1)
    if result.metadata.trigger_time:
        try:
            import dateparser

            parsed = dateparser.parse(
                result.metadata.trigger_time,
                settings={"RETURN_AS_TIMEZONE_AWARE": True},
            )
            if parsed:
                trigger_at = parsed
        except Exception:  # noqa: BLE001
            pass

    reminder = Reminder(
        id=reminder_id,
        content=result.content,
        trigger_at=trigger_at,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        device_id=device_id or None,
        sync_version=0,
    )
    repo = RemindersRepo(session)
    await repo.save(reminder)
    return reminder_id


async def _save_snippet(result: ProcessResult, session: AsyncSession, device_id: str) -> str:
    from smartpad.db.repositories.snippets import SnippetsRepo

    snippet_id = str(uuid.uuid4())
    snippet = Snippet(
        id=snippet_id,
        content=result.content,
        language=result.metadata.language,
        tags=",".join(result.metadata.tags) if result.metadata.tags else None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        device_id=device_id or None,
        sync_version=0,
    )
    repo = SnippetsRepo(session)
    await repo.save(snippet)
    return snippet_id


async def _save_message(
    role: str,
    content: str,
    kind: str,
    session: AsyncSession,
    device_id: str,
) -> None:
    from smartpad.db.repositories.chat import ChatRepo

    msg = Message(
        role=role,
        content=content,
        kind=kind,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        device_id=device_id or None,
        sync_version=0,
    )
    repo = ChatRepo(session)
    await repo.save(msg)


def _action_to_kind(action: ActionKind) -> str:
    match action:
        case ActionKind.SAVE_NOTE:
            return "note"
        case ActionKind.SAVE_TASK:
            return "task"
        case ActionKind.SAVE_REMINDER:
            return "reminder"
        case ActionKind.SAVE_SNIPPET:
            return "snippet"
        case ActionKind.CHAT | ActionKind.QUERY_DB:
            return "chat"
        case _:
            return "chat"
