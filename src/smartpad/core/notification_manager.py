"""Notification manager — SPEC.md section 14.

Determines whether a notification should be shown based on:
- Category-level toggles (reminders, tasks, errors, etc.)
- Quiet hours (configurable start/end hour)
- Global mute (duration-based or indefinite)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger


class NotificationManager:
    """Controls whether notifications are delivered.

    Args:
        settings: A ``SmartPadSettings`` instance (or duck-typed equivalent).
            Reads ``notifications`` (NotificationSettings) and
            ``quiet_hours_*`` fields.
    """

    def __init__(self, settings: Any) -> None:
        self._settings = settings
        self._muted_until: datetime | None = None  # None = not muted

    # ── public API ─────────────────────────────────────────────────────────────

    def should_notify(self, category: str) -> bool:
        """Return True if a notification for *category* should be shown now.

        A notification is suppressed when:
        - The global mute is active, OR
        - The current time is within quiet hours, OR
        - The category's ``toast`` toggle is False.

        Args:
            category: One of ``reminders``, ``tasks_due_today``,
                ``tasks_overdue``, ``sync_events``, ``new_messages``, ``errors``.

        Returns:
            True if the notification should be delivered.
        """
        if self.is_muted():
            logger.debug("Notification suppressed: globally muted (category={}).", category)
            return False
        if self.is_quiet_hours():
            logger.debug("Notification suppressed: quiet hours (category={}).", category)
            return False
        if not self._category_enabled(category):
            logger.debug("Notification suppressed: category '{}' toast disabled.", category)
            return False
        return True

    def mute(self, duration_minutes: int | None = None) -> None:
        """Mute all notifications.

        Args:
            duration_minutes: How long to mute. Pass ``None`` to mute indefinitely.
        """
        if duration_minutes is None:
            self._muted_until = datetime.max.replace(tzinfo=UTC)
            logger.info("Notifications muted indefinitely.")
        else:
            self._muted_until = datetime.now(UTC) + timedelta(minutes=duration_minutes)
            logger.info("Notifications muted for {} minutes.", duration_minutes)

    def unmute(self) -> None:
        """Clear the global mute."""
        self._muted_until = None
        logger.info("Notifications unmuted.")

    def is_muted(self) -> bool:
        """Return True if the global mute is currently active."""
        if self._muted_until is None:
            return False
        if datetime.now(UTC) < self._muted_until:
            return True
        # Mute has expired — clear it
        self._muted_until = None
        return False

    def is_quiet_hours(self, *, now: datetime | None = None) -> bool:
        """Return True if current local time is within quiet hours.

        Args:
            now: Override current time (for testing).

        Returns:
            True during quiet hours.
        """
        ns = self._settings
        if not getattr(ns, "quiet_hours_enabled", True):
            return False

        local_now = (now or datetime.now()).replace(tzinfo=None)
        hour = local_now.hour
        start: int = getattr(ns, "quiet_hours_start", 22)
        end: int = getattr(ns, "quiet_hours_end", 8)

        if start > end:
            # Spans midnight (e.g. 22 – 8)
            return hour >= start or hour < end
        return start <= hour < end

    # ── internal ──────────────────────────────────────────────────────────────

    def _category_enabled(self, category: str) -> bool:
        """Return True if the toast toggle for *category* is on."""
        notifications = getattr(self._settings, "notifications", None)
        if notifications is None:
            return True  # default allow
        cat_settings = getattr(notifications, category, None)
        if cat_settings is None:
            logger.warning("Unknown notification category '{}'; allowing.", category)
            return True
        return bool(getattr(cat_settings, "toast", True))
