"""In-session search history — SPEC.MD section 20.

Keeps last 10 searches in memory for suggestion display.
Cleared on app close (not persisted).
"""

from __future__ import annotations

_MAX = 10


class SearchHistory:
    """Session-scoped search history (in-memory only)."""

    def __init__(self, max_size: int = _MAX) -> None:
        self._history: list[str] = []
        self._max = max_size

    def add(self, query: str) -> None:
        """Add a query, deduplicating and keeping most-recent first."""
        q = query.strip()
        if not q:
            return
        if q in self._history:
            self._history.remove(q)
        self._history.insert(0, q)
        if len(self._history) > self._max:
            self._history.pop()

    def get_suggestions(self, prefix: str = "") -> list[str]:
        """Return history entries matching prefix (case-insensitive)."""
        p = prefix.lower()
        if not p:
            return list(self._history)
        return [h for h in self._history if h.lower().startswith(p)]

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
