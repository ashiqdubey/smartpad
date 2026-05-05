"""Custom UI primitives — gradient logo, iOS-style toggle, segmented control, hour slider.

Designed to match the Aside design system (violet-purple accent, fluid modern feel).
All widgets use QPainter for crisp rendering — they don't rely on QSS for the
non-rectangular shapes that QSS can't handle.
"""
from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget


# Aside colour palette — keep in sync with styles.py
ACCENT = QColor("#7c6ef5")
ACCENT_2 = QColor("#c87ec8")
ACCENT_GLOW = QColor(124, 110, 245, 115)
WHITE_INSET = QColor(255, 255, 255, 217)
TEXT_DIM = QColor(246, 246, 250, 158)
TEXT = QColor(246, 246, 250, 235)
SURFACE = QColor(246, 246, 250, 13)
SURFACE_STRONG = QColor(246, 246, 250, 26)
STROKE = QColor(240, 240, 248, 31)
STROKE_STRONG = QColor(240, 240, 248, 51)


class LogoMark(QWidget):
    """Aside brand mark — gradient rounded square with white inset square.

    Sizes: pass a side length; the inner square scales proportionally.
    """

    def __init__(self, size: int = 22, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(QSize(size, size))

    def paintEvent(self, event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(self._size)
        radius = s * 0.32

        # Gradient fill: 135° from accent → accent-2
        grad = QLinearGradient(0.0, 0.0, s, s)
        grad.setColorAt(0.0, ACCENT)
        grad.setColorAt(1.0, ACCENT_2)

        outer = QPainterPath()
        outer.addRoundedRect(0.0, 0.0, s, s, radius, radius)
        p.fillPath(outer, QBrush(grad))

        # Inner highlight (1px inset white-ish stroke)
        p.setPen(QPen(QColor(255, 255, 255, 51), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, s - 1.0, s - 1.0), radius - 0.5, radius - 0.5)

        # White inner rounded square
        inset = s * 0.27
        inner_size = s - inset * 2
        inner_radius = inner_size * 0.30
        inner_path = QPainterPath()
        inner_path.addRoundedRect(inset, inset, inner_size, inner_size, inner_radius, inner_radius)
        p.fillPath(inner_path, WHITE_INSET)

        p.end()


class ToggleSwitch(QWidget):
    """iOS-style toggle: pill background + sliding circle thumb. Animated."""

    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self._thumb_pos = 1.0 if checked else 0.0  # animatable 0..1
        self.setFixedSize(QSize(44, 24))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"thumbPos", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def isChecked(self) -> bool:  # noqa: N802 (Qt camelCase)
        return self._checked

    def setChecked(self, value: bool) -> None:  # noqa: N802
        if value == self._checked:
            return
        self._checked = value
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(1.0 if value else 0.0)
        self._anim.start()
        self.toggled.emit(value)

    @pyqtProperty(float)
    def thumbPos(self) -> float:  # noqa: N802
        return self._thumb_pos

    @thumbPos.setter  # type: ignore[no-redef]
    def thumbPos(self, value: float) -> None:  # noqa: N802
        self._thumb_pos = max(0.0, min(1.0, value))
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        radius = h / 2.0

        # Track
        off_color = QColor(246, 246, 250, 38)
        on_color = ACCENT
        # Blend
        t = self._thumb_pos
        track = QColor(
            int(off_color.red() * (1 - t) + on_color.red() * t),
            int(off_color.green() * (1 - t) + on_color.green() * t),
            int(off_color.blue() * (1 - t) + on_color.blue() * t),
            int(off_color.alpha() * (1 - t) + on_color.alpha() * t),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # Thumb
        thumb_d = h - 4.0
        x_min, x_max = 2.0, w - thumb_d - 2.0
        thumb_x = x_min + (x_max - x_min) * self._thumb_pos
        thumb_rect = QRectF(thumb_x, 2.0, thumb_d, thumb_d)
        # Subtle thumb shadow
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(thumb_rect.translated(0, 1))
        p.setBrush(QColor(255, 255, 255, 245))
        p.drawEllipse(thumb_rect)

        p.end()


class SegmentedControl(QWidget):
    """Segmented picker with sliding white thumb under the active label."""

    valueChanged = pyqtSignal(int)

    def __init__(self, options: list[str], index: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._options = list(options)
        self._index = max(0, min(len(options) - 1, index))
        self._thumb_pos = float(self._index)  # animatable
        self.setMinimumHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"thumbPos", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def value(self) -> int:
        return self._index

    def setValue(self, idx: int) -> None:  # noqa: N802
        idx = max(0, min(len(self._options) - 1, idx))
        if idx == self._index:
            return
        self._index = idx
        self._anim.stop()
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(float(idx))
        self._anim.start()
        self.valueChanged.emit(idx)

    @pyqtProperty(float)
    def thumbPos(self) -> float:  # noqa: N802
        return self._thumb_pos

    @thumbPos.setter  # type: ignore[no-redef]
    def thumbPos(self, value: float) -> None:  # noqa: N802
        self._thumb_pos = value
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._options:
            seg_w = self.width() / len(self._options)
            idx = int(event.position().x() // seg_w)
            self.setValue(idx)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(max(280, len(self._options) * 70), 30)

    def paintEvent(self, event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        n = len(self._options)
        if n == 0:
            return
        radius = 8.0

        # Track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(246, 246, 250, 18))
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)
        # Hairline border
        p.setPen(QPen(STROKE, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), radius - 0.5, radius - 0.5)

        # Sliding thumb
        seg_w = (w - 4.0) / n
        thumb_x = 2.0 + seg_w * self._thumb_pos
        thumb_rect = QRectF(thumb_x, 2.0, seg_w, h - 4.0)
        thumb_grad = QLinearGradient(0, thumb_rect.top(), 0, thumb_rect.bottom())
        thumb_grad.setColorAt(0.0, QColor(255, 255, 255, 38))
        thumb_grad.setColorAt(1.0, QColor(255, 255, 255, 18))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(thumb_grad))
        p.drawRoundedRect(thumb_rect, radius - 2, radius - 2)
        p.setPen(QPen(QColor(255, 255, 255, 50), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(thumb_rect.adjusted(0.5, 0.5, -0.5, -0.5), radius - 2, radius - 2)

        # Labels
        font = self.font()
        font.setPixelSize(12)
        font.setWeight(QFont.Weight.Medium)
        p.setFont(font)
        for i, label in enumerate(self._options):
            x = 2.0 + seg_w * i
            rect = QRect(int(x), 0, int(seg_w), int(h))
            color = TEXT if i == self._index else TEXT_DIM
            p.setPen(QPen(color))
            p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), label)

        p.end()


class HourSlider(QWidget):
    """Modern thin horizontal slider for hour values (0–23) with HH:00 label."""

    valueChanged = pyqtSignal(int)

    def __init__(self, value: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = max(0, min(23, value))
        self._dragging = False
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def value(self) -> int:
        return self._value

    def setValue(self, v: int) -> None:  # noqa: N802
        v = max(0, min(23, int(v)))
        if v != self._value:
            self._value = v
            self.update()
            self.valueChanged.emit(v)

    def _track_rect(self) -> QRectF:
        h = float(self.height())
        margin = 14.0
        return QRectF(margin, h / 2 + 6, float(self.width()) - margin * 2, 4.0)

    def _value_from_x(self, x: float) -> int:
        track = self._track_rect()
        if track.width() <= 0:
            return 0
        ratio = (x - track.left()) / track.width()
        ratio = max(0.0, min(1.0, ratio))
        return round(ratio * 23)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.setValue(self._value_from_x(event.position().x()))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging:
            self.setValue(self._value_from_x(event.position().x()))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._dragging = False

    def paintEvent(self, event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = self._track_rect()
        # Track bg
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(246, 246, 250, 26))
        p.drawRoundedRect(track, track.height() / 2, track.height() / 2)
        # Filled portion
        ratio = self._value / 23.0
        filled = QRectF(track.left(), track.top(), track.width() * ratio, track.height())
        grad = QLinearGradient(filled.left(), 0, filled.right(), 0)
        grad.setColorAt(0.0, ACCENT)
        grad.setColorAt(1.0, ACCENT_2)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(filled, track.height() / 2, track.height() / 2)

        # Thumb
        thumb_x = track.left() + track.width() * ratio
        thumb_y = track.center().y()
        # Glow
        glow = QRadialGradient(thumb_x, thumb_y, 14.0)
        glow.setColorAt(0.0, QColor(124, 110, 245, 110))
        glow.setColorAt(1.0, QColor(124, 110, 245, 0))
        p.setBrush(QBrush(glow))
        p.drawEllipse(QRectF(thumb_x - 14, thumb_y - 14, 28, 28))
        # Thumb body
        p.setBrush(QColor(255, 255, 255, 240))
        p.setPen(QPen(QColor(0, 0, 0, 50), 0.5))
        p.drawEllipse(QRectF(thumb_x - 7, thumb_y - 7, 14, 14))

        # Value label above thumb
        font = self.font()
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        label = f"{self._value:02d}:00"
        label_rect = QRectF(thumb_x - 28, 2, 56, 20)
        p.setPen(QPen(TEXT))
        p.drawText(label_rect, int(Qt.AlignmentFlag.AlignCenter), label)

        p.end()


__all__ = ["LogoMark", "ToggleSwitch", "SegmentedControl", "HourSlider"]
