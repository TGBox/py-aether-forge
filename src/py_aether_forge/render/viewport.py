"""Viewport projection and tactical arena rendering."""

import pygame

from py_aether_forge.config import COLORS, GRID_CONFIG
from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.enemies.creep import Creep
from py_aether_forge.towers.elements import ElementType
from py_aether_forge.towers.tower import Tower

ELEMENT_COLOR_MAP = {
    ElementType.FIRE: COLORS.element_fire,
    ElementType.ICE: COLORS.element_ice,
    ElementType.ARCANE: COLORS.element_arcane,
    ElementType.NATURE: COLORS.element_nature,
    ElementType.FROSTFIRE: COLORS.hybrid_frostfire,
    ElementType.PLASMA: COLORS.hybrid_plasma,
    ElementType.STEAM: COLORS.hybrid_steam,
    ElementType.GLACIER_ROOT: COLORS.hybrid_glacier_root,
    ElementType.ASTRAL_SPORE: COLORS.hybrid_plasma,
    ElementType.VOID_CHILL: COLORS.hybrid_frostfire,
}


class Viewport:
    """Projects grid coordinates onto screen space and renders battle entities."""

    def __init__(self, tile_size: int = GRID_CONFIG.tile_size) -> None:
        self.tile_size = tile_size
        self.offset_x: int = 40
        self.offset_y: int = 50

    def grid_to_screen(self, gx: float, gy: float) -> tuple[int, int]:
        """Converts grid coordinates to screen pixel coordinates (top-left of tile)."""
        sx = int(self.offset_x + gx * self.tile_size)
        sy = int(self.offset_y + gy * self.tile_size)
        return sx, sy

    def grid_center_to_screen(self, gx: float, gy: float) -> tuple[int, int]:
        """Converts grid coordinates to screen pixel coordinates (center of tile)."""
        sx = int(self.offset_x + (gx + 0.5) * self.tile_size)
        sy = int(self.offset_y + (gy + 0.5) * self.tile_size)
        return sx, sy

    def screen_to_grid(self, sx: int, sy: int) -> tuple[int, int]:
        """Converts mouse pixel coordinates to integer grid coordinates."""
        gx = (sx - self.offset_x) // self.tile_size
        gy = (sy - self.offset_y) // self.tile_size
        return gx, gy

    def draw_grid(
        self, surface: pygame.Surface, grid: Grid, hover_tile: tuple[int, int] | None = None
    ) -> None:
        """Renders the floating platform tiles and border outlines."""
        for y in range(grid.height):
            for x in range(grid.width):
                tile = grid.get_tile(x, y)
                if tile.tile_type == TileType.VOID:
                    continue

                sx, sy = self.grid_to_screen(x, y)
                rect = pygame.Rect(sx, sy, self.tile_size, self.tile_size)

                # Base tile coloring
                if tile.tile_type == TileType.PLATFORM_WALK:
                    pygame.draw.rect(surface, COLORS.platform_walk, rect)
                    pygame.draw.rect(surface, COLORS.platform_border, rect, 1)
                elif tile.tile_type == TileType.PLATFORM_BUILD:
                    pygame.draw.rect(surface, COLORS.platform_build_slot, rect)
                    pygame.draw.rect(surface, COLORS.platform_border, rect, 2)
                    # Rune pedestal center dot
                    cx, cy = self.grid_center_to_screen(x, y)
                    pygame.draw.circle(surface, COLORS.platform_border, (cx, cy), 4)
                elif tile.tile_type == TileType.CORE:
                    pygame.draw.rect(surface, (25, 45, 80), rect)
                    cx, cy = self.grid_center_to_screen(x, y)
                    pygame.draw.circle(surface, COLORS.core_glow, (cx, cy), self.tile_size // 3)
                    pygame.draw.circle(surface, COLORS.core_core, (cx, cy), self.tile_size // 6)
                elif tile.tile_type == TileType.PORTAL:
                    pygame.draw.rect(surface, (40, 20, 60), rect)
                    cx, cy = self.grid_center_to_screen(x, y)
                    pygame.draw.circle(
                        surface, COLORS.portal_purple, (cx, cy), self.tile_size // 3, 3
                    )

                # Draw barrier monolith if placed
                if tile.has_barrier:
                    cx, cy = self.grid_center_to_screen(x, y)
                    r = self.tile_size // 3
                    # Crystal barrier
                    barrier_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
                    pygame.draw.rect(surface, (15, 35, 55), barrier_rect, border_radius=4)
                    pygame.draw.rect(surface, (79, 195, 247), barrier_rect, 2, border_radius=4)
                    pygame.draw.line(
                        surface, (130, 220, 255), (cx - r + 3, cy), (cx + r - 3, cy), 2
                    )
                    pygame.draw.line(
                        surface, (130, 220, 255), (cx, cy - r + 3), (cx, cy + r - 3), 2
                    )

                # Hover highlight
                if hover_tile == (x, y):
                    highlight = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                    highlight.fill((255, 255, 255, 40))
                    surface.blit(highlight, (sx, sy))

    def draw_path_telegraph(
        self, surface: pygame.Surface, path: list[tuple[int, int]] | None
    ) -> None:
        """Renders a soft glowing path line indicating the route the swarms will follow."""
        if not path or len(path) < 2:
            return

        points = [self.grid_center_to_screen(gx, gy) for gx, gy in path]
        # Glow line
        pygame.draw.lines(surface, (50, 160, 220, 100), False, points, 3)
        # Small route beads
        for i, pt in enumerate(points):
            if i % 2 == 0:
                pygame.draw.circle(surface, (130, 220, 255), pt, 3)

    def draw_towers(
        self,
        surface: pygame.Surface,
        towers: list[Tower],
        selected_tower: Tower | None = None,
    ) -> None:
        """Renders all placed defense monuments."""
        for tower in towers:
            cx, cy = self.grid_center_to_screen(tower.x, tower.y)
            color = ELEMENT_COLOR_MAP.get(tower.element, (255, 255, 255))

            # Base pedestal
            radius = self.tile_size // 3
            pygame.draw.circle(surface, (20, 25, 45), (cx, cy), radius + 2)
            pygame.draw.circle(surface, color, (cx, cy), radius)

            # Core rune gem
            inner_radius = max(3, radius // 2)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), inner_radius)

            # Selected indicator / range circle
            if tower is selected_tower:
                range_px = int(tower.range_radius * self.tile_size)
                range_surf = pygame.Surface((range_px * 2 + 4, range_px * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(range_surf, (*color, 35), (range_px + 2, range_px + 2), range_px)
                pygame.draw.circle(
                    range_surf, (*color, 160), (range_px + 2, range_px + 2), range_px, 2
                )
                surface.blit(range_surf, (cx - range_px - 2, cy - range_px - 2))

    def draw_creeps(self, surface: pygame.Surface, creeps: list[Creep]) -> None:
        """Renders creeping chaos swarms and health bars."""
        for creep in creeps:
            if not creep.is_alive:
                continue

            cx, cy = self.grid_center_to_screen(creep.x, creep.y)
            radius = self.tile_size // 4

            # Shadow
            pygame.draw.circle(surface, (5, 5, 10), (cx, cy + 3), radius)
            # Body
            pygame.draw.circle(surface, (220, 60, 85), (cx, cy), radius)
            pygame.draw.circle(surface, (255, 180, 195), (cx, cy), radius // 2)

            # Health bar above
            hp_w = self.tile_size - 10
            hp_h = 4
            bx = cx - hp_w // 2
            by = cy - radius - 8

            pct = max(0.0, min(1.0, creep.hp / creep.max_hp)) if creep.max_hp > 0 else 0.0
            pygame.draw.rect(surface, (40, 40, 50), (bx, by, hp_w, hp_h))
            pygame.draw.rect(surface, (80, 225, 100), (bx, by, int(hp_w * pct), hp_h))
