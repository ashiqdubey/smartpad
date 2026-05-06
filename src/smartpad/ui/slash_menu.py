"""Slash command popup — futuristic glass list with icon glyph + name + desc."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QKeyEvent,
    QPainter,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from smartpad.core.intent_detector import ALL_SLASH_COMMANDS, get_slash_completions

# Description + glyph (single char) + accent tint per command.
_COMMANDS: dict[str, tuple[str, str, str]] = {
    "/note": ("Save a note", "✎", "#7c6ef5"),
    "/task": ("Save a task", "✓", "#60a5fa"),
    "/todo": ("Save a task", "✓", "#60a5fa"),
    "/remind": ("Set a reminder", "⏰", "#fb923c"),
    "/reminder": ("Set a reminder", "⏰", "#fb923c"),
    "/snippet": ("Save a code snippet", "<>", "#34d399"),
    "/snip": ("Save a code snippet", "<>", "#34d399"),
    "/find": ("Search your notes", "⌕", "#a78bfa"),
    "/search": ("Search your notes", "⌕", "#a78bfa"),
    "/tasks": ("List your tasks", "≡", "#60a5fa"),
    "/today": ("Show today's items", "◷", "#fb923c"),
    "/snippets": ("Browse snippets", "<>", "#34d399"),
    "/notes": ("Browse notes", "✎", "#7c6ef5"),
    "/done": ("Mark a task done", "✓", "#34d399"),
    "/remove": ("Delete an item", "✕", "#f87171"),
    "/delete": ("Delete an item", "✕", "#f87171"),
    "/clear": ("Clear chat stream", "∅", "#94a3b8"),
    "/settings": ("Open settings", "⚙", "#94a3b8"),
    "/browse": ("Open browse window", "▤", "#7c6ef5"),
    "/model": ("Change AI model", "◆", "#c87ec8"),
    "/help": ("Show help", "?", "#94a3b8"),
    "/ai": ("AI level settings", "✦", "#c87ec8"),
    "/level": ("AI level settings", "✦", "#c87ec8"),
}


class _SlashRow(QWidget):
    """One row in the slash menu — icon glyph + command + description."""

    ROW_HEIGHT = 38

    def __init__(self, cmd: str, desc: str, glyph: str, tint: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cmd = cmd
        self._desc = desc
        self._glyph = glyph
        self._tint = QColor(tint)
        self.setFixedHeight(self.ROW_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 12, 0)
        layout.setSpacing(10)

        # Glyph badge (24×24 colored square)
        self._badge = _Badge(self._glyph, self._tint)
        layout.addWidget(self._badge)

        name = QLabel(cmd)
        name.setObjectName("SlashName")
        layout.addWidget(name)

        layout.addStretch()

        d = QLabel(desc)
        d.setObjectName("SlashDesc")
        layout.addWidget(d)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(280, self.ROW_HEIGHT)


class _Badge(QWidget):
    """24×24 rounded-square badge with a single-char glyph in the accent tint."""

    def __init__(self, glyph: str, tint: QColor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._glyph = glyph
        self._tint = tint
        self.setFixedSize(QSize(24, 24))

    def paintEvent(self, event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Soft tinted square
        bg = QColor(self._tint)
        bg.setAlpha(38)
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, 24.0, 24.0, 6.0, 6.0)
        p.fillPath(path, QBrush(bg))

        # Glyph in accent
        font = self.font()
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        p.setPen(self._tint)
        p.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), self._glyph)
        p.end()


class SlashMenu(QFrame):
    """Floating popup listing matching slash commands."""

    command_selected = pyqtSignal(str)
    dismissed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SlashMenu")
        self._setup_ui()
        self._populate(list(sorted(ALL_SLASH_COMMANDS)))
        self.hide()

    # ── Public API ────────────────────────────────────────────────────────────

    def update_filter(self, prefix: str) -> None:
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
        count = self._list.count()
        if count == 0:
            return
        current = self._list.currentRow()
        self._list.setCurrentRow((current + delta) % count)

    def accept_selection(self) -> None:
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
        self._list.setObjectName("SlashList")
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setSpacing(0)
        self._list.itemActivated.connect(self._on_item_activated)
        self._list.itemClicked.connect(self._on_item_activated)
        layout.addWidget(self._list)

        self.setMinimumWidth(280)
        self.setMaximumHeight(280)

    def _populate(self, commands: list[str]) -> None:
        self._list.clear()
        for cmd in commands:
            desc, glyph, tint = _COMMANDS.get(cmd, (cmd, "›", "#94a3b8"))
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            item.setSizeHint(QSize(280, _SlashRow.ROW_HEIGHT))
            self._list.addItem(item)
            self._list.setItemWidget(item, _SlashRow(cmd, desc, glyph, tint))
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.command_selected.emit(cmd)
        self.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
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
