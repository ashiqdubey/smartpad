"""Settings dialog — fluid Aside-style UI with sliders, segmented controls and toggles."""
from __future__ import annotations

import contextlib

import keyring
from loguru import logger
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from smartpad.config import load_settings
from smartpad.ui.widgets import HourSlider, LogoMark, SegmentedControl, ToggleSwitch

_SVC = "smartpad"

_AI_LEVEL_LABELS = ["Off", "Organise", "Grammar", "Tidy", "Enhance"]


def _kr(key: str) -> str:
    try:
        return keyring.get_password(_SVC, key) or ""
    except Exception:
        return ""


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SmartPad — Settings")
        # Frameless but still on taskbar (Window flag, not Dialog)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumSize(540, 620)
        self.resize(560, 660)
        self._settings = load_settings()
        self._drag_pos: QPoint | None = None
        self._setup_ui()

    def paintEvent(self, event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()), 16.0, 16.0)
        p.fillPath(path, QColor(22, 20, 34, 244))
        # Soft accent glow at the top — sets the brand tone
        from PyQt6.QtGui import QBrush, QRadialGradient
        glow = QRadialGradient(self.width() / 2, 0, self.width() * 0.7)
        glow.setColorAt(0.0, QColor(124, 110, 245, 60))
        glow.setColorAt(1.0, QColor(124, 110, 245, 0))
        p.fillPath(path, QBrush(glow))
        p.end()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_title_bar())

        tabs = QTabWidget()
        tabs.setObjectName("SettingsTabs")
        tabs.addTab(self._make_general_tab(), "General")
        tabs.addTab(self._make_ai_tab(), "AI & Notifications")
        tabs.addTab(self._make_providers_tab(), "Providers")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 12, 20, 18)
        cl.addWidget(tabs)
        root.addWidget(content, stretch=1)

    def _make_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("DialogTitleBar")
        bar.setFixedHeight(56)
        row = QHBoxLayout(bar)
        row.setContentsMargins(18, 0, 14, 0)
        row.setSpacing(10)

        row.addWidget(LogoMark(20))

        title = QLabel("Settings")
        title.setObjectName("DialogTitle")
        row.addWidget(title)
        row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setObjectName("DialogDoneButton")
        save_btn.setFixedSize(QSize(70, 30))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("DialogCloseButton")
        close_btn.setFixedSize(QSize(28, 28))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)

        row.addWidget(save_btn)
        row.addWidget(close_btn)

        bar.mousePressEvent = self._bar_press   # type: ignore[method-assign]
        bar.mouseMoveEvent = self._bar_move     # type: ignore[method-assign]
        bar.mouseReleaseEvent = self._bar_release  # type: ignore[method-assign]
        return bar

    def _bar_press(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _bar_move(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _bar_release(self, event) -> None:  # type: ignore[no-untyped-def]
        self._drag_pos = None

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _make_general_tab(self) -> QWidget:
        wrap = self._scroll_wrap()
        layout = wrap.body  # type: ignore[attr-defined]

        # APP BEHAVIOUR card
        card = self._card("APP")
        cl = card.body  # type: ignore[attr-defined]

        # Hotkey
        cl.addLayout(self._row(
            "Global hotkey",
            "Press anywhere to summon the panel",
            self._hotkey_field()
        ))

        # Theme
        self._theme = QComboBox()
        self._theme.addItems(["system", "dark", "light"])
        self._theme.setCurrentText(self._settings.theme)
        self._theme.setFixedWidth(160)
        cl.addLayout(self._row("Theme", "Window appearance", self._theme))

        # Startup toggle
        self._startup = ToggleSwitch(checked=self._settings.startup_with_os)
        cl.addLayout(self._row(
            "Launch at login",
            "Start SmartPad when your computer wakes up",
            self._startup
        ))

        layout.addWidget(card)
        layout.addStretch()
        return wrap

    def _make_ai_tab(self) -> QWidget:
        wrap = self._scroll_wrap()
        layout = wrap.body  # type: ignore[attr-defined]

        # AI level — segmented control
        ai_card = self._card("AI ASSIST")
        cl = ai_card.body  # type: ignore[attr-defined]

        sub = QLabel("How aggressively should AI clean up your captures?")
        sub.setObjectName("CardSub")
        sub.setWordWrap(True)
        cl.addWidget(sub)
        cl.addSpacing(6)

        self._ai_level = SegmentedControl(_AI_LEVEL_LABELS, index=int(self._settings.ai_level))
        self._ai_level.setMinimumHeight(34)
        cl.addWidget(self._ai_level)

        layout.addWidget(ai_card)

        # Quiet hours — sliders
        q_card = self._card("QUIET HOURS")
        ql = q_card.body  # type: ignore[attr-defined]

        sub2 = QLabel("Mute reminder notifications between these hours.")
        sub2.setObjectName("CardSub")
        sub2.setWordWrap(True)
        ql.addWidget(sub2)
        ql.addSpacing(6)

        # Start
        start_label = QLabel("Start")
        start_label.setObjectName("RowLabel")
        ql.addWidget(start_label)
        self._quiet_start = HourSlider(value=int(self._settings.quiet_hours_start))
        ql.addWidget(self._quiet_start)
        ql.addSpacing(6)

        # End
        end_label = QLabel("End")
        end_label.setObjectName("RowLabel")
        ql.addWidget(end_label)
        self._quiet_end = HourSlider(value=int(self._settings.quiet_hours_end))
        ql.addWidget(self._quiet_end)

        layout.addWidget(q_card)
        layout.addStretch()
        return wrap

    def _make_providers_tab(self) -> QWidget:
        wrap = self._scroll_wrap()
        layout = wrap.body  # type: ignore[attr-defined]

        # Active provider
        active_card = self._card("ACTIVE PROVIDER")
        al = active_card.body  # type: ignore[attr-defined]
        self._preferred = QComboBox()
        self._preferred.addItems(["auto", "anthropic", "openai", "google", "local"])
        self._preferred.setCurrentText(_kr("preferred_provider") or "auto")
        al.addLayout(self._row(
            "Provider",
            "auto picks the first configured one",
            self._preferred,
        ))
        layout.addWidget(active_card)

        # Anthropic
        ant_card = self._card("ANTHROPIC — CLAUDE")
        anl = ant_card.body  # type: ignore[attr-defined]
        self._ant_key = self._key_widget("sk-ant-api03-…", _kr("anthropic_api_key"))
        anl.addLayout(self._row("API key", "Used for /chat with Claude", self._ant_key))
        layout.addWidget(ant_card)

        # OpenAI
        oai_card = self._card("OPENAI / COMPATIBLE")
        ol = oai_card.body  # type: ignore[attr-defined]
        self._oai_key = self._key_widget("sk-…", _kr("openai_api_key"))
        self._oai_url = QLineEdit(_kr("openai_base_url"))
        self._oai_url.setPlaceholderText("https://api.openai.com/v1")
        self._oai_model = QLineEdit(_kr("openai_model"))
        self._oai_model.setPlaceholderText("gpt-4o-mini")
        ol.addLayout(self._row("API key", "Or any compatible endpoint", self._oai_key))
        ol.addLayout(self._row("Base URL", "Leave empty for OpenAI", self._oai_url))
        ol.addLayout(self._row("Model", "Override the default", self._oai_model))
        layout.addWidget(oai_card)

        # Google
        g_card = self._card("GOOGLE — GEMINI")
        gl = g_card.body  # type: ignore[attr-defined]
        self._goo_key = self._key_widget("AIza…", _kr("google_api_key"))
        gl.addLayout(self._row("API key", "Get one at aistudio.google.com", self._goo_key))
        layout.addWidget(g_card)

        # Local
        l_card = self._card("LOCAL — OLLAMA / LM STUDIO")
        ll = l_card.body  # type: ignore[attr-defined]
        self._loc_url = QLineEdit(_kr("local_server_url"))
        self._loc_url.setPlaceholderText("http://localhost:11434")
        self._loc_model = QLineEdit(_kr("local_model"))
        self._loc_model.setPlaceholderText("llama3.2:3b")
        ll.addLayout(self._row("Server URL", "Where your model is running", self._loc_url))
        ll.addLayout(self._row("Model", "Tag served by the endpoint", self._loc_model))
        layout.addWidget(l_card)

        layout.addStretch()
        return wrap

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _scroll_wrap(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        body = QVBoxLayout(inner)
        body.setContentsMargins(2, 4, 6, 14)
        body.setSpacing(14)
        scroll.setWidget(inner)
        scroll.body = body  # type: ignore[attr-defined]
        return scroll

    @staticmethod
    def _card(title: str) -> QWidget:
        card = QWidget()
        card.setObjectName("SettingsCard")
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 12, 16, 16)
        v.setSpacing(12)

        kicker = QLabel(title)
        kicker.setObjectName("CardKicker")
        v.addWidget(kicker)
        card.body = v  # type: ignore[attr-defined]
        return card

    @staticmethod
    def _row(label: str, sub: str, control: QWidget) -> QHBoxLayout:
        h = QHBoxLayout()
        h.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        l = QLabel(label)
        l.setObjectName("RowLabel")
        text_col.addWidget(l)
        if sub:
            s = QLabel(sub)
            s.setObjectName("RowSub")
            s.setWordWrap(True)
            text_col.addWidget(s)
        h.addLayout(text_col, stretch=1)
        h.addWidget(control, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return h

    def _hotkey_field(self) -> QLineEdit:
        self._hotkey = QLineEdit(self._settings.hotkey)
        self._hotkey.setPlaceholderText("ctrl+alt+space")
        self._hotkey.setFixedWidth(180)
        return self._hotkey

    @staticmethod
    def _key_widget(placeholder: str, value: str) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        field = QLineEdit(value)
        field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setPlaceholderText(placeholder)
        field.setMinimumWidth(220)

        toggle = QPushButton("Show")
        toggle.setObjectName("KeyToggleButton")
        toggle.setFixedWidth(54)
        toggle.setCheckable(True)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)

        def _toggle(checked: bool) -> None:
            field.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
            toggle.setText("Hide" if checked else "Show")

        toggle.toggled.connect(_toggle)
        row.addWidget(field)
        row.addWidget(toggle)
        container._field = field  # type: ignore[attr-defined]
        return container

    @staticmethod
    def _field_text(container: QWidget) -> str:
        f = getattr(container, "_field", None)
        if f is None:
            for child in container.children():
                if isinstance(child, QLineEdit):
                    return child.text()
            return ""
        return f.text()

    def _save(self) -> None:
        def _store(key: str, val: str) -> None:
            if val.strip():
                with contextlib.suppress(Exception):
                    keyring.set_password(_SVC, key, val.strip())
            else:
                with contextlib.suppress(Exception):
                    keyring.delete_password(_SVC, key)

        _store("preferred_provider", self._preferred.currentText())
        _store("anthropic_api_key", self._field_text(self._ant_key))
        _store("openai_api_key", self._field_text(self._oai_key))
        _store("openai_base_url", self._oai_url.text())
        _store("openai_model", self._oai_model.text())
        _store("google_api_key", self._field_text(self._goo_key))
        _store("local_server_url", self._loc_url.text())
        _store("local_model", self._loc_model.text())

        self._settings.hotkey = self._hotkey.text()
        self._settings.theme = self._theme.currentText()
        self._settings.ai_level = int(self._ai_level.value())
        self._settings.startup_with_os = self._startup.isChecked()
        self._settings.quiet_hours_start = int(self._quiet_start.value())
        self._settings.quiet_hours_end = int(self._quiet_end.value())
        try:
            self._settings.save()
            logger.info("Settings saved.")
        except Exception as exc:
            logger.error("Could not save settings: {}", exc)
        self.accept()
