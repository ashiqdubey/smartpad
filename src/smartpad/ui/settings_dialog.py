"""Settings dialog — provider keys, general settings."""
from __future__ import annotations

import contextlib

import keyring
from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from smartpad.config import load_settings

_SVC = "smartpad"


def _kr(key: str) -> str:
    """Read from keyring safely, returning '' on any error (incl. no backend)."""
    try:
        return keyring.get_password(_SVC, key) or ""
    except Exception:
        return ""


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SmartPad Settings")
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)
        self._settings = load_settings()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.addTab(self._make_providers_tab(), "Providers")
        tabs.addTab(self._make_general_tab(), "General")
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _make_providers_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        # Preferred provider
        pref_group = QGroupBox("Active Provider")
        pref_form = QFormLayout(pref_group)
        self._preferred = QComboBox()
        self._preferred.addItems(["auto", "anthropic", "openai", "google", "local"])
        stored_pref = _kr("preferred_provider") or "auto"
        self._preferred.setCurrentText(stored_pref)
        pref_form.addRow("Preferred:", self._preferred)
        layout.addWidget(pref_group)

        # Anthropic
        ant_group = QGroupBox("Anthropic (Claude)")
        ant_form = QFormLayout(ant_group)
        self._ant_key = self._make_key_field(
            "sk-ant-api03-…", _kr("anthropic_api_key")
        )
        ant_form.addRow("API Key:", self._ant_key)
        layout.addWidget(ant_group)

        # OpenAI / compatible
        oai_group = QGroupBox("OpenAI / Compatible")
        oai_form = QFormLayout(oai_group)
        self._oai_key = self._make_key_field(
            "sk-…", _kr("openai_api_key")
        )
        self._oai_url = QLineEdit(_kr("openai_base_url"))
        self._oai_url.setPlaceholderText("https://api.openai.com/v1  (leave blank for OpenAI)")
        self._oai_model = QLineEdit(_kr("openai_model"))
        self._oai_model.setPlaceholderText("gpt-4o-mini")
        oai_form.addRow("API Key:", self._oai_key)
        oai_form.addRow("Base URL:", self._oai_url)
        oai_form.addRow("Model:", self._oai_model)
        layout.addWidget(oai_group)

        # Google
        goo_group = QGroupBox("Google (Gemini)")
        goo_form = QFormLayout(goo_group)
        self._goo_key = self._make_key_field(
            "AIza…", _kr("google_api_key")
        )
        goo_form.addRow("API Key:", self._goo_key)
        layout.addWidget(goo_group)

        # Local
        loc_group = QGroupBox("Local Server (Ollama / LM Studio)")
        loc_form = QFormLayout(loc_group)
        self._loc_url = QLineEdit(_kr("local_server_url"))
        self._loc_url.setPlaceholderText("http://localhost:11434")
        self._loc_model = QLineEdit(_kr("local_model"))
        self._loc_model.setPlaceholderText("llama3.2:3b")
        loc_form.addRow("Server URL:", self._loc_url)
        loc_form.addRow("Model:", self._loc_model)
        layout.addWidget(loc_group)

        layout.addStretch()
        return w

    def _make_general_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(12)

        self._hotkey = QLineEdit(self._settings.hotkey)
        self._hotkey.setPlaceholderText("ctrl+alt+space")
        form.addRow("Global Hotkey:", self._hotkey)

        self._theme = QComboBox()
        self._theme.addItems(["system", "dark", "light"])
        self._theme.setCurrentText(self._settings.theme)
        form.addRow("Theme:", self._theme)

        self._ai_level = QSpinBox()
        self._ai_level.setRange(0, 4)
        self._ai_level.setValue(self._settings.ai_level)
        self._ai_level.setToolTip("0=off  1=organise  2=grammar  3=tidy  4=enhance")
        form.addRow("AI Level:", self._ai_level)

        self._startup = QCheckBox("Launch SmartPad when Windows starts")
        self._startup.setChecked(self._settings.startup_with_os)
        form.addRow("Startup:", self._startup)

        self._quiet_start = QSpinBox()
        self._quiet_start.setRange(0, 23)
        self._quiet_start.setValue(self._settings.quiet_hours_start)
        form.addRow("Quiet hours start:", self._quiet_start)

        self._quiet_end = QSpinBox()
        self._quiet_end.setRange(0, 23)
        self._quiet_end.setValue(self._settings.quiet_hours_end)
        form.addRow("Quiet hours end:", self._quiet_end)

        return w

    @staticmethod
    def _make_key_field(placeholder: str, value: str) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        field = QLineEdit(value)
        field.setEchoMode(QLineEdit.EchoMode.Password)
        field.setPlaceholderText(placeholder)
        field.setObjectName("_key_field")
        toggle = QPushButton("Show")
        toggle.setFixedWidth(52)
        toggle.setCheckable(True)

        def _toggle(checked: bool) -> None:
            field.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
            toggle.setText("Hide" if checked else "Show")

        toggle.toggled.connect(_toggle)
        row.addWidget(field)
        row.addWidget(toggle)
        # Store ref so _save can find it
        container._field = field  # type: ignore[attr-defined]
        return container

    @staticmethod
    def _key_text(container: QWidget) -> str:
        f = getattr(container, "_field", None)
        if f is None:
            # fallback: find QLineEdit child
            for child in container.children():
                if isinstance(child, QLineEdit):
                    return child.text()
        return f.text() if f else ""

    def _save(self) -> None:
        def _store(key: str, val: str) -> None:
            if val.strip():
                keyring.set_password(_SVC, key, val.strip())
            else:
                with contextlib.suppress(Exception):
                    keyring.delete_password(_SVC, key)

        _store("preferred_provider", self._preferred.currentText())
        _store("anthropic_api_key", self._key_text(self._ant_key))
        _store("openai_api_key", self._key_text(self._oai_key))
        _store("openai_base_url", self._oai_url.text())
        _store("openai_model", self._oai_model.text())
        _store("google_api_key", self._key_text(self._goo_key))
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
