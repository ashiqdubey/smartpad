"""Slash command popup menu — SPEC.md section 7 + section 12.

Appears above the input field when the user types "/".
Filters as the user types, navigated with arrow keys, executed with Enter.
Dismissed with Esc or when text no longer starts with "/".
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QFrame,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from smartpad.core.intent_detector import ALL_SLASH_COMMANDS, get_slash_completions

# Human-readable descriptions for each command
_COMMAND_DESCRIPTIONS: dict[str, str] = {
    "/note": "Save a note",
    "/task": "Save a task",
    "/todo": "Save a task",
    "/remind": "Set a reminder",
    "/reminder": "Set a reminder",
    "/snippet": "Save a code snippet",
    "/snip": "Save a code snippet",
    "/find": "Search your notes",
    "/search": "Search your notes",
    "/tasks": "List your tasks",
    "/today": "Show today's items",
    "/snippets": "Browse snippets",
    "/notes": "Browse notes",
    "/done": "Mark a task done",
    "/remove": "Delete an item",
    "/delete": "Delete an item",
    "/clear": "Clear chat stream",
    "/settings": "Open settings",
    "/browse": "Open browse window",
    "/model": "Change AI model",
    "/help": "Show help",
    "/ai": "AI level settings",
    "/level": "AI level settings",
}


class SlashMenu(QFrame):
    """Floating popup listing matching slash commands."""

    command_selected = pyqtSignal(str)  # emits e.g. "/note"
    dismissed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SlashMenu")
        self._setup_ui()
        self._populate(list(sorted(ALL_SLASH_COMMANDS)))
        self.hide()

    # ── Public API ────────────────────────────────────────────────────────────

    def update_filter(self, prefix: str) -> None:
        """Filter to commands matching prefix and show/hide accordingly."""
        if not prefix.startswith("/"):
            self.hide()
            return

        matches = get_slash_completions(prefix)
        if not matches:
            self.hide()
            return

        self._populate(matches)
        self.show()

    def move_selection(self, delta: int) -> None:
        """Move selection by delta rows (±1). Wraps around."""
        count = self._list.count()
        if count == 0:
            return
        current = self._list.currentRow()
        self._list.setCurrentRow((current + delta) % count)

    def accept_selection(self) -> None:
        """Emit command_selected with the currently highlighted command."""
        item = self._list.currentItem()
        if item is not None:
            cmd = item.data(Qt.ItemDataRole.UserRole)
            self.command_selected.emit(cmd)
            self.hide()

    def is_visible(self) -> bool:
        return self.isVisible()

    # ── Private ───────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemActivated.connect(self._on_item_activated)
        self._list.itemClicked.connect(self._on_item_activated)
        layout.addWidget(self._list)

        self.setStyleSheet("""
            SlashMenu {
                background: #2b2d31;
                border: 1px solid #3d3f45;
                border-radius: 6px;
            }
            QListWidget {
                background: transparent;
                color: #dcddde;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #5865f2;
                color: white;
            }
            QListWidget::item:hover {
                background: #3d3f45;
            }
        """)
        self.setMinimumWidth(260)
        self.setMaximumHeight(280)

    def _populate(self, commands: list[str]) -> None:
        self._list.clear()
        for cmd in commands:
            desc = _COMMAND_DESCRIPTIONS.get(cmd, "")
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            # Display: "/command  — description"
            item.setText(f"{cmd}  {desc}" if desc else cmd)
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.command_selected.emit(cmd)
        self.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.dismissed.emit()
            self.hide()
        elif key == Qt.Key.Key_Up:
            self.move_selection(-1)
        elif key == Qt.Key.Key_Down:
            self.move_selection(1)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept_selection()
        else:
            super().keyPressEvent(event)
