"""Browse view — embedded inside the floating panel via QStackedWidget."""
from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from smartpad.core.event_bus import event_bus
from smartpad.ui.widgets import NoteCard


class _DBLoader(QThread):
    finished = pyqtSignal(list, list, list, list)

    def run(self) -> None:
        try:
            result = asyncio.run(self._load())
        except Exception as exc:
            logger.error("BrowseView DB load failed: {}", exc)
            result = ([], [], [], [])
        self.finished.emit(*result)

    @staticmethod
    async def _load() -> tuple[list, list, list, list]:
        from smartpad.db.engine import get_async_session
        from smartpad.db.repositories.notes import NotesRepo
        from smartpad.db.repositories.reminders import RemindersRepo
        from smartpad.db.repositories.snippets import SnippetsRepo
        from smartpad.db.repositories.tasks import TasksRepo

        async with get_async_session() as s:
            notes = await NotesRepo(s).list(limit=200)
        async with get_async_session() as s:
            tasks = await TasksRepo(s).list(limit=200)
        async with get_async_session() as s:
            reminders = await RemindersRepo(s).list(limit=200)
        async with get_async_session() as s:
            snippets = await SnippetsRepo(s).list(limit=200)
        return notes, tasks, reminders, snippets


class BrowseView(QWidget):
    """Browse page — lives inside the floating panel's QStackedWidget."""

    back_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_notes: list[Any] = []
        self._all_tasks: list[Any] = []
        self._all_reminders: list[Any] = []
        self._all_snippets: list[Any] = []
        self._loader: _DBLoader | None = None
        self._setup_ui()
        self._load()

        # Live refresh — panel saves notify us via the bus.
        event_bus().item_saved.connect(self._on_item_saved)

        # Poll fallback for cross-process saves (e.g. from the API server).
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(4000)
        self._poll_timer.timeout.connect(self._load)
        self._poll_timer.start()

    def _setup_ui(self) -> None:
        cl = QVBoxLayout(self)
        cl.setContentsMargins(20, 8, 20, 16)
        cl.setSpacing(10)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search notes, tasks, reminders, snippets…")
        self._search.textChanged.connect(self._filter)
        refresh_btn = QPushButton("↺  Refresh")
        refresh_btn.setObjectName("RefreshButton")
        refresh_btn.setFixedWidth(110)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load)
        search_row.addWidget(self._search)
        search_row.addWidget(refresh_btn)
        cl.addLayout(search_row)

        # Tabs
        self._tabs = QTabWidget()
        self._notes_list = QListWidget()
        self._tasks_list = QListWidget()
        self._reminders_list = QListWidget()
        self._snippets_list = QListWidget()

        for name, lst in [
            ("Notes", self._notes_list),
            ("Tasks", self._tasks_list),
            ("Reminders", self._reminders_list),
            ("Snippets", self._snippets_list),
        ]:
            splitter = QSplitter(Qt.Orientation.Horizontal)
            detail = QTextEdit()
            detail.setReadOnly(True)
            lst.setProperty("_detail", detail)
            splitter.addWidget(lst)
            splitter.addWidget(detail)
            splitter.setSizes([400, 320])
            lst.currentItemChanged.connect(
                lambda cur, prev, d=detail: self._on_select(cur, d)
            )
            self._tabs.addTab(splitter, name)

        cl.addWidget(self._tabs, stretch=1)

        # Status row
        self._status = QLabel("Loading…")
        self._status.setObjectName("BrowseStatus")
        cl.addWidget(self._status)

    @pyqtSlot(str)
    def _on_item_saved(self, _kind: str) -> None:
        """Event-bus slot — reload lists when anything is saved app-wide."""
        self._load()

    def set_tab(self, index: int) -> None:
        """Programmatically switch to a tab (0=Notes, 1=Tasks, 2=Reminders, 3=Snippets)."""
        if 0 <= index < self._tabs.count():
            self._tabs.setCurrentIndex(index)

    def set_search(self, query: str) -> None:
        """Set the search filter text."""
        self._search.setText(query or "")

    def teardown(self) -> None:
        """Stop timers + disconnect listeners. Called by FloatingPanel
        before the panel is destroyed."""
        if hasattr(self, "_poll_timer"):
            self._poll_timer.stop()
        try:
            event_bus().item_saved.disconnect(self._on_item_saved)
        except (TypeError, RuntimeError):
            pass
        loader = self._loader
        if loader is not None:
            try:
                loader.finished.disconnect()
            except (TypeError, RuntimeError):
                pass
            try:
                if loader.isRunning():
                    loader.quit()
                    loader.wait(2000)
            except RuntimeError:
                pass
        self._loader = None

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        self._status.setText("Loading…")
        # Disconnect any previous loader so a late finish doesn't poke us.
        # Don't use deleteLater here — `self._loader` keeps the Python
        # wrapper alive while the C++ object is destroyed, which then
        # blows up on the next isRunning() check.
        old = self._loader
        if old is not None:
            try:
                old.finished.disconnect()
            except (TypeError, RuntimeError):
                pass
        loader = _DBLoader(self)  # parent=self anchors lifetime to dialog
        loader.finished.connect(self._on_loaded)
        self._loader = loader
        loader.start()

    @pyqtSlot(list, list, list, list)
    def _on_loaded(self, notes: list, tasks: list, reminders: list, snippets: list) -> None:
        self._all_notes = notes
        self._all_tasks = tasks
        self._all_reminders = reminders
        self._all_snippets = snippets
        self._populate(self._search.text())

    def _filter(self, text: str) -> None:
        self._populate(text)

    def _populate(self, query: str) -> None:
        q = query.lower()

        def _match(content: str) -> bool:
            return not q or q in content.lower()

        self._notes_list.clear()
        # Notes get the sticky-card treatment — feed style.
        self._notes_list.setSpacing(6)
        for n in self._all_notes:
            if _match(n.content):
                when = self._humanize_time(getattr(n, "created_at", None))
                card = NoteCard(content=n.content, when=when, glyph="✎")
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, n.content)
                item.setSizeHint(card.sizeHint())
                self._notes_list.addItem(item)
                self._notes_list.setItemWidget(item, card)

        self._tasks_list.clear()
        for t in self._all_tasks:
            if _match(t.content):
                icon = "✓" if t.status == "done" else "○"
                dl = (f"  [due {t.deadline.strftime('%Y-%m-%d')}]" if getattr(t, "deadline", None) else "")
                item = QListWidgetItem(f"{icon} {t.content[:80]}{dl}")
                detail = f"Status: {t.status}\nContent: {t.content}"
                if getattr(t, "deadline", None):
                    detail += f"\nDeadline: {t.deadline}"
                item.setData(Qt.ItemDataRole.UserRole, detail)
                self._tasks_list.addItem(item)

        self._reminders_list.clear()
        for r in self._all_reminders:
            if _match(r.content):
                t_str = (r.trigger_at.strftime("%Y-%m-%d %H:%M") if getattr(r, "trigger_at", None) else "—")
                done = "✓" if getattr(r, "notified", False) else "\U0001f514"
                item = QListWidgetItem(f"{done} {r.content[:70]}  @{t_str}")
                detail = f"Content: {r.content}\nTrigger: {t_str}\nNotified: {r.notified}"
                item.setData(Qt.ItemDataRole.UserRole, detail)
                self._reminders_list.addItem(item)

        self._snippets_list.clear()
        for s in self._all_snippets:
            if _match(s.content):
                lang = getattr(s, "language", "") or ""
                label = f"[{lang}] " if lang else ""
                item = QListWidgetItem(f"{label}{s.content[:80]}")
                item.setData(Qt.ItemDataRole.UserRole, s.content)
                self._snippets_list.addItem(item)

        counts = [
            len([n for n in self._all_notes if _match(n.content)]),
            len([t for t in self._all_tasks if _match(t.content)]),
            len([r for r in self._all_reminders if _match(r.content)]),
            len([s for s in self._all_snippets if _match(s.content)]),
        ]
        self._status.setText(
            f"{counts[0]} notes · {counts[1]} tasks · {counts[2]} reminders · {counts[3]} snippets"
        )

    @staticmethod
    def _on_select(item: QListWidgetItem | None, detail: QTextEdit) -> None:
        if item is not None:
            detail.setPlainText(item.data(Qt.ItemDataRole.UserRole) or "")
        else:
            detail.clear()

    @staticmethod
    def _humanize_time(ts: object) -> str:
        if ts is None:
            return ""
        try:
            from datetime import UTC, datetime, timedelta  # noqa: PLC0415
            now = datetime.now(UTC)
            if hasattr(ts, "tzinfo") and ts.tzinfo is None:  # type: ignore[union-attr]
                ts = ts.replace(tzinfo=UTC)  # type: ignore[union-attr]
            delta = now - ts  # type: ignore[operator]
            if delta < timedelta(minutes=1):
                return "just now"
            if delta < timedelta(hours=1):
                return f"{int(delta.total_seconds() // 60)}m ago"
            if delta < timedelta(days=1):
                return f"{int(delta.total_seconds() // 3600)}h ago"
            if delta < timedelta(days=7):
                return f"{delta.days}d ago"
            return ts.strftime("%b %d")  # type: ignore[union-attr]
        except Exception:
            return ""
