"""Floating platform shards and layout definitions."""

from dataclasses import dataclass

from py_aether_forge.core.grid import Grid, TileType


@dataclass
class PlatformShard:
    """A multi-tile floating landmass fragment that can be manifested on the grid."""

    name: str
    layout: list[list[TileType]]  # 2D matrix: row (y) by col (x)
    description: str = ""
    rune_affinity: str | None = None
    portal_offset: tuple[int, int] | None = None  # Optional relative coords where portal manifests
    bonus_aether: int = 0

    @property
    def height(self) -> int:
        return len(self.layout)

    @property
    def width(self) -> int:
        return len(self.layout[0]) if self.layout else 0

    def place_on_grid(self, grid: Grid, origin_x: int, origin_y: int) -> bool:
        """Places the shard onto the grid at (origin_x, origin_y).

        Returns True if all tiles were in-bounds and placed.
        """
        # First verify bounds
        for dy, row in enumerate(self.layout):
            for dx, tile_type in enumerate(row):
                if tile_type != TileType.VOID and not grid.in_bounds(origin_x + dx, origin_y + dy):
                    return False

        # Apply tiles
        for dy, row in enumerate(self.layout):
            for dx, tile_type in enumerate(row):
                if tile_type != TileType.VOID:
                    grid.set_tile(
                        origin_x + dx,
                        origin_y + dy,
                        tile_type,
                        rune_affinity=self.rune_affinity,
                    )

        if self.portal_offset is not None:
            px, py = self.portal_offset
            grid.set_tile(origin_x + px, origin_y + py, TileType.PORTAL)

        return True
