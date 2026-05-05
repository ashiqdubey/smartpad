"""First-run onboarding wizard."""
from __future__ import annotations

import keyring
from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from smartpad.config import load_settings

_SVC = "smartpad"


class OnboardingWizard(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to SmartPad")
        self.setMinimumSize(500, 380)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._settings = load_settings()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_welcome())
        self._stack.addWidget(self._page_provider())
        self._stack.addWidget(self._page_hotkey())
        self._stack.addWidget(self._page_done())
        layout.addWidget(self._stack, stretch=1)

        nav = QHBoxLayout()
        self._back_btn = QPushButton("Back")
        self._back_btn.clicked.connect(self._go_back)
        self._next_btn = QPushButton("Next")
        self._next_btn.setDefault(True)
        self._next_btn.clicked.connect(self._go_next)
        nav.addWidget(self._back_btn)
        nav.addStretch()
        self._page_indicator = QLabel("Step 1 of 4")
        self._page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self._page_indicator)
        nav.addStretch()
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)
        self._update_nav()

    def _page_welcome(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Welcome to SmartPad")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin: 20px 0;")
        desc = QLabel(
            "SmartPad is your floating AI second brain.\n"
            "Press a hotkey from any app to capture notes, tasks,\n"
            "reminders, and snippets — all stored locally.\n\n"
            "Let's get you set up in a few steps."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        return w

    def _page_provider(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        title = QLabel("Choose your AI provider")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(
            [
                "Anthropic (Claude)",
                "OpenAI / Compatible",
                "Google (Gemini)",
                "Local (Ollama / LM Studio)",
                "Skip for now",
            ]
        )
        self._provider_combo.currentIndexChanged.connect(self._update_provider_fields)
        layout.addWidget(self._provider_combo)

        self._key_label = QLabel("API Key:")
        self._key_field = QLineEdit()
        self._key_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_field.setPlaceholderText("Paste your API key here")
        layout.addWidget(self._key_label)
        layout.addWidget(self._key_field)

        self._url_label = QLabel("Server URL:")
        self._url_field = QLineEdit()
        self._url_field.setPlaceholderText("http://localhost:11434")
        layout.addWidget(self._url_label)
        layout.addWidget(self._url_field)

        self._model_label = QLabel("Model (optional):")
        self._model_field = QLineEdit()
        self._model_field.setPlaceholderText("gpt-4o-mini / llama3.2:3b")
        layout.addWidget(self._model_label)
        layout.addWidget(self._model_field)

        self._hint = QLabel("")
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._hint)

        layout.addStretch()
        self._update_provider_fields(0)
        return w

    def _update_provider_fields(self, idx: int) -> None:
        provider = self._provider_combo.currentText()
        show_key = "Skip" not in provider and "Local" not in provider
        show_url = "Compatible" in provider or "Local" in provider
        show_model = "Compatible" in provider or "Local" in provider
        self._key_label.setVisible(show_key)
        self._key_field.setVisible(show_key)
        self._url_label.setVisible(show_url)
        self._url_field.setVisible(show_url)
        self._model_label.setVisible(show_model)
        self._model_field.setVisible(show_model)
        hints = {
            "Anthropic": "Get your key at console.anthropic.com → API Keys",
            "OpenAI": (
                "Get your key at platform.openai.com → API keys.\n"
                "For a custom server, also enter the base URL."
            ),
            "Google": "Get your key at aistudio.google.com → Get API key",
            "Local": (
                "Start Ollama (ollama serve) or LM Studio first,\n"
                "then enter the server URL."
            ),
            "Skip": "You can configure a provider later in Settings.",
        }
        for k, v in hints.items():
            if k in provider:
                self._hint.setText(v)
                break

    def _page_hotkey(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        title = QLabel("Set your global hotkey")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        desc = QLabel(
            "This key combination summons the SmartPad panel from any application.\n"
            "Use + to separate keys, e.g.  ctrl+alt+space  or  ctrl+shift+space"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._hotkey_field = QLineEdit(self._settings.hotkey)
        self._hotkey_field.setPlaceholderText("ctrl+alt+space")
        layout.addWidget(self._hotkey_field)

        import sys

        if sys.platform == "darwin":
            note = QLabel(
                "macOS requires Accessibility permission:\n"
                "System Settings → Privacy & Security → Accessibility → enable SmartPad."
            )
            note.setWordWrap(True)
            note.setStyleSheet("color: orange; font-size: 11px;")
            layout.addWidget(note)

        layout.addStretch()
        return w

    def _page_done(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("You're all set!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin: 20px 0;")
        desc = QLabel(
            "SmartPad is ready to use.\n\n"
            "Press your hotkey or click the tray icon to open the panel.\n"
            "Type anything to chat, or use /note /task /remind /snippet\n"
            "to save items directly."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch()
        return w

    def _go_next(self) -> None:
        idx = self._stack.currentIndex()
        if idx == 1:
            self._save_provider()
        elif idx == 2:
            self._save_hotkey()
        if idx < self._stack.count() - 1:
            self._stack.setCurrentIndex(idx + 1)
        else:
            self.accept()
        self._update_nav()

    def _go_back(self) -> None:
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
        self._update_nav()

    def _update_nav(self) -> None:
        idx = self._stack.currentIndex()
        total = self._stack.count()
        self._back_btn.setEnabled(idx > 0)
        self._next_btn.setText("Finish" if idx == total - 1 else "Next")
        self._page_indicator.setText(f"Step {idx + 1} of {total}")

    def _save_provider(self) -> None:
        provider = self._provider_combo.currentText()
        if "Skip" in provider:
            return
        key = self._key_field.text().strip()
        url = self._url_field.text().strip()
        model = self._model_field.text().strip()
        if "Anthropic" in provider and key:
            keyring.set_password(_SVC, "anthropic_api_key", key)
            keyring.set_password(_SVC, "preferred_provider", "anthropic")
        elif "OpenAI" in provider:
            if key:
                keyring.set_password(_SVC, "openai_api_key", key)
            if url:
                keyring.set_password(_SVC, "openai_base_url", url)
            if model:
                keyring.set_password(_SVC, "openai_model", model)
            keyring.set_password(_SVC, "preferred_provider", "openai")
        elif "Google" in provider and key:
            keyring.set_password(_SVC, "google_api_key", key)
            keyring.set_password(_SVC, "preferred_provider", "google")
        elif "Local" in provider and url:
            keyring.set_password(_SVC, "local_server_url", url)
            if model:
                keyring.set_password(_SVC, "local_model", model)
            keyring.set_password(_SVC, "preferred_provider", "local")
        logger.info("Onboarding: provider saved.")

    def _save_hotkey(self) -> None:
        hotkey = self._hotkey_field.text().strip()
        if hotkey:
            self._settings.hotkey = hotkey
            try:
                self._settings.save()
            except Exception as exc:
                logger.warning("Could not save hotkey: {}", exc)


def needs_onboarding() -> bool:
    """Return True if no provider is configured yet."""
    import os

    env_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "LOCAL_SERVER_URL"]
    if any(os.environ.get(k) for k in env_keys):
        return False
    kr_keys = ["anthropic_api_key", "openai_api_key", "google_api_key", "local_server_url"]
    for key in kr_keys:
        try:
            if keyring.get_password(_SVC, key):
                return False
        except Exception:
            pass
    return True
