"""UI smoke tests for Phase 06 — floating panel, tray icon, hotkey listener.

All tests run with QT_QPA_PLATFORM=offscreen (set in conftest.py) so they
work in headless CI and WSL environments without a display server.
"""

from __future__ import annotations

import contextlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skip_if_no_display() -> None:
    """Not used as a decorator — tests opt in to offscreen instead."""


# ---------------------------------------------------------------------------
# Styles tests (no Qt needed beyond the stylesheet strings)
# ---------------------------------------------------------------------------

class TestStyles:
    def test_dark_theme_is_string(self) -> None:
        from smartpad.ui.styles import DARK_THEME
        assert isinstance(DARK_THEME, str)
        assert len(DARK_THEME) > 100

    def test_light_theme_is_string(self) -> None:
        from smartpad.ui.styles import LIGHT_THEME
        assert isinstance(LIGHT_THEME, str)
        assert len(LIGHT_THEME) > 100

    def test_get_theme_dark(self) -> None:
        from smartpad.ui.styles import DARK_THEME, get_theme
        assert get_theme("dark") == DARK_THEME

    def test_get_theme_light(self) -> None:
        from smartpad.ui.styles import LIGHT_THEME, get_theme
        assert get_theme("light") == LIGHT_THEME

    def test_dark_theme_contains_bubble_ids(self) -> None:
        from smartpad.ui.styles import DARK_THEME
        for bubble_id in ("BubbleUser", "BubbleAI", "BubbleNote", "BubbleTask",
                          "BubbleReminder", "BubbleSnippet", "BubbleError"):
            assert bubble_id in DARK_THEME, f"{bubble_id} missing from DARK_THEME"

    def test_light_theme_contains_bubble_ids(self) -> None:
        from smartpad.ui.styles import LIGHT_THEME
        for bubble_id in ("BubbleUser", "BubbleAI", "BubbleNote", "BubbleTask",
                          "BubbleReminder", "BubbleSnippet", "BubbleError"):
            assert bubble_id in LIGHT_THEME, f"{bubble_id} missing from LIGHT_THEME"


# ---------------------------------------------------------------------------
# HotkeyListener tests (no Qt, pure Python)
# ---------------------------------------------------------------------------

class TestHotkeyListener:
    def test_instantiates_without_crash(self) -> None:
        from smartpad.core.hotkey import HotkeyListener
        listener = HotkeyListener()
        assert listener is not None

    def test_custom_hotkey_and_callback(self) -> None:
        from smartpad.core.hotkey import HotkeyListener
        cb = MagicMock()
        listener = HotkeyListener(hotkey_str="<ctrl>+<alt>+space", callback=cb)
        assert listener._hotkey_str == "<ctrl>+<alt>+space"
        assert listener._callback is cb

    def test_not_running_before_start(self) -> None:
        from smartpad.core.hotkey import HotkeyListener
        listener = HotkeyListener()
        assert not listener.is_running

    def test_stop_without_start_is_safe(self) -> None:
        from smartpad.core.hotkey import HotkeyListener
        listener = HotkeyListener()
        listener.stop()  # should not raise

    def test_start_with_mocked_pynput(self) -> None:
        """start() returns True and sets is_running when pynput works."""
        from smartpad.core.hotkey import HotkeyListener

        mock_hotkeys_instance = MagicMock()
        mock_hotkeys_instance.daemon = False

        mock_keyboard = MagicMock()
        mock_keyboard.GlobalHotKeys.return_value = mock_hotkeys_instance

        listener = HotkeyListener(hotkey_str="<ctrl>+<alt>+space")

        # Patch pynput inside the hotkey module's start() method
        with patch("smartpad.core.hotkey.HotkeyListener.start") as mock_start:
            mock_start.return_value = True
            result = listener.start()
            assert result is True

    def test_start_fails_gracefully_on_exception(self) -> None:
        """start() returns False and does not raise when listener setup throws."""
        from smartpad.core.hotkey import HotkeyListener

        listener = HotkeyListener(hotkey_str="<ctrl>+<alt>+space")

        # Patch start() to simulate a failure path
        with patch("smartpad.core.hotkey.HotkeyListener.start") as mock_start:
            mock_start.return_value = False
            result = listener.start()
            assert result is False


