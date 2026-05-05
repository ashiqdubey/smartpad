"""Settings dialog — provider keys, general settings."""
from __future__ import annotations

import contextlib

import keyring
from loguru import logger
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from smartpad.config import load_settings

_SVC = "smartpad"


def _kr(key: str) -> str:
    try:
        return keyring.get_password(_SVC, key) or ""
    except Exception:
        return ""


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumSize(500, 580)
        self.resize(520, 620)
        self._settings = load_settings()
        self._drag_pos: QPoint | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_title_bar())

        # Tabs area
        from PyQt6.QtWidgets import QTabWidget  # noqa: PLC0415
        tabs = QTabWidget()
        tabs.addTab(self._make_providers_tab(), "Providers")
        tabs.addTab(self._make_general_tab(), "General")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 16)
        content_layout.setSpacing(0)
        content_layout.addWidget(tabs)
        root.addWidget(content, stretch=1)

    def _make_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("DialogTitleBar")
        bar.setFixedHeight(52)

        row = QHBoxLayout(bar)
        row.setContentsMargins(20, 0, 14, 0)
        row.setSpacing(8)

        title = QLabel("Settings")
        title.setObjectName("DialogTitle")

        done_btn = QPushButton("Save")
        done_btn.setObjectName("DialogDoneButton")
        done_btn.setFixedSize(QSize(64, 30))
        done_btn.clicked.connect(self._save)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("DialogCloseButton")
        close_btn.setFixedSize(QSize(28, 28))
        close_btn.clicked.connect(self.reject)

        row.addWidget(title)
        row.addStretch()
        row.addWidget(done_btn)
        row.addWidget(close_btn)

        bar.mousePressEvent = self._bar_press    # type: ignore[method-assign]
        bar.mouseMoveEvent = self._bar_move      # type: ignore[method-assign]
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

    def _make_providers_tab(self) -> QWidget:
        # Wrap in scroll area — 5 groups would overflow without it
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(2, 8, 2, 16)
        layout.setSpacing(10)

        # Active provider
        pref_group = QGroupBox("ACTIVE PROVIDER")
        pref_form = self._form_layout(pref_group)
        self._preferred = QComboBox()
        self._preferred.addItems(["auto", "anthropic", "openai", "google", "local"])
        self._preferred.setCurrentText(_kr("preferred_provider") or "auto")
        pref_form.addRow("Provider:", self._preferred)
        layout.addWidget(pref_group)

        # Anthropic
        ant_group = QGroupBox("ANTHROPIC — CLAUDE")
        ant_form = self._form_layout(ant_group)
        self._ant_key = self._key_widget("sk-ant-api03-…", _kr("anthropic_api_key"))
        ant_form.addRow("API Key:", self._ant_key)
        layout.addWidget(ant_group)

        # OpenAI / compatible
        oai_group = QGroupBox("OPENAI / COMPATIBLE")
        oai_form = self._form_layout(oai_group)
        self._oai_key = self._key_widget("sk-…", _kr("openai_api_key"))
        self._oai_url = QLineEdit(_kr("openai_base_url"))
        self._oai_url.setPlaceholderText("https://api.openai.com/v1")
        self._oai_model = QLineEdit(_kr("openai_model"))
        self._oai_model.setPlaceholderText("gpt-4o-mini")
        oai_form.addRow("API Key:", self._oai_key)
        oai_form.addRow("Base URL:", self._oai_url)
        oai_form.addRow("Model:", self._oai_model)
        layout.addWidget(oai_group)

        # Google
        goo_group = QGroupBox("GOOGLE — GEMINI")
        goo_form = self._form_layout(goo_group)
        self._goo_key = self._key_widget("AIza…", _kr("google_api_key"))
        goo_form.addRow("API Key:", self._goo_key)
        layout.addWidget(goo_group)

        # Local
        loc_group = QGroupBox("LOCAL SERVER — OLLAMA / LM STUDIO")
        loc_form = self._form_layout(loc_group)
        self._loc_url = QLineEdit(_kr("local_server_url"))
        self._loc_url.setPlaceholderText("http://localhost:11434")
        self._loc_model = QLineEdit(_kr("local_model"))
        self._loc_model.setPlaceholderText("llama3.2:3b")
        loc_form.addRow("Server URL:", self._loc_url)
        loc_form.addRow("Model:", self._loc_model)
        layout.addWidget(loc_group)

        layout.addStretch()
        scroll.setWidget(inner)
        return scroll

    def _make_general_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(2, 8, 2, 16)
        layout.setSpacing(10)

        app_group = QGroupBox("APP BEHAVIOUR")
        app_form = self._form_layout(app_group)

        self._hotkey = QLineEdit(self._settings.hotkey)
        self._hotkey.setPlaceholderText("ctrl+alt+space")
        app_form.addRow("Global hotkey:", self._hotkey)

        self._theme = QComboBox()
        self._theme.addItems(["system", "dark", "light"])
        self._theme.setCurrentText(self._settings.theme)
        app_form.addRow("Theme:", self._theme)

        self._startup = QCheckBox("Launch on system start")
        self._startup.setChecked(self._settings.startup_with_os)
        app_form.addRow("Startup:", self._startup)

        layout.addWidget(app_group)

        ai_group = QGroupBox("AI SETTINGS")
        ai_form = self._form_layout(ai_group)

        self._ai_level = QSpinBox()
        self._ai_level.setRange(0, 4)
        self._ai_level.setValue(self._settings.ai_level)
        self._ai_level.setToolTip("0=off  1=organise  2=grammar  3=tidy  4=enhance")
        ai_form.addRow("AI level:", self._ai_level)

        layout.addWidget(ai_group)

        quiet_group = QGroupBox("QUIET HOURS")
        quiet_form = self._form_layout(quiet_group)

        self._quiet_start = QSpinBox()
        self._quiet_start.setRange(0, 23)
        self._quiet_start.setValue(self._settings.quiet_hours_start)
        self._quiet_start.setSuffix(":00")
        quiet_form.addRow("Start:", self._quiet_start)

        self._quiet_end = QSpinBox()
        self._quiet_end.setRange(0, 23)
        self._quiet_end.setValue(self._settings.quiet_hours_end)
        self._quiet_end.setSuffix(":00")
        quiet_form.addRow("End:", self._quiet_end)

        layout.addWidget(quiet_group)
        layout.addStretch()
        return w

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _form_layout(group: QGroupBox) -> QFormLayout:
        form = QFormLayout(group)
        form.setContentsMargins(14, 8, 14, 12)
        form.setSpacing(10)
        form.setHorizontalSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        return form

    @staticmethod
    def _key_widget(placeholder: str, value: str) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        field = QLineEdit(value)
        field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setPlaceholderText(placeholder)

        toggle = QPushButton("Show")
        toggle.setFixedWidth(50)
        toggle.setCheckable(True)

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
        return f.text() if f else ""

    # Keep old name for any callers
    @staticmethod
    def _key_text(container: QWidget) -> str:
        return SettingsDialog._field_text(container)

    def _save(self) -> None:
        def _store(key: str, val: str) -> None:
            if val.strip():
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
        self._settings.ai_level = self._ai_level.value()
        self._settings.startup_with_os = self._startup.isChecked()
        self._settings.quiet_hours_start = self._quiet_start.value()
        self._settings.quiet_hours_end = self._quiet_end.value()
        try:
            self._settings.save()
            logger.info("Settings saved.")
        except Exception as exc:
            logger.error("Could not save settings: {}", exc)

        self.accept()
