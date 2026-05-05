"""QSS theme — macOS/iOS-inspired glass dark/light themes."""
from __future__ import annotations

DARK_THEME = """
/* ── Reset ─────────────────────────────────────────────────────────────────── */
* {
    font-family: "SF Pro Text", "Segoe UI Variable", "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    outline: none;
}

QWidget {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.88);
}

/* ── Floating panel ─────────────────────────────────────────────────────────── */
#FloatingPanel {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

/* ── Header ─────────────────────────────────────────────────────────────────── */
#PanelHeader {
    background-color: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    min-height: 46px;
    max-height: 46px;
}

#HeaderDot {
    color: #007AFF;
    font-size: 9px;
}

#HeaderTitle {
    color: rgba(255, 255, 255, 0.85);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.1px;
}

#CloseButton, #SettingsButton, #BrowseButton {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.32);
    border: none;
    border-radius: 6px;
    font-size: 13px;
    padding: 3px 6px;
}

#CloseButton:hover {
    background-color: rgba(255, 59, 48, 0.14);
    color: rgba(255, 80, 70, 1.0);
}

#SettingsButton:hover, #BrowseButton:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.80);
}

/* ── Chat scroll area ───────────────────────────────────────────────────────── */
#ChatScrollArea {
    background-color: transparent;
    border: none;
}

#ChatScrollArea QScrollBar:vertical {
    background-color: transparent;
    width: 3px;
    margin: 8px 0;
}

#ChatScrollArea QScrollBar::handle:vertical {
    background-color: rgba(255, 255, 255, 0.12);
    border-radius: 2px;
    min-height: 24px;
}

#ChatScrollArea QScrollBar::handle:vertical:hover {
    background-color: rgba(255, 255, 255, 0.22);
}

#ChatScrollArea QScrollBar::add-line:vertical,
#ChatScrollArea QScrollBar::sub-line:vertical { height: 0; }

#ChatContainer {
    background-color: transparent;
}

/* ── Bubbles ─────────────────────────────────────────────────────────────────── */
#BubbleUser {
    background-color: #007AFF;
    color: #ffffff;
    border-radius: 16px 16px 4px 16px;
    padding: 10px 14px;
    margin: 2px 10px 2px 52px;
}

#BubbleUser QLabel {
    background-color: transparent;
    color: #ffffff;
}

#BubbleAI {
    background-color: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 4px 16px 16px 16px;
    padding: 10px 14px;
    margin: 2px 52px 2px 10px;
}

#BubbleAI QLabel {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.88);
}

#BubbleNote {
    background-color: rgba(255, 214, 10, 0.06);
    color: rgba(255, 220, 80, 0.90);
    border: 1px solid rgba(255, 214, 10, 0.10);
    border-left: 2px solid rgba(255, 214, 10, 0.50);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 10px;
}
#BubbleNote QLabel { background-color: transparent; }

#BubbleTask {
    background-color: rgba(0, 122, 255, 0.06);
    color: rgba(100, 180, 255, 0.90);
    border: 1px solid rgba(0, 122, 255, 0.10);
    border-left: 2px solid rgba(0, 122, 255, 0.50);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 10px;
}
#BubbleTask QLabel { background-color: transparent; }

#BubbleReminder {
    background-color: rgba(255, 149, 0, 0.06);
    color: rgba(255, 185, 80, 0.90);
    border: 1px solid rgba(255, 149, 0, 0.10);
    border-left: 2px solid rgba(255, 149, 0, 0.50);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 10px;
}
#BubbleReminder QLabel { background-color: transparent; }

#BubbleSnippet {
    background-color: rgba(48, 209, 88, 0.05);
    color: rgba(140, 225, 140, 0.90);
    border: 1px solid rgba(48, 209, 88, 0.09);
    border-left: 2px solid rgba(48, 209, 88, 0.45);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 10px;
    font-family: "SF Mono", "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}
#BubbleSnippet QLabel { background-color: transparent; }

#BubbleError {
    background-color: rgba(255, 59, 48, 0.06);
    color: rgba(255, 100, 90, 0.90);
    border: 1px solid rgba(255, 59, 48, 0.10);
    border-left: 2px solid rgba(255, 59, 48, 0.45);
    border-radius: 10px;
    padding: 9px 14px;
    margin: 2px 10px;
}
#BubbleError QLabel { background-color: transparent; }

/* ── Input area ──────────────────────────────────────────────────────────────── */
#InputArea {
    background-color: rgba(255, 255, 255, 0.02);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding: 10px 12px 12px 12px;
}

#MessageInput {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 9px 12px;
    font-size: 13px;
    selection-background-color: rgba(0, 122, 255, 0.30);
}

#MessageInput:focus {
    border: 1px solid rgba(0, 122, 255, 0.45);
    background-color: rgba(255, 255, 255, 0.07);
}

/* ── Status bar ──────────────────────────────────────────────────────────────── */
#StatusBar {
    color: rgba(255, 255, 255, 0.22);
    font-size: 10px;
    padding: 1px 14px 6px 14px;
    min-height: 16px;
    max-height: 16px;
}

/* ── Send button ─────────────────────────────────────────────────────────────── */
#SendButton {
    background-color: #007AFF;
    color: #ffffff;
    border: none;
    border-radius: 20px;
    font-size: 16px;
    min-width: 40px;
    min-height: 40px;
    max-width: 40px;
    max-height: 40px;
}

#SendButton:hover { background-color: #0a84ff; }
#SendButton:pressed { background-color: #005ec9; }

/* ── Tray / context menu ─────────────────────────────────────────────────────── */
QMenu {
    background-color: rgba(24, 24, 34, 0.97);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    padding: 4px;
    font-size: 13px;
}
QMenu::item { padding: 6px 20px; border-radius: 6px; }
QMenu::item:selected { background-color: rgba(0, 122, 255, 0.18); color: #ffffff; }
QMenu::separator { height: 1px; background-color: rgba(255, 255, 255, 0.06); margin: 3px 8px; }

/* ── Dialogs ─────────────────────────────────────────────────────────────────── */
QDialog {
    background-color: #0c0c18;
    color: rgba(255, 255, 255, 0.88);
    border-radius: 12px;
}

QLabel {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.80);
}

/* ── Dialog title bar ────────────────────────────────────────────────────────── */
#DialogTitleBar {
    background-color: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

#DialogTitle {
    color: rgba(255, 255, 255, 0.90);
    font-size: 14px;
    font-weight: 600;
}

#DialogDoneButton {
    background-color: #007AFF;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 14px;
    min-height: 28px;
    max-height: 28px;
}
#DialogDoneButton:hover { background-color: #0a84ff; }
#DialogDoneButton:pressed { background-color: #005ec9; }

#DialogCloseButton {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.35);
    border: none;
    border-radius: 6px;
    font-size: 14px;
    padding: 4px 8px;
}
#DialogCloseButton:hover { background-color: rgba(255, 59, 48, 0.14); color: rgba(255, 80, 70, 1.0); }

/* ── Tabs ────────────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px;
    background-color: rgba(255, 255, 255, 0.02);
    top: -1px;
}
QTabBar { background-color: transparent; }
QTabBar::tab {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.40);
    padding: 8px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}
QTabBar::tab:selected { color: rgba(255, 255, 255, 0.90); border-bottom: 2px solid #007AFF; }
QTabBar::tab:hover:!selected { color: rgba(255, 255, 255, 0.65); }

/* ── Group boxes ─────────────────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px;
    margin-top: 18px;
    padding-top: 10px;
    color: rgba(255, 255, 255, 0.38);
    font-size: 11px;
    font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; top: -1px; }

/* ── Form inputs ─────────────────────────────────────────────────────────────── */
QLineEdit {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 30px;
    selection-background-color: rgba(0, 122, 255, 0.30);
}
QLineEdit:focus { border: 1px solid rgba(0, 122, 255, 0.48); background-color: rgba(255, 255, 255, 0.07); }
QLineEdit:disabled { color: rgba(255, 255, 255, 0.22); border-color: rgba(255, 255, 255, 0.04); }

QComboBox {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 30px;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #1a1a28;
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 8px;
    selection-background-color: rgba(0, 122, 255, 0.18);
    outline: none;
    padding: 4px;
}

QSpinBox {
    background-color: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 13px;
    min-height: 30px;
}
QSpinBox::up-button, QSpinBox::down-button { background-color: transparent; border: none; width: 18px; }

QCheckBox { color: rgba(255, 255, 255, 0.78); spacing: 8px; font-size: 13px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1.5px solid rgba(255, 255, 255, 0.18); border-radius: 5px; background-color: rgba(255, 255, 255, 0.04); }
QCheckBox::indicator:checked { background-color: #007AFF; border-color: #007AFF; }

QPushButton {
    background-color: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    min-height: 30px;
}
QPushButton:hover { background-color: rgba(255, 255, 255, 0.11); color: rgba(255, 255, 255, 0.96); }
QPushButton:pressed { background-color: rgba(255, 255, 255, 0.04); }
QPushButton[default="true"], QPushButton:default { background-color: #007AFF; border: none; color: #ffffff; font-weight: 600; }
QPushButton[default="true"]:hover, QPushButton:default:hover { background-color: #0a84ff; }
QDialogButtonBox QPushButton { min-width: 80px; }

/* ── Scrollbars ──────────────────────────────────────────────────────────────── */
QScrollBar:vertical { background-color: transparent; width: 3px; }
QScrollBar::handle:vertical { background-color: rgba(255, 255, 255, 0.12); border-radius: 2px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background-color: rgba(255, 255, 255, 0.22); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── List & text widgets ─────────────────────────────────────────────────────── */
QListWidget {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    color: rgba(255, 255, 255, 0.88);
    padding: 4px;
    outline: none;
}
QListWidget::item { padding: 8px 10px; border-radius: 7px; color: rgba(255, 255, 255, 0.75); }
QListWidget::item:selected { background-color: rgba(0, 122, 255, 0.16); color: #ffffff; }
QListWidget::item:hover:!selected { background-color: rgba(255, 255, 255, 0.05); }

QTextEdit {
    background-color: rgba(255, 255, 255, 0.03);
    color: rgba(255, 255, 255, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 10px;
    font-size: 13px;
}

QSplitter::handle { background-color: rgba(255, 255, 255, 0.05); width: 1px; }

/* ── Slash menu ──────────────────────────────────────────────────────────────── */
#SlashMenu {
    background-color: rgba(16, 16, 26, 0.98);
    border: 1px solid rgba(255, 255, 255, 0.11);
    border-radius: 12px;
}
#SlashMenu QListWidget { background-color: transparent; border: none; border-radius: 0; color: rgba(255, 255, 255, 0.82); font-size: 13px; padding: 4px; }
#SlashMenu QListWidget::item { padding: 8px 12px; border-radius: 7px; color: rgba(255, 255, 255, 0.72); }
#SlashMenu QListWidget::item:selected { background-color: rgba(0, 122, 255, 0.20); color: #ffffff; }
#SlashMenu QListWidget::item:hover:!selected { background-color: rgba(255, 255, 255, 0.06); }
"""

