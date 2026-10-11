"""Headless Qt test suite for UI screens and window management."""

import os
import sys

# Configure offscreen drivers for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from PySide6.QtWidgets import QApplication

from py_aether_forge.app import AetherForgeWindow
from py_aether_forge.core.state import GameState
from py_aether_forge.meta.save_system import SaveSystem
from py_aether_forge.towers.elements import ElementType


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


def test_ui_draft_cards_shown_across_multiple_waves(tmp_path) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    save_file = tmp_path / "test_profile_draft.json"
    window = AetherForgeWindow()
    window.save_system = SaveSystem(save_path=save_file)
    bv = window.battle_view
    bv.save_system = window.save_system
    window.show()

    window._start_battle()
    engine = bv.engine
    assert engine is not None

    # --- WAVE 1 ---
    engine.start_next_wave()
    engine.wave_spawner.spawn_queue.clear()
    engine.creeps.clear()
    engine.update(0.1)
    bv._update_hud_display()

    assert engine.match_state.current_state == GameState.DRAFT
    assert not bv.draft_container.isHidden(), "Draft container should be shown in wave 1"
    assert bv.draft_cards_layout.count() == 3

    # Select draft option 0
    bv._select_draft_option(0)
    assert engine.selected_draft_shard is not None

    # Dock shard
    for x in range(engine.grid.width):
        for y in range(engine.grid.height):
            if engine.place_draft_shard(x, y):
                break
        if engine.match_state.current_state == GameState.PREPARATION:
            break

    assert engine.match_state.current_state == GameState.PREPARATION
    bv._update_hud_display()
    assert bv.draft_container.isHidden(), "Draft container should be hidden once placed"

    # --- WAVE 2 ---
    engine.start_next_wave()
    engine.wave_spawner.spawn_queue.clear()
    engine.creeps.clear()
    engine.update(0.1)
    bv._update_hud_display()

    assert engine.match_state.current_state == GameState.DRAFT
    assert not bv.draft_container.isHidden(), (
        "Draft container MUST be visible in wave 2 after wave completes!"
    )
    assert bv.draft_cards_layout.count() == 3, "Draft cards MUST be rebuilt and shown for wave 2!"


def test_ui_tower_inspector_and_stats_display(tmp_path) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    save_file = tmp_path / "test_profile_inspector.json"
    window = AetherForgeWindow()
    window.save_system = SaveSystem(save_path=save_file)
    bv = window.battle_view
    bv.save_system = window.save_system
    window.show()

    window._start_battle()
    engine = bv.engine
    assert engine is not None

    # Initially build bar is shown and inspector is hidden
    assert not bv.build_bar.isHidden()
    assert bv.inspector_panel.isHidden()

    # Build a fire tower at valid slot
    build_slots = engine.grid.find_tiles_of_type(engine.grid.get_tile(3, 4).tile_type)
    bx, by = build_slots[0].x, build_slots[0].y
    engine.build_tower(bx, by, ElementType.FIRE)
    bv._update_hud_display()

    # Now inspector should be visible because selected_tower is set
    assert not bv.inspector_panel.isHidden()
    assert bv.build_bar.isHidden()
    assert "Feuer" in bv.lbl_insp_title.text()
    assert "Schaden:" in bv.lbl_insp_stats.text()
    assert "Upgrade" in bv.btn_upgrade.text()

    # Deselect
    bv._deselect_tower()
    assert bv.inspector_panel.isHidden()
    assert not bv.build_bar.isHidden()
