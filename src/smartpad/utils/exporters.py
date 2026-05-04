"""Export utilities — SPEC.MD section 20.

Exports notes, tasks, reminders, snippets to Markdown or JSON.
Supports date range and book filters.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.repositories.notes import NotesRepo
from smartpad.db.repositories.tasks import TasksRepo


async def export_notes(
    session: AsyncSession,
    fmt: str = "markdown",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    book_id: str | None = None,
) -> str:
    repo = NotesRepo(session)
    notes = await repo.list(book_id=book_id)
    if date_from:
        notes = [n for n in notes if n.created_at and _strip_tz(n.created_at) >= _strip_tz(date_from)]
    if date_to:
        notes = [n for n in notes if n.created_at and _strip_tz(n.created_at) <= _strip_tz(date_to)]

    if fmt == "json":
        return json.dumps([_note_to_dict(n) for n in notes], indent=2, default=str)

    lines = ["# Notes\n"]
    for n in notes:
        lines.append(f"## Note — {_fmt_dt(n.created_at)}")
        lines.append(f"\n{n.content}\n")
        if n.tags:
            lines.append(f"*Tags: {n.tags}*\n")
    return "\n".join(lines)


async def export_tasks(
    session: AsyncSession,
    fmt: str = "markdown",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: str | None = None,
) -> str:
    repo = TasksRepo(session)
    tasks = await repo.list(status=status)
    if date_from:
        tasks = [t for t in tasks if t.created_at and t.created_at >= date_from]
    if date_to:
        tasks = [t for t in tasks if t.created_at and t.created_at <= date_to]

    if fmt == "json":
        return json.dumps([_task_to_dict(t) for t in tasks], indent=2, default=str)

    lines = ["# Tasks\n"]
    for t in tasks:
        done = "x" if t.status == "done" else " "
        dl = f" (due {_fmt_dt(t.deadline)})" if t.deadline else ""
        lines.append(f"- [{done}] {t.content}{dl}")
    return "\n".join(lines)


async def export_all(
    session: AsyncSession,
    fmt: str = "markdown",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> str:
    notes_str = await export_notes(session, fmt, date_from, date_to)
    tasks_str = await export_tasks(session, fmt, date_from, date_to)

    if fmt == "json":
        return json.dumps({
            "notes": json.loads(notes_str),
            "tasks": json.loads(tasks_str),
        }, indent=2, default=str)

    return f"{notes_str}\n\n---\n\n{tasks_str}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_tz(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "—"


def _note_to_dict(n: Any) -> dict[str, Any]:
    return {
        "id": n.id,
        "content": n.content,
        "original_content": n.original_content,
        "tags": n.tags,
        "pinned": n.pinned,
        "created_at": str(n.created_at),
        "updated_at": str(n.updated_at),
    }


def _task_to_dict(t: Any) -> dict[str, Any]:
    return {
        "id": t.id,
        "content": t.content,
        "status": t.status,
        "deadline": str(t.deadline) if t.deadline else None,
        "priority": t.priority,
        "created_at": str(t.created_at),
    }
