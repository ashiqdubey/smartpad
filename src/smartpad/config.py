"""Application configuration via pydantic-settings.

Settings are loaded from <DATA_DIR>/config.json and can be overridden
via environment variables prefixed with SMARTPAD_.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, JsonConfigSettingsSource, PydanticBaseSettingsSource

from smartpad.utils.paths import get_data_dir
from smartpad.utils.portable import get_portable_dir


def _resolve_data_dir() -> Path:
    portable = get_portable_dir()
    if portable is not None:
        return portable
    return get_data_dir()


DATA_DIR: Path = _resolve_data_dir()


class NotificationCategory(BaseSettings):
    toast: bool = True
    sound: bool = False
    tray_badge: bool = False


class NotificationSettings(BaseSettings):
    reminders: NotificationCategory = Field(
        default_factory=lambda: NotificationCategory(toast=True, sound=True, tray_badge=True)
    )
    tasks_due_today: NotificationCategory = Field(
        default_factory=lambda: NotificationCategory(toast=False, sound=False, tray_badge=True)
    )
    tasks_overdue: NotificationCategory = Field(
        default_factory=lambda: NotificationCategory(toast=True, sound=False, tray_badge=False)
    )
    sync_events: NotificationCategory = Field(
        default_factory=lambda: NotificationCategory(toast=False, sound=False, tray_badge=False)
    )
    new_messages: NotificationCategory = Field(
        default_factory=lambda: NotificationCategory(toast=False, sound=False, tray_badge=False)
    )
    errors: NotificationCategory = Field(
        default_factory=lambda: NotificationCategory(toast=True, sound=False, tray_badge=True)
    )


class ContextSettings(BaseSettings):
    strategy: Literal["none", "truncate", "sliding_summary"] = "sliding_summary"
    trigger_messages: int = 30
    trigger_tokens: int = 6000
    messages_per_summary: int = 15
    recent_messages_kept: int = 15
    show_summarised_originals: bool = True


class BackupSettings(BaseSettings):
    enabled: bool = True
    retention_days: int = 7
    backup_path: Path | None = None


class LocalModelSettings(BaseSettings):
    idle_unload_enabled: bool = True
    idle_threshold_minutes: int = 30


class SmartPadSettings(BaseSettings):
    # Panel / UI
    hotkey: str = "ctrl+alt+space"
    theme: Literal["dark", "light", "system"] = "system"
    ai_level: int = Field(default=1, ge=0, le=4)
    panel_position_x: int = -1  # -1 = use default (right-anchored)
    panel_position_y: int = 80
    panel_width: int = 420
    panel_height: int = 560
    startup_with_os: bool = False

    # AI / LLM
    local_model_name: str = "Qwen3-1.7B-Q4_K_M.gguf"
    routing_temperature: float = 0.0
    chat_temperature: float = 0.6

    # Context window management
    context: ContextSettings = Field(default_factory=ContextSettings)

    # Search
    fts_results_limit: int = 50

    # Reminders
    reminder_check_interval_seconds: int = 30

    # Quiet hours (24h format)
    quiet_hours_enabled: bool = True
    quiet_hours_start: int = 22  # 10pm
    quiet_hours_end: int = 8  # 8am

    # Notifications
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)

    # Local API
    api_port: int = 7823

    # Backup
    backup: BackupSettings = Field(default_factory=BackupSettings)

    # Local model lifecycle
    local_model: LocalModelSettings = Field(default_factory=LocalModelSettings)

    model_config = {
        "env_prefix": "SMARTPAD_",
        "env_nested_delimiter": "__",
    }

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        **kwargs: object,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        config_file = DATA_DIR / "config.json"
        if config_file.exists():
            return (
                kwargs["init_settings"],
                kwargs["env_settings"],
                JsonConfigSettingsSource(settings_cls, json_file=config_file),
                kwargs["dotenv_settings"],
            )
        return (
            kwargs["init_settings"],
            kwargs["env_settings"],
            kwargs["dotenv_settings"],
        )

    def save(self) -> None:
        """Persist current settings to <DATA_DIR>/config.json."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        config_file = DATA_DIR / "config.json"
        config_file.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2)
        )


def load_settings() -> SmartPadSettings:
    """Load settings, creating DATA_DIR if needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return SmartPadSettings()
