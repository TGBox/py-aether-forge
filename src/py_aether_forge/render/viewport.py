"""Viewport projection and tactical arena rendering with zoom and pan camera controls."""

from __future__ import annotations

import pygame

from py_aether_forge.config import COLORS, GRID_CONFIG
from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.enemies.creep import Creep
from py_aether_forge.expansion.platform import PlatformShard
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
    """Projects grid coordinates onto screen space and renders battle entities with zoom & pan."""

    def __init__(self, tile_size: int = GRID_CONFIG.tile_size) -> None:
        self.base_tile_size = tile_size
        self.zoom: float = 1.0
        self.min_zoom: float = 0.4
        self.max_zoom: float = 2.5
        self.offset_x: int = 40
        self.offset_y: int = 50

    @property
    def tile_size(self) -> int:
        """Dynamically scaled tile size in screen pixels."""
        return max(16, int(self.base_tile_size * self.zoom))

    def center_on_grid(self, screen_w: int, screen_h: int, grid_w: int, grid_h: int) -> None:
        """Centers the tactical grid inside the visible canvas."""
        ts = self.tile_size
        total_w = grid_w * ts
        total_h = grid_h * ts
        self.offset_x = (screen_w - total_w) // 2
        self.offset_y = (screen_h - total_h) // 2

    def pan(self, dx: int, dy: int) -> None:
        """Pans the tactical camera by delta pixels."""
        self.offset_x += dx
        self.offset_y += dy

    def zoom_at(self, screen_x: int, screen_y: int, factor: float) -> None:
        """Scales zoom centered around a screen point (e.g. mouse cursor)."""
        old_ts = self.tile_size
        gx = (screen_x - self.offset_x) / old_ts
        gy = (screen_y - self.offset_y) / old_ts

        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        new_ts = self.tile_size

        self.offset_x = int(screen_x - gx * new_ts)
        self.offset_y = int(screen_y - gy * new_ts)

    def grid_to_screen(self, gx: float, gy: float) -> tuple[int, int]:
        """Converts grid coordinates to screen pixel coordinates (top-left of tile)."""
        ts = self.tile_size
        sx = int(self.offset_x + gx * ts)
        sy = int(self.offset_y + gy * ts)
        return sx, sy

    def grid_center_to_screen(self, gx: float, gy: float) -> tuple[int, int]:
        """Converts grid coordinates to screen pixel coordinates (center of tile)."""
        ts = self.tile_size
        sx = int(self.offset_x + (gx + 0.5) * ts)
        sy = int(self.offset_y + (gy + 0.5) * ts)
        return sx, sy

    def screen_to_grid(self, sx: int, sy: int) -> tuple[int, int]:
        """Converts mouse pixel coordinates to integer grid coordinates."""
        ts = self.tile_size
        gx = int((sx - self.offset_x) // ts)
        gy = int((sy - self.offset_y) // ts)
        return gx, gy

    def draw_grid(
        self, surface: pygame.Surface, grid: Grid, hover_tile: tuple[int, int] | None = None
    ) -> None:
        """Renders the floating platform tiles and border outlines."""
        ts = self.tile_size
        for y in range(grid.height):
            for x in range(grid.width):
                tile = grid.get_tile(x, y)
                if tile.tile_type == TileType.VOID:
                    continue

                sx, sy = self.grid_to_screen(x, y)
                rect = pygame.Rect(sx, sy, ts, ts)

                # Base tile coloring
                if tile.tile_type == TileType.PLATFORM_WALK:
                    pygame.draw.rect(surface, COLORS.platform_walk, rect)
                    pygame.draw.rect(surface, COLORS.platform_border, rect, 1)
                elif tile.tile_type == TileType.PLATFORM_BUILD:
                    pygame.draw.rect(surface, COLORS.platform_build_slot, rect)
                    pygame.draw.rect(surface, COLORS.platform_border, rect, 2)
                    # Rune pedestal center dot
                    cx, cy = self.grid_center_to_screen(x, y)
                    pygame.draw.circle(surface, COLORS.platform_border, (cx, cy), max(2, ts // 12))
                elif tile.tile_type == TileType.CORE:
                    pygame.draw.rect(surface, (25, 45, 80), rect)
                    cx, cy = self.grid_center_to_screen(x, y)
                    pygame.draw.circle(surface, COLORS.core_glow, (cx, cy), ts // 3)
                    pygame.draw.circle(surface, COLORS.core_core, (cx, cy), ts // 6)
                elif tile.tile_type == TileType.PORTAL:
                    pygame.draw.rect(surface, (40, 20, 60), rect)
                    cx, cy = self.grid_center_to_screen(x, y)
                    pygame.draw.circle(
                        surface, COLORS.portal_purple, (cx, cy), ts // 3, max(2, ts // 16)
                    )

                # Draw barrier monolith if placed
                if tile.has_barrier:
                    cx, cy = self.grid_center_to_screen(x, y)
                    r = ts // 3
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
                    highlight = pygame.Surface((ts, ts), pygame.SRCALPHA)
                    highlight.fill((255, 255, 255, 40))
                    surface.blit(highlight, (sx, sy))

    def draw_draft_preview(
        self,
        surface: pygame.Surface,
        grid: Grid,
        shard: PlatformShard,
        hover_origin: tuple[int, int],
    ) -> None:
        """Renders an interactive ghost projection of the platform shard prior to docking."""
        from py_aether_forge.expansion.drafter import is_valid_docking_location

        ox, oy = hover_origin
        is_valid = is_valid_docking_location(grid, shard, ox, oy)
        ts = self.tile_size

        for dy, row in enumerate(shard.layout):
            for dx, tile_type in enumerate(row):
                if tile_type == TileType.VOID:
                    continue

                tx, ty = ox + dx, oy + dy
                sx, sy = self.grid_to_screen(tx, ty)

                ghost_surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
                if is_valid:
                    # Valid docking location: energetic glowing blueprint
                    if tile_type == TileType.PLATFORM_WALK:
                        ghost_surf.fill((52, 120, 190, 160))
                        pygame.draw.rect(ghost_surf, (100, 220, 255, 220), (0, 0, ts, ts), 1)
                    elif tile_type == TileType.PLATFORM_BUILD:
                        ghost_surf.fill((70, 150, 220, 170))
                        # Center rune circle
                        pygame.draw.circle(
                            ghost_surf, (220, 245, 255, 220), (ts // 2, ts // 2), max(3, ts // 6)
                        )
                        pygame.draw.rect(ghost_surf, (120, 255, 180, 230), (0, 0, ts, ts), 2)
                    # Outer border
                    pygame.draw.rect(ghost_surf, (80, 255, 140, 220), (0, 0, ts, ts), 2)
                else:
                    # Invalid docking: warning tint
                    ghost_surf.fill((160, 45, 60, 140))
                    pygame.draw.rect(ghost_surf, (255, 70, 80, 220), (0, 0, ts, ts), 2)

                surface.blit(ghost_surf, (sx, sy))

    def draw_path_telegraph(
        self, surface: pygame.Surface, path: list[tuple[int, int]] | None
    ) -> None:
        """Renders a soft glowing path line indicating the route the swarms will follow."""
        if not path or len(path) < 2:
            return

        points = [self.grid_center_to_screen(gx, gy) for gx, gy in path]
        # Glow line
        pygame.draw.lines(surface, (50, 160, 220, 100), False, points, max(2, self.tile_size // 16))
        # Small route beads
        bead_radius = max(2, self.tile_size // 16)
        for i, pt in enumerate(points):
            if i % 2 == 0:
                pygame.draw.circle(surface, (130, 220, 255), pt, bead_radius)

    def draw_towers(
        self,
        surface: pygame.Surface,
        towers: list[Tower],
        selected_tower: Tower | None = None,
    ) -> None:
        """Renders all placed defense monuments."""
        ts = self.tile_size
        for tower in towers:
            cx, cy = self.grid_center_to_screen(tower.x, tower.y)
            color = ELEMENT_COLOR_MAP.get(tower.element, (255, 255, 255))

            # Base pedestal
            radius = ts // 3
            pygame.draw.circle(surface, (20, 25, 45), (cx, cy), radius + 2)
            pygame.draw.circle(surface, color, (cx, cy), radius)

            # Core rune gem
            inner_radius = max(3, radius // 2)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), inner_radius)

            # Selected indicator / range circle
            if tower is selected_tower:
                range_px = int(tower.range_radius * ts)
                range_surf = pygame.Surface((range_px * 2 + 4, range_px * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(range_surf, (*color, 35), (range_px + 2, range_px + 2), range_px)
                pygame.draw.circle(
                    range_surf, (*color, 160), (range_px + 2, range_px + 2), range_px, 2
                )
                surface.blit(range_surf, (cx - range_px - 2, cy - range_px - 2))

    def draw_creeps(self, surface: pygame.Surface, creeps: list[Creep]) -> None:
        """Renders creeping chaos swarms and health bars."""
        ts = self.tile_size
        for creep in creeps:
            if not creep.is_alive:
                continue

            cx, cy = self.grid_center_to_screen(creep.x, creep.y)
            radius = max(3, ts // 4)

            # Shadow
            pygame.draw.circle(surface, (5, 5, 10), (cx, cy + 3), radius)
            # Body
            pygame.draw.circle(surface, (220, 60, 85), (cx, cy), radius)
            pygame.draw.circle(surface, (255, 180, 195), (cx, cy), max(2, radius // 2))

            # Health bar above
            hp_w = max(10, ts - 10)
            hp_h = max(3, ts // 12)
            bx = cx - hp_w // 2
            by = cy - radius - 8

            pct = max(0.0, min(1.0, creep.hp / creep.max_hp)) if creep.max_hp > 0 else 0.0
            pygame.draw.rect(surface, (40, 40, 50), (bx, by, hp_w, hp_h))
            pygame.draw.rect(surface, (80, 225, 100), (bx, by, int(hp_w * pct), hp_h))
