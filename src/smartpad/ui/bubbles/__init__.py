"""Bubble widget package — all visual bubble types for SmartPad.

Exports:
    BubbleBase       — common base (status dot, margins, created_at)
    ChatBubble       — user / AI chat messages
    NoteBubble       — saved notes
    TaskBubble       — saved tasks with checkbox
    ReminderBubble   — saved reminders with time pill
    SnippetBubble    — code snippets with copy button
    ErrorBubble      — error display with retry button
"""

from smartpad.ui.bubbles.base import BubbleBase
from smartpad.ui.bubbles.chat_bubble import ChatBubble
from smartpad.ui.bubbles.error_bubble import ErrorBubble
from smartpad.ui.bubbles.note_bubble import NoteBubble
from smartpad.ui.bubbles.reminder_bubble import ReminderBubble
from smartpad.ui.bubbles.snippet_bubble import SnippetBubble
from smartpad.ui.bubbles.task_bubble import TaskBubble

__all__ = [
    "BubbleBase",
    "ChatBubble",
    "ErrorBubble",
    "NoteBubble",
    "ReminderBubble",
    "SnippetBubble",
    "TaskBubble",
]
