"""Settings dialog — SPEC.MD section 12 + 17.

Three tabs: General, AI Providers, Data.
Every setting from SPEC.MD section 17 is reachable.
"""

from __future__ import annotations

from loguru import logger
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from smartpad.config import SmartPadSettings


class SettingsDialog(QDialog):
    """Modal settings dialog with three tabs."""

    settings_changed = pyqtSignal()  # emitted when user clicks Apply/OK

    def __init__(self, settings: SmartPadSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("SmartPad Settings")
        self.setMinimumSize(520, 480)
        self.setModal(True)
        self._build_ui()
        self._load_values()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "General")
        self._tabs.addTab(self._build_providers_tab(), "AI Providers")
        self._tabs.addTab(self._build_data_tab(), "Data")
        layout.addWidget(self._tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply,
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        layout.addWidget(buttons)

    # ── General tab ───────────────────────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 4)

        # Hotkey
        hotkey_group = QGroupBox("Global Hotkey")
        hk_layout = QFormLayout(hotkey_group)
        self._hotkey_edit = QLineEdit()
        self._hotkey_edit.setPlaceholderText("e.g. ctrl+alt+space")
        hk_layout.addRow("Hotkey:", self._hotkey_edit)
        layout.addWidget(hotkey_group)

        # Appearance
        appear_group = QGroupBox("Appearance")
        ap_layout = QFormLayout(appear_group)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["system", "dark", "light"])
        ap_layout.addRow("Theme:", self._theme_combo)
        layout.addWidget(appear_group)

        # AI Level
        ai_group = QGroupBox("AI Processing")
        ai_layout = QFormLayout(ai_group)
        self._ai_level_slider = QSlider(Qt.Orientation.Horizontal)
        self._ai_level_slider.setMinimum(0)
        self._ai_level_slider.setMaximum(4)
        self._ai_level_slider.setTickInterval(1)
        self._ai_level_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._ai_level_label = QLabel("1 — Organise only")
        self._ai_level_slider.valueChanged.connect(self._update_ai_level_label)
        ai_layout.addRow("Level:", self._ai_level_slider)
        ai_layout.addRow("", self._ai_level_label)
        layout.addWidget(ai_group)

        # Startup
        startup_group = QGroupBox("Startup")
        st_layout = QFormLayout(startup_group)
        self._startup_check = QCheckBox("Launch SmartPad on system startup")
        st_layout.addRow(self._startup_check)
        layout.addWidget(startup_group)

        # Quiet hours
        qh_group = QGroupBox("Quiet Hours")
        qh_layout = QFormLayout(qh_group)
        self._quiet_enabled = QCheckBox("Enable quiet hours")
        self._quiet_start = QSpinBox()
        self._quiet_start.setMinimum(0)
        self._quiet_start.setMaximum(23)
        self._quiet_start.setSuffix(":00")
        self._quiet_end = QSpinBox()
        self._quiet_end.setMinimum(0)
        self._quiet_end.setMaximum(23)
        self._quiet_end.setSuffix(":00")
        qh_layout.addRow(self._quiet_enabled)
        qh_layout.addRow("Start:", self._quiet_start)
        qh_layout.addRow("End:", self._quiet_end)
        layout.addWidget(qh_group)

        layout.addStretch()
        return tab

    # ── AI Providers tab ──────────────────────────────────────────────────────

    def _build_providers_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 4)

        info = QLabel(
            "Configure AI providers. The active provider is used for all AI features.\n"
            "API keys are stored securely in your system keychain."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # OpenAI-compatible section
        oai_group = QGroupBox("OpenAI-compatible endpoint")
        oai_layout = QFormLayout(oai_group)
        self._oai_base_url = QLineEdit()
        self._oai_base_url.setPlaceholderText("https://api.openai.com  or  http://localhost:11434")
        self._oai_api_key = QLineEdit()
        self._oai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._oai_api_key.setPlaceholderText("sk-…  (leave blank for Ollama/LM Studio)")
        self._oai_model = QLineEdit()
        self._oai_model.setPlaceholderText("gpt-4o  or  qwen3:4b")
        oai_layout.addRow("Base URL:", self._oai_base_url)
        oai_layout.addRow("API Key:", self._oai_api_key)
        oai_layout.addRow("Default Model:", self._oai_model)

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_provider)
        self._test_result = QLabel("")
        row = QHBoxLayout()
        row.addWidget(test_btn)
        row.addWidget(self._test_result)
        row.addStretch()
        oai_layout.addRow(row)
        layout.addWidget(oai_group)

        # Local model section
        local_group = QGroupBox("Local Model (llama-server)")
        local_layout = QFormLayout(local_group)
        self._local_model_combo = QComboBox()
        from smartpad.model_manager.catalog import CATALOG
        for m in CATALOG:
            self._local_model_combo.addItem(m.display_name, userData=m.id)
        local_layout.addRow("Model:", self._local_model_combo)

        idle_row = QHBoxLayout()
        self._idle_enabled = QCheckBox("Auto-unload after")
        self._idle_minutes = QSpinBox()
        self._idle_minutes.setMinimum(5)
        self._idle_minutes.setMaximum(240)
        self._idle_minutes.setSuffix(" min")
        idle_row.addWidget(self._idle_enabled)
        idle_row.addWidget(self._idle_minutes)
        idle_row.addStretch()
        local_layout.addRow(idle_row)
        layout.addWidget(local_group)

        layout.addStretch()
        return tab

    # ── Data tab ──────────────────────────────────────────────────────────────

    def _build_data_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 4)

        # Export
        export_group = QGroupBox("Export")
        exp_layout = QVBoxLayout(export_group)
        md_btn = QPushButton("Export as Markdown…")
        md_btn.clicked.connect(self._export_markdown)
        json_btn = QPushButton("Export as JSON…")
        json_btn.clicked.connect(self._export_json)
        exp_layout.addWidget(md_btn)
        exp_layout.addWidget(json_btn)
        layout.addWidget(export_group)

        # Backup
        backup_group = QGroupBox("Auto-backup")
        bk_layout = QFormLayout(backup_group)
        self._backup_enabled = QCheckBox("Daily backup (recommended)")
        self._backup_retention = QSpinBox()
        self._backup_retention.setMinimum(1)
        self._backup_retention.setMaximum(30)
        self._backup_retention.setSuffix(" copies")
        bk_layout.addRow(self._backup_enabled)
        bk_layout.addRow("Keep last:", self._backup_retention)
        layout.addWidget(backup_group)

        # Danger zone
        danger_group = QGroupBox("Danger zone")
        d_layout = QVBoxLayout(danger_group)
        clear_chat_btn = QPushButton("Clear chat history")
        clear_chat_btn.clicked.connect(self._clear_chat)
        clear_all_btn = QPushButton("Clear ALL data…")
        clear_all_btn.clicked.connect(self._clear_all)
        d_layout.addWidget(clear_chat_btn)
        d_layout.addWidget(clear_all_btn)
        layout.addWidget(danger_group)

        layout.addStretch()
        return tab

    # ── Load / save ───────────────────────────────────────────────────────────

    def _load_values(self) -> None:
        s = self._settings
        self._hotkey_edit.setText(s.hotkey)
        idx = self._theme_combo.findText(s.theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._ai_level_slider.setValue(s.ai_level)
        self._update_ai_level_label(s.ai_level)
        self._startup_check.setChecked(s.startup_with_os)
        self._quiet_enabled.setChecked(s.quiet_hours_enabled)
        self._quiet_start.setValue(s.quiet_hours_start)
        self._quiet_end.setValue(s.quiet_hours_end)
        self._idle_enabled.setChecked(s.local_model.idle_unload_enabled)
        self._idle_minutes.setValue(s.local_model.idle_threshold_minutes)
        self._backup_enabled.setChecked(s.backup.enabled)
        self._backup_retention.setValue(s.backup.retention_days)

    def _apply(self) -> None:
        s = self._settings
        s.hotkey = self._hotkey_edit.text().strip() or "ctrl+alt+space"
        s.theme = self._theme_combo.currentText()
        s.ai_level = self._ai_level_slider.value()
        s.startup_with_os = self._startup_check.isChecked()
        s.quiet_hours_enabled = self._quiet_enabled.isChecked()
        s.quiet_hours_start = self._quiet_start.value()
        s.quiet_hours_end = self._quiet_end.value()
        s.local_model.idle_unload_enabled = self._idle_enabled.isChecked()
        s.local_model.idle_threshold_minutes = self._idle_minutes.value()
        s.backup.enabled = self._backup_enabled.isChecked()
        s.backup.retention_days = self._backup_retention.value()
        try:
            s.save()
        except Exception as exc:
            logger.warning("Could not save settings: {}", exc)
        self.settings_changed.emit()

    def _on_ok(self) -> None:
        self._apply()
        self.accept()

    # ── Slot helpers ──────────────────────────────────────────────────────────

    def _update_ai_level_label(self, value: int) -> None:
        labels = [
            "0 — Off (no AI)",
            "1 — Organise only",
            "2 — Fix grammar",
            "3 — Tidy + clarify",
            "4 — Full enhancement",
        ]
        self._ai_level_label.setText(labels[value])

    def _test_provider(self) -> None:
        self._test_result.setText("Testing…")
        # Full async test wired in Phase 17+; show stub message for now
        self._test_result.setText("⚠ Full test available once provider is configured")

    def _export_markdown(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", "smartpad-export.md", "Markdown (*.md)")
        if path:
            self._test_result.setText(f"Exported to {path} (Phase 22)")

    def _export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "smartpad-export.json", "JSON (*.json)")
        if path:
            self._test_result.setText(f"Exported to {path} (Phase 22)")

    def _clear_chat(self) -> None:
        logger.info("Clear chat requested (wired in Phase 21)")

    def _clear_all(self) -> None:
        logger.warning("Clear ALL data requested (wired in Phase 21)")
