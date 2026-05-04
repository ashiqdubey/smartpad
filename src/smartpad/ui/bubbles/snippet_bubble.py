"""SnippetBubble — displays a code snippet.

Visual:
- Full-width, dark mono-font background (BubbleSnippet QSS ID)
- Optional language label pill (top-left area)
- 📋 copy button top-right that copies content to clipboard; briefly shows "Copied!"

Status dot: top-right corner (saving → saved → error).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase

# How long "Copied!" text persists (ms)
_COPIED_RESET_MS = 1500


class SnippetBubble(BubbleBase):
    """A code-snippet bubble with a copy-to-clipboard button.

    Args:
        content: The raw snippet/code text.
        language: Optional language label (e.g. ``'python'``, ``'bash'``).
        parent: Optional parent widget.
    """

    def __init__(
        self,
        content: str = "",
        language: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._content = content
        self._language = language

        self._build_ui()
        self._refresh()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._bubble_frame = QWidget(self._content_widget)
        self._bubble_frame.setObjectName("BubbleSnippet")
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        outer = QVBoxLayout(self._bubble_frame)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(6)

        # ── Top bar: language pill + copy button ──────────────────────────────
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(6)

        self._lang_pill = QLabel()
        self._lang_pill.setObjectName("LanguagePill")
        self._lang_pill.setStyleSheet(
            "background-color: rgba(166,227,161,0.15);"
            "color: #a6e3a1;"
            "border-radius: 6px;"
            "padding: 1px 6px;"
            "font-size: 11px;"
        )
        self._lang_pill.setVisible(False)
        top_bar_layout.addWidget(self._lang_pill)
        top_bar_layout.addStretch()

        self._copy_btn = QPushButton("📋")
        self._copy_btn.setObjectName("CopyButton")
        self._copy_btn.setToolTip("Copy to clipboard")
        self._copy_btn.setFixedSize(28, 22)
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: rgba(166,227,161,0.15);"
            "  color: #a6e3a1;"
            "  border: none;"
            "  border-radius: 4px;"
            "  font-size: 13px;"
            "}"
            "QPushButton:hover {"
            "  background-color: rgba(166,227,161,0.30);"
            "}"
        )
        self._copy_btn.clicked.connect(self._on_copy)
        top_bar_layout.addWidget(self._copy_btn)

        outer.addWidget(top_bar)

        # ── Code content ──────────────────────────────────────────────────────
        self._code_label = QLabel()
        self._code_label.setWordWrap(True)
        self._code_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._code_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        # Mono font applied inline (QSS on BubbleSnippet already sets monospace
        # for the frame; we mirror it here for the label)
        font = self._code_label.font()
        font.setFamily("Cascadia Code, Consolas, Monaco, monospace")
        font.setPointSize(11)
        self._code_label.setFont(font)
        outer.addWidget(self._code_label)

        self._content_layout.addWidget(self._bubble_frame)

        # Timer to reset copy button text
        self._copy_reset_timer = QTimer(self)
        self._copy_reset_timer.setSingleShot(True)
        self._copy_reset_timer.setInterval(_COPIED_RESET_MS)
        self._copy_reset_timer.timeout.connect(self._reset_copy_btn)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_content(self, content: str) -> None:
        """Update the displayed code content.

        Args:
            content: New snippet text.
        """
        self._content = content
        self._refresh()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_copy(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._content)
        self._copy_btn.setText("Copied!")
        self._copy_reset_timer.start()

    def _reset_copy_btn(self) -> None:
        self._copy_btn.setText("📋")

    def _refresh(self) -> None:
        self._code_label.setText(self._content)
        if self._language:
            self._lang_pill.setText(self._language)
            self._lang_pill.setVisible(True)
        else:
            self._lang_pill.setVisible(False)
