"""Tests for platform shard drafting and edge docking validation."""

from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.expansion.drafter import PlatformDrafter, is_valid_docking_location
from py_aether_forge.expansion.platform import PlatformShard


def test_drafter_generates_three_distinct_options() -> None:
    drafter = PlatformDrafter()
    options = drafter.generate_draft_options(count=3)
    assert len(options) == 3
    names = [opt.name for opt in options]
    assert len(set(names)) >= 2  # Variety


def test_docking_requires_adjacency_to_existing_platform() -> None:
    grid = Grid(width=10, height=10)
    # Start with a single core tile at (5, 5)
    grid.set_tile(5, 5, TileType.CORE)

    # 1x1 shard
    shard = PlatformShard(name="Mini-Insel", layout=[[TileType.PLATFORM_WALK]])

    # Docking at (5, 6) is adjacent to (5, 5) -> valid
    assert is_valid_docking_location(grid, shard, origin_x=5, origin_y=6)

    # Docking at (0, 0) is far away in empty void -> invalid
    assert not is_valid_docking_location(grid, shard, origin_x=0, origin_y=0)


def test_docking_cannot_overlap_existing_tiles() -> None:
    grid = Grid(width=10, height=10)
    grid.set_tile(5, 5, TileType.CORE)

    shard = PlatformShard(name="Mini-Insel", layout=[[TileType.PLATFORM_WALK]])

    # Overlapping directly on (5, 5) is invalid
    assert not is_valid_docking_location(grid, shard, origin_x=5, origin_y=5)


def test_docking_must_be_within_bounds() -> None:
    grid = Grid(width=5, height=5)
    grid.set_tile(4, 4, TileType.CORE)

    # 2x2 shard extending out of bounds
    shard = PlatformShard(
        name="Block",
        layout=[
            [TileType.PLATFORM_BUILD, TileType.PLATFORM_BUILD],
            [TileType.PLATFORM_BUILD, TileType.PLATFORM_BUILD],
        ],
    )
    assert not is_valid_docking_location(grid, shard, origin_x=4, origin_y=4)


def test_platform_shard_rotation() -> None:
    """Verifies that platform shards can be rotated 90 degrees clockwise and counter-clockwise."""
    w = TileType.PLATFORM_WALK
    b = TileType.PLATFORM_BUILD

    shard = PlatformShard(
        name="TestShard",
        layout=[
            [w, b, b],
            [w, w, b],
        ],  # width=3, height=2
    )
    assert shard.width == 3
    assert shard.height == 2

    # Rotate 90 degrees clockwise -> width=2, height=3
    shard.rotate(clockwise=True)
    assert shard.width == 2
    assert shard.height == 3
    assert shard.layout == [
        [w, w],
        [w, b],
        [b, b],
    ]

    # Rotate 3 more times -> full 360 rotation restores original orientation
    shard.rotate(clockwise=True)
    shard.rotate(clockwise=True)
    shard.rotate(clockwise=True)
    assert shard.width == 3
    assert shard.height == 2
    assert shard.layout == [
        [w, b, b],
        [w, w, b],
    ]


def test_viewport_camera_pan_zoom_and_center() -> None:
    """Verifies that the tactical viewport supports centering, panning, and zooming."""
    import pygame

    from py_aether_forge.render.viewport import Viewport

    pygame.init()
    vp = Viewport(tile_size=48)
    assert vp.zoom == 1.0

    # Center on a 20x20 grid within a 1280x720 window
    vp.center_on_grid(screen_w=1280, screen_h=720, grid_w=20, grid_h=20)
    # Total grid px = 20 * 48 = 960 width, 960 height
    # Offset x = (1280 - 960) // 2 = 160
    assert vp.offset_x == 160
    assert vp.offset_y == (720 - 960) // 2

    # Pan
    vp.pan(50, -30)
    assert vp.offset_x == 210

    # Zoom at center
    old_zoom = vp.zoom
    vp.zoom_at(screen_x=640, screen_y=360, factor=1.2)
    assert vp.zoom > old_zoom
    assert vp.tile_size > 48


def test_battle_engine_draft_shard_rotation_and_preview() -> None:
    """Verifies that BattleEngine allows rotating selected draft shards and rendering previews."""
    import pygame

    from py_aether_forge.core.state import GameState
    from py_aether_forge.render.battle_engine import BattleEngine

    pygame.init()
    engine = BattleEngine(width=1024, height=768)

    # Transition to draft state
    engine.draft_options = engine.drafter.generate_draft_options(count=3)
    engine.match_state.finish_wave_and_enter_draft()
    assert engine.match_state.current_state == GameState.DRAFT

    # Select shard 0
    engine.select_draft_shard(0)
    assert engine.selected_draft_shard is not None
    orig_w, orig_h = engine.selected_draft_shard.width, engine.selected_draft_shard.height

    # Rotate shard
    rotated = engine.rotate_selected_draft_shard(clockwise=True)
    assert rotated
    assert engine.selected_draft_shard.width == orig_h
    assert engine.selected_draft_shard.height == orig_w

    # Right click also rotates when in draft mode
    engine.handle_mouse_click(100, 100, button=3)
    assert engine.selected_draft_shard.width == orig_w
    assert engine.selected_draft_shard.height == orig_h

    # Test preview rendering without error
    surf = pygame.Surface((1024, 768))
    engine.hover_tile = (5, 5)
    engine.draw(surf)
