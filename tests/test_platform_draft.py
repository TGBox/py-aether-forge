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
