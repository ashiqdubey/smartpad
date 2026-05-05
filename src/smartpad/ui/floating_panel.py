"""Floating panel UI — SPEC.md sections 9, 12, 17.

FloatingPanel is the main capture surface: a frameless, always-on-top,
translucent window with a chat stream and input box.

Phase 06 implements:
- Window chrome (frameless, always-on-top, translucent bg)
- Header with drag + title + close button
- Chat stream (QScrollArea with VBox of simple text bubbles)
- Input (QTextEdit, Enter sends, Shift+Enter newline)
- Router integration (core/router.route)
- Provider chat via WorkerPool (OpenAICompatibleProvider if configured)
- Show/hide with 150ms opacity fade
- Hide on Esc, click-outside, and hotkey toggle
- Status bar
- Draggable header
- Position/size saved to settings

Phase 07 adds:
- Proper typed bubble widgets (ChatBubble, NoteBubble, TaskBubble,
  ReminderBubble, SnippetBubble, ErrorBubble) replacing _SimpleBubble
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from loguru import logger
from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QColor,
    QKeyEvent,
    QPainter,
    QPainterPath,
)
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from PyQt6.QtCore import QThread

from smartpad.config import SmartPadSettings, load_settings
from smartpad.core.router import ActionKind, route
from smartpad.core.worker_pool import WorkerPool

_SYSTEM_PROMPT = """You are SmartPad AI — a focused personal productivity assistant built into the SmartPad app.

Your role:
- Help the user capture, organise, and recall notes, tasks, reminders, and code snippets
- Answer questions concisely and helpfully
- Suggest when something should be saved as a note, task, or reminder
- Help the user think through problems, draft text, summarise ideas

