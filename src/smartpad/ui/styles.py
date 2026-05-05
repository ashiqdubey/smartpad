"""QSS theme — glassmorphism dark/light themes."""
from __future__ import annotations

DARK_THEME = """
/* ── Base ───────────────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI Variable", "Segoe UI", "Inter", "SF Pro Text", sans-serif;
    font-size: 13px;
    outline: none;
}

QWidget {
    background-color: transparent;
    color: #e2e2f0;
}

QDialog, QMainWindow {
    background-color: #12122a;
    color: #e2e2f0;
}

/* ── Floating panel ──────────────────────────────────────────────────────── */
#FloatingPanel {
    background-color: rgba(12, 12, 28, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 16px;
}

/* ── Header ─────────────────────────────────────────────────────────────── */
#PanelHeader {
    background-color: rgba(255, 255, 255, 0.04);
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    min-height: 46px;
    max-height: 46px;
    padding: 0 4px;
}

#HeaderTitle {
    color: rgba(230, 230, 255, 0.9);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

#CloseButton, #SettingsButton, #BrowseButton {
    background-color: transparent;
    color: rgba(200, 200, 230, 0.55);
    border: none;
    border-radius: 7px;
    font-size: 15px;
    padding: 2px;
}

#CloseButton:hover {
    background-color: rgba(243, 139, 168, 0.18);
    color: #f38ba8;
}

#SettingsButton:hover, #BrowseButton:hover {
    background-color: rgba(124, 139, 255, 0.18);
    color: #a0aaff;
}

/* ── Chat scroll area ────────────────────────────────────────────────────── */
#ChatScrollArea {
    background-color: transparent;
    border: none;
}

#ChatScrollArea QScrollBar:vertical {
    background-color: transparent;
    width: 5px;
    margin: 4px 0;
}

#ChatScrollArea QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
    min-height: 20px;
}

#ChatScrollArea QScrollBar::handle:vertical:hover {
    background-color: rgba(255, 255, 255, 0.28);
}

#ChatScrollArea QScrollBar::add-line:vertical,
#ChatScrollArea QScrollBar::sub-line:vertical {
    height: 0;
}

#ChatContainer {
    background-color: transparent;
}

/* ── Bubbles ─────────────────────────────────────────────────────────────── */
#BubbleUser {
    background-color: rgba(100, 115, 255, 0.82);
    color: #ffffff;
    border-radius: 14px 14px 4px 14px;
    padding: 9px 14px;
    margin: 2px 8px 2px 40px;
}

#BubbleUser QLabel {
    background-color: transparent;
    color: #ffffff;
}

#BubbleAI {
    background-color: rgba(255, 255, 255, 0.07);
    color: #dde0f5;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px 14px 14px 4px;
    padding: 9px 14px;
    margin: 2px 40px 2px 8px;
}

#BubbleAI QLabel {
    background-color: transparent;
    color: #dde0f5;
}

#BubbleNote {
    background-color: rgba(249, 226, 175, 0.10);
    color: #f5deb3;
    border: 1px solid rgba(249, 226, 175, 0.18);
    border-left: 3px solid rgba(249, 226, 175, 0.6);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 8px;
}

#BubbleNote QLabel { background-color: transparent; }

#BubbleTask {
    background-color: rgba(137, 180, 250, 0.09);
    color: #c0d4ff;
    border: 1px solid rgba(137, 180, 250, 0.18);
    border-left: 3px solid rgba(137, 180, 250, 0.7);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 8px;
}

#BubbleTask QLabel { background-color: transparent; }

#BubbleReminder {
    background-color: rgba(250, 179, 135, 0.09);
    color: #ffd0a0;
    border: 1px solid rgba(250, 179, 135, 0.18);
    border-left: 3px solid rgba(250, 179, 135, 0.7);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 8px;
}

#BubbleReminder QLabel { background-color: transparent; }

#BubbleSnippet {
    background-color: rgba(166, 227, 161, 0.07);
    color: #b8f0b0;
    border: 1px solid rgba(166, 227, 161, 0.15);
    border-left: 3px solid rgba(166, 227, 161, 0.6);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 8px;
    font-family: "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 12px;
}

#BubbleSnippet QLabel { background-color: transparent; }

#BubbleError {
    background-color: rgba(243, 139, 168, 0.09);
    color: #ffb0c0;
    border: 1px solid rgba(243, 139, 168, 0.18);
    border-left: 3px solid rgba(243, 139, 168, 0.7);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 8px;
}

#BubbleError QLabel { background-color: transparent; }

/* ── Input area ──────────────────────────────────────────────────────────── */
#InputArea {
    background-color: rgba(255, 255, 255, 0.03);
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    padding: 10px 10px 10px 10px;
}

#MessageInput {
    background-color: rgba(255, 255, 255, 0.07);
    color: #e2e2f0;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: rgba(124, 139, 255, 0.4);
}

#MessageInput:focus {
    border: 1px solid rgba(124, 139, 255, 0.55);
    background-color: rgba(255, 255, 255, 0.09);
}

/* ── Status bar ──────────────────────────────────────────────────────────── */
#StatusBar {
    background-color: transparent;
    color: rgba(180, 180, 210, 0.4);
    font-size: 10px;
    padding: 2px 14px 5px 14px;
    border-bottom-left-radius: 16px;
    border-bottom-right-radius: 16px;
    min-height: 18px;
    max-height: 18px;
}

/* ── Send button ─────────────────────────────────────────────────────────── */
#SendButton {
    background-color: rgba(100, 115, 255, 0.80);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 36px;
}

#SendButton:hover {
    background-color: rgba(120, 135, 255, 0.95);
}

#SendButton:pressed {
    background-color: rgba(80, 95, 230, 0.95);
}

/* ── Tray / context menu ─────────────────────────────────────────────────── */
QMenu {
    background-color: rgba(18, 18, 40, 0.96);
    color: #dde0f5;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 5px;
    font-size: 13px;
}

QMenu::item {
    padding: 7px 22px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: rgba(124, 139, 255, 0.22);
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: rgba(255, 255, 255, 0.08);
    margin: 4px 8px;
}

/* ── Dialogs (Settings, Browse, Onboarding) ──────────────────────────────── */
QDialog {
    background-color: #14142e;
    color: #e2e2f0;
}

QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    background-color: rgba(255,255,255,0.03);
}

QTabBar::tab {
    background-color: transparent;
    color: rgba(200, 200, 230, 0.6);
    padding: 8px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}

QTabBar::tab:selected {
    color: #e2e2f0;
    border-bottom: 2px solid #7c8bff;
}

QTabBar::tab:hover:!selected {
    color: rgba(200, 200, 230, 0.9);
    background-color: rgba(255,255,255,0.04);
}

QGroupBox {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    font-weight: 600;
    color: rgba(200,200,230,0.8);
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    top: -1px;
}

QLineEdit {
    background-color: rgba(255, 255, 255, 0.07);
    color: #e2e2f0;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: rgba(124,139,255,0.4);
}

QLineEdit:focus {
    border: 1px solid rgba(124, 139, 255, 0.6);
    background-color: rgba(255, 255, 255, 0.10);
}

QComboBox {
    background-color: rgba(255,255,255,0.07);
    color: #e2e2f0;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    padding: 5px 10px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a38;
    color: #e2e2f0;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 6px;
    selection-background-color: rgba(124,139,255,0.3);
}

QSpinBox {
    background-color: rgba(255,255,255,0.07);
    color: #e2e2f0;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    padding: 5px 8px;
}

QCheckBox {
    color: #c8c8e8;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid rgba(255,255,255,0.20);
    border-radius: 4px;
    background-color: rgba(255,255,255,0.06);
}

QCheckBox::indicator:checked {
    background-color: #7c8bff;
    border-color: #7c8bff;
    image: none;
}

QPushButton {
    background-color: rgba(255,255,255,0.08);
    color: #dde0f5;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 7px;
    padding: 6px 14px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: rgba(124,139,255,0.18);
    border-color: rgba(124,139,255,0.35);
    color: #ffffff;
}

QPushButton:pressed {
    background-color: rgba(100,115,235,0.35);
}

QPushButton[default="true"], QPushButton:default {
    background-color: rgba(100,115,255,0.75);
    border-color: rgba(124,139,255,0.5);
    color: #ffffff;
    font-weight: 600;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 5px;
}

QScrollBar::handle:vertical {
    background-color: rgba(255,255,255,0.15);
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: rgba(255,255,255,0.28);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QListWidget {
    background-color: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    color: #dde0f5;
    padding: 4px;
}

QListWidget::item {
    padding: 7px 10px;
    border-radius: 6px;
    color: #dde0f5;
}

QListWidget::item:selected {
    background-color: rgba(124,139,255,0.25);
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: rgba(255,255,255,0.05);
}

QTextEdit {
    background-color: rgba(255,255,255,0.04);
    color: #dde0f5;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}

QLabel {
    background-color: transparent;
    color: #dde0f5;
}

QSplitter::handle {
    background-color: rgba(255,255,255,0.06);
    width: 1px;
}

/* ── Slash menu ──────────────────────────────────────────────────────────── */
#SlashMenu {
    background-color: rgba(16, 16, 36, 0.97);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
}

#SlashMenu QListWidget {
    background-color: transparent;
    border: none;
    border-radius: 0;
    color: #dde0f5;
    font-size: 13px;
    padding: 4px;
}

#SlashMenu QListWidget::item {
    padding: 7px 12px;
    border-radius: 6px;
    color: #c8c8e8;
}

#SlashMenu QListWidget::item:selected {
    background-color: rgba(124, 139, 255, 0.30);
    color: #ffffff;
}

#SlashMenu QListWidget::item:hover:!selected {
    background-color: rgba(255,255,255,0.06);
}
"""

