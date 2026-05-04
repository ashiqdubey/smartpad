"""Tests for Phases 14, 15, 16, 19 UI components."""

from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot


# ── Settings Dialog ───────────────────────────────────────────────────────────

class TestSettingsDialog:
    def test_creates_without_crash(self, qtbot: QtBot) -> None:
        from smartpad.config import SmartPadSettings
        from smartpad.ui.settings_dialog import SettingsDialog

        s = SmartPadSettings()
        dlg = SettingsDialog(s)
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_has_three_tabs(self, qtbot: QtBot) -> None:
        from smartpad.config import SmartPadSettings
        from smartpad.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(SmartPadSettings())
        qtbot.addWidget(dlg)
        assert dlg._tabs.count() == 3

    def test_tab_labels(self, qtbot: QtBot) -> None:
        from smartpad.config import SmartPadSettings
        from smartpad.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(SmartPadSettings())
        qtbot.addWidget(dlg)
        labels = [dlg._tabs.tabText(i) for i in range(dlg._tabs.count())]
        assert "General" in labels
        assert "AI Providers" in labels
        assert "Data" in labels

    def test_settings_changed_signal_exists(self, qtbot: QtBot) -> None:
        from smartpad.config import SmartPadSettings
        from smartpad.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(SmartPadSettings())
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "settings_changed")

    def test_ai_level_slider_range(self, qtbot: QtBot) -> None:
        from smartpad.config import SmartPadSettings
        from smartpad.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(SmartPadSettings())
        qtbot.addWidget(dlg)
        assert dlg._ai_level_slider.minimum() == 0
        assert dlg._ai_level_slider.maximum() == 4

    def test_apply_updates_settings(self, qtbot: QtBot) -> None:
        from smartpad.config import SmartPadSettings
        from smartpad.ui.settings_dialog import SettingsDialog

        s = SmartPadSettings()
        dlg = SettingsDialog(s)
        qtbot.addWidget(dlg)
        dlg._ai_level_slider.setValue(3)
        dlg._apply()
        assert s.ai_level == 3


# ── Onboarding Dialog ─────────────────────────────────────────────────────────

class TestOnboardingDialog:
    def test_creates_without_crash(self, qtbot: QtBot) -> None:
        from smartpad.ui.onboarding import OnboardingDialog

        dlg = OnboardingDialog()
        qtbot.addWidget(dlg)
        assert dlg is not None

    def test_setup_complete_signal_exists(self, qtbot: QtBot) -> None:
        from smartpad.ui.onboarding import OnboardingDialog

        dlg = OnboardingDialog()
        qtbot.addWidget(dlg)
        assert hasattr(dlg, "setup_complete")

    def test_starts_on_setup_page(self, qtbot: QtBot) -> None:
        from smartpad.ui.onboarding import OnboardingDialog

        dlg = OnboardingDialog()
        qtbot.addWidget(dlg)
        assert dlg._stack.currentIndex() == 0

    def test_choose_advances_to_walkthrough(self, qtbot: QtBot) -> None:
        from smartpad.ui.onboarding import OnboardingDialog

        dlg = OnboardingDialog()
        qtbot.addWidget(dlg)
        dlg._choose("quick_start")
        assert dlg._stack.currentIndex() == 1

    def test_setup_complete_emits_on_finish(self, qtbot: QtBot) -> None:
        from smartpad.ui.onboarding import OnboardingDialog

        dlg = OnboardingDialog()
        qtbot.addWidget(dlg)
        dlg._choose("cloud")
        with qtbot.waitSignal(dlg.setup_complete, timeout=1000) as blocker:
            # Fast-forward through walkthrough cards
            for _ in range(dlg._card_stack.count()):
                dlg._next_card()
        assert blocker.args[0] == "cloud"

    def test_ollama_detected_updates_label(self, qtbot: QtBot) -> None:
        from smartpad.ui.onboarding import OnboardingDialog

        dlg = OnboardingDialog(detected_ollama=True)
        qtbot.addWidget(dlg)
        assert dlg._detected_ollama is True


# ── Browse Window ─────────────────────────────────────────────────────────────

class TestBrowseWindow:
    def test_creates_without_crash(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        assert w is not None

    def test_default_size(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        assert w.width() == 900
        assert w.height() == 600

    def test_search_box_exists(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        assert w._search_box is not None

    def test_populate_books(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        w.populate_books([{"id": "1", "name": "Work"}, {"id": "2", "name": "Personal"}])
        assert w._books_list.count() == 2

    def test_populate_cards(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        w.populate_cards([
            {"id": "a", "type": "note", "content": "Test note", "created_at": "2026-01-01"},
        ])
        # Empty label should be hidden, one card added
        assert not w._empty_label.isVisible()

    def test_search_signal_emitted(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        w._search_box.setText("python")
        with qtbot.waitSignal(w.search_requested, timeout=1000) as blocker:
            w._on_search()
        assert blocker.args[0] == "python"

    def test_signals_exist(self, qtbot: QtBot) -> None:
        from smartpad.ui.browse_window import BrowseWindow

        w = BrowseWindow()
        qtbot.addWidget(w)
        assert hasattr(w, "search_requested")
        assert hasattr(w, "item_selected")


# ── Model Manager ─────────────────────────────────────────────────────────────

class TestModelCatalog:
    def test_catalog_has_models(self) -> None:
        from smartpad.model_manager.catalog import CATALOG, DEFAULT_MODEL_ID
        assert len(CATALOG) >= 3
        assert DEFAULT_MODEL_ID

    def test_get_by_id(self) -> None:
        from smartpad.model_manager.catalog import get_by_id
        m = get_by_id("qwen3-1.7b-q4")
        assert m is not None
        assert m.tier == "fast"

    def test_get_by_tier(self) -> None:
        from smartpad.model_manager.catalog import get_by_tier
        fast = get_by_tier("fast")
        assert all(m.tier == "fast" for m in fast)
        assert len(fast) >= 1

    def test_unknown_id_returns_none(self) -> None:
        from smartpad.model_manager.catalog import get_by_id
        assert get_by_id("does-not-exist") is None
