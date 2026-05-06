"""QSS theme — Aside-inspired glass dark/light themes."""
from __future__ import annotations

# Accent colours (oklch → rgb approximations):
#   --accent:   oklch(0.66 0.22 290) ≈ #7c6ef5  violet-purple
#   --accent-2: oklch(0.72 0.20 340) ≈ #c87ec8  pink-purple
#   --accent-soft:  rgba(124,110,245, 0.16)
#   --accent-glow:  rgba(124,110,245, 0.40)
#
# Dark panel bg: oklch(0.22 0.014 270 / ~0.92) ≈ QColor(22, 20, 34, 242) in paintEvent
# Stroke:       oklch(0.95 0.01 270 / 0.10) ≈ rgba(240,240,248, 0.10)
# Stroke-strong: rgba(240,240,248, 0.16)

DARK_THEME = """
/* ── Reset ─────────────────────────────────────────────────────────────────── */
* {
    font-family: "SF Pro Text", "Segoe UI Variable", "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
    outline: none;
}

QWidget {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.92);
}

/* ── Floating panel window ──────────────────────────────────────────────────── */
#FloatingPanel {
    border: 1px solid rgba(240, 240, 248, 0.16);
    border-radius: 18px;
}

/* ── Header ─────────────────────────────────────────────────────────────────── */
#PanelHeader {
    background-color: transparent;
    border-bottom: 1px solid rgba(240, 240, 248, 0.08);
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    min-height: 44px;
    max-height: 44px;
}

#HeaderTitle {
    color: rgba(246, 246, 250, 0.90);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.01em;
}

#CloseButton, #SettingsButton, #BrowseButton {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.38);
    border: none;
    border-radius: 7px;
    font-size: 13px;
    padding: 2px 6px;
    min-width: 26px;
    min-height: 26px;
    max-width: 26px;
    max-height: 26px;
}

#CloseButton:hover {
    background-color: rgba(255, 59, 48, 0.14);
    color: rgba(255, 80, 70, 1.0);
}

#SettingsButton:hover, #BrowseButton:hover {
    background-color: rgba(246, 246, 250, 0.07);
    color: rgba(246, 246, 250, 0.80);
}

/* ── Chat scroll area ───────────────────────────────────────────────────────── */
#ChatScrollArea {
    background-color: transparent;
    border: none;
}

#ChatScrollArea QScrollBar:vertical {
    background-color: transparent;
    width: 4px;
    margin: 10px 0;
}

#ChatScrollArea QScrollBar::handle:vertical {
    background-color: rgba(240, 240, 248, 0.14);
    border-radius: 2px;
    min-height: 28px;
}

#ChatScrollArea QScrollBar::handle:vertical:hover {
    background-color: rgba(240, 240, 248, 0.26);
}

#ChatScrollArea QScrollBar::add-line:vertical,
#ChatScrollArea QScrollBar::sub-line:vertical { height: 0; }

#ChatContainer { background-color: transparent; }

/* ── Chat bubbles ─────────────────────────────────────────────────────────────
   User:  accent purple bg, white text, bottom-right nub
   AI:    barely-there glass, subtle border, bottom-left nub
   ────────────────────────────────────────────────────────────────────────── */
#BubbleUser {
    background-color: #7c6ef5;
    color: #ffffff;
    border-radius: 14px 14px 5px 14px;
    padding: 10px 14px;
}
#BubbleUser QLabel {
    background-color: transparent;
    color: #ffffff;
    font-size: 13.5px;
}

#BubbleAI {
    background-color: rgba(246, 246, 250, 0.05);
    color: rgba(246, 246, 250, 0.92);
    border: 1px solid rgba(240, 240, 248, 0.10);
    border-radius: 5px 14px 14px 14px;
    padding: 10px 14px;
}
#BubbleAI QLabel {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.92);
    font-size: 13.5px;
}

/* Saved-note bubble — warm amber sticky-note treatment */
#BubbleNote {
    background-color: rgba(252, 196, 88, 0.08);
    border: 1px solid rgba(252, 196, 88, 0.20);
    border-left: 3px solid rgba(252, 188, 64, 0.78);
    border-radius: 10px;
}
#NoteGlyph {
    color: rgba(252, 188, 64, 0.92);
    font-size: 14px;
    font-weight: 700;
    background-color: transparent;
    padding-right: 2px;
}
#NoteKicker {
    color: rgba(252, 188, 64, 0.72);
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.10em;
    background-color: transparent;
}
#NotePin {
    color: rgba(252, 188, 64, 0.85);
    background-color: transparent;
}
#NoteContent {
    color: rgba(255, 240, 215, 0.96);
    font-size: 13.5px;
    background-color: transparent;
}

#BubbleTask {
    background-color: rgba(96, 165, 250, 0.06);
    color: rgba(180, 210, 255, 0.92);
    border: 1px solid rgba(96, 165, 250, 0.12);
    border-left: 2px solid rgba(96, 165, 250, 0.55);
    border-radius: 10px;
    padding: 9px 13px 9px 12px;
    margin: 3px 10px;
}
#BubbleTask QLabel { background-color: transparent; }

#BubbleReminder {
    background-color: rgba(251, 146, 60, 0.06);
    color: rgba(255, 195, 130, 0.92);
    border: 1px solid rgba(251, 146, 60, 0.12);
    border-left: 2px solid rgba(251, 146, 60, 0.55);
    border-radius: 10px;
    padding: 9px 13px 9px 12px;
    margin: 3px 10px;
}
#BubbleReminder QLabel { background-color: transparent; }

#BubbleSnippet {
    background-color: rgba(52, 211, 153, 0.05);
    color: rgba(150, 240, 190, 0.92);
    border: 1px solid rgba(52, 211, 153, 0.10);
    border-left: 2px solid rgba(52, 211, 153, 0.50);
    border-radius: 10px;
    padding: 9px 13px 9px 12px;
    margin: 3px 10px;
    font-family: "SF Mono", "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 12px;
}
#BubbleSnippet QLabel { background-color: transparent; }

#BubbleError {
    background-color: rgba(248, 113, 113, 0.06);
    color: rgba(255, 160, 150, 0.92);
    border: 1px solid rgba(248, 113, 113, 0.12);
    border-left: 2px solid rgba(248, 113, 113, 0.50);
    border-radius: 10px;
    padding: 9px 13px 9px 12px;
    margin: 3px 10px;
}
#BubbleError QLabel { background-color: transparent; }

/* ── Composer (input section) ───────────────────────────────────────────────── */
#ComposerFrame {
    background-color: rgba(246, 246, 250, 0.04);
    border: 1px solid rgba(240, 240, 248, 0.14);
    border-radius: 12px;
}

#ComposerFrame[focused="true"] {
    border-color: rgba(124, 110, 245, 0.52);
    background-color: rgba(124, 110, 245, 0.04);
}

#MessageInput {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.90);
    border: none;
    padding: 2px 4px;
    font-size: 13.5px;
    selection-background-color: rgba(124, 110, 245, 0.32);
}

/* ── Send button ─────────────────────────────────────────────────────────────── */
#SendButton {
    background-color: #7c6ef5;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    min-width: 30px;
    min-height: 30px;
    max-width: 30px;
    max-height: 30px;
}
#SendButton:hover { background-color: #8d80ff; }
#SendButton:pressed { background-color: #5e50d0; }
#SendButton:disabled { background-color: rgba(124, 110, 245, 0.25); }

/* ── Composer hint bar ──────────────────────────────────────────────────────── */
#ComposerHint {
    padding: 0 2px;
    min-height: 18px;
    max-height: 18px;
}

#HintKbd {
    background-color: rgba(246, 246, 250, 0.06);
    color: rgba(246, 246, 250, 0.55);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-bottom-width: 2px;
    border-radius: 4px;
    font-family: "SF Mono", "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 10px;
    padding: 0px 4px;
}

#HintText {
    color: rgba(246, 246, 250, 0.32);
    font-size: 10.5px;
    padding: 0;
    margin-right: 6px;
}

/* ── Status bar ──────────────────────────────────────────────────────────────── */
#StatusBar {
    color: rgba(246, 246, 250, 0.25);
    font-size: 10px;
    padding: 0 16px 6px 16px;
    min-height: 16px;
    max-height: 16px;
}

/* ── Tray / context menu ─────────────────────────────────────────────────────── */
QMenu {
    background-color: rgba(28, 26, 44, 0.98);
    color: rgba(246, 246, 250, 0.88);
    border: 1px solid rgba(240, 240, 248, 0.14);
    border-radius: 10px;
    padding: 4px;
    font-size: 13px;
}
QMenu::item { padding: 6px 20px; border-radius: 6px; }
QMenu::item:selected { background-color: rgba(124, 110, 245, 0.20); color: #ffffff; }
QMenu::separator { height: 1px; background-color: rgba(240, 240, 248, 0.07); margin: 3px 8px; }

/* ── Dialogs ─────────────────────────────────────────────────────────────────── */
QDialog {
    background-color: #100f1c;
    color: rgba(246, 246, 250, 0.88);
    border-radius: 14px;
}

QLabel {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.80);
}

/* ── Dialog title bar ────────────────────────────────────────────────────────── */
#DialogTitleBar {
    background-color: rgba(246, 246, 250, 0.02);
    border-bottom: 1px solid rgba(240, 240, 248, 0.08);
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}

#DialogTitle {
    color: rgba(246, 246, 250, 0.90);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.01em;
}

#DialogDoneButton {
    background-color: #7c6ef5;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 600;
    padding: 4px 14px;
    min-height: 28px;
    max-height: 28px;
}
#DialogDoneButton:hover { background-color: #8d80ff; }
#DialogDoneButton:pressed { background-color: #5e50d0; }

#DialogCloseButton {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.35);
    border: none;
    border-radius: 6px;
    font-size: 13px;
    padding: 3px 7px;
    min-height: 26px;
    max-height: 26px;
    min-width: 26px;
    max-width: 26px;
}
#DialogCloseButton:hover { background-color: rgba(255, 59, 48, 0.14); color: rgba(255, 80, 70, 1.0); }

#DialogBackButton {
    background-color: rgba(246, 246, 250, 0.05);
    color: rgba(246, 246, 250, 0.78);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 0;
}
#DialogBackButton:hover {
    background-color: rgba(124, 110, 245, 0.18);
    border-color: rgba(124, 110, 245, 0.45);
    color: rgba(255, 255, 255, 0.95);
}

/* ── Settings cards (glass tiles inside tabs) ──────────────────────────────── */
#SettingsCard {
    background-color: rgba(246, 246, 250, 0.025);
    border: 1px solid rgba(240, 240, 248, 0.08);
    border-radius: 14px;
}
#CardKicker {
    color: rgba(246, 246, 250, 0.42);
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.08em;
    background-color: transparent;
}
#CardSub {
    color: rgba(246, 246, 250, 0.50);
    font-size: 12px;
    background-color: transparent;
}
#RowLabel {
    color: rgba(246, 246, 250, 0.90);
    font-size: 13px;
    font-weight: 500;
    background-color: transparent;
}
#RowSub {
    color: rgba(246, 246, 250, 0.42);
    font-size: 11.5px;
    background-color: transparent;
}
#KeyToggleButton {
    background-color: rgba(246, 246, 250, 0.06);
    color: rgba(246, 246, 250, 0.78);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-radius: 7px;
    padding: 4px 8px;
    font-size: 11.5px;
    min-height: 30px;
}
#KeyToggleButton:hover { background-color: rgba(246, 246, 250, 0.10); }
#KeyToggleButton:checked { background-color: rgba(124, 110, 245, 0.20); color: #ffffff; border-color: rgba(124, 110, 245, 0.55); }

#RefreshButton {
    background-color: rgba(124, 110, 245, 0.12);
    color: rgba(220, 215, 255, 0.95);
    border: 1px solid rgba(124, 110, 245, 0.30);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12.5px;
    min-height: 30px;
}
#RefreshButton:hover { background-color: rgba(124, 110, 245, 0.22); }

#BrowseStatus {
    color: rgba(246, 246, 250, 0.42);
    font-size: 11.5px;
    padding: 2px 4px;
    background-color: transparent;
}

#NoteCardText {
    color: rgba(246, 246, 250, 0.92);
    font-size: 13px;
    background-color: transparent;
}

#SettingsTabs::pane {
    border: none;
    background-color: transparent;
    top: 4px;
}

/* ── Tabs ────────────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid rgba(240, 240, 248, 0.08);
    border-radius: 10px;
    background-color: transparent;
    top: -1px;
}
QTabBar { background-color: transparent; }
QTabBar::tab {
    background-color: transparent;
    color: rgba(246, 246, 250, 0.40);
    padding: 8px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}
QTabBar::tab:selected { color: rgba(246, 246, 250, 0.90); border-bottom: 2px solid #7c6ef5; }
QTabBar::tab:hover:!selected { color: rgba(246, 246, 250, 0.65); }

/* ── Group boxes ─────────────────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid rgba(240, 240, 248, 0.08);
    border-radius: 10px;
    margin-top: 20px;
    padding-top: 12px;
    color: rgba(246, 246, 250, 0.38);
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.05em;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; top: -1px; }

/* ── Form inputs ─────────────────────────────────────────────────────────────── */
QLineEdit {
    background-color: rgba(246, 246, 250, 0.04);
    color: rgba(246, 246, 250, 0.88);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 30px;
    selection-background-color: rgba(124, 110, 245, 0.30);
}
QLineEdit:focus { border-color: rgba(124, 110, 245, 0.52); background-color: rgba(124, 110, 245, 0.05); }
QLineEdit:disabled { color: rgba(246, 246, 250, 0.22); border-color: rgba(240, 240, 248, 0.05); }

QComboBox {
    background-color: rgba(246, 246, 250, 0.04);
    color: rgba(246, 246, 250, 0.88);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 30px;
}
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #1c1a30;
    color: rgba(246, 246, 250, 0.88);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-radius: 8px;
    selection-background-color: rgba(124, 110, 245, 0.20);
    outline: none;
    padding: 4px;
}

QSpinBox {
    background-color: rgba(246, 246, 250, 0.04);
    color: rgba(246, 246, 250, 0.88);
    border: 1px solid rgba(240, 240, 248, 0.12);
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 13px;
    min-height: 30px;
}
QSpinBox::up-button, QSpinBox::down-button { background-color: transparent; border: none; width: 18px; }

QCheckBox { color: rgba(246, 246, 250, 0.80); spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1.5px solid rgba(240, 240, 248, 0.20);
    border-radius: 5px;
    background-color: rgba(246, 246, 250, 0.04);
}
QCheckBox::indicator:checked { background-color: #7c6ef5; border-color: #7c6ef5; }

QPushButton {
    background-color: rgba(246, 246, 250, 0.06);
    color: rgba(246, 246, 250, 0.78);
    border: 1px solid rgba(240, 240, 248, 0.10);
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    min-height: 30px;
}
QPushButton:hover { background-color: rgba(246, 246, 250, 0.10); color: rgba(246, 246, 250, 0.96); }
QPushButton:pressed { background-color: rgba(246, 246, 250, 0.04); }
QPushButton[default="true"], QPushButton:default { background-color: #7c6ef5; border: none; color: #ffffff; font-weight: 600; }
QPushButton[default="true"]:hover, QPushButton:default:hover { background-color: #8d80ff; }
QDialogButtonBox QPushButton { min-width: 80px; }

/* ── Scrollbars ──────────────────────────────────────────────────────────────── */
QScrollBar:vertical { background-color: transparent; width: 4px; }
QScrollBar::handle:vertical { background-color: rgba(240, 240, 248, 0.14); border-radius: 2px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background-color: rgba(240, 240, 248, 0.26); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── List & text widgets ─────────────────────────────────────────────────────── */
QListWidget {
    background-color: rgba(246, 246, 250, 0.03);
    border: 1px solid rgba(240, 240, 248, 0.07);
    border-radius: 10px;
    color: rgba(246, 246, 250, 0.88);
    padding: 4px;
    outline: none;
}
QListWidget::item { padding: 8px 10px; border-radius: 7px; color: rgba(246, 246, 250, 0.72); }
QListWidget::item:selected { background-color: rgba(124, 110, 245, 0.18); color: rgba(246, 246, 250, 1.0); }
QListWidget::item:hover:!selected { background-color: rgba(246, 246, 250, 0.04); }

QTextEdit {
    background-color: rgba(246, 246, 250, 0.03);
    color: rgba(246, 246, 250, 0.86);
    border: 1px solid rgba(240, 240, 248, 0.07);
    border-radius: 10px;
    padding: 10px;
    font-size: 13px;
}

QSplitter::handle { background-color: rgba(240, 240, 248, 0.06); width: 1px; }

/* ── Slash menu ──────────────────────────────────────────────────────────────── */
#SlashMenu {
    background-color: rgba(20, 18, 32, 0.985);
    border: 1px solid rgba(240, 240, 248, 0.14);
    border-radius: 12px;
}
#SlashList {
    background-color: transparent;
    border: none;
    padding: 5px;
    outline: none;
}
#SlashList::item { padding: 0; border-radius: 8px; margin: 1px; }
#SlashList::item:selected { background-color: rgba(124, 110, 245, 0.20); }
#SlashList::item:hover:!selected { background-color: rgba(246, 246, 250, 0.05); }
#SlashName {
    font-family: "SF Mono", "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 12.5px;
    font-weight: 600;
    color: rgba(246, 246, 250, 0.96);
    background-color: transparent;
}
#SlashDesc {
    font-size: 11.5px;
    color: rgba(246, 246, 250, 0.45);
    background-color: transparent;
}
"""

