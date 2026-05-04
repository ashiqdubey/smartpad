"""QSS theme definitions — SPEC.md section 12.

Token reference (comments — QSS has no variables):
  window-bg:        dark=#1e1e2e  light=#f5f5f5
  surface-bg:       dark=#2a2a3e  light=#ffffff
  surface-alt:      dark=#313147  light=#f0f0f0
  border:           dark=#44445a  light=#d0d0d0
  text-primary:     dark=#cdd6f4  light=#1a1a2e
  text-secondary:   dark=#a6adc8  light=#5a5a7a
  accent:           dark=#89b4fa  light=#3b82f6
  bubble-user:      dark=#89b4fa  light=#3b82f6   (chat user — accent blue)
  bubble-ai:        dark=#313147  light=#e8e8f0   (chat AI — neutral)
  bubble-note:      dark=#3a3a20  light=#fffde7   (pale yellow)
  bubble-task:      dark=#1e2d3d  light=#e3f2fd   (blue tint)
  bubble-reminder:  dark=#3d2e1e  light=#fff8e1   (amber tint)
  bubble-snippet:   dark=#1a1a2a  light=#1e1e2e   (dark mono)
  bubble-error:     dark=#3d1e1e  light=#ffebee   (red tint)
  input-bg:         dark=#2a2a3e  light=#ffffff
  scrollbar-bg:     dark=#2a2a3e  light=#e0e0e0
  scrollbar-handle: dark=#585878  light=#b0b0c0
  header-bg:        dark=#181825  light=#e8e8f0
  status-bg:        dark=#181825  light=#eeeeee
"""

# ── Dark theme ────────────────────────────────────────────────────────────────

DARK_THEME = """
/* === Base === */
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    font-size: 13px;
}

/* === Floating panel === */
#FloatingPanel {
    background-color: #1e1e2e;
    border: 1px solid #44445a;
    border-radius: 12px;
}

/* === Header === */
#PanelHeader {
    background-color: #181825;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid #313147;
    min-height: 42px;
    max-height: 42px;
}

#HeaderTitle {
    color: #cdd6f4;
    font-size: 14px;
    font-weight: 600;
}

#CloseButton {
    background-color: transparent;
    color: #a6adc8;
    border: none;
    font-size: 16px;
    padding: 2px 6px;
    border-radius: 4px;
}

#CloseButton:hover {
    background-color: #44445a;
    color: #f38ba8;
}

/* === Chat scroll area === */
#ChatScrollArea {
    background-color: transparent;
    border: none;
}

#ChatScrollArea QScrollBar:vertical {
    background-color: #2a2a3e;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}

#ChatScrollArea QScrollBar::handle:vertical {
    background-color: #585878;
    border-radius: 3px;
    min-height: 24px;
}

#ChatScrollArea QScrollBar::handle:vertical:hover {
    background-color: #7070a0;
}

#ChatScrollArea QScrollBar::add-line:vertical,
#ChatScrollArea QScrollBar::sub-line:vertical {
    height: 0;
}

#ChatScrollArea QScrollBar::add-page:vertical,
#ChatScrollArea QScrollBar::sub-page:vertical {
    background: none;
}

#ChatContainer {
    background-color: transparent;
}

/* === Bubbles === */
.BubbleBase {
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
}

#BubbleUser {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
}

#BubbleUser QLabel {
    background-color: transparent;
    color: #1e1e2e;
}

#BubbleAI {
    background-color: #313147;
    color: #cdd6f4;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
}

#BubbleAI QLabel {
    background-color: transparent;
    color: #cdd6f4;
}

#BubbleNote {
    background-color: #3a3a20;
    color: #f5e0dc;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #f9e2af;
}

#BubbleNote QLabel {
    background-color: transparent;
}

#BubbleTask {
    background-color: #1e2d3d;
    color: #89dceb;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #89b4fa;
}

#BubbleTask QLabel {
    background-color: transparent;
}

#BubbleReminder {
    background-color: #3d2e1e;
    color: #fab387;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #fab387;
}

#BubbleReminder QLabel {
    background-color: transparent;
}

#BubbleSnippet {
    background-color: #1a1a2a;
    color: #a6e3a1;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
    font-size: 12px;
}

#BubbleSnippet QLabel {
    background-color: transparent;
}

#BubbleError {
    background-color: #3d1e1e;
    color: #f38ba8;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #f38ba8;
}

#BubbleError QLabel {
    background-color: transparent;
}

/* === Input area === */
#InputArea {
    background-color: #181825;
    border-top: 1px solid #313147;
    padding: 8px;
}

#MessageInput {
    background-color: #2a2a3e;
    color: #cdd6f4;
    border: 1px solid #44445a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #585878;
}

#MessageInput:focus {
    border: 1px solid #89b4fa;
}

/* === Status bar === */
#StatusBar {
    background-color: #181825;
    color: #a6adc8;
    font-size: 11px;
    padding: 2px 12px;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    min-height: 20px;
    max-height: 20px;
}

/* === Send button === */
#SendButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}

#SendButton:hover {
    background-color: #b4d0fc;
}

#SendButton:pressed {
    background-color: #74a0e8;
}

#SendButton:disabled {
    background-color: #44445a;
    color: #585878;
}

/* === Tray icon menu === */
QMenu {
    background-color: #2a2a3e;
    color: #cdd6f4;
    border: 1px solid #44445a;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #44445a;
}

QMenu::separator {
    height: 1px;
    background-color: #44445a;
    margin: 4px 8px;
}
"""

