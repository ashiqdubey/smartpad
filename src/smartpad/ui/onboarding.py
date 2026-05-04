"""Onboarding flow — SPEC.MD section 11.

Four-tier AI setup wizard followed by 3-card walkthrough.
Shown on first launch (settings key 'onboarding_complete' not set).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class OnboardingDialog(QDialog):
    """First-run wizard.

    Signals:
        setup_complete(str): emitted when onboarding finishes.
            Value is the chosen setup type:
            "quick_start" | "ollama" | "cloud" | "advanced" | "skip"
    """

    setup_complete = pyqtSignal(str)

    def __init__(self, detected_ollama: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to SmartPad")
        self.setFixedSize(480, 420)
        self.setModal(True)
        self._detected_ollama = detected_ollama
        self._choice: str = "skip"
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._stack.addWidget(self._build_setup_page())
        self._stack.addWidget(self._build_walkthrough_page())

    # ── Page 1: AI setup ──────────────────────────────────────────────────────

    def _build_setup_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 16)
        layout.setSpacing(12)

        title = QLabel("Welcome to SmartPad 👋")
        title.setObjectName("OnboardingTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        subtitle = QLabel("How would you like to set up your AI?")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        def _option_btn(emoji: str, title: str, desc: str, key: str) -> QPushButton:
            btn = QPushButton(f"{emoji}  {title}\n{desc}")
            btn.setObjectName("OnboardingOption")
            btn.setFixedHeight(64)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 16px;
                    border: 1px solid #3d3f45;
                    border-radius: 8px;
                    background: #2b2d31;
                    color: #dcddde;
                    font-size: 13px;
                }
                QPushButton:hover { background: #36393f; border-color: #5865f2; }
                QPushButton:pressed { background: #5865f2; }
            """)
            btn.clicked.connect(lambda: self._choose(key))
            return btn

        layout.addWidget(_option_btn(
            "✨", "Quick start (recommended)",
            "Download a small AI — runs locally, free, no setup",
            "quick_start",
        ))

        ollama_label = "Use Ollama (detected)" if self._detected_ollama else "Use Ollama / LM Studio"
        layout.addWidget(_option_btn(
            "🔌", ollama_label,
            "Use models you already have running",
            "ollama",
        ))

        layout.addWidget(_option_btn(
            "☁️", "Use a cloud API",
            "OpenAI, Anthropic Claude, Google Gemini, OpenRouter",
            "cloud",
        ))

        layout.addWidget(_option_btn(
            "⚙️", "Advanced setup",
            "Custom endpoint, vLLM, remote server",
            "advanced",
        ))

        skip = QPushButton("Skip for now →")
        skip.setFlat(True)
        skip.clicked.connect(lambda: self._choose("skip"))
        layout.addWidget(skip, alignment=Qt.AlignmentFlag.AlignRight)
        return page

    # ── Page 2: Walkthrough ───────────────────────────────────────────────────

    def _build_walkthrough_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 16)
        layout.setSpacing(16)

        cards = [
            ("⌨️  Open anywhere", "Press Ctrl+Alt+Space to open SmartPad from any app."),
            ("💬  Capture anything", "Type a question, note, task, or reminder. SmartPad organises it automatically."),
            ("🔍  Use slash commands", "Type / to see all commands: /note, /task, /remind, /find, and more."),
        ]

        self._card_stack = QStackedWidget()
        self._card_idx = 0

        for title, desc in cards:
            card = QWidget()
            card.setStyleSheet("background: #2b2d31; border-radius: 12px;")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 24, 24, 24)
            t = QLabel(title)
            t.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #b9bbbe;")
            cl.addWidget(t)
            cl.addWidget(d)
            self._card_stack.addWidget(card)

        layout.addWidget(self._card_stack, stretch=1)

        nav = QHBoxLayout()
        self._back_btn = QPushButton("← Back")
        self._back_btn.clicked.connect(self._prev_card)
        self._next_btn = QPushButton("Next →")
        self._next_btn.clicked.connect(self._next_card)
        self._dots = QLabel("● ○ ○")
        self._dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self._back_btn)
        nav.addWidget(self._dots, stretch=1)
        nav.addWidget(self._next_btn)
        layout.addLayout(nav)
        self._update_nav()
        return page

    # ── Navigation ────────────────────────────────────────────────────────────

    def _choose(self, key: str) -> None:
        self._choice = key
        self._card_idx = 0
        self._card_stack.setCurrentIndex(0)
        self._update_nav()
        self._stack.setCurrentIndex(1)

    def _prev_card(self) -> None:
        if self._card_idx > 0:
            self._card_idx -= 1
            self._card_stack.setCurrentIndex(self._card_idx)
            self._update_nav()

    def _next_card(self) -> None:
        n = self._card_stack.count()
        if self._card_idx < n - 1:
            self._card_idx += 1
            self._card_stack.setCurrentIndex(self._card_idx)
            self._update_nav()
        else:
            self.setup_complete.emit(self._choice)
            self.accept()

    def _update_nav(self) -> None:
        n = self._card_stack.count()
        i = self._card_idx
        self._back_btn.setEnabled(i > 0)
        self._next_btn.setText("Get started →" if i == n - 1 else "Next →")
        dots = " ".join("●" if j == i else "○" for j in range(n))
        self._dots.setText(dots)
