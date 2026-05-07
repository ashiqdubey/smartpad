"""Note editor view — edit a saved note with a formatting toolbar + live
markdown preview. Embedded in the floating panel's QStackedWidget.

Layout:
  [toolbar: B / I / • / ☑ / `code` / link]
  [QSplitter horizontal]
    [QTextEdit  — markdown source]   [QTextBrowser — rendered preview]
  [Save] [Cancel]
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any

from loguru import logger
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class NoteEditorView(QWidget):
    """Per-note editor with markdown source + live rendered preview."""

    saved = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._note: Any = None  # the loaded note row
        self._setup_ui()

    # ── Public ────────────────────────────────────────────────────────────────

    def load(self, note: Any) -> None:
        """Populate editor from a Note row. Pass None to clear."""
        self._note = note
        if note is None:
            self._editor.setPlainText("")
            self._preview.setMarkdown("")
            self._meta.setText("")
            return
        self._editor.setPlainText(note.content or "")
        self._preview.setMarkdown(note.content or "")
        self._meta.setText(self._format_meta(note))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 8, 20, 16)
        v.setSpacing(10)

        # Top: meta line ("Editing · saved 5m ago")
        self._meta = QLabel("")
        self._meta.setObjectName("CardKicker")
        v.addWidget(self._meta)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        def _tool_btn(label: str, tip: str, slot) -> QPushButton:  # type: ignore[no-untyped-def]
            b = QPushButton(label)
            b.setObjectName("EditorToolBtn")
            b.setFixedHeight(28)
            b.setMinimumWidth(34)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            return b

        toolbar.addWidget(_tool_btn("B",  "Bold (Ctrl+B)",          self._toggle_bold))
        toolbar.addWidget(_tool_btn("I",  "Italic (Ctrl+I)",        self._toggle_italic))
        toolbar.addWidget(_tool_btn("S",  "Strikethrough",          self._toggle_strike))
        toolbar.addWidget(_tool_btn("•",  "Bullet list",            self._make_bullet))
        toolbar.addWidget(_tool_btn("☐",  "Checkbox",               self._make_checkbox))
        toolbar.addWidget(_tool_btn("`",  "Inline code",            self._toggle_code))
        toolbar.addWidget(_tool_btn("⌗",  "Code block",             self._make_code_block))
        toolbar.addWidget(_tool_btn("🔗", "Link",                   self._make_link))
        toolbar.addWidget(_tool_btn("H₁", "Heading",                self._make_heading))
        toolbar.addStretch()
        v.addLayout(toolbar)

        # Split: source + preview
        split = QSplitter(Qt.Orientation.Horizontal)

        self._editor = QTextEdit()
        self._editor.setObjectName("NoteEditor")
        f = QFont("SF Mono")
        f.setStyleHint(QFont.StyleHint.TypeWriter)
        f.setPixelSize(13)
        self._editor.setFont(f)
        self._editor.setAcceptRichText(False)  # store as plain markdown
        self._editor.textChanged.connect(self._on_text_changed)

        self._preview = QTextBrowser()
        self._preview.setObjectName("NotePreview")
        self._preview.setOpenExternalLinks(True)

        split.addWidget(self._editor)
        split.addWidget(self._preview)
        split.setSizes([520, 380])
        v.addWidget(split, stretch=1)

        # Save bar
        save_row = QHBoxLayout()
        save_row.setSpacing(8)
        save_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("EditorCancelBtn")
        cancel_btn.setMinimumHeight(34)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.back_requested.emit)
        save_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("DialogDoneButton")
        save_btn.setMinimumHeight(34)
        save_btn.setMinimumWidth(100)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        save_row.addWidget(save_btn)
        v.addLayout(save_row)

        # Debounced preview refresh
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(120)
        self._preview_timer.timeout.connect(self._refresh_preview)

    # ── Toolbar handlers ──────────────────────────────────────────────────────

    def _wrap_selection(self, prefix: str, suffix: str = "") -> None:
        cur = self._editor.textCursor()
        if not cur.hasSelection():
            cur.insertText(prefix + suffix)
            # Move cursor between prefix/suffix when inserting empty wrap
            for _ in range(len(suffix)):
                cur.movePosition(QTextCursor.MoveOperation.Left)
            self._editor.setTextCursor(cur)
            return
        sel = cur.selectedText()
        cur.insertText(f"{prefix}{sel}{suffix}")

    def _line_prefix(self, prefix: str) -> None:
        cur = self._editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.insertText(prefix)
        self._editor.setTextCursor(cur)

    def _toggle_bold(self) -> None:    self._wrap_selection("**", "**")
    def _toggle_italic(self) -> None:  self._wrap_selection("*", "*")
    def _toggle_strike(self) -> None:  self._wrap_selection("~~", "~~")
    def _toggle_code(self) -> None:    self._wrap_selection("`", "`")
    def _make_bullet(self) -> None:    self._line_prefix("- ")
    def _make_checkbox(self) -> None:  self._line_prefix("- [ ] ")
    def _make_heading(self) -> None:   self._line_prefix("# ")
    def _make_code_block(self) -> None:
        cur = self._editor.textCursor()
        cur.insertText("\n```\n\n```\n")
        # leave cursor inside the code block
        for _ in range(5):
            cur.movePosition(QTextCursor.MoveOperation.Left)
        self._editor.setTextCursor(cur)

    def _make_link(self) -> None:
        cur = self._editor.textCursor()
        if cur.hasSelection():
            sel = cur.selectedText()
            cur.insertText(f"[{sel}](url)")
        else:
            cur.insertText("[text](url)")

    # ── Preview / save ────────────────────────────────────────────────────────

    def _on_text_changed(self) -> None:
        self._preview_timer.start()

    def _refresh_preview(self) -> None:
        self._preview.setMarkdown(self._editor.toPlainText())

    def _on_save(self) -> None:
        if self._note is None:
            self.back_requested.emit()
            return
        new_text = self._editor.toPlainText()
        note_id = self._note.id

        async def _do() -> None:
            try:
                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.repositories.notes import NotesRepo  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415
                async with get_async_session() as s:
                    note = await NotesRepo(s).get(note_id)
                    if note is None:
                        return
                    note.content = new_text
                    note.updated_at = datetime.now(UTC)
                    await NotesRepo(s).save(note)
                logger.info("Note edited: {!r}", new_text[:60])
                from smartpad.core.event_bus import event_bus  # noqa: PLC0415
                event_bus().note_saved.emit()
                event_bus().item_saved.emit("note")
            except Exception as exc:
                logger.error("Note edit save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()
        self.saved.emit()
        self.back_requested.emit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _format_meta(note: Any) -> str:
        when = ""
        ts = getattr(note, "updated_at", None) or getattr(note, "created_at", None)
        if ts is not None:
            try:
                when = ts.strftime("%b %d · %H:%M")
            except Exception:
                when = ""
        col = getattr(note, "color", None) or "amber"
        return f"EDITING NOTE  ·  {when}  ·  {col.upper()}"