# ── Light theme ────────────────────────────────────────────────────────────────

LIGHT_THEME = """
/* === Base === */
QWidget {
    background-color: #f5f5f5;
    color: #1a1a2e;
    font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
    font-size: 13px;
}

/* === Floating panel === */
#FloatingPanel {
    background-color: #f5f5f5;
    border: 1px solid #d0d0d0;
    border-radius: 12px;
}

/* === Header === */
#PanelHeader {
    background-color: #e8e8f0;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid #d0d0d0;
    min-height: 42px;
    max-height: 42px;
}

#HeaderTitle {
    color: #1a1a2e;
    font-size: 14px;
    font-weight: 600;
}

#CloseButton {
    background-color: transparent;
    color: #5a5a7a;
    border: none;
    font-size: 16px;
    padding: 2px 6px;
    border-radius: 4px;
}

#CloseButton:hover {
    background-color: #d0d0e0;
    color: #e53935;
}

/* === Chat scroll area === */
#ChatScrollArea {
    background-color: transparent;
    border: none;
}

#ChatScrollArea QScrollBar:vertical {
    background-color: #e0e0e0;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}

#ChatScrollArea QScrollBar::handle:vertical {
    background-color: #b0b0c0;
    border-radius: 3px;
    min-height: 24px;
}

#ChatScrollArea QScrollBar::handle:vertical:hover {
    background-color: #9090b0;
}

#ChatScrollArea QScrollBar::add-line:vertical,
#ChatScrollArea QScrollBar::sub-line:vertical {
    height: 0;
}

#ChatScrollArea QScrollBar::add-page:vertical,
#ChatScrollArea QScrollBar::sub-page:vertical {
    background: none;
}

#ChatContainer {
    background-color: transparent;
}

/* === Bubbles === */
#BubbleUser {
    background-color: #3b82f6;
    color: #ffffff;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
}

#BubbleUser QLabel {
    background-color: transparent;
    color: #ffffff;
}

#BubbleAI {
    background-color: #e8e8f0;
    color: #1a1a2e;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
}

#BubbleAI QLabel {
    background-color: transparent;
    color: #1a1a2e;
}

#BubbleNote {
    background-color: #fffde7;
    color: #5a4000;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #f9c74f;
}

#BubbleNote QLabel {
    background-color: transparent;
}

#BubbleTask {
    background-color: #e3f2fd;
    color: #1a3a5c;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #3b82f6;
}

#BubbleTask QLabel {
    background-color: transparent;
}

#BubbleReminder {
    background-color: #fff8e1;
    color: #5a3a00;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #f59e0b;
}

#BubbleReminder QLabel {
    background-color: transparent;
}

#BubbleSnippet {
    background-color: #1e1e2e;
    color: #a6e3a1;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
    font-size: 12px;
}

#BubbleSnippet QLabel {
    background-color: transparent;
}

#BubbleError {
    background-color: #ffebee;
    color: #c62828;
    border-radius: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    border-left: 3px solid #ef5350;
}

#BubbleError QLabel {
    background-color: transparent;
}

/* === Input area === */
#InputArea {
    background-color: #e8e8f0;
    border-top: 1px solid #d0d0d0;
    padding: 8px;
}

#MessageInput {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #b0c8f0;
}

#MessageInput:focus {
    border: 1px solid #3b82f6;
}

/* === Status bar === */
#StatusBar {
    background-color: #e8e8f0;
    color: #5a5a7a;
    font-size: 11px;
    padding: 2px 12px;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
    min-height: 20px;
    max-height: 20px;
}

/* === Send button === */
#SendButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 13px;
}

#SendButton:hover {
    background-color: #2563eb;
}

#SendButton:pressed {
    background-color: #1d4ed8;
}

#SendButton:disabled {
    background-color: #d0d0d0;
    color: #a0a0b0;
}

/* === Tray icon menu === */
QMenu {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #e8e8f0;
}

QMenu::separator {
    height: 1px;
    background-color: #d0d0d0;
    margin: 4px 8px;
}
"""


def get_theme(name: str) -> str:
    """Return QSS string for the given theme name.

    Args:
        name: One of "dark", "light", or "system".

    Returns:
        QSS stylesheet string.
    """
    if name == "dark":
        return DARK_THEME
    if name == "light":
        return LIGHT_THEME
    # system: detect via palette
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            palette = app.palette()
            # Compare window background lightness — dark if below 128
            bg = palette.window().color()
            if bg.lightness() < 128:
                return DARK_THEME
        return LIGHT_THEME
    except Exception:
        return DARK_THEME
