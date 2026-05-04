"""Global hotkey listener — SPEC.md sections 12, 17, 16.5.

Uses pynput.keyboard.GlobalHotKeys for cross-platform support.

Platform notes:
- macOS: requires Accessibility permission; logs a clear message if missing.
- Linux/Wayland: pynput registration may fail; logs the error and continues.
- Windows: works out of the box.

The listener runs in a daemon thread (owned by pynput). When the hotkey fires
it calls the callback on that thread, so callers must be thread-safe.
Use Qt signals (emit-from-any-thread is safe with queued connections).
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from typing import Any

from loguru import logger


class HotkeyListener:
    """Registers a global hotkey and calls *callback* when triggered.

    Args:
        hotkey_str: pynput combo string, e.g. "<ctrl>+<alt>+space".
        callback: zero-argument callable; called on the pynput thread.
    """

    def __init__(
        self,
        hotkey_str: str = "<ctrl>+<alt>+space",
        callback: Callable[[], None] | None = None,
    ) -> None:
        self._hotkey_str = hotkey_str
        self._callback = callback
        self._listener: Any = None
        self._lock = threading.Lock()

    # ── Public interface ──────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start the hotkey listener in a background thread.

        Returns:
            True if the listener started successfully, False otherwise.
        """
        try:
            from pynput import keyboard as _keyboard  # noqa: PLC0415
        except ImportError:
            logger.error(
                "pynput is not installed — global hotkey disabled. "
                "Install it with: pip install pynput"
            )
            return False

        try:
            mapping = {self._hotkey_str: self._on_hotkey}
            listener = _keyboard.GlobalHotKeys(mapping)
            listener.daemon = True
            listener.start()
            with self._lock:
                self._listener = listener
            logger.info("Global hotkey registered: {}", self._hotkey_str)
            return True
        except Exception as exc:
            self._handle_start_failure(exc)
            return False

    def stop(self) -> None:
        """Stop the hotkey listener if running."""
        with self._lock:
            listener = self._listener
            self._listener = None
        if listener is not None:
            try:
                listener.stop()
                logger.debug("Hotkey listener stopped.")
            except Exception as exc:
                logger.warning("Error stopping hotkey listener: {}", exc)

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._listener is not None

    # ── Private ───────────────────────────────────────────────────────────────

    def _on_hotkey(self) -> None:
        logger.debug("Hotkey fired: {}", self._hotkey_str)
        if self._callback is not None:
            try:
                self._callback()
            except Exception as exc:
                logger.exception("Hotkey callback raised: {}", exc)

    def _handle_start_failure(self, exc: Exception) -> None:
        """Log a clear, platform-specific message when listener fails to start."""
        if sys.platform == "darwin":
            logger.error(
                "Failed to register global hotkey on macOS. "
                "SmartPad needs Accessibility permission: "
                "System Settings → Privacy & Security → Accessibility → enable SmartPad. "
                "Error: {}",
                exc,
            )
        elif sys.platform == "linux":
            import os  # noqa: PLC0415
            wayland = os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE", "") == "wayland"
            if wayland:
                logger.warning(
                    "Global hotkey registration failed on Wayland ({}). "
                    "Wayland blocks global hotkeys by design. "
                    "Use the tray icon to open SmartPad instead.",
                    exc,
                )
            else:
                logger.error(
                    "Failed to register global hotkey on Linux: {}. "
                    "Use the tray icon to open SmartPad.",
                    exc,
                )
        else:
            logger.error(
                "Failed to register global hotkey ({}): {}. "
                "Use the tray icon to open SmartPad.",
                self._hotkey_str,
                exc,
            )
