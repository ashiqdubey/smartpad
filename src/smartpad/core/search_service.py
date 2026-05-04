"""Cross-entity FTS5 search service — SPEC.md section 7.

Searches the search_index virtual table and fetches full entities.
Also handles natural-language personal-data queries (tasks today, etc.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Note, Reminder, Snippet, Task


@dataclass
class SearchResult:
    """A single hit from the cross-entity FTS5 search."""

    item_id: str
    item_type: str  # note | task | reminder | snippet
    snippet: str  # first 100 chars of content
    entity: Any  # the full ORM object


async def search(
    query: str,
    session: AsyncSession,
    limit: int = 50,
) -> list[SearchResult]:
    """FTS5 search across all entity types.

    Args:
        query: FTS5 match query string.
        session: Active async DB session.
        limit: Maximum number of results to return.

    Returns:
        List of SearchResult objects, ordered by relevance.
    """
    query = query.strip()
    if not query:
        logger.debug("search() called with empty query — returning [].")
        return []

    logger.debug("FTS5 search: query={!r} limit={}", query, limit)

    try:
        rows = await session.execute(
            text(
                "SELECT item_id, item_type, content"
                " FROM search_index"
                " WHERE search_index MATCH :q"
                " ORDER BY rank"
                " LIMIT :lim"
            ),
            {"q": query, "lim": limit},
        )
        hits = list(rows)
    except Exception as exc:  # noqa: BLE001
        logger.error("FTS5 search failed: {}", exc)
        return []

    if not hits:
        return []

    # Group IDs by type for batched fetches
    by_type: dict[str, list[str]] = {}
    order: list[tuple[str, str]] = []  # (item_id, item_type) in rank order
    for item_id, item_type, _content in hits:
        by_type.setdefault(item_type, []).append(item_id)
        order.append((item_id, item_type))

    # Fetch entities
    entity_map: dict[tuple[str, str], Any] = {}

    if "note" in by_type:
        rows_n = await session.execute(
            select(Note).where(Note.id.in_(by_type["note"]), Note.deleted_at.is_(None))
        )
        for n in rows_n.scalars():
            entity_map[("note", n.id)] = n

    if "task" in by_type:
        rows_t = await session.execute(
            select(Task).where(Task.id.in_(by_type["task"]), Task.deleted_at.is_(None))
        )
        for t in rows_t.scalars():
            entity_map[("task", t.id)] = t

    if "reminder" in by_type:
        rows_r = await session.execute(
            select(Reminder).where(
                Reminder.id.in_(by_type["reminder"]), Reminder.deleted_at.is_(None)
            )
        )
        for r in rows_r.scalars():
            entity_map[("reminder", r.id)] = r

    if "snippet" in by_type:
        rows_s = await session.execute(
            select(Snippet).where(
                Snippet.id.in_(by_type["snippet"]), Snippet.deleted_at.is_(None)
            )
        )
        for s in rows_s.scalars():
            entity_map[("snippet", s.id)] = s

    # Build results in rank order, skipping deleted/missing
    results: list[SearchResult] = []
    for item_id, item_type in order:
        entity = entity_map.get((item_type, item_id))
        if entity is None:
            continue
        content = getattr(entity, "content", "") or ""
        snippet_text = content[:100]
        results.append(
            SearchResult(
                item_id=item_id,
                item_type=item_type,
                snippet=snippet_text,
                entity=entity,
            )
        )

    logger.debug("FTS5 search returned {} results.", len(results))
    return results


# ── Personal-data query patterns ───────────────────────────────────────────────

_TASKS_TODAY_PATTERNS = re.compile(
    r"(what|any|show|list).*(task|todo|due|deadline).*(today|now)|"
    r"(task|todo).*(today)|"
    r"(what do i have today)",
    re.IGNORECASE,
)

_REMINDERS_DUE_PATTERNS = re.compile(
    r"(any|what|show).*(reminder|remind).*(due|pending|today|now)|"
    r"(reminder|remind).*(today|now|due)",
    re.IGNORECASE,
)

_ALL_TASKS_PATTERNS = re.compile(
    r"(my|show|list|what are my).*(task|todo)|"
    r"(task|todo).*(list|all|pending)",
    re.IGNORECASE,
)


async def search_personal_query(text_input: str, session: AsyncSession) -> str:
    """Handle natural-language personal-data queries using DB queries.

    Detects patterns like "what tasks do I have today", "any reminders due",
    etc. and returns a formatted summary string.

    Args:
        text_input: Raw user query text.
        session: Active async DB session.

    Returns:
        Formatted summary string for display in the UI.
    """
    text_input = text_input.strip()
    logger.debug("Personal query: {!r}", text_input)

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # Reminders due — check BEFORE tasks because "any reminders due today"
    # also matches the generic task pattern (contains "due.*today")
    if _REMINDERS_DUE_PATTERNS.search(text_input):
        rows = await session.execute(
            select(Reminder).where(
                Reminder.deleted_at.is_(None),
                Reminder.notified == False,  # noqa: E712
                Reminder.trigger_at <= today_end,
            )
        )
        reminders = list(rows.scalars().all())
        return _format_reminders_due(reminders, now)

    # Tasks due today
    if _TASKS_TODAY_PATTERNS.search(text_input):
        rows = await session.execute(
            select(Task).where(
                Task.deleted_at.is_(None),
                Task.status == "todo",
                Task.deadline >= today_start,
                Task.deadline < today_end,
            )
        )
        tasks = list(rows.scalars().all())
        return _format_tasks_today(tasks, now)

    # General task list
    if _ALL_TASKS_PATTERNS.search(text_input):
        rows = await session.execute(
            select(Task).where(
                Task.deleted_at.is_(None),
                Task.status == "todo",
            ).order_by(Task.created_at.desc()).limit(20)
        )
        tasks = list(rows.scalars().all())
        return _format_all_tasks(tasks)

    # Fallback: FTS search
    results = await search(text_input, session)
    if not results:
        return "No matching items found."
    lines = [f"Found {len(results)} result(s):"]
    for r in results[:5]:
        lines.append(f"  [{r.item_type}] {r.snippet}")
    return "\n".join(lines)


# ── Formatting helpers ─────────────────────────────────────────────────────────


def _format_tasks_today(tasks: list[Task], now: datetime) -> str:
    if not tasks:
        return "You have no tasks due today."
    lines = [f"You have {len(tasks)} task(s) due today:"]
    for t in tasks:
        deadline_str = ""
        if t.deadline:
            deadline_str = f" (by {t.deadline.strftime('%H:%M')})"
        lines.append(f"  • {t.content}{deadline_str}")
    return "\n".join(lines)


def _format_reminders_due(reminders: list[Reminder], now: datetime) -> str:
    if not reminders:
        return "No reminders due today."
    lines = [f"You have {len(reminders)} reminder(s) due:"]
    for r in reminders:
        time_str = r.trigger_at.strftime("%H:%M") if r.trigger_at else ""
        lines.append(f"  • {r.content} at {time_str}")
    return "\n".join(lines)


def _format_all_tasks(tasks: list[Task]) -> str:
    if not tasks:
        return "You have no pending tasks."
    lines = [f"You have {len(tasks)} pending task(s):"]
    for t in tasks:
        lines.append(f"  • {t.content}")
    return "\n".join(lines)