LIGHT_THEME = """
* { font-family: "SF Pro Text", "Segoe UI Variable", "Segoe UI", "Inter", sans-serif; font-size: 13px; outline: none; }
QWidget { background-color: transparent; color: #1a1830; }
QDialog { background-color: #f4f3ff; color: #1a1830; border-radius: 14px; }
QLabel { background-color: transparent; color: #1a1830; }

#FloatingPanel { border: 1px solid rgba(26, 24, 48, 0.14); border-radius: 18px; }
#PanelHeader { background-color: rgba(255, 255, 255, 0.55); border-bottom: 1px solid rgba(26,24,48,0.08); border-top-left-radius: 18px; border-top-right-radius: 18px; min-height: 44px; max-height: 44px; }
#HeaderTitle { color: rgba(26,24,48,0.85); font-size: 13px; font-weight: 600; letter-spacing: -0.01em; }
#CloseButton, #SettingsButton, #BrowseButton { background-color: transparent; color: rgba(26,24,48,0.32); border: none; border-radius: 7px; font-size: 13px; padding: 2px 6px; min-width: 26px; min-height: 26px; max-width: 26px; max-height: 26px; }
#CloseButton:hover { background-color: rgba(255,59,48,0.10); color: rgba(200,30,20,1.0); }
#SettingsButton:hover, #BrowseButton:hover { background-color: rgba(26,24,48,0.06); color: rgba(26,24,48,0.65); }

#ChatScrollArea { background-color: transparent; border: none; }
#ChatScrollArea QScrollBar:vertical { background-color: transparent; width: 4px; }
#ChatScrollArea QScrollBar::handle:vertical { background-color: rgba(0,0,0,0.14); border-radius: 2px; min-height: 28px; }
#ChatScrollArea QScrollBar::add-line:vertical, #ChatScrollArea QScrollBar::sub-line:vertical { height: 0; }
#ChatContainer { background-color: transparent; }

#BubbleUser { background-color: #7c6ef5; color: #fff; border-radius: 14px 14px 5px 14px; padding: 10px 14px; }
#BubbleUser QLabel { background-color: transparent; color: #fff; font-size: 13.5px; }
#BubbleAI { background-color: rgba(26,24,48,0.05); color: #1a1830; border: 1px solid rgba(26,24,48,0.08); border-radius: 5px 14px 14px 14px; padding: 10px 14px; }
#BubbleAI QLabel { background-color: transparent; color: #1a1830; font-size: 13.5px; }
#BubbleNote { background-color: rgba(124,110,245,0.06); color: #3d2e99; border: 1px solid rgba(124,110,245,0.12); border-left: 2px solid rgba(124,110,245,0.55); border-radius: 10px; padding: 9px 13px 9px 12px; margin: 3px 10px; }
#BubbleNote QLabel { background-color: transparent; }
#BubbleTask { background-color: rgba(59,130,246,0.06); color: #1e3a8a; border: 1px solid rgba(59,130,246,0.12); border-left: 2px solid rgba(59,130,246,0.55); border-radius: 10px; padding: 9px 13px 9px 12px; margin: 3px 10px; }
#BubbleTask QLabel { background-color: transparent; }
#BubbleReminder { background-color: rgba(251,146,60,0.06); color: #7c3a00; border: 1px solid rgba(251,146,60,0.12); border-left: 2px solid rgba(251,146,60,0.55); border-radius: 10px; padding: 9px 13px 9px 12px; margin: 3px 10px; }
#BubbleReminder QLabel { background-color: transparent; }
#BubbleSnippet { background-color: rgba(0,0,0,0.90); color: #a8f0a0; border: 1px solid rgba(0,0,0,0.15); border-left: 2px solid #34d399; border-radius: 10px; padding: 9px 13px 9px 12px; margin: 3px 10px; font-family: "SF Mono","Cascadia Code","Consolas",monospace; font-size: 12px; }
#BubbleSnippet QLabel { background-color: transparent; }
#BubbleError { background-color: rgba(248,113,113,0.06); color: #7f1d1d; border: 1px solid rgba(248,113,113,0.12); border-left: 2px solid rgba(248,113,113,0.55); border-radius: 10px; padding: 9px 13px 9px 12px; margin: 3px 10px; }
#BubbleError QLabel { background-color: transparent; }

#ComposerFrame { background-color: rgba(26,24,48,0.05); border: 1px solid rgba(26,24,48,0.12); border-radius: 12px; }
#ComposerFrame[focused="true"] { border-color: rgba(124,110,245,0.50); background-color: rgba(124,110,245,0.04); }
#MessageInput { background-color: transparent; border: none; color: #1a1830; padding: 2px 4px; font-size: 13.5px; selection-background-color: rgba(124,110,245,0.25); }
#SendButton { background-color: #7c6ef5; color: #fff; border: none; border-radius: 8px; font-size: 14px; min-width: 30px; min-height: 30px; max-width: 30px; max-height: 30px; }
#SendButton:hover { background-color: #8d80ff; }
#SendButton:pressed { background-color: #5e50d0; }
#SendButton:disabled { background-color: rgba(124,110,245,0.25); }
#ComposerHint { padding: 0 2px; min-height: 18px; max-height: 18px; }
#HintKbd { background-color: rgba(26,24,48,0.06); color: rgba(26,24,48,0.45); border: 1px solid rgba(26,24,48,0.12); border-bottom-width: 2px; border-radius: 4px; font-family: "SF Mono","Cascadia Code","Consolas",monospace; font-size: 10px; padding: 0px 4px; }
#HintText { color: rgba(26,24,48,0.35); font-size: 10.5px; padding: 0; margin-right: 6px; }
#StatusBar { color: rgba(26,24,48,0.28); font-size: 10px; padding: 0 16px 6px 16px; min-height: 16px; max-height: 16px; }

QMenu { background-color: rgba(244,243,255,0.98); color: #1a1830; border: 1px solid rgba(26,24,48,0.10); border-radius: 10px; padding: 4px; }
QMenu::item { padding: 6px 20px; border-radius: 6px; }
QMenu::item:selected { background-color: rgba(124,110,245,0.10); }
QMenu::separator { height: 1px; background-color: rgba(26,24,48,0.07); margin: 3px 8px; }

#DialogTitleBar { background-color: rgba(26,24,48,0.02); border-bottom: 1px solid rgba(26,24,48,0.07); border-top-left-radius: 14px; border-top-right-radius: 14px; }
#DialogTitle { color: rgba(26,24,48,0.88); font-size: 13px; font-weight: 600; }
#DialogDoneButton { background-color: #7c6ef5; color: #fff; border: none; border-radius: 8px; font-size: 12.5px; font-weight: 600; padding: 4px 14px; min-height: 28px; max-height: 28px; }
#DialogDoneButton:hover { background-color: #8d80ff; }
#DialogCloseButton { background-color: transparent; color: rgba(26,24,48,0.32); border: none; border-radius: 6px; font-size: 13px; padding: 3px 7px; min-height: 26px; max-height: 26px; min-width: 26px; max-width: 26px; }
#DialogCloseButton:hover { background-color: rgba(255,59,48,0.10); color: rgba(200,30,20,1.0); }

#SettingsCard { background-color: rgba(26,24,48,0.025); border: 1px solid rgba(26,24,48,0.08); border-radius: 14px; }
#CardKicker { color: rgba(26,24,48,0.45); font-size: 10.5px; font-weight: 600; letter-spacing: 0.08em; background-color: transparent; }
#CardSub { color: rgba(26,24,48,0.55); font-size: 12px; background-color: transparent; }
#RowLabel { color: rgba(26,24,48,0.90); font-size: 13px; font-weight: 500; background-color: transparent; }
#RowSub { color: rgba(26,24,48,0.50); font-size: 11.5px; background-color: transparent; }
#KeyToggleButton { background-color: rgba(26,24,48,0.06); color: rgba(26,24,48,0.78); border: 1px solid rgba(26,24,48,0.10); border-radius: 7px; padding: 4px 8px; font-size: 11.5px; min-height: 30px; }
#KeyToggleButton:hover { background-color: rgba(26,24,48,0.10); }
#KeyToggleButton:checked { background-color: rgba(124,110,245,0.18); color: #1a1830; border-color: rgba(124,110,245,0.50); }
#RefreshButton { background-color: rgba(124,110,245,0.10); color: #2a1f80; border: 1px solid rgba(124,110,245,0.30); border-radius: 8px; padding: 6px 12px; font-size: 12.5px; min-height: 30px; }
#RefreshButton:hover { background-color: rgba(124,110,245,0.18); }
#BrowseStatus { color: rgba(26,24,48,0.42); font-size: 11.5px; padding: 2px 4px; background-color: transparent; }
#SettingsTabs::pane { border: none; background-color: transparent; top: 4px; }

QTabWidget::pane { border: 1px solid rgba(26,24,48,0.08); border-radius: 10px; background-color: transparent; top: -1px; }
QTabBar { background-color: transparent; }
QTabBar::tab { background-color: transparent; color: rgba(26,24,48,0.40); padding: 8px 18px; border: none; border-bottom: 2px solid transparent; font-size: 13px; font-weight: 500; }
QTabBar::tab:selected { color: #1a1830; border-bottom: 2px solid #7c6ef5; }
QTabBar::tab:hover:!selected { color: rgba(26,24,48,0.65); }

QGroupBox { border: 1px solid rgba(26,24,48,0.08); border-radius: 10px; margin-top: 20px; padding-top: 12px; color: rgba(26,24,48,0.38); font-size: 10.5px; font-weight: 600; letter-spacing: 0.05em; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; top: -1px; }

QLineEdit { background-color: rgba(255,255,255,0.80); color: #1a1830; border: 1px solid rgba(26,24,48,0.10); border-radius: 8px; padding: 6px 10px; font-size: 13px; min-height: 30px; selection-background-color: rgba(124,110,245,0.25); }
QLineEdit:focus { border-color: rgba(124,110,245,0.52); background-color: #ffffff; }
QComboBox { background-color: rgba(255,255,255,0.80); color: #1a1830; border: 1px solid rgba(26,24,48,0.10); border-radius: 8px; padding: 6px 10px; font-size: 13px; min-height: 30px; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #1a1830; border: 1px solid rgba(26,24,48,0.10); selection-background-color: rgba(124,110,245,0.10); outline: none; padding: 4px; }
QSpinBox { background-color: rgba(255,255,255,0.80); color: #1a1830; border: 1px solid rgba(26,24,48,0.10); border-radius: 8px; padding: 6px 8px; font-size: 13px; min-height: 30px; }
QSpinBox::up-button, QSpinBox::down-button { background-color: transparent; border: none; width: 18px; }
QCheckBox { color: #1a1830; spacing: 8px; font-size: 13px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1.5px solid rgba(26,24,48,0.18); border-radius: 5px; background-color: #fff; }
QCheckBox::indicator:checked { background-color: #7c6ef5; border-color: #7c6ef5; }
QPushButton { background-color: rgba(26,24,48,0.05); color: #1a1830; border: 1px solid rgba(26,24,48,0.10); border-radius: 8px; padding: 6px 14px; font-size: 13px; min-height: 30px; }
QPushButton:hover { background-color: rgba(124,110,245,0.08); border-color: rgba(124,110,245,0.25); }
QPushButton:pressed { background-color: rgba(124,110,245,0.12); }
QPushButton[default="true"], QPushButton:default { background-color: #7c6ef5; color: #fff; border: none; font-weight: 600; }
QPushButton[default="true"]:hover, QPushButton:default:hover { background-color: #8d80ff; }
QDialogButtonBox QPushButton { min-width: 80px; }

QScrollBar:vertical { background-color: transparent; width: 4px; }
QScrollBar::handle:vertical { background-color: rgba(0,0,0,0.14); border-radius: 2px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background-color: rgba(0,0,0,0.25); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QListWidget { background-color: rgba(255,255,255,0.65); border: 1px solid rgba(26,24,48,0.08); border-radius: 10px; color: #1a1830; padding: 4px; outline: none; }
QListWidget::item { padding: 8px 10px; border-radius: 7px; }
QListWidget::item:selected { background-color: rgba(124,110,245,0.12); color: #1a1830; }
QListWidget::item:hover:!selected { background-color: rgba(26,24,48,0.04); }
QTextEdit { background-color: rgba(255,255,255,0.65); color: #1a1830; border: 1px solid rgba(26,24,48,0.08); border-radius: 10px; padding: 10px; }
QSplitter::handle { background-color: rgba(26,24,48,0.06); width: 1px; }

#SlashMenu { background-color: rgba(244,243,255,0.99); border: 1px solid rgba(26,24,48,0.12); border-radius: 12px; }
#SlashMenu QListWidget { background-color: transparent; border: none; color: #1a1830; font-size: 13px; padding: 4px; }
#SlashMenu QListWidget::item { padding: 7px 12px; border-radius: 7px; }
#SlashMenu QListWidget::item:selected { background-color: rgba(124,110,245,0.12); }
#SlashMenu QListWidget::item:hover:!selected { background-color: rgba(26,24,48,0.04); }
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
