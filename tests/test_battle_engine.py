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
