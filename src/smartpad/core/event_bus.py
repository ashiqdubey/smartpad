"""Tiny app-wide event bus for cross-window UI signals.

Qt signals are routed through the running event loop, so any QObject
listening on the same singleton instance receives the event regardless
of which window/widget emitted it.

Used to push DB-save notifications from the floating panel to the
browse window (and any other view) so they can refresh in real time
without polling.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class _EventBus(QObject):
    note_saved = pyqtSignal()
    task_saved = pyqtSignal()
    reminder_saved = pyqtSignal()
    snippet_saved = pyqtSignal()
    item_saved = pyqtSignal(str)  # generic — fires after any of the above (kind name)


_bus: _EventBus | None = None


def event_bus() -> _EventBus:
    global _bus
    if _bus is None:
        _bus = _EventBus()
    return _bus