LIGHT_THEME = """
* { font-family: "SF Pro Text", "Segoe UI Variable", "Segoe UI", "Inter", sans-serif; font-size: 13px; outline: none; }
QWidget { background-color: transparent; color: #1c1c1e; }
QDialog { background-color: #f2f2f7; color: #1c1c1e; border-radius: 12px; }
QLabel { background-color: transparent; color: #1c1c1e; }

#FloatingPanel { border: 1px solid rgba(0,0,0,0.12); border-radius: 16px; }
#PanelHeader { background-color: rgba(255,255,255,0.60); border-bottom: 1px solid rgba(0,0,0,0.08); border-top-left-radius: 16px; border-top-right-radius: 16px; min-height: 46px; max-height: 46px; }
#HeaderDot { color: #007AFF; font-size: 9px; }
#HeaderTitle { color: rgba(0,0,0,0.82); font-size: 13px; font-weight: 600; }
#CloseButton, #SettingsButton, #BrowseButton { background-color: transparent; color: rgba(0,0,0,0.30); border: none; border-radius: 6px; font-size: 13px; padding: 3px 6px; }
#CloseButton:hover { background-color: rgba(255,59,48,0.10); color: rgba(220,40,30,1.0); }
#SettingsButton:hover, #BrowseButton:hover { background-color: rgba(0,0,0,0.06); color: rgba(0,0,0,0.65); }

#ChatScrollArea { background-color: transparent; border: none; }
#ChatScrollArea QScrollBar:vertical { background-color: transparent; width: 3px; }
#ChatScrollArea QScrollBar::handle:vertical { background-color: rgba(0,0,0,0.14); border-radius: 2px; min-height: 24px; }
#ChatScrollArea QScrollBar::add-line:vertical, #ChatScrollArea QScrollBar::sub-line:vertical { height: 0; }
#ChatContainer { background-color: transparent; }

#BubbleUser { background-color: #007AFF; color: #fff; border-radius: 16px 16px 4px 16px; padding: 10px 14px; margin: 2px 10px 2px 52px; }
#BubbleUser QLabel { background-color: transparent; color: #fff; }
#BubbleAI { background-color: rgba(0,0,0,0.05); color: #1c1c1e; border: 1px solid rgba(0,0,0,0.07); border-radius: 4px 16px 16px 16px; padding: 10px 14px; margin: 2px 52px 2px 10px; }
#BubbleAI QLabel { background-color: transparent; color: #1c1c1e; }
#BubbleNote { background-color: rgba(255,204,0,0.10); color: #7a5800; border: 1px solid rgba(255,204,0,0.20); border-left: 2px solid rgba(255,149,0,0.70); border-radius: 10px; padding: 9px 14px; margin: 2px 10px; }
#BubbleNote QLabel { background-color: transparent; }
#BubbleTask { background-color: rgba(0,122,255,0.07); color: #003f99; border: 1px solid rgba(0,122,255,0.15); border-left: 2px solid #007AFF; border-radius: 10px; padding: 9px 14px; margin: 2px 10px; }
#BubbleTask QLabel { background-color: transparent; }
#BubbleReminder { background-color: rgba(255,149,0,0.07); color: #7a3800; border: 1px solid rgba(255,149,0,0.15); border-left: 2px solid rgba(255,149,0,0.70); border-radius: 10px; padding: 9px 14px; margin: 2px 10px; }
#BubbleReminder QLabel { background-color: transparent; }
#BubbleSnippet { background-color: rgba(0,0,0,0.88); color: #a8f0a0; border: 1px solid rgba(0,0,0,0.15); border-left: 2px solid #30d158; border-radius: 10px; padding: 9px 14px; margin: 2px 10px; font-family: "SF Mono","Cascadia Code","Consolas",monospace; font-size: 12px; }
#BubbleSnippet QLabel { background-color: transparent; }
#BubbleError { background-color: rgba(255,59,48,0.07); color: #8b0000; border: 1px solid rgba(255,59,48,0.15); border-left: 2px solid rgba(255,59,48,0.70); border-radius: 10px; padding: 9px 14px; margin: 2px 10px; }
#BubbleError QLabel { background-color: transparent; }

#InputArea { background-color: rgba(0,0,0,0.02); border-top: 1px solid rgba(0,0,0,0.07); padding: 10px 12px 12px 12px; }
#MessageInput { background-color: rgba(255,255,255,0.80); color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); border-radius: 12px; padding: 9px 12px; font-size: 13px; selection-background-color: rgba(0,122,255,0.25); }
#MessageInput:focus { border: 1px solid rgba(0,122,255,0.50); }
#StatusBar { color: rgba(0,0,0,0.28); font-size: 10px; padding: 1px 14px 6px 14px; min-height: 16px; max-height: 16px; }
#SendButton { background-color: #007AFF; color: #fff; border: none; border-radius: 20px; font-size: 16px; min-width: 40px; min-height: 40px; max-width: 40px; max-height: 40px; }
#SendButton:hover { background-color: #0a84ff; }
#SendButton:pressed { background-color: #005ec9; }

QMenu { background-color: rgba(242,242,247,0.97); color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); border-radius: 10px; padding: 4px; }
QMenu::item { padding: 6px 20px; border-radius: 6px; }
QMenu::item:selected { background-color: rgba(0,122,255,0.10); }
QMenu::separator { height: 1px; background-color: rgba(0,0,0,0.07); margin: 3px 8px; }

#DialogTitleBar { background-color: rgba(0,0,0,0.03); border-bottom: 1px solid rgba(0,0,0,0.07); border-top-left-radius: 12px; border-top-right-radius: 12px; }
#DialogTitle { color: rgba(0,0,0,0.85); font-size: 14px; font-weight: 600; }
#DialogDoneButton { background-color: #007AFF; color: #fff; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; padding: 4px 14px; min-height: 28px; max-height: 28px; }
#DialogDoneButton:hover { background-color: #0a84ff; }
#DialogCloseButton { background-color: transparent; color: rgba(0,0,0,0.30); border: none; border-radius: 6px; font-size: 14px; padding: 4px 8px; }
#DialogCloseButton:hover { background-color: rgba(255,59,48,0.10); color: rgba(220,40,30,1.0); }

QTabWidget::pane { border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; background-color: rgba(255,255,255,0.40); top: -1px; }
QTabBar { background-color: transparent; }
QTabBar::tab { background-color: transparent; color: rgba(0,0,0,0.40); padding: 8px 20px; border: none; border-bottom: 2px solid transparent; font-size: 13px; font-weight: 500; }
QTabBar::tab:selected { color: #1c1c1e; border-bottom: 2px solid #007AFF; }
QTabBar::tab:hover:!selected { color: rgba(0,0,0,0.60); }

QGroupBox { border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; margin-top: 18px; padding-top: 10px; color: rgba(0,0,0,0.38); font-size: 11px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; top: -1px; }

QLineEdit { background-color: #ffffff; color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); border-radius: 8px; padding: 6px 10px; font-size: 13px; min-height: 30px; selection-background-color: rgba(0,122,255,0.25); }
QLineEdit:focus { border: 1px solid rgba(0,122,255,0.50); }
QComboBox { background-color: #ffffff; color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); border-radius: 8px; padding: 6px 10px; font-size: 13px; min-height: 30px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); selection-background-color: rgba(0,122,255,0.10); outline: none; padding: 4px; }
QSpinBox { background-color: #ffffff; color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); border-radius: 8px; padding: 6px 8px; font-size: 13px; min-height: 30px; }
QSpinBox::up-button, QSpinBox::down-button { background-color: transparent; border: none; width: 18px; }
QCheckBox { color: #1c1c1e; spacing: 8px; font-size: 13px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1.5px solid rgba(0,0,0,0.18); border-radius: 5px; background-color: #fff; }
QCheckBox::indicator:checked { background-color: #007AFF; border-color: #007AFF; }
QPushButton { background-color: rgba(0,0,0,0.05); color: #1c1c1e; border: 1px solid rgba(0,0,0,0.10); border-radius: 8px; padding: 6px 14px; font-size: 13px; min-height: 30px; }
QPushButton:hover { background-color: rgba(0,122,255,0.08); border-color: rgba(0,122,255,0.25); }
QPushButton:pressed { background-color: rgba(0,122,255,0.12); }
QPushButton[default="true"], QPushButton:default { background-color: #007AFF; color: #fff; border: none; font-weight: 600; }
QPushButton[default="true"]:hover, QPushButton:default:hover { background-color: #0a84ff; }
QDialogButtonBox QPushButton { min-width: 80px; }

QScrollBar:vertical { background-color: transparent; width: 3px; }
QScrollBar::handle:vertical { background-color: rgba(0,0,0,0.14); border-radius: 2px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background-color: rgba(0,0,0,0.25); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QListWidget { background-color: rgba(255,255,255,0.70); border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; color: #1c1c1e; padding: 4px; outline: none; }
QListWidget::item { padding: 8px 10px; border-radius: 7px; }
QListWidget::item:selected { background-color: rgba(0,122,255,0.12); color: #1c1c1e; }
QListWidget::item:hover:!selected { background-color: rgba(0,0,0,0.04); }
QTextEdit { background-color: rgba(255,255,255,0.70); color: #1c1c1e; border: 1px solid rgba(0,0,0,0.08); border-radius: 10px; padding: 10px; }
QSplitter::handle { background-color: rgba(0,0,0,0.06); width: 1px; }

#SlashMenu { background-color: rgba(242,242,247,0.98); border: 1px solid rgba(0,0,0,0.12); border-radius: 12px; }
#SlashMenu QListWidget { background-color: transparent; border: none; color: #1c1c1e; font-size: 13px; padding: 4px; }
#SlashMenu QListWidget::item { padding: 8px 12px; border-radius: 7px; }
#SlashMenu QListWidget::item:selected { background-color: rgba(0,122,255,0.12); }
#SlashMenu QListWidget::item:hover:!selected { background-color: rgba(0,0,0,0.04); }
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
