"""NoteBubble — displays a saved note.

Visual:
- Full-width, pale yellow background (BubbleNote QSS ID)
- note prefix before content text
- Content text in italic
- Pinned indicator shown when pinned=True
- Right-click context menu -> "Show original" displays original_content

Status dot: top-right corner (saving -> saved -> error).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase


class NoteBubble(BubbleBase):
    """A saved-note bubble.

    Args:
        content: The (possibly AI-processed) note text to display.
        original_content: The user's original raw text, accessible via right-click.
        pinned: If True, shows a pin indicator.
        parent: Optional parent widget.
    """

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

        frame_layout = QHBoxLayout(self._bubble_frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(6)

        self._icon_label = QLabel("\U0001f4dd")
        self._icon_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        frame_layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        self._content_label = QLabel()
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        font = self._content_label.font()
        font.setItalic(True)
        self._content_label.setFont(font)
        frame_layout.addWidget(self._content_label)

        self._pin_label = QLabel("\U0001f4cc")
        self._pin_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        self._pin_label.setVisible(self._pinned)
        frame_layout.addWidget(self._pin_label, 0, Qt.AlignmentFlag.AlignTop)

        self._content_layout.addWidget(self._bubble_frame)

        self._bubble_frame.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._bubble_frame.customContextMenuRequested.connect(  # type: ignore[attr-defined]
            self._show_context_menu
        )

    def set_content(self, content: str) -> None:
        """Update the displayed note content.

        Args:
            content: New note text.
        """
        self._content = content
        self._refresh()

    def set_pinned(self, pinned: bool) -> None:
        """Show or hide the pin indicator.

        Args:
            pinned: Whether the note is pinned.
        """
        self._pinned = pinned
        self._pin_label.setVisible(pinned)

    def _show_context_menu(self, pos: object) -> None:
        menu = QMenu(self._bubble_frame)
        show_orig = menu.addAction("Show original")
        action = menu.exec(
            self._bubble_frame.mapToGlobal(pos)  # type: ignore[arg-type]
        )
        if action is show_orig:
            self._show_original_dialog()

    def _show_original_dialog(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Original content")
        dlg.setText(self._original_content or "(no original stored)")
        dlg.exec()

    def _refresh(self) -> None:
        self._content_label.setText(self._content)
