"""TaskBubble — displays a saved task.

Visual:
- Full-width, blue tint background (BubbleTask QSS ID)
- QCheckBox on the left
- Content text (strike-through when done=True)
- Deadline pill (small rounded label) if deadline is set
- Clicking the checkbox emits mark_done(task_id) signal

Status dot: top-right corner (saving -> saved -> error).
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from smartpad.ui.bubbles.base import BubbleBase


class TaskBubble(BubbleBase):
    """A saved-task bubble with a checkbox and optional deadline.

    Signals:
        mark_done(str): Emitted when the checkbox is toggled; carries task_id.

    Args:
        task_id: Unique identifier for the task (UUID string).
        content: The task description text.
        done: Initial done state.
        deadline: Optional datetime for the deadline pill.
        parent: Optional parent widget.
    """

    mark_done = pyqtSignal(str)

    def __init__(
        self,
        task_id: str = "",
        content: str = "",
        done: bool = False,
        deadline: datetime | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._task_id = task_id
        self._content = content
        self._done = done
        self._deadline = deadline

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self._bubble_frame = QWidget(self._content_widget)
        self._bubble_frame.setObjectName("BubbleTask")
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        frame_layout = QHBoxLayout(self._bubble_frame)
        frame_layout.setContentsMargins(12, 8, 12, 8)
        frame_layout.setSpacing(8)

        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._done)
        self._checkbox.stateChanged.connect(self._on_checkbox_changed)  # type: ignore[attr-defined]
        frame_layout.addWidget(self._checkbox)

        self._content_label = QLabel()
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        frame_layout.addWidget(self._content_label)

        self._deadline_pill = QLabel()
        self._deadline_pill.setObjectName("DeadlinePill")
        self._deadline_pill.setVisible(False)
        self._deadline_pill.setStyleSheet(
            "background-color: rgba(137,180,250,0.25);"
            "color: #89b4fa;"
            "border-radius: 8px;"
            "padding: 2px 8px;"
            "font-size: 11px;"
        )
        frame_layout.addWidget(self._deadline_pill)

        self._content_layout.addWidget(self._bubble_frame)

    def set_done(self, done: bool) -> None:
        """Update the done state without emitting a signal.

        Args:
            done: New done state.
        """
        self._done = done
        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(done)
        self._checkbox.blockSignals(False)
        self._refresh()

    def _on_checkbox_changed(self, state: int) -> None:
        self._done = bool(state)
        self._refresh()
        if self._task_id:
            self.mark_done.emit(self._task_id)

    def _refresh(self) -> None:
        font = self._content_label.font()
        font.setStrikeOut(self._done)
        self._content_label.setFont(font)
        self._content_label.setText(self._content)

        if self._deadline is not None:
            try:
                pill_text = self._deadline.strftime("%b %d, %H:%M")
            except Exception:  # noqa: BLE001
                pill_text = str(self._deadline)
            self._deadline_pill.setText(pill_text)
            self._deadline_pill.setVisible(True)
        else:
            self._deadline_pill.setVisible(False)
