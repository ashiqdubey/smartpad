"""Browse window — view all notes, tasks, reminders, snippets."""
from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger
from PyQt6.QtCore import Qt, QPoint, QSize, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
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


class _DBLoader(QThread):
    finished = pyqtSignal(list, list, list, list)

    def run(self) -> None:
        try:
            result = asyncio.run(self._load())
        except Exception as exc:
            logger.error("BrowseWindow DB load failed: {}", exc)
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


class BrowseWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Notes & Tasks")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumSize(720, 520)
        self.resize(820, 560)
        self._drag_pos: QPoint | None = None
        self._all_notes: list[Any] = []
        self._all_tasks: list[Any] = []
        self._all_reminders: list[Any] = []
        self._all_snippets: list[Any] = []
        self._setup_ui()
        self._load()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_title_bar())

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 8, 16, 14)
        cl.setSpacing(8)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search…")
        self._search.textChanged.connect(self._filter)
        refresh_btn = QPushButton("↺  Refresh")
        refresh_btn.setFixedWidth(100)
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
        self._status.setStyleSheet("color: rgba(255,255,255,0.30); font-size: 11px;")
        cl.addWidget(self._status)

        root.addWidget(content, stretch=1)

    def _make_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("DialogTitleBar")
        bar.setFixedHeight(52)

        row = QHBoxLayout(bar)
        row.setContentsMargins(20, 0, 14, 0)
        row.setSpacing(8)

        title = QLabel("Notes & Tasks")
        title.setObjectName("DialogTitle")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("DialogCloseButton")
        close_btn.setFixedSize(QSize(28, 28))
        close_btn.clicked.connect(self.close)

        row.addWidget(title)
        row.addStretch()
        row.addWidget(close_btn)

        bar.mousePressEvent = self._bar_press    # type: ignore[method-assign]
        bar.mouseMoveEvent = self._bar_move      # type: ignore[method-assign]
        bar.mouseReleaseEvent = self._bar_release  # type: ignore[method-assign]
        return bar

    def _bar_press(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _bar_move(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _bar_release(self, event) -> None:  # type: ignore[no-untyped-def]
        self._drag_pos = None

    def _load(self) -> None:
        self._status.setText("Loading…")
        self._loader = _DBLoader()
        self._loader.finished.connect(self._on_loaded)
        self._loader.start()

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
        for n in self._all_notes:
            if _match(n.content):
                item = QListWidgetItem(n.content[:90] + ("…" if len(n.content) > 90 else ""))
                item.setData(Qt.ItemDataRole.UserRole, n.content)
                self._notes_list.addItem(item)

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
            f"{counts[0]} notes  ·  {counts[1]} tasks  ·  {counts[2]} reminders  ·  {counts[3]} snippets"
        )

    @staticmethod
    def _on_select(item: QListWidgetItem | None, detail: QTextEdit) -> None:
        if item is not None:
            detail.setPlainText(item.data(Qt.ItemDataRole.UserRole) or "")
        else:
            detail.clear()