LIGHT_THEME = """
* {
    font-family: "Segoe UI Variable", "Segoe UI", "Inter", "SF Pro Text", sans-serif;
    font-size: 13px;
    outline: none;
}

QWidget { background-color: transparent; color: #1a1a2e; }
QDialog, QMainWindow { background-color: #f0f0f8; color: #1a1a2e; }

#FloatingPanel {
    background-color: rgba(240, 240, 252, 0.92);
    border: 1px solid rgba(0,0,0,0.10);
    border-radius: 16px;
}

#PanelHeader {
    background-color: rgba(0,0,0,0.04);
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    border-bottom: 1px solid rgba(0,0,0,0.07);
    min-height: 46px;
    max-height: 46px;
}

#HeaderTitle { color: #1a1a2e; font-size: 13px; font-weight: 600; }

#CloseButton, #SettingsButton, #BrowseButton {
    background-color: transparent;
    color: rgba(0,0,0,0.35);
    border: none;
    border-radius: 7px;
    font-size: 15px;
}

#CloseButton:hover { background-color: rgba(220,30,30,0.12); color: #cc2020; }
#SettingsButton:hover, #BrowseButton:hover { background-color: rgba(59,130,246,0.12); color: #3b82f6; }

#ChatScrollArea { background-color: transparent; border: none; }
#ChatScrollArea QScrollBar:vertical { background-color: transparent; width: 5px; }
#ChatScrollArea QScrollBar::handle:vertical { background-color: rgba(0,0,0,0.15); border-radius: 3px; min-height: 20px; }
#ChatScrollArea QScrollBar::add-line:vertical, #ChatScrollArea QScrollBar::sub-line:vertical { height: 0; }
#ChatContainer { background-color: transparent; }

#BubbleUser { background-color: #3b82f6; color: #fff; border-radius: 14px 14px 4px 14px; padding: 9px 14px; margin: 2px 8px 2px 40px; }
#BubbleUser QLabel { background-color: transparent; color: #fff; }
#BubbleAI { background-color: rgba(0,0,0,0.05); color: #1a1a2e; border: 1px solid rgba(0,0,0,0.07); border-radius: 14px 14px 14px 4px; padding: 9px 14px; margin: 2px 40px 2px 8px; }
#BubbleAI QLabel { background-color: transparent; color: #1a1a2e; }
#BubbleNote { background-color: rgba(253,230,138,0.25); color: #7c5800; border: 1px solid rgba(253,230,138,0.5); border-left: 3px solid #f59e0b; border-radius: 10px; padding: 9px 14px; margin: 2px 8px; }
#BubbleNote QLabel { background-color: transparent; }
#BubbleTask { background-color: rgba(59,130,246,0.08); color: #1e3a70; border: 1px solid rgba(59,130,246,0.20); border-left: 3px solid #3b82f6; border-radius: 10px; padding: 9px 14px; margin: 2px 8px; }
#BubbleTask QLabel { background-color: transparent; }
#BubbleReminder { background-color: rgba(245,158,11,0.08); color: #7c3a00; border: 1px solid rgba(245,158,11,0.20); border-left: 3px solid #f59e0b; border-radius: 10px; padding: 9px 14px; margin: 2px 8px; }
#BubbleReminder QLabel { background-color: transparent; }
#BubbleSnippet { background-color: rgba(16,16,28,0.90); color: #a6e3a1; border: 1px solid rgba(0,0,0,0.15); border-left: 3px solid #22c55e; border-radius: 10px; padding: 9px 14px; margin: 2px 8px; font-family: "Cascadia Code","Consolas",monospace; font-size: 12px; }
#BubbleSnippet QLabel { background-color: transparent; }
#BubbleError { background-color: rgba(239,68,68,0.07); color: #991b1b; border: 1px solid rgba(239,68,68,0.18); border-left: 3px solid #ef4444; border-radius: 10px; padding: 9px 14px; margin: 2px 8px; }
#BubbleError QLabel { background-color: transparent; }

#InputArea { background-color: rgba(0,0,0,0.03); border-top: 1px solid rgba(0,0,0,0.07); padding: 10px; }
#MessageInput { background-color: #fff; color: #1a1a2e; border: 1px solid rgba(0,0,0,0.12); border-radius: 10px; padding: 8px 12px; font-size: 13px; selection-background-color: rgba(59,130,246,0.25); }
#MessageInput:focus { border: 1px solid rgba(59,130,246,0.55); }

#StatusBar { background-color: transparent; color: rgba(0,0,0,0.30); font-size: 10px; padding: 2px 14px 5px 14px; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px; min-height: 18px; max-height: 18px; }

#SendButton { background-color: #3b82f6; color: #fff; border: none; border-radius: 8px; padding: 0 16px; font-weight: 600; font-size: 13px; min-height: 36px; }
#SendButton:hover { background-color: #2563eb; }
#SendButton:pressed { background-color: #1d4ed8; }

QMenu { background-color: rgba(240,240,250,0.97); color: #1a1a2e; border: 1px solid rgba(0,0,0,0.12); border-radius: 10px; padding: 5px; }
QMenu::item { padding: 7px 22px; border-radius: 6px; }
QMenu::item:selected { background-color: rgba(59,130,246,0.12); }
QMenu::separator { height: 1px; background-color: rgba(0,0,0,0.08); margin: 4px 8px; }

QDialog { background-color: #f0f0f8; color: #1a1a2e; }
QTabWidget::pane { border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; background-color: rgba(255,255,255,0.5); }
QTabBar::tab { background-color: transparent; color: rgba(0,0,0,0.45); padding: 8px 18px; border: none; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: #1a1a2e; border-bottom: 2px solid #3b82f6; }
QGroupBox { border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; margin-top: 10px; padding-top: 6px; font-weight: 600; color: rgba(0,0,30,0.7); }
QLineEdit { background-color: #fff; color: #1a1a2e; border: 1px solid rgba(0,0,0,0.12); border-radius: 7px; padding: 6px 10px; }
QLineEdit:focus { border: 1px solid rgba(59,130,246,0.6); }
QComboBox { background-color: #fff; color: #1a1a2e; border: 1px solid rgba(0,0,0,0.12); border-radius: 7px; padding: 5px 10px; }
QComboBox QAbstractItemView { background-color: #fff; color: #1a1a2e; border: 1px solid rgba(0,0,0,0.12); selection-background-color: rgba(59,130,246,0.12); }
QSpinBox { background-color: #fff; color: #1a1a2e; border: 1px solid rgba(0,0,0,0.12); border-radius: 7px; padding: 5px 8px; }
QCheckBox { color: #1a1a2e; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid rgba(0,0,0,0.20); border-radius: 4px; background-color: #fff; }
QCheckBox::indicator:checked { background-color: #3b82f6; border-color: #3b82f6; }
QPushButton { background-color: rgba(0,0,0,0.05); color: #1a1a2e; border: 1px solid rgba(0,0,0,0.10); border-radius: 7px; padding: 6px 14px; }
QPushButton:hover { background-color: rgba(59,130,246,0.10); border-color: rgba(59,130,246,0.30); }
QPushButton[default="true"], QPushButton:default { background-color: #3b82f6; color: #fff; font-weight: 600; border-color: #2563eb; }
QListWidget { background-color: rgba(255,255,255,0.7); border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; color: #1a1a2e; padding: 4px; }
QListWidget::item { padding: 7px 10px; border-radius: 6px; }
QListWidget::item:selected { background-color: rgba(59,130,246,0.15); color: #1a1a2e; }
QTextEdit { background-color: rgba(255,255,255,0.7); color: #1a1a2e; border: 1px solid rgba(0,0,0,0.08); border-radius: 8px; padding: 8px; }
QLabel { background-color: transparent; color: #1a1a2e; }
QScrollBar:vertical { background-color: transparent; width: 5px; }
QScrollBar::handle:vertical { background-color: rgba(0,0,0,0.15); border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

#SlashMenu { background-color: rgba(240,240,250,0.98); border: 1px solid rgba(0,0,0,0.12); border-radius: 10px; }
#SlashMenu QListWidget { background-color: transparent; border: none; color: #1a1a2e; }
#SlashMenu QListWidget::item { padding: 7px 12px; border-radius: 6px; }
#SlashMenu QListWidget::item:selected { background-color: rgba(59,130,246,0.15); }
"""


def get_theme(name: str) -> str:
    if name == "dark":
        return DARK_THEME
    if name == "light":
        return LIGHT_THEME
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            bg = app.palette().window().color()
            if bg.lightness() < 128:
                return DARK_THEME
        return LIGHT_THEME
    except Exception:
        return DARK_THEME
