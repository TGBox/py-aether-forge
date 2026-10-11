"""Tests for discrete grid, platform shards, and A* pathfinding."""

from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.core.pathfinding import can_build_without_blocking, find_path_astar
from py_aether_forge.expansion.platform import PlatformShard


def test_grid_initialization_and_tile_placement() -> None:
    grid = Grid(width=10, height=10)
    assert grid.get_tile(0, 0).tile_type == TileType.VOID

    grid.set_tile(2, 3, TileType.PLATFORM_WALK)
    assert grid.get_tile(2, 3).tile_type == TileType.PLATFORM_WALK
    assert grid.is_walkable(2, 3)
    assert not grid.is_buildable(2, 3)

    grid.set_tile(2, 4, TileType.PLATFORM_BUILD)
    assert grid.is_buildable(2, 4)
    assert not grid.is_walkable(2, 4)


def test_grid_neighbors() -> None:
    grid = Grid(width=5, height=5)
    neighbors = grid.get_neighbors(2, 2)
    assert len(neighbors) == 4
    coords = {(t.x, t.y) for t in neighbors}
    assert coords == {(1, 2), (3, 2), (2, 1), (2, 3)}

    corner_neighbors = grid.get_neighbors(0, 0)
    assert len(corner_neighbors) == 2


def test_platform_shard_attachment() -> None:
    # 3x3 shard: middle is walk, others build slots
    layout = [
        [TileType.PLATFORM_BUILD, TileType.PLATFORM_WALK, TileType.PLATFORM_BUILD],
        [TileType.PLATFORM_BUILD, TileType.PLATFORM_WALK, TileType.PLATFORM_BUILD],
        [TileType.PLATFORM_BUILD, TileType.PLATFORM_WALK, TileType.PLATFORM_BUILD],
    ]
    shard = PlatformShard(name="Standardbrücke", layout=layout)
    grid = Grid(width=10, height=10)
    shard.place_on_grid(grid, origin_x=1, origin_y=1)

    assert grid.get_tile(2, 1).tile_type == TileType.PLATFORM_WALK
    assert grid.get_tile(2, 2).tile_type == TileType.PLATFORM_WALK
    assert grid.get_tile(1, 1).tile_type == TileType.PLATFORM_BUILD


def test_pathfinding_direct_line() -> None:
    grid = Grid(width=5, height=5)
    # Straight path from (0, 2) to (4, 2)
    for x in range(5):
        grid.set_tile(x, 2, TileType.PLATFORM_WALK)

    grid.set_tile(0, 2, TileType.PORTAL)
    grid.set_tile(4, 2, TileType.CORE)

    path = find_path_astar(grid, start=(0, 2), goal=(4, 2))
    assert path is not None
    assert len(path) == 5
    assert path[0] == (0, 2)
    assert path[-1] == (4, 2)


def test_pathfinding_obstacle_detour() -> None:
    grid = Grid(width=5, height=5)
    # Fill with walk tiles
    for x in range(5):
        for y in range(5):
            grid.set_tile(x, y, TileType.PLATFORM_WALK)

    grid.set_tile(0, 2, TileType.PORTAL)
    grid.set_tile(4, 2, TileType.CORE)

    # Place wall / tower in between at (2, 2)
    grid.set_tile(2, 2, TileType.PLATFORM_BUILD)

    path = find_path_astar(grid, start=(0, 2), goal=(4, 2))
    assert path is not None
    assert (2, 2) not in path
    assert path[0] == (0, 2)
    assert path[-1] == (4, 2)


def test_pathfinding_no_path_returns_none() -> None:
    grid = Grid(width=5, height=5)
    grid.set_tile(0, 2, TileType.PORTAL)
    grid.set_tile(4, 2, TileType.CORE)
    # No walk tiles between them (VOID)
    path = find_path_astar(grid, start=(0, 2), goal=(4, 2))
    assert path is None


def test_can_build_without_blocking() -> None:
    grid = Grid(width=5, height=5)
    # Single 1-wide corridor
    for x in range(5):
        grid.set_tile(x, 2, TileType.PLATFORM_WALK)

    # Attempting to build on (2, 2) would sever the only corridor
    assert not can_build_without_blocking(grid, start=(0, 2), goal=(4, 2), target_tile=(2, 2))

    # Add alternate route at y=3
    for x in range(5):
        grid.set_tile(x, 3, TileType.PLATFORM_WALK)

    # Now blocking (2, 2) is allowed because alternate path exists
    assert can_build_without_blocking(grid, start=(0, 2), goal=(4, 2), target_tile=(2, 2))
