"""Unit and headless simulation tests for BattleEngine."""

import os

# Headless dummy video driver for testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

from py_aether_forge.core.state import GameState
from py_aether_forge.render.battle_engine import BattleEngine
from py_aether_forge.towers.elements import ElementType


def test_battle_engine_initialization() -> None:
    pygame.init()
    engine = BattleEngine(width=800, height=600)
    assert engine.economy.aether_dust >= 150
    assert engine.match_state.current_state == GameState.PREPARATION
    assert len(engine.towers) == 0


def test_battle_engine_build_and_start_wave() -> None:
    pygame.init()
    engine = BattleEngine(width=800, height=600)

    # Find a valid build slot
    build_slots = engine.grid.find_tiles_of_type(engine.grid.get_tile(3, 4).tile_type)
    assert len(build_slots) > 0
    bx, by = build_slots[0].x, build_slots[0].y

    # Build a fire tower
    built = engine.build_tower(bx, by, ElementType.FIRE)
    assert built
    assert len(engine.towers) == 1

    # Start wave
    started = engine.start_next_wave()
    assert started
    assert engine.match_state.current_state == GameState.WAVE

    # Tick simulation forward
    for _ in range(60):
        engine.update(1.0 / 60.0)

    # Surface render test
    surf = pygame.Surface((800, 600))
    engine.draw(surf)


def test_multi_wave_and_draft_progression() -> None:
    pygame.init()
    engine = BattleEngine(width=800, height=600)

    # --- WAVE 1 ---
    assert engine.match_state.current_state == GameState.PREPARATION
    assert engine.start_next_wave()
    assert engine.match_state.current_state == GameState.WAVE

    # Force-clear spawning and creeps to simulate wave 1 victory
    engine.wave_spawner.spawn_queue.clear()
    engine.creeps.clear()
    engine.update(0.1)

    assert engine.match_state.current_state == GameState.DRAFT
    assert len(engine.draft_options) == 3

    # Select draft shard 0 and dock it at a valid location (e.g. above portal at (2, 3))
    engine.select_draft_shard(0)
    placed = False
    for x in range(engine.grid.width):
        for y in range(engine.grid.height):
            if engine.place_draft_shard(x, y):
                placed = True
                break
        if placed:
            break

    assert placed, "Could not find a valid docking spot for shard in wave 1"
    assert engine.match_state.current_state == GameState.PREPARATION
    assert len(engine.draft_options) == 0

    # --- WAVE 2 ---
    assert engine.start_next_wave()
    assert engine.match_state.current_state == GameState.WAVE
    assert engine.match_state.wave_number == 2

    # Force-clear wave 2
    engine.wave_spawner.spawn_queue.clear()
    engine.creeps.clear()
    engine.update(0.1)

    assert engine.match_state.current_state == GameState.DRAFT
    assert len(engine.draft_options) == 3, "Draft options must be populated after wave 2!"

    # Select draft shard 1 and dock it
    engine.select_draft_shard(1)
    placed_wave2 = False
    for x in range(engine.grid.width):
        for y in range(engine.grid.height):
            if engine.place_draft_shard(x, y):
                placed_wave2 = True
                break
        if placed_wave2:
            break

    assert placed_wave2, "Could not find a valid docking spot for shard in wave 2"
    assert engine.match_state.current_state == GameState.PREPARATION
    assert len(engine.draft_options) == 0
