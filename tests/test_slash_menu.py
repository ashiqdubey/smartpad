"""Tests for the slash command popup menu."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from smartpad.ui.slash_menu import SlashMenu


def test_slash_menu_creates(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    assert menu is not None


def test_slash_menu_hidden_by_default(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    assert not menu.isVisible()


def test_update_filter_shows_menu(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/no")
    assert menu.isVisible()
    assert menu._list.count() >= 1


def test_update_filter_hides_on_no_match(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/zzzznotacommand")
    assert not menu.isVisible()


def test_update_filter_hides_when_no_slash(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/no")  # show first
    menu.update_filter("hello")  # then non-slash
    assert not menu.isVisible()


def test_update_filter_slash_only_shows_all(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/")
    assert menu.isVisible()
    # Should show all commands
    from smartpad.core.intent_detector import ALL_SLASH_COMMANDS
    assert menu._list.count() == len(ALL_SLASH_COMMANDS)


def test_move_selection(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/")
    initial = menu._list.currentRow()
    menu.move_selection(1)
    assert menu._list.currentRow() == initial + 1


def test_move_selection_wraps(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/")
    # Go to first item
    menu._list.setCurrentRow(0)
    menu.move_selection(-1)
    # Should wrap to last
    assert menu._list.currentRow() == menu._list.count() - 1


def test_command_selected_signal(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/note")
    with qtbot.waitSignal(menu.command_selected, timeout=1000) as blocker:
        menu.accept_selection()
    assert blocker.args[0] == "/note"


def test_accept_selection_hides_menu(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/note")
    menu.accept_selection()
    assert not menu.isVisible()


def test_dismissed_signal_on_esc(qtbot: QtBot) -> None:
    menu = SlashMenu()
    qtbot.addWidget(menu)
    menu.update_filter("/note")
    with qtbot.waitSignal(menu.dismissed, timeout=1000):
        qtbot.keyClick(menu, Qt.Key.Key_Escape)
    assert not menu.isVisible()
