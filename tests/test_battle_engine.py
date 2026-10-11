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


def test_barrier_blockade_prevention() -> None:
    pygame.init()
    engine = BattleEngine(width=800, height=600)
    mid_y = engine.grid.height // 2

    # Attempting to block the entry choke point (portal_x + 1 = 3) cuts off all paths
    success = engine.build_barrier(3, mid_y)
    assert not success
    assert "Der Pfad zum Weltenkern darf nicht komplett versperrt werden" in engine.warning_message
    assert not engine.grid.get_tile(3, mid_y).has_barrier

    # However, building on the central lane (x=5) succeeds because bypass lanes exist!
    can_maze = engine.build_barrier(5, mid_y)
    assert can_maze
    assert engine.grid.get_tile(5, mid_y).has_barrier


def test_barrier_mazing_reroute_and_demolish() -> None:
    from py_aether_forge.core.grid import TileType
    from py_aether_forge.render.battle_engine import BARRIER_COST

    pygame.init()
    engine = BattleEngine(width=800, height=600)
    mid_y = engine.grid.height // 2

    # Add a detour above the middle line between x=4 and x=6
    # Path: (4, mid_y) -> (4, mid_y-1) -> (5, mid_y-1) -> (6, mid_y-1) -> (6, mid_y)
    engine.grid.set_tile(4, mid_y - 1, TileType.PLATFORM_WALK)
    engine.grid.set_tile(5, mid_y - 1, TileType.PLATFORM_WALK)
    engine.grid.set_tile(6, mid_y - 1, TileType.PLATFORM_WALK)

    # Before barrier: shortest path goes straight through (5, mid_y)
    p_before = engine._recalculate_swarm_path()
    assert p_before is not None
    assert (5, mid_y) in p_before
    assert (5, mid_y - 1) not in p_before

    initial_dust = engine.economy.aether_dust

    # Build barrier on (5, mid_y)
    built = engine.build_barrier(5, mid_y)
    assert built
    assert engine.economy.aether_dust == initial_dust - BARRIER_COST
    assert engine.grid.get_tile(5, mid_y).has_barrier

    # After barrier: swarm path must divert through the detour at (5, mid_y - 1)
    p_after = engine.cached_path
    assert p_after is not None
    assert (5, mid_y) not in p_after
    assert (5, mid_y - 1) in p_after

    # Demolish barrier
    removed = engine.remove_barrier(5, mid_y)
    assert removed
    assert engine.economy.aether_dust == initial_dust
    assert not engine.grid.get_tile(5, mid_y).has_barrier

    # Path restores straight route
    p_restored = engine.cached_path
    assert p_restored is not None
    assert (5, mid_y) in p_restored


def test_barrier_placement_in_initial_arena() -> None:
    """Verifies that barriers can be placed on the central lane of the initial arena right from wave 1."""
    pygame.init()
    engine = BattleEngine(width=800, height=600)
    mid_y = engine.grid.height // 2

    # Initial direct path takes the middle lane
    assert engine.cached_path is not None
    assert (6, mid_y) in engine.cached_path

    # Place barrier on (6, mid_y)
    built = engine.build_barrier(6, mid_y)
    assert built, "Barrier placement on central lane should succeed because bypass lanes exist"
    assert engine.grid.get_tile(6, mid_y).has_barrier

    # Mobs now take bypass lane around (6, mid_y)
    assert (6, mid_y) not in engine.cached_path

    # Ensure draw renders with barrier and does not crash
    surf = pygame.Surface((800, 600))
    engine.draw(surf)


def test_tower_placement_and_sale_reroutes_swarm_path() -> None:
    """Verifies that empty tower build slots are walkable and that placing/selling a tower reroutes swarm path."""
    pygame.init()
    engine = BattleEngine(width=800, height=600)
    mid_y = engine.grid.height // 2

    # Block the direct middle path at x=5 with a barrier, forcing path to go north or south
    # through build slots (e.g. (5, mid_y - 1) or (5, mid_y + 1))
    assert engine.build_barrier(5, mid_y)
    path_with_barrier = engine.cached_path
    assert path_with_barrier is not None

    # The detour must use one of the adjacent rows containing PLATFORM_BUILD slots
    detour_slot = (5, mid_y - 1) if (5, mid_y - 1) in path_with_barrier else (5, mid_y + 1)
    assert engine.grid.is_buildable(detour_slot[0], detour_slot[1]), (
        "Detour slot should be a valid tower build slot"
    )
    assert engine.grid.is_walkable(detour_slot[0], detour_slot[1]), (
        "Unoccupied tower build slot must be walkable by creeps"
    )

    # Now place a tower on this detour slot
    built_tower = engine.build_tower(detour_slot[0], detour_slot[1], ElementType.ICE)
    assert built_tower, "Building tower on walkable build slot must succeed"
    assert not engine.grid.is_walkable(detour_slot[0], detour_slot[1]), (
        "Tile occupied by tower must no longer be walkable"
    )

    # Path must recalculate around the placed tower
    path_with_tower = engine.cached_path
    assert path_with_tower is not None
    assert detour_slot not in path_with_tower, "Swarm path must not walk through the tower"

    # Now select and sell the tower
    engine.selected_tower = engine.towers[0]
    initial_dust = engine.economy.aether_dust
    assert engine.sell_selected_tower()
    assert engine.economy.aether_dust > initial_dust
    assert engine.grid.is_walkable(detour_slot[0], detour_slot[1]), (
        "Selling tower must reopen slot for creep movement"
    )

    # Swarm path can now freely pass through the slot again
    path_after_sale = engine.cached_path
    assert path_after_sale is not None
