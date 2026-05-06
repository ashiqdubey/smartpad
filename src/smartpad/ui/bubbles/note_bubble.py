"""NoteBubble — sticky-note style saved-note display.

Visual:
- Warm amber tint card (distinct from chat bubbles)
- Top kicker row: ✎ NOTE · saved <time>  + pin indicator on right
- Content below in a clean readable face (not italic — it makes wraps hard to read)
- Right-click → "Show original" to recover pre-AI text

Status dot: top-right corner (saving → saved → error).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase


class NoteBubble(BubbleBase):
    """A saved-note bubble shown in the chat stream."""

    def __init__(
        self,
        content: str = "",
        original_content: str = "",
        pinned: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._content = content
        self._original_content = original_content
        self._pinned = pinned
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self._bubble_frame = QWidget(self._content_widget)
        self._bubble_frame.setObjectName("BubbleNote")
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        v = QVBoxLayout(self._bubble_frame)
        v.setContentsMargins(14, 10, 14, 12)
        v.setSpacing(6)

        # Kicker line: ✎ NOTE  ·  saved
        kicker_row = QHBoxLayout()
        kicker_row.setContentsMargins(0, 0, 0, 0)
        kicker_row.setSpacing(6)

        glyph = QLabel("✎")
        glyph.setObjectName("NoteGlyph")
        kicker_row.addWidget(glyph)

        kicker = QLabel("NOTE")
        kicker.setObjectName("NoteKicker")
        kicker_row.addWidget(kicker)

        kicker_row.addStretch()

        self._pin_label = QLabel("📌")
        self._pin_label.setObjectName("NotePin")
        self._pin_label.setVisible(self._pinned)
        kicker_row.addWidget(self._pin_label)

        v.addLayout(kicker_row)

        # Content
        self._content_label = QLabel()
        self._content_label.setObjectName("NoteContent")
        self._content_label.setWordWrap(True)
        self._content_label.setMinimumWidth(0)
        self._content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        v.addWidget(self._content_label)

        self._content_layout.addWidget(self._bubble_frame)

        self._bubble_frame.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._bubble_frame.customContextMenuRequested.connect(  # type: ignore[attr-defined]
            self._show_context_menu
        )

    def set_content(self, content: str) -> None:
        self._content = content
        self._refresh()

    def set_pinned(self, pinned: bool) -> None:
        self._pinned = pinned
        self._pin_label.setVisible(pinned)

    def _show_context_menu(self, pos: object) -> None:
        menu = QMenu(self._bubble_frame)
        show_orig = menu.addAction("Show original")
        action = menu.exec(self._bubble_frame.mapToGlobal(pos))  # type: ignore[arg-type]
        if action is show_orig:
            self._show_original_dialog()

    def _show_original_dialog(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Original content")
        dlg.setText(self._original_content or "(no original stored)")
        dlg.exec()

    def _refresh(self) -> None:
        self._content_label.setText(self._content)