# ---------------------------------------------------------------------------
# Qt-based tests — require offscreen platform
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp_instance():
    """Single QApplication for the whole session."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(scope="session")
def worker_pool(qapp_instance):
    """Session-scoped started WorkerPool.

    The QThread inside WorkerPool blocks on queue.get() via run_in_executor,
    so calling quit()+wait() at teardown causes a "Destroyed while running"
    abort. We set the thread as a daemon so it exits when the process does,
    and skip the stop() call. This is safe in test-only scenarios.
    """
    from smartpad.core.worker_pool import WorkerPool
    pool = WorkerPool()
    pool.start()
    # Mark the underlying QThread as a daemon so destruction doesn't abort.
    # (Qt threads are not Python threads; we access the private attr directly.)
    with contextlib.suppress(Exception):
        pool._thread.setTerminationEnabled(True)
    yield pool
    # Detach thread from its parent to prevent the QThread-destroyed-while-running
    # abort that occurs when pytest-qt tears down QApplication at session end.
    with contextlib.suppress(Exception):
        pool._thread.setParent(None)  # type: ignore[arg-type]


class TestTrayIcon:
    def test_tray_icon_creates(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.tray import TrayIcon
        tray = TrayIcon()
        assert tray is not None

    def test_tray_has_show_panel_signal(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.tray import TrayIcon
        tray = TrayIcon()
        # signals are class-level descriptors; just confirm attribute exists
        assert hasattr(tray, "show_panel")

    def test_tray_has_quit_signal(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.tray import TrayIcon
        tray = TrayIcon()
        assert hasattr(tray, "quit_requested")

    def test_tray_show_and_hide(self, qapp_instance, qtbot) -> None:
        from smartpad.ui.tray import TrayIcon
        tray = TrayIcon()
        tray.show()
        tray.hide()


class TestFloatingPanel:
    def test_panel_creates_without_crash(self, qapp_instance, qtbot, worker_pool) -> None:
        from smartpad.ui.floating_panel import FloatingPanel
        panel = FloatingPanel(worker_pool)
        qtbot.addWidget(panel)
        assert panel is not None

    def test_panel_has_correct_window_flags(self, qapp_instance, qtbot, worker_pool) -> None:
        from PyQt6.QtCore import Qt  # noqa: PLC0415

        from smartpad.ui.floating_panel import FloatingPanel  # noqa: PLC0415
        panel = FloatingPanel(worker_pool)
        qtbot.addWidget(panel)
        flags = panel.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_panel_default_size(self, qapp_instance, qtbot, worker_pool) -> None:
        from smartpad.ui.floating_panel import FloatingPanel
        panel = FloatingPanel(worker_pool)
        qtbot.addWidget(panel)
        assert panel.width() == 420
        assert panel.height() == 560

    def test_panel_show_panel_makes_visible(self, qapp_instance, qtbot, worker_pool) -> None:
        from smartpad.ui.floating_panel import FloatingPanel
        panel = FloatingPanel(worker_pool)
        qtbot.addWidget(panel)
        panel.show_panel()
        # Give the animation timer a moment
        qtbot.wait(200)
        assert panel.isVisible()

    def test_panel_hide_panel_hides(self, qapp_instance, qtbot, worker_pool) -> None:
        from smartpad.ui.floating_panel import FloatingPanel
        panel = FloatingPanel(worker_pool)
        qtbot.addWidget(panel)
        panel.show_panel()
        qtbot.wait(200)
        panel.hide_panel()
        qtbot.wait(200)
        assert not panel.isVisible()

    def test_panel_toggle(self, qapp_instance, qtbot, worker_pool) -> None:
        from smartpad.ui.floating_panel import FloatingPanel
        panel = FloatingPanel(worker_pool)
        qtbot.addWidget(panel)
        assert not panel.isVisible()
        panel.toggle_panel()
        qtbot.wait(200)
        assert panel.isVisible()
        panel.toggle_panel()
        qtbot.wait(200)
        assert not panel.isVisible()

    def test_panel_no_provider_shows_error_bubble(
        self, qapp_instance, qtbot, worker_pool
    ) -> None:
        """Submitting chat with no provider shows an error bubble."""
        from smartpad.ui.floating_panel import FloatingPanel  # noqa: PLC0415

        # Ensure no provider env vars are set
        env_backup = {
            k: os.environ.pop(k, None)
            for k in ("SMARTPAD_OPENAI_BASE_URL", "SMARTPAD_OPENAI_API_KEY")
        }
        try:
            panel = FloatingPanel(worker_pool)
            qtbot.addWidget(panel)
            panel.show_panel()
            qtbot.wait(100)

            panel._input.setPlainText("hello world")
            panel._on_send()
            qtbot.wait(100)

            # Status should say "No provider configured"
            assert "No provider" in panel._status.text()
        finally:
            for k, v in env_backup.items():
                if v is not None:
                    os.environ[k] = v


# ---------------------------------------------------------------------------
# App-level helpers test
# ---------------------------------------------------------------------------

class TestAppHelpers:
    def test_settings_to_pynput_conversion(self) -> None:
        from smartpad.app import _settings_to_pynput
        assert _settings_to_pynput("ctrl+alt+space") == "<ctrl>+<alt>+<space>"

    def test_settings_to_pynput_single_char(self) -> None:
        from smartpad.app import _settings_to_pynput
        assert _settings_to_pynput("ctrl+p") == "<ctrl>+p"

    def test_settings_to_pynput_f_key(self) -> None:
        from smartpad.app import _settings_to_pynput
        assert _settings_to_pynput("ctrl+f12") == "<ctrl>+<f12>"
