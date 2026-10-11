"""Headless Qt test suite for UI screens and window management."""

import os
import sys

# Configure offscreen drivers for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from PySide6.QtWidgets import QApplication

from py_aether_forge.app import AetherForgeWindow
from py_aether_forge.meta.save_system import SaveSystem


def test_app_window_screens_and_fullscreen_toggle(tmp_path) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    save_file = tmp_path / "test_profile.json"
    window = AetherForgeWindow()
    window.save_system = SaveSystem(save_path=save_file)
    window.sanctuary.save_system = window.save_system
    window.battle_view.save_system = window.save_system

    # Initial screen: Main Menu (index 0)
    assert window.stack.currentIndex() == 0

    # Switch to Sanctuary (index 1)
    window._open_sanctuary()
    assert window.stack.currentIndex() == 1

    # Switch to Battle View (index 2)
    window._start_battle()
    assert window.stack.currentIndex() == 2

    # Switch back to Main Menu (index 0)
    window._open_main_menu()
    assert window.stack.currentIndex() == 0

    # Test fullscreen toggle
    assert not window.isFullScreen()
    window.toggle_fullscreen()
    assert window.isFullScreen()
    window.toggle_fullscreen()
    assert not window.isFullScreen()
