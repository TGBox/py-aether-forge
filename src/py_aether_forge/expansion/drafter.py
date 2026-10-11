"""Roguelite platform shard drafting and docking validation."""

import random

from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.expansion.platform import PlatformShard


def get_default_shard_templates() -> list[PlatformShard]:
    """Catalog of craftable platform shards manifestable in the aether."""
    w = TileType.PLATFORM_WALK
    b = TileType.PLATFORM_BUILD

    return [
        PlatformShard(
            name="Astral-Bastion",
            description="Solide Plattform mit vier Turmplätzen und zentralem Korridor.",
            layout=[
                [b, w, b],
                [b, w, b],
            ],
            bonus_aether=15,
        ),
        PlatformShard(
            name="Serpentinen-Steg",
            description="Verlängert den Anmarschweg der Schwärme durch gewundenen Pfad.",
            layout=[
                [w, w, w],
                [b, b, w],
                [w, w, w],
            ],
            bonus_aether=25,
        ),
        PlatformShard(
            name="Flammen-Runen-Scholle",
            description="Gewährt +20% Feuerschaden auf platzierten Türmen.",
            layout=[
                [b, w],
                [b, w],
            ],
            rune_affinity="FIRE_BONUS",
            bonus_aether=20,
        ),
        PlatformShard(
            name="Frost-Zuflucht",
            description="Erhöht Verlangsamungseffekte von Eistürmen auf dieser Scholle.",
            layout=[
                [w, b, b],
                [w, w, b],
            ],
            rune_affinity="ICE_BONUS",
            bonus_aether=20,
        ),
        PlatformShard(
            name="Arkaner Ausblick",
            description="Erhöht die Reichweite gebauter Türme um 1 Feld.",
            layout=[
                [b, b, b],
                [w, w, w],
            ],
            rune_affinity="RANGE_BONUS",
            bonus_aether=30,
        ),
    ]


def is_valid_docking_location(
    grid: Grid,
    shard: PlatformShard,
    origin_x: int,
    origin_y: int,
) -> bool:
    """Validates if a platform shard can legally dock at (origin_x, origin_y).

    Requirements:
    1. All shard tiles must fit within the grid bounds.
    2. Non-VOID tiles of the shard cannot overlap existing non-VOID tiles.
    3. At least one tile of the shard must be orthogonally adjacent to an existing non-VOID tile.
    """
    has_adjacent_connection = False

    for dy, row in enumerate(shard.layout):
        for dx, tile_type in enumerate(row):
            if tile_type == TileType.VOID:
                continue

            tx = origin_x + dx
            ty = origin_y + dy

            # 1. Bounds check
            if not grid.in_bounds(tx, ty):
                return False

            # 2. Overlap check
            existing_tile = grid.get_tile(tx, ty)
            if existing_tile.tile_type != TileType.VOID:
                return False

            # 3. Adjacency check to an existing platform
            for nx, ny in ((tx - 1, ty), (tx + 1, ty), (tx, ty - 1), (tx, ty + 1)):
                if grid.in_bounds(nx, ny):
                    neighbor = grid.get_tile(nx, ny)
                    if neighbor.tile_type != TileType.VOID:
                        has_adjacent_connection = True

    return has_adjacent_connection


class PlatformDrafter:
    """Selects random platform shard offerings for post-wave drafting."""

    def __init__(self, templates: list[PlatformShard] | None = None) -> None:
        self.templates: list[PlatformShard] = (
            templates if templates is not None else get_default_shard_templates()
        )

    def generate_draft_options(
        self,
        count: int = 3,
        seed: int | None = None,
    ) -> list[PlatformShard]:
        """Returns a list of random platform shard options."""
        rng = random.Random(seed)
        if len(self.templates) <= count:
            return list(self.templates)
        return rng.sample(self.templates, count)
