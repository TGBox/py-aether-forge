"""Discrete 2D aether grid and tile definitions."""

from dataclasses import dataclass
from enum import Enum, auto


class TileType(Enum):
    """Types of tiles in the aether arena."""

    VOID = auto()  # Abyss / empty aether
    PLATFORM_WALK = auto()  # Walkable stone / rune path for swarms
    PLATFORM_BUILD = auto()  # Solid foundation slot for towers
    CORE = auto()  # The astral world core (goal destination)
    PORTAL = auto()  # Chaos swarm spawn rift
    BARRIER = auto()  # Player-built aether barrier wall


@dataclass
class Tile:
    """Represents a single cell in the grid."""

    x: int
    y: int
    tile_type: TileType = TileType.VOID
    has_tower: bool = False
    has_barrier: bool = False
    rune_affinity: str | None = None  # e.g., 'FIRE_BONUS', 'RANGE_BONUS'


class Grid:
    """The 2D coordinate grid managing tiles, bounds, and adjacency."""

    def __init__(self, width: int = 20, height: int = 15) -> None:
        self.width: int = width
        self.height: int = height
        self._tiles: dict[tuple[int, int], Tile] = {
            (x, y): Tile(x=x, y=y, tile_type=TileType.VOID)
            for x in range(width)
            for y in range(height)
        }

    def in_bounds(self, x: int, y: int) -> bool:
        """Returns True if the coordinates are within the grid bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> Tile:
        """Retrieves a tile at given coordinates, defaulting to VOID if outside."""
        if (x, y) in self._tiles:
            return self._tiles[(x, y)]
        return Tile(x=x, y=y, tile_type=TileType.VOID)

    def set_tile(
        self,
        x: int,
        y: int,
        tile_type: TileType,
        rune_affinity: str | None = None,
    ) -> None:
        """Sets the type and optional rune affinity of a tile."""
        if self.in_bounds(x, y):
            tile = self._tiles[(x, y)]
            tile.tile_type = tile_type
            if rune_affinity is not None:
                tile.rune_affinity = rune_affinity

    def is_walkable(self, x: int, y: int) -> bool:
        """Checks if a tile can be traversed by enemy swarms.

        Enemy swarms can traverse walk paths, cores, portals, and unoccupied tower build slots.
        Towers and aether barriers block traversal.
        """
        if not self.in_bounds(x, y):
            return False
        tile = self.get_tile(x, y)
        if tile.has_barrier or tile.has_tower:
            return False
        return tile.tile_type in (
            TileType.PLATFORM_WALK,
            TileType.PLATFORM_BUILD,
            TileType.CORE,
            TileType.PORTAL,
        )

    def is_buildable(self, x: int, y: int) -> bool:
        """Checks if a tower can be placed on this designated build slot."""
        if not self.in_bounds(x, y):
            return False
        tile = self.get_tile(x, y)
        if tile.has_tower or tile.has_barrier:
            return False
        return tile.tile_type == TileType.PLATFORM_BUILD

    def can_place_barrier(self, x: int, y: int) -> bool:
        """Checks if an aether barrier wall can be placed on this platform tile."""
        if not self.in_bounds(x, y):
            return False
        tile = self.get_tile(x, y)
        if tile.has_barrier or tile.has_tower:
            return False
        return tile.tile_type in (TileType.PLATFORM_WALK, TileType.PLATFORM_BUILD)

    def get_neighbors(self, x: int, y: int) -> list[Tile]:
        """Returns the 4 orthogonal neighbor tiles that are within bounds."""
        neighbors: list[Tile] = []
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                neighbors.append(self.get_tile(nx, ny))
        return neighbors

    def find_tiles_of_type(self, tile_type: TileType) -> list[Tile]:
        """Returns all tiles matching the specified type."""
        return [t for t in self._tiles.values() if t.tile_type == tile_type]
