"""Tests for Phase 07 bubble widgets.

Runs with QT_QPA_PLATFORM=offscreen (set in conftest.py).

Coverage:
- BubbleBase: status dot colour transitions
- ChatBubble: creation, set_content, finish_streaming, 80% width user bubble
- NoteBubble: creation, bg style, pinned indicator
- TaskBubble: creation, mark_done signal, done=True strike-through
- ReminderBubble: creation, time pill text
- SnippetBubble: creation, copy button, clipboard, language pill
- ErrorBubble: creation, retry button, retry_requested signal
"""

from __future__ import annotations

import sys

import pytest


# ---------------------------------------------------------------------------
# Session fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp_instance():
    """Single QApplication for the whole session."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# ---------------------------------------------------------------------------
# BubbleBase
# ---------------------------------------------------------------------------


class TestBubbleBase:
    def test_creates_without_crash(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.base import BubbleBase

        bubble = BubbleBase()
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_default_status_is_saving(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.base import BubbleBase

        bubble = BubbleBase()
        qtbot.addWidget(bubble)
        assert bubble.status == "saving"

    def test_set_status_saved(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.base import BubbleBase

        bubble = BubbleBase()
        qtbot.addWidget(bubble)
        bubble.set_status("saved")
        assert bubble.status == "saved"

    def test_set_status_error(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.base import BubbleBase

        bubble = BubbleBase()
        qtbot.addWidget(bubble)
        bubble.set_status("error")
        assert bubble.status == "error"

    def test_invalid_status_ignored(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.base import BubbleBase

        bubble = BubbleBase()
        qtbot.addWidget(bubble)
        bubble.set_status("unknown")
        assert bubble.status == "saving"  # unchanged

    def test_has_created_at(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.base import BubbleBase

        bubble = BubbleBase()
        qtbot.addWidget(bubble)
        assert bubble.created_at is not None


# ---------------------------------------------------------------------------
# ChatBubble
# ---------------------------------------------------------------------------


class TestChatBubble:
    def test_user_bubble_creates(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="user", text="Hello")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_ai_bubble_creates(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="Hi there")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_user_bubble_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="user", text="Hello")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleUser"

    def test_ai_bubble_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="Hello")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleAI"

    def test_set_content_updates_label(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="initial")
        qtbot.addWidget(bubble)
        bubble.set_content("updated text")
        assert bubble._label.text() == "updated text"

    def test_streaming_shows_cursor(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="Hello", streaming=True)
        qtbot.addWidget(bubble)
        assert bubble._streaming is True
        assert bubble._blink_timer.isActive()

    def test_finish_streaming_removes_cursor(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="Hello", streaming=True)
        qtbot.addWidget(bubble)
        bubble.finish_streaming()
        assert not bubble._streaming
        assert not bubble._blink_timer.isActive()
        assert bubble._label.text() == "Hello"

    def test_finish_streaming_sets_status_saved(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="Hello", streaming=True)
        qtbot.addWidget(bubble)
        bubble.finish_streaming()
        assert bubble.status == "saved"

    def test_append_text(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="assistant", text="Hello")
        qtbot.addWidget(bubble)
        bubble.append_text(" world")
        assert "Hello world" in bubble._label.text()

    def test_user_bubble_has_status_dot(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.chat_bubble import ChatBubble

        bubble = ChatBubble(role="user", text="Hi")
        qtbot.addWidget(bubble)
        assert bubble._dot is not None


# ---------------------------------------------------------------------------
# NoteBubble
# ---------------------------------------------------------------------------


class TestNoteBubble:
    def test_creates_without_crash(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="A note", original_content="original")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_bg_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="A note")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleNote"

    def test_content_label_italic(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="italic text")
        qtbot.addWidget(bubble)
        assert bubble._content_label.font().italic()

    def test_pin_indicator_hidden_when_not_pinned(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="note", pinned=False)
        qtbot.addWidget(bubble)
        # isHidden() is always reliable regardless of whether parent is shown
        assert bubble._pin_label.isHidden()

    def test_pin_indicator_visible_when_pinned(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="note", pinned=True)
        qtbot.addWidget(bubble)
        assert not bubble._pin_label.isHidden()

    def test_set_pinned(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="note", pinned=False)
        qtbot.addWidget(bubble)
        bubble.set_pinned(True)
        assert not bubble._pin_label.isHidden()

    def test_set_content(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="original")
        qtbot.addWidget(bubble)
        bubble.set_content("updated")
        assert bubble._content_label.text() == "updated"

    def test_has_status_dot(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble()
        qtbot.addWidget(bubble)
        assert bubble._dot is not None

    def test_has_note_emoji(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.note_bubble import NoteBubble

        bubble = NoteBubble(content="test")
        qtbot.addWidget(bubble)
        assert "📝" in bubble._icon_label.text()


# ---------------------------------------------------------------------------
# TaskBubble
# ---------------------------------------------------------------------------


class TestTaskBubble:
    def test_creates_without_crash(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(task_id="abc", content="Do something")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_bg_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(content="task")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleTask"

    def test_has_mark_done_signal(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(task_id="tid", content="task")
        qtbot.addWidget(bubble)
        assert hasattr(bubble, "mark_done")

    def test_checkbox_click_emits_mark_done(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(task_id="my-task-id", content="task", done=False)
        qtbot.addWidget(bubble)

        received: list[str] = []
        bubble.mark_done.connect(lambda tid: received.append(tid))

        # Simulate checking the checkbox
        bubble._checkbox.setChecked(True)

        assert "my-task-id" in received

    def test_done_true_strike_through(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(task_id="t", content="Done task", done=True)
        qtbot.addWidget(bubble)
        assert bubble._content_label.font().strikeOut()

    def test_done_false_no_strike_through(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(task_id="t", content="Active task", done=False)
        qtbot.addWidget(bubble)
        assert not bubble._content_label.font().strikeOut()

    def test_deadline_pill_hidden_when_no_deadline(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(content="task", deadline=None)
        qtbot.addWidget(bubble)
        assert not bubble._deadline_pill.isVisible()

    def test_deadline_pill_visible_when_set(self, qapp_instance, qtbot) -> None:
        from datetime import datetime, timezone

        from smartpad.ui.bubbles.task_bubble import TaskBubble

        dl = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)
        bubble = TaskBubble(content="task", deadline=dl)
        qtbot.addWidget(bubble)
        bubble.show()
        assert bubble._deadline_pill.isVisible()
        assert "Jun" in bubble._deadline_pill.text()

    def test_set_done(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.task_bubble import TaskBubble

        bubble = TaskBubble(task_id="t", content="task", done=False)
        qtbot.addWidget(bubble)
        bubble.set_done(True)
        assert bubble._done is True
        assert bubble._content_label.font().strikeOut()


# ---------------------------------------------------------------------------
# ReminderBubble
# ---------------------------------------------------------------------------


class TestReminderBubble:
    def test_creates_without_crash(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        bubble = ReminderBubble(content="Call dentist")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_bg_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        bubble = ReminderBubble(content="reminder")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleReminder"

    def test_has_clock_icon(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        bubble = ReminderBubble(content="test")
        qtbot.addWidget(bubble)
        assert "⏰" in bubble._icon_label.text()

    def test_time_pill_future(self, qapp_instance, qtbot) -> None:
        from datetime import datetime, timedelta, timezone

        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        future = datetime.now(timezone.utc) + timedelta(minutes=30)
        bubble = ReminderBubble(content="meeting", trigger_at=future)
        qtbot.addWidget(bubble)
        text = bubble._time_pill.text()
        assert "in" in text and "min" in text

    def test_time_pill_notified(self, qapp_instance, qtbot) -> None:
        from datetime import datetime, timedelta, timezone

        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        bubble = ReminderBubble(content="done", trigger_at=past, notified=True)
        qtbot.addWidget(bubble)
        assert "Reminded" in bubble._time_pill.text()

    def test_set_notified(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        bubble = ReminderBubble(content="test", notified=False)
        qtbot.addWidget(bubble)
        bubble.set_notified(True)
        assert "Reminded" in bubble._time_pill.text()

    def test_has_status_dot(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.reminder_bubble import ReminderBubble

        bubble = ReminderBubble()
        qtbot.addWidget(bubble)
        assert bubble._dot is not None


# ---------------------------------------------------------------------------
# SnippetBubble
# ---------------------------------------------------------------------------


class TestSnippetBubble:
    def test_creates_without_crash(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="print('hello')", language="python")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_bg_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="code")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleSnippet"

    def test_language_pill_visible(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="x = 1", language="python")
        qtbot.addWidget(bubble)
        bubble.show()
        assert bubble._lang_pill.isVisible()
        assert bubble._lang_pill.text() == "python"

    def test_language_pill_hidden_when_no_language(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="some code")
        qtbot.addWidget(bubble)
        bubble.show()
        assert not bubble._lang_pill.isVisible()

    def test_copy_button_exists(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="code")
        qtbot.addWidget(bubble)
        assert bubble._copy_btn is not None
        assert "📋" in bubble._copy_btn.text()

    def test_copy_button_copies_to_clipboard(self, qapp_instance, qtbot) -> None:
        from PyQt6.QtWidgets import QApplication

        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        code = "import os\nprint(os.getcwd())"
        bubble = SnippetBubble(content=code)
        qtbot.addWidget(bubble)

        bubble._copy_btn.click()

        clipboard = QApplication.clipboard()
        assert clipboard is not None
        assert clipboard.text() == code

    def test_copy_button_shows_copied_text(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="some code")
        qtbot.addWidget(bubble)
        bubble._copy_btn.click()
        assert "Copied" in bubble._copy_btn.text()

    def test_has_status_dot(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.snippet_bubble import SnippetBubble

        bubble = SnippetBubble(content="code")
        qtbot.addWidget(bubble)
        assert bubble._dot is not None


# ---------------------------------------------------------------------------
# ErrorBubble
# ---------------------------------------------------------------------------


class TestErrorBubble:
    def test_creates_without_crash(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="Something went wrong")
        qtbot.addWidget(bubble)
        assert bubble is not None

    def test_bg_object_name(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="error")
        qtbot.addWidget(bubble)
        assert bubble._bubble_frame.objectName() == "BubbleError"

    def test_has_warning_icon(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="oops")
        qtbot.addWidget(bubble)
        assert "⚠" in bubble._icon_label.text()

    def test_has_retry_signal(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="error")
        qtbot.addWidget(bubble)
        assert hasattr(bubble, "retry_requested")

    def test_retry_button_emits_signal(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="failed")
        qtbot.addWidget(bubble)

        received: list[bool] = []
        bubble.retry_requested.connect(lambda: received.append(True))

        bubble._retry_btn.click()
        assert received == [True]

    def test_status_is_error(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="error")
        qtbot.addWidget(bubble)
        assert bubble.status == "error"

    def test_message_label_shows_text(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.bubbles.error_bubble import ErrorBubble

        bubble = ErrorBubble(message="Connection refused")
        qtbot.addWidget(bubble)
        assert "Connection refused" in bubble._message_label.text()


# ---------------------------------------------------------------------------
# __init__ exports
# ---------------------------------------------------------------------------


class TestBubblesPackageExports:
    def test_all_classes_importable(self) -> None:
        from smartpad.ui.bubbles import (
            BubbleBase,
            ChatBubble,
            ErrorBubble,
            NoteBubble,
            ReminderBubble,
            SnippetBubble,
            TaskBubble,
        )

        for cls in (
            BubbleBase,
            ChatBubble,
            ErrorBubble,
            NoteBubble,
            ReminderBubble,
            SnippetBubble,
            TaskBubble,
        ):
            assert cls is not None

    def test_all_in_dunder_all(self) -> None:
        import smartpad.ui.bubbles as pkg

        for name in (
            "BubbleBase",
            "ChatBubble",
            "ErrorBubble",
            "NoteBubble",
            "ReminderBubble",
            "SnippetBubble",
            "TaskBubble",
        ):
            assert name in pkg.__all__


# ---------------------------------------------------------------------------
# format_trigger helper (ReminderBubble)
# ---------------------------------------------------------------------------


class TestFormatTrigger:
    def test_notified_returns_reminded(self) -> None:
        from smartpad.ui.bubbles.reminder_bubble import _format_trigger

        assert _format_trigger(None, notified=True) == "✓ Reminded"

    def test_none_trigger_at(self) -> None:
        from smartpad.ui.bubbles.reminder_bubble import _format_trigger

        result = _format_trigger(None, notified=False)
        assert result == "—"

    def test_future_in_minutes(self) -> None:
        from datetime import datetime, timedelta, timezone

        from smartpad.ui.bubbles.reminder_bubble import _format_trigger

        future = datetime.now(timezone.utc) + timedelta(minutes=45)
        result = _format_trigger(future, notified=False)
        assert "in" in result and "min" in result

    def test_past_shows_date(self) -> None:
        from datetime import datetime, timedelta, timezone

        from smartpad.ui.bubbles.reminder_bubble import _format_trigger

        past = datetime.now(timezone.utc) - timedelta(hours=2)
        result = _format_trigger(past, notified=False)
        # Should be an absolute time string
        assert ":" in result  # HH:MM