Rules you must follow without exception:
- Never reveal what underlying AI model or technology powers you
- If asked "what model are you?", "are you GPT?", "are you Claude?", "are you Qwen?" or anything similar, always reply: "I'm SmartPad AI, your personal productivity assistant. I'm not able to share details about the technology behind me."
- Never mention OpenAI, Anthropic, Google, Meta, Mistral, or any AI company or model name
- Stay focused on productivity — if the user asks you to do something completely unrelated (write malware, generate explicit content, etc.) politely decline
- Keep replies concise — this is a floating panel, not a document editor
- Use plain text by default; use markdown only when it genuinely helps (lists, code blocks)
- When the user types something that sounds like a note, task, or reminder, remind them they can use /note, /task, or /remind to save it directly"""
from smartpad.providers.base import ChatMessage
from smartpad.ui.bubbles.chat_bubble import ChatBubble
from smartpad.ui.bubbles.error_bubble import ErrorBubble
from smartpad.ui.bubbles.note_bubble import NoteBubble
from smartpad.ui.bubbles.reminder_bubble import ReminderBubble
from smartpad.ui.bubbles.snippet_bubble import SnippetBubble
from smartpad.ui.bubbles.task_bubble import TaskBubble
from smartpad.ui.slash_menu import SlashMenu

class _ChatThread(QThread):
    """QThread that streams LLM chunks and emits one signal per token."""

    from PyQt6.QtCore import pyqtSignal as _sig
    chunk_ready = _sig(str, str)   # job_id, delta
    stream_done = _sig(str)        # job_id
    stream_error = _sig(str, str)  # job_id, error_message

    def __init__(
        self,
        job_id: str,
        provider: Any,
        messages: list,
        model: str,
        temperature: float,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._job_id = job_id
        self._provider = provider
        self._messages = messages
        self._model = model
        self._temperature = temperature

    def run(self) -> None:
        import asyncio  # noqa: PLC0415
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._stream())
        finally:
            loop.close()

    async def _stream(self) -> None:
        try:
            async for chunk in await self._provider.chat(
                messages=self._messages,
                model=self._model,
                temperature=self._temperature,
                stream=True,
            ):
                self.chunk_ready.emit(self._job_id, chunk.delta)
            self.stream_done.emit(self._job_id)
        except Exception as exc:
            self.stream_error.emit(self._job_id, str(exc))


# Module-level settings singleton to avoid re-instantiation during GC
_settings: SmartPadSettings | None = None


def _get_settings() -> SmartPadSettings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


# ── Main panel ────────────────────────────────────────────────────────────────


class FloatingPanel(QWidget):
    """Frameless floating panel — the primary SmartPad UI surface."""

    def __init__(self, pool: WorkerPool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pool = pool
        self._settings = _get_settings()
        self._drag_pos: QPoint | None = None
        # job_id → ChatBubble (AI placeholder while streaming)
        self._pending_jobs: dict[str, ChatBubble] = {}
        self._chat_history: list[ChatMessage] = []

        self._build_window()
        self._build_ui()
        self._apply_geometry()
        self._setup_slash_menu()
        self._connect_pool()

        # Install event filter on application to detect click-outside
        QApplication.instance().installEventFilter(self)  # type: ignore[union-attr]

    # ── Window setup ──────────────────────────────────────────────────────────

    def _build_window(self) -> None:
        self.setObjectName("FloatingPanel")
        self.setWindowTitle("SmartPad")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            # No Tool flag — keeps it in taskbar and Alt+Tab
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(440, 540)

        # Subtle neutral shadow — no colour tint
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(shadow)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_chat_area(), stretch=1)
        root.addWidget(self._build_input_area())
        root.addWidget(self._build_status_bar())

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("PanelHeader")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(6)

        # Coloured dot logo
        dot = QLabel("●")
        dot.setObjectName("HeaderDot")

        title = QLabel("SmartPad")
        title.setObjectName("HeaderTitle")

        def _icon_btn(icon: str, tip: str) -> QPushButton:
            btn = QPushButton(icon)
            btn.setFixedSize(QSize(30, 30))
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            return btn

        browse_btn = _icon_btn("📋", "Notes & Tasks  (☰)")
        browse_btn.setObjectName("BrowseButton")
        browse_btn.clicked.connect(self._open_browse)

        settings_btn = _icon_btn("⚙", "Settings")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.clicked.connect(self._open_settings)

        close_btn = _icon_btn("✕", "Hide panel  (Esc)")
        close_btn.setObjectName("CloseButton")
        close_btn.clicked.connect(self.hide_panel)

        layout.addWidget(dot)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(browse_btn)
        layout.addWidget(settings_btn)
        layout.addWidget(close_btn)

        # Make the header draggable
        header.mousePressEvent = self._header_mouse_press  # type: ignore[method-assign]
        header.mouseMoveEvent = self._header_mouse_move  # type: ignore[method-assign]
        header.mouseReleaseEvent = self._header_mouse_release  # type: ignore[method-assign]

        return header

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        from smartpad.ui.settings_dialog import SettingsDialog  # noqa: PLC0415

        dlg = SettingsDialog(parent=self)
        dlg.exec()

    def _open_browse(self) -> None:
        """Open the browse window."""
        from smartpad.ui.browse_window import BrowseWindow  # noqa: PLC0415

        dlg = BrowseWindow(parent=self)
        dlg.exec()

    def _build_chat_area(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setObjectName("ChatScrollArea")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._chat_container = QWidget()
        self._chat_container.setObjectName("ChatContainer")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(0, 8, 0, 8)
        self._chat_layout.setSpacing(4)
        self._chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Spacer so bubbles hug top
        self._chat_layout.addStretch()

        self._scroll.setWidget(self._chat_container)
        return self._scroll

    def _build_input_area(self) -> QWidget:
        area = QWidget()

        outer = QVBoxLayout(area)
        outer.setContentsMargins(10, 6, 10, 8)
        outer.setSpacing(5)

        # Composer frame (focus ring is applied here via QSS property)
        self._composer_frame = QWidget()
        self._composer_frame.setObjectName("ComposerFrame")
        composer_layout = QHBoxLayout(self._composer_frame)
        composer_layout.setContentsMargins(10, 6, 6, 6)
        composer_layout.setSpacing(6)

        self._input = QTextEdit()
        self._input.setObjectName("MessageInput")
        self._input.setPlaceholderText("Ask anything… or type / for commands")
        self._input.setFixedHeight(62)
        self._input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._input.installEventFilter(self)

        send_btn = QPushButton("➤")
        send_btn.setObjectName("SendButton")
        send_btn.setFixedSize(QSize(30, 30))
        send_btn.setToolTip("Send  (Enter)")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._on_send)

        composer_layout.addWidget(self._input)
        composer_layout.addWidget(send_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        # Keyboard hint bar
        hint_bar = QWidget()
        hint_bar.setObjectName("ComposerHint")
        hint_layout = QHBoxLayout(hint_bar)
        hint_layout.setContentsMargins(2, 0, 2, 0)
        hint_layout.setSpacing(3)

        def _hint_pair(kbd: str, label: str) -> tuple:
            k = QLabel(kbd)
            k.setObjectName("HintKbd")
            t = QLabel(label)
            t.setObjectName("HintText")
            return k, t

        for kbd_text, lbl_text in [("↵ Enter", "send"), ("⇧ Shift+Enter", "new line"), ("/", "commands")]:
            k, t = _hint_pair(kbd_text, lbl_text)
            hint_layout.addWidget(k)
            hint_layout.addWidget(t)
        hint_layout.addStretch()

        outer.addWidget(self._composer_frame)
        outer.addWidget(hint_bar)
        return area

    def _build_status_bar(self) -> QLabel:
        self._status = QLabel("Ready")
        self._status.setObjectName("StatusBar")
        self._status.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return self._status

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _apply_geometry(self) -> None:
        s = self._settings
        w = max(s.panel_width, 460)
        h = max(s.panel_height, 560)

        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None

        # Compute the right-anchored default position
        if avail:
            default_x = avail.right() - w - 40
            default_y = avail.top() + 60
        else:
            default_x, default_y = 900, 60

        if s.panel_position_x == -1:
            x, y = default_x, default_y
        else:
            x, y = s.panel_position_x, s.panel_position_y

        # Clamp so the panel is always fully on screen
        if avail:
            x = max(avail.left() + 8, min(x, avail.right() - w - 8))
            y = max(avail.top() + 8, min(y, avail.bottom() - h - 8))
            # If only a sliver of the panel would be visible, reset to default
            if x + w < avail.left() + 100 or x > avail.right() - 100:
                x, y = default_x, default_y

        self.setGeometry(x, y, w, h)

    def _save_geometry(self) -> None:
        geo = self.geometry()
        self._settings.panel_position_x = geo.x()
        self._settings.panel_position_y = geo.y()
        self._settings.panel_width = geo.width()
        self._settings.panel_height = geo.height()
        try:
            self._settings.save()
        except Exception as exc:
            logger.warning("Could not save panel geometry: {}", exc)

    # ── Show / Hide with fade animation ───────────────────────────────────────

    def show_panel(self) -> None:
        """Show the panel with a smooth 180ms opacity fade."""
        if self.isVisible():
            self.activateWindow()
            self._input.setFocus()
            return

        # Stop any in-progress hide animation first
        if hasattr(self, "_hide_anim") and self._hide_anim.state() == QPropertyAnimation.State.Running:
            self._hide_anim.stop()

        self.setWindowOpacity(0.0)
        self.show()
        self._enable_acrylic_blur()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        self._show_anim = anim

    def hide_panel(self) -> None:
        """Hide the panel with a smooth 200ms opacity fade."""
        if not self.isVisible():
            return

        self._save_geometry()

        # Stop any in-progress hide animation
        if hasattr(self, "_hide_anim") and self._hide_anim.state() == QPropertyAnimation.State.Running:
            self._hide_anim.stop()

        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.finished.connect(self.hide)
        anim.start()
        self._hide_anim = anim

    @pyqtSlot()
    def toggle_panel(self) -> None:
        """Toggle show/hide (called from hotkey)."""
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel()

    def _enable_acrylic_blur(self) -> None:
        """Enable Windows 10/11 Acrylic blur behind the panel window."""
        import sys
        if sys.platform != "win32":
            return
        try:
            import ctypes
            import ctypes.wintypes

            class ACCENT_POLICY(ctypes.Structure):
                _fields_ = [
                    ("AccentState", ctypes.c_int),
                    ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_int),
                    ("AnimationId", ctypes.c_int),
                ]

            class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                _fields_ = [
                    ("Attribute", ctypes.c_int),
                    ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_size_t),
                ]

            accent = ACCENT_POLICY()
            accent.AccentState = 4  # ACCENT_ENABLE_ACRYLICBLURBEHIND
            accent.AccentFlags = 2
            accent.GradientColor = 0xBB12122a  # ABGR semi-transparent dark blue

            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19  # WCA_ACCENT_POLICY
            data.SizeOfData = ctypes.sizeof(accent)
            data.Data = ctypes.cast(ctypes.addressof(accent), ctypes.c_void_p)

            ctypes.windll.user32.SetWindowCompositionAttribute(  # type: ignore[attr-defined]
                int(self.winId()), ctypes.byref(data)
            )
            logger.debug("Acrylic blur enabled.")
        except Exception as exc:
            logger.debug("Acrylic blur not available: {}", exc)

    # ── Event handling ────────────────────────────────────────────────────────

    def paintEvent(self, event: Any) -> None:
        """Paint the panel background with anti-aliased rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()), 18.0, 18.0)
        painter.fillPath(path, QColor(22, 20, 34, 242))
        painter.end()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide_panel()
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj: Any, event: Any) -> bool:
        # Focus ring on the composer frame
        if obj is self._input:
            if event.type() == QEvent.Type.FocusIn:
                self._composer_frame.setProperty("focused", True)
                self._composer_frame.style().unpolish(self._composer_frame)
                self._composer_frame.style().polish(self._composer_frame)
            elif event.type() == QEvent.Type.FocusOut:
                self._composer_frame.setProperty("focused", False)
                self._composer_frame.style().unpolish(self._composer_frame)
                self._composer_frame.style().polish(self._composer_frame)

        if obj is self._input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            # Route arrow keys + Enter to slash menu when it's visible
            if self._slash_menu.isVisible():
                if key == Qt.Key.Key_Up:
                    self._slash_menu.move_selection(-1)
                    return True
                if key == Qt.Key.Key_Down:
                    self._slash_menu.move_selection(1)
                    return True
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (mods & Qt.KeyboardModifier.ShiftModifier):
                    self._slash_menu.accept_selection()
                    return True
                if key == Qt.Key.Key_Escape:
                    self._slash_menu.hide()
                    return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if mods & Qt.KeyboardModifier.ShiftModifier:
                    return False
                self._on_send()
                return True

        # Click outside the panel → hide
        if event.type() == QEvent.Type.MouseButtonPress and self.isVisible():
            try:
                gpos = event.globalPosition().toPoint()
                if not self.geometry().contains(gpos):
                    self.hide_panel()
            except AttributeError:
                pass  # event without globalPosition (e.g. tablet events)

        return False

    # ── Drag via header ───────────────────────────────────────────────────────

    def _header_mouse_press(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )

    def _header_mouse_move(self, event: Any) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _header_mouse_release(self, event: Any) -> None:
        self._drag_pos = None

    # ── Slash menu ────────────────────────────────────────────────────────────

    def _setup_slash_menu(self) -> None:
        self._slash_menu = SlashMenu(parent=self)
        self._slash_menu.command_selected.connect(self._on_slash_selected)
        self._slash_menu.dismissed.connect(self._slash_menu.hide)
        self._input.textChanged.connect(self._update_slash_menu)

    def _update_slash_menu(self) -> None:
        text = self._input.toPlainText()
        # Show menu only while typing the command (no space yet = still typing command word)
        if text.startswith("/") and " " not in text:
            self._slash_menu.update_filter(text.strip())
            self._position_slash_menu()
        else:
            self._slash_menu.hide()

    def _position_slash_menu(self) -> None:
        # Place the menu above the input field, inside the panel
        input_pos = self._input.mapTo(self, QPoint(0, 0))
        menu_h = min(self._slash_menu.sizeHint().height(), 260)
        menu_w = self._input.width()
        x = input_pos.x()
        y = input_pos.y() - menu_h - 6
        self._slash_menu.setGeometry(x, y, menu_w, menu_h)
        self._slash_menu.raise_()

    def _on_slash_selected(self, command: str) -> None:
        # Put the selected command in the input with a trailing space so user types content
        self._input.setPlainText(command + " ")
        cursor = self._input.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._input.setTextCursor(cursor)
        self._slash_menu.hide()
        self._input.setFocus()

    # ── Send / routing ────────────────────────────────────────────────────────

    @pyqtSlot()
    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            return

        self._input.clear()

        # Show user bubble immediately (optimistic UI)
        self._add_widget(ChatBubble(role="user", text=text))

        # Route the text
        result = route(text)
        logger.debug("Route result: {} → {}", text[:40], result.action)

        match result.action:
            case ActionKind.CHAT:
                self._chat_history.append(ChatMessage(role="user", content=result.body))
                self._start_chat(result.body)
            case ActionKind.SAVE_NOTE:
                note = NoteBubble(
                    content=result.body,
                    original_content=result.body,
                )
                note.set_status("saved")
                self._add_widget(note)
                self._set_status("Note saved")
                self._save_note_to_db(result.body)
            case ActionKind.SAVE_TASK:
                task = TaskBubble(
                    task_id=str(uuid.uuid4()),
                    content=result.body,
                )
                task.set_status("saved")
                self._add_widget(task)
                self._set_status("Task saved")
                self._save_task_to_db(result.body)
            case ActionKind.SAVE_REMINDER:
                reminder = ReminderBubble(content=result.body)
                reminder.set_status("saved")
                self._add_widget(reminder)
                self._set_status("Reminder set")
                self._save_reminder_to_db(result.body)
            case ActionKind.SAVE_SNIPPET:
                snippet = SnippetBubble(content=result.body)
                snippet.set_status("saved")
                self._add_widget(snippet)
                self._set_status("Snippet saved")
                self._save_snippet_to_db(result.body)
            case ActionKind.APP_COMMAND:
                app_action = result.metadata.get("app_action", "")
                if app_action == "settings":
                    self._open_settings()
                elif app_action in ("browse", "notes", "snippets"):
                    self._open_browse()
                else:
                    self._add_widget(
                        ChatBubble(
                            role="assistant",
                            text=f"/{app_action} — use the buttons in the header.",
                        )
                    )
            case ActionKind.QUERY_DB:
                ai_bubble = ChatBubble(
                    role="assistant",
                    text="Personal-data queries not yet connected to DB.",
                )
                ai_bubble.set_status("saved")
                self._add_widget(ai_bubble)
            case ActionKind.CALCULATOR:
                ai_bubble = ChatBubble(role="assistant", text=f"Calc: {result.body}")
                ai_bubble.set_status("saved")
                self._add_widget(ai_bubble)
            case _:
                self._chat_history.append(ChatMessage(role="user", content=result.body))
                self._start_chat(result.body)

    def _start_chat(self, text: str) -> None:
        """Stream LLM response via a dedicated QThread (true per-token streaming)."""
        provider = self._get_provider()
        if provider is None:
            self._add_widget(ErrorBubble(
                message=(
                    "No provider configured. Open Settings (⚙) to add an API key."
                )
            ))
            self._set_status("No provider configured")
            return

        ai_bubble = ChatBubble(role="assistant", text="", streaming=True)
        self._add_widget(ai_bubble)
        self._set_status("Thinking…")

        messages = [ChatMessage(role="system", content=_SYSTEM_PROMPT)] + list(self._chat_history)
        job_id = str(uuid.uuid4())
        self._pending_jobs[job_id] = ai_bubble

        thread = _ChatThread(
            job_id=job_id,
            provider=provider,
            messages=messages,
            model=self._resolve_model(),
            temperature=self._settings.chat_temperature,
            parent=self,
        )
        thread.chunk_ready.connect(self._on_chunk)
        thread.stream_done.connect(self._on_stream_done)
        thread.stream_error.connect(self._on_stream_error)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _resolve_model(self) -> str:
        """Return the right model name based on the active provider."""
        import keyring  # noqa: PLC0415
        _SVC = "smartpad"
        def _kr(k: str) -> str:
            try:
                return keyring.get_password(_SVC, k) or ""
            except Exception:
                return ""
        preferred = _kr("preferred_provider")
        if preferred == "anthropic":
            return _kr("anthropic_model") or os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
        if preferred == "google":
            return _kr("google_model") or os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash")
        if preferred == "local":
            return _kr("local_model") or os.environ.get("LOCAL_MODEL", "llama3.2:3b")
        # openai / openai_compatible / auto
        return (
            _kr("openai_model")
            or os.environ.get("SMARTPAD_OPENAI_MODEL", "")
            or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        )

    def _get_provider(self) -> Any:
        """Instantiate an AI provider, checking keyring first then env vars."""
        import keyring  # noqa: PLC0415

        _SVC = "smartpad"

        def _kr(key: str) -> str:
            """Read from keyring, returning '' on any error (incl. no backend)."""
            try:
                return keyring.get_password(_SVC, key) or ""
            except Exception:
                return ""

        # Check which keys are available (keyring first, then env vars)
        anthropic_key = _kr("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        openai_key = _kr("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
        openai_url = (
            _kr("openai_base_url")
            or os.environ.get("OPENAI_BASE_URL", "")
            or os.environ.get("SMARTPAD_OPENAI_BASE_URL", "")
        )
        google_key = _kr("google_api_key") or os.environ.get("GOOGLE_API_KEY", "")
        local_url = _kr("local_server_url") or os.environ.get("LOCAL_SERVER_URL", "")
        preferred = _kr("preferred_provider")

        # Honor explicit preference first
        if preferred == "anthropic" and anthropic_key:
            from smartpad.providers.anthropic import AnthropicProvider  # noqa: PLC0415

            return AnthropicProvider(api_key=anthropic_key)
        if preferred == "google" and google_key:
            from smartpad.providers.google import GoogleProvider  # noqa: PLC0415

            return GoogleProvider(api_key=google_key)
        if preferred in ("openai", "openai_compatible") and (openai_key or openai_url):
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=openai_url or "https://api.openai.com/v1",
                api_key=openai_key or None,
                name="openai",
            )
        if preferred == "local" and local_url:
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=local_url, api_key=None, name="local"
            )

        # Fall back: first available key wins
        if anthropic_key:
            from smartpad.providers.anthropic import AnthropicProvider  # noqa: PLC0415

            return AnthropicProvider(api_key=anthropic_key)
        if openai_key or openai_url:
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=openai_url or "https://api.openai.com/v1",
                api_key=openai_key or None,
                name="openai",
            )
        if google_key:
            from smartpad.providers.google import GoogleProvider  # noqa: PLC0415

            return GoogleProvider(api_key=google_key)
        if local_url:
            from smartpad.providers.openai_compatible import (
                OpenAICompatibleProvider,  # noqa: PLC0415
            )

            return OpenAICompatibleProvider(
                base_url=local_url, api_key=None, name="local"
            )
        return None

    # ── DB save helpers (fire-and-forget background threads) ──────────────────

    def _save_note_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Note  # noqa: PLC0415
                from smartpad.db.repositories.notes import NotesRepo  # noqa: PLC0415

                async with get_async_session() as s:
                    await NotesRepo(s).save(
                        Note(
                            id=str(_uuid.uuid4()),
                            content=content,
                            original_content=content,
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB note save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    def _save_task_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Task  # noqa: PLC0415
                from smartpad.db.repositories.tasks import TasksRepo  # noqa: PLC0415

                async with get_async_session() as s:
                    await TasksRepo(s).save(
                        Task(
                            id=str(_uuid.uuid4()),
                            content=content,
                            status="todo",
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB task save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    def _save_reminder_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime, timedelta  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Reminder  # noqa: PLC0415
                from smartpad.db.repositories.reminders import RemindersRepo  # noqa: PLC0415

                # Try to parse a time from the content; fall back to 1 hour from now
                trigger_at: datetime | None = None
                try:
                    import dateparser  # noqa: PLC0415

                    parsed = dateparser.parse(content, settings={"PREFER_DATES_FROM": "future"})
                    if parsed is not None:
                        trigger_at = parsed.astimezone(UTC)
                except Exception:
                    pass
                if trigger_at is None:
                    trigger_at = datetime.now(UTC) + timedelta(hours=1)

                async with get_async_session() as s:
                    await RemindersRepo(s).save(
                        Reminder(
                            id=str(_uuid.uuid4()),
                            content=content,
                            trigger_at=trigger_at,
                            notified=False,
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB reminder save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    def _save_snippet_to_db(self, content: str) -> None:
        import asyncio  # noqa: PLC0415
        import threading  # noqa: PLC0415

        async def _do() -> None:
            try:
                import uuid as _uuid  # noqa: PLC0415
                from datetime import UTC, datetime  # noqa: PLC0415

                from smartpad.db.engine import get_async_session  # noqa: PLC0415
                from smartpad.db.models import Snippet  # noqa: PLC0415
                from smartpad.db.repositories.snippets import SnippetsRepo  # noqa: PLC0415

                async with get_async_session() as s:
                    await SnippetsRepo(s).save(
                        Snippet(
                            id=str(_uuid.uuid4()),
                            content=content,
                            created_at=datetime.now(UTC),
                            sync_version=0,
                        )
                    )
            except Exception as exc:
                logger.error("DB snippet save failed: {}", exc)

        threading.Thread(target=lambda: asyncio.run(_do()), daemon=True).start()

    # ── Worker pool callbacks (used for non-chat jobs) ────────────────────────

    def _connect_pool(self) -> None:
        self._pool.result_ready.connect(self._on_job_result)
        self._pool.error_occurred.connect(self._on_job_error)

    @pyqtSlot(str, object)
    def _on_job_result(self, job_id: str, result: Any) -> None:
        bubble = self._pending_jobs.pop(job_id, None)
        if bubble is not None:
            bubble.finish_streaming()
        self._set_status("Ready")

    @pyqtSlot(str, object)
    def _on_job_error(self, job_id: str, exc: Any) -> None:
        pending_bubble = self._pending_jobs.pop(job_id, None)
        if pending_bubble is not None:
            idx = self._chat_layout.indexOf(pending_bubble)
            if idx >= 0:
                self._chat_layout.removeWidget(pending_bubble)
                pending_bubble.deleteLater()
        self._add_widget(ErrorBubble(message=f"Error: {exc}"))
        self._set_status("Error")
        logger.error("Worker job {} failed: {}", job_id, exc)

    # ── Chat streaming callbacks (_ChatThread) ────────────────────────────────

    @pyqtSlot(str, str)
    def _on_chunk(self, job_id: str, delta: str) -> None:
        bubble = self._pending_jobs.get(job_id)
        if bubble is not None and delta:
            bubble.append_text(delta)
            self._scroll_to_bottom()

    @pyqtSlot(str)
    def _on_stream_done(self, job_id: str) -> None:
        bubble = self._pending_jobs.pop(job_id, None)
        if bubble is not None:
            full_text = bubble.text
            bubble.finish_streaming()
            self._chat_history.append(ChatMessage(role="assistant", content=full_text))
        self._set_status("Ready")
        self._scroll_to_bottom()

    @pyqtSlot(str, str)
    def _on_stream_error(self, job_id: str, message: str) -> None:
        pending_bubble = self._pending_jobs.pop(job_id, None)
        if pending_bubble is not None:
            idx = self._chat_layout.indexOf(pending_bubble)
            if idx >= 0:
                self._chat_layout.removeWidget(pending_bubble)
                pending_bubble.deleteLater()
        self._add_widget(ErrorBubble(message=f"Error: {message}"))
        self._set_status("Error")
        logger.error("Stream error for job {}: {}", job_id, message)

    # ── Bubble helpers ────────────────────────────────────────────────────────

    def _add_widget(self, widget: QWidget) -> QWidget:
        """Insert a bubble widget before the trailing stretch.

        Args:
            widget: Any QWidget (typically a bubble subclass).

        Returns:
            The same widget for chaining.
        """
        count = self._chat_layout.count()
        self._chat_layout.insertWidget(count - 1, widget)
        QTimer.singleShot(0, self._scroll_to_bottom)
        return widget

    # Legacy helper kept for backward-compat with existing tests that call
    # _add_bubble() directly.
    def _add_bubble(
        self,
        text: str,
        object_name: str,
        align_right: bool = False,
    ) -> ChatBubble:
        """Backward-compatible wrapper — creates a ChatBubble.

        Args:
            text: Message text.
            object_name: QSS object name (used to guess role).
            align_right: If ``True``, use ``role='user'`` (right-aligned).

        Returns:
            The created ChatBubble.
        """
        role = "user" if align_right or object_name == "BubbleUser" else "assistant"
        bubble = ChatBubble(role=role, text=text)
        self._add_widget(bubble)
        return bubble

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _set_status(self, text: str) -> None:
        self._status.setText(text)
