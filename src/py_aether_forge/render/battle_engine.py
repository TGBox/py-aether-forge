"""Full battle simulation engine connecting grid, towers, creeps, particles, and input."""

import math

import pygame

from py_aether_forge.config import GRID_CONFIG
from py_aether_forge.core.economy import Economy
from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.core.pathfinding import find_path_astar
from py_aether_forge.core.state import GameState, MatchState
from py_aether_forge.core.wave_spawner import WaveSpawner
from py_aether_forge.enemies.creep import Creep
from py_aether_forge.expansion.drafter import PlatformDrafter, is_valid_docking_location
from py_aether_forge.expansion.platform import PlatformShard
from py_aether_forge.render.audio import AudioManager
from py_aether_forge.render.particles import ParticleSystem
from py_aether_forge.render.starfield import Starfield
from py_aether_forge.render.viewport import Viewport
from py_aether_forge.towers.elements import ElementType
from py_aether_forge.towers.fusion import FusionRegistry
from py_aether_forge.towers.tower import Tower


class BattleEngine:
    """Manages tactical 60-FPS loop, entity simulation, and user interaction."""

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        unlocked_hybrids: set[ElementType] | None = None,
        starting_aether_bonus: int = 0,
        core_health_bonus: int = 0,
    ) -> None:
        self.width = width
        self.height = height
        self.unlocked_hybrids: set[ElementType] = unlocked_hybrids or set()

        # Core systems
        self.economy = Economy(
            aether_dust=150 + starting_aether_bonus,
            core_health=20 + core_health_bonus,
        )
        self.match_state = MatchState()
        self.grid = Grid(width=GRID_CONFIG.initial_cols, height=GRID_CONFIG.initial_rows)
        self.wave_spawner = WaveSpawner()
        self.fusion_registry = FusionRegistry()
        self.drafter = PlatformDrafter()

        # Rendering & audio
        self.viewport = Viewport()
        self.starfield = Starfield(width, height)
        self.particles = ParticleSystem()
        self.audio = AudioManager()

        # Entities
        self.towers: list[Tower] = []
        self.creeps: list[Creep] = []
        self.creep_paths: dict[int, list[tuple[int, int]]] = {}  # id(creep) -> path coordinates

        # Selections & drafting state
        self.selected_tower: Tower | None = None
        self.hover_tile: tuple[int, int] | None = None
        self.draft_options: list[PlatformShard] = []
        self.selected_draft_shard: PlatformShard | None = None
        self.selected_build_element: ElementType = ElementType.FIRE

        self._setup_initial_arena()
        self._recalculate_swarm_path()

    def _setup_initial_arena(self) -> None:
        """Constructs the initial floating platform with a core and entry portal."""
        # Middle row is walkway
        mid_y = self.grid.height // 2
        portal_x = 2
        core_x = self.grid.width - 3

        # Path from portal to core
        for x in range(portal_x, core_x + 1):
            self.grid.set_tile(x, mid_y, TileType.PLATFORM_WALK)

        self.grid.set_tile(portal_x, mid_y, TileType.PORTAL)
        self.grid.set_tile(core_x, mid_y, TileType.CORE)

        # Build slots above and below
        for x in range(portal_x + 1, core_x):
            self.grid.set_tile(x, mid_y - 1, TileType.PLATFORM_BUILD)
            self.grid.set_tile(x, mid_y + 1, TileType.PLATFORM_BUILD)

    def _get_portal_and_core_positions(self) -> tuple[tuple[int, int], tuple[int, int]]:
        portals = self.grid.find_tiles_of_type(TileType.PORTAL)
        cores = self.grid.find_tiles_of_type(TileType.CORE)

        portal_pos = (portals[0].x, portals[0].y) if portals else (2, self.grid.height // 2)
        core_pos = (
            (cores[0].x, cores[0].y) if cores else (self.grid.width - 3, self.grid.height // 2)
        )
        return portal_pos, core_pos

    def _recalculate_swarm_path(self) -> list[tuple[int, int]] | None:
        p_pos, c_pos = self._get_portal_and_core_positions()
        self.cached_path = find_path_astar(self.grid, start=p_pos, goal=c_pos)
        return self.cached_path

    def start_next_wave(self) -> bool:
        """Starts the next combat wave if currently in preparation."""
        if self.match_state.current_state != GameState.PREPARATION:
            return False

        next_wave = self.match_state.wave_number + 1
        self.match_state.start_wave(next_wave)
        self.wave_spawner.start_wave(next_wave)
        self.audio.play("wave")
        return True

    def build_tower(self, gx: int, gy: int, element: ElementType) -> bool:
        """Places a tower on an available build slot using its specific element specs."""
        from py_aether_forge.towers.elements import ELEMENT_SPECS

        spec = ELEMENT_SPECS.get(element)
        cost = spec.cost if spec else 80
        damage = spec.damage if spec else 25.0
        fire_rate = spec.fire_rate if spec else 1.1
        range_radius = spec.range_radius if spec else 3.0

        if not self.grid.is_buildable(gx, gy) or not self.economy.spend(cost):
            return False

        tower = Tower(
            x=gx,
            y=gy,
            element=element,
            damage=damage,
            fire_rate=fire_rate,
            range_radius=range_radius,
            cost=cost,
        )
        self.towers.append(tower)
        self.grid.get_tile(gx, gy).has_tower = True
        self.selected_tower = tower
        self.audio.play("shoot")
        return True

    def get_upgrade_cost(self, tower: Tower) -> int:
        """Calculates cost to upgrade a tower to the next level."""
        return int(tower.cost * 0.75 * tower.level)

    def upgrade_selected_tower(self) -> bool:
        """Upgrades the currently selected tower if affordable."""
        if self.selected_tower is None:
            return False
        cost = self.get_upgrade_cost(self.selected_tower)
        if not self.economy.spend(cost):
            return False
        self.selected_tower.upgrade()
        cx, cy = self.viewport.grid_center_to_screen(self.selected_tower.x, self.selected_tower.y)
        self.particles.emit_burst(cx, cy, (130, 220, 255), count=18, speed=100.0)
        self.audio.play("wave")
        return True

    def get_sell_refund(self, tower: Tower) -> int:
        """Calculates resale value (70% of base cost)."""
        return int(tower.cost * 0.7)

    def sell_selected_tower(self) -> bool:
        """Sells the currently selected tower and refunds aether dust."""
        if self.selected_tower is None:
            return False
        refund = self.get_sell_refund(self.selected_tower)
        self.economy.add_aether(refund)
        self.grid.get_tile(self.selected_tower.x, self.selected_tower.y).has_tower = False
        cx, cy = self.viewport.grid_center_to_screen(self.selected_tower.x, self.selected_tower.y)
        self.particles.emit_burst(cx, cy, (255, 205, 60), count=15, speed=80.0)
        self.towers.remove(self.selected_tower)
        self.selected_tower = None
        self.audio.play("hit")
        return True

    def fuse_selected_tower(self, second_element: ElementType) -> bool:
        """Fuses the currently selected tower with a complementary element."""
        if self.selected_tower is None or self.selected_tower.is_hybrid:
            return False

        cost = 120
        if not self.economy.can_afford(cost):
            return False

        target_hybrid = self.fusion_registry.get_recipe(self.selected_tower.element, second_element)
        if target_hybrid is None or not self.fusion_registry.can_fuse(
            self.selected_tower.element, second_element, self.unlocked_hybrids
        ):
            return False

        self.economy.spend(cost)
        self.selected_tower.fuse(target_hybrid)
        cx, cy = self.viewport.grid_center_to_screen(self.selected_tower.x, self.selected_tower.y)
        self.particles.emit_burst(cx, cy, (255, 200, 255), count=25, speed=140.0)
        self.audio.play("wave")
        return True

    def select_draft_shard(self, index: int) -> None:
        """Picks one of the drafted shards for grid placement."""
        if 0 <= index < len(self.draft_options):
            self.selected_draft_shard = self.draft_options[index]

    def place_draft_shard(self, origin_x: int, origin_y: int) -> bool:
        """Docks the chosen draft shard onto the grid at the designated anchor."""
        if self.selected_draft_shard is None:
            return False

        if not is_valid_docking_location(self.grid, self.selected_draft_shard, origin_x, origin_y):
            return False

        self.selected_draft_shard.place_on_grid(self.grid, origin_x, origin_y)
        self.economy.add_aether(self.selected_draft_shard.bonus_aether)
        self._recalculate_swarm_path()

        self.selected_draft_shard = None
        self.draft_options.clear()
        self.match_state.complete_draft()
        self.audio.play("wave")
        return True

    def update(self, dt: float) -> None:
        """Main tick for simulation, movement, projectiles, and game progression."""
        self.starfield.update(dt)
        self.particles.update(dt)

        if self.match_state.current_state == GameState.WAVE:
            p_pos, c_pos = self._get_portal_and_core_positions()

            # 1. Spawn creeps
            new_creeps = self.wave_spawner.update(dt, (float(p_pos[0]), float(p_pos[1])))
            for nc in new_creeps:
                self.creeps.append(nc)
                if self.cached_path:
                    self.creep_paths[id(nc)] = list(self.cached_path)

            # 2. Update creeps movement along cached path
            remaining_creeps: list[Creep] = []
            for creep in self.creeps:
                creep.update(dt)
                if not creep.is_alive:
                    # Bounty reward
                    self.economy.add_aether(creep.bounty)
                    cx, cy = self.viewport.grid_center_to_screen(creep.x, creep.y)
                    self.particles.emit_burst(cx, cy, (255, 215, 80), count=10)
                    self.audio.play("hit")
                    continue

                path = self.creep_paths.get(id(creep))
                if path and len(path) > 1:
                    target_wpt = path[1]
                    dx = target_wpt[0] - creep.x
                    dy = target_wpt[1] - creep.y
                    dist = math.hypot(dx, dy)
                    step = creep.speed * dt

                    if dist <= step:
                        creep.x = float(target_wpt[0])
                        creep.y = float(target_wpt[1])
                        creep.path_progress += dist
                        path.pop(0)
                        if len(path) == 1:
                            # Creep reached core -> Leak!
                            self.economy.register_leak(damage=1)
                            self.audio.play("leak")
                            cx, cy = self.viewport.grid_center_to_screen(c_pos[0], c_pos[1])
                            self.particles.emit_burst(cx, cy, (255, 60, 60), count=20)
                            continue
                    else:
                        creep.x += (dx / dist) * step
                        creep.y += (dy / dist) * step
                        creep.path_progress += step

                remaining_creeps.append(creep)

            self.creeps = remaining_creeps

            # Check core defeat
            if self.economy.is_defeated():
                self.match_state.set_game_over()
                return

            # 3. Towers acquire and attack
            for tower in self.towers:
                tower.update(dt)
                hit_target = tower.acquire_and_fire(self.creeps)
                if hit_target is not None:
                    # Emit beam / tracer particles
                    tx, ty = self.viewport.grid_center_to_screen(tower.x, tower.y)
                    cx, cy = self.viewport.grid_center_to_screen(hit_target.x, hit_target.y)
                    # Tracer spark mid-point
                    mx = (tx + cx) / 2.0
                    my = (ty + cy) / 2.0
                    self.particles.emit_burst(mx, my, (255, 200, 100), count=4, speed=30.0)
                    self.particles.emit_burst(cx, cy, (255, 120, 60), count=6, speed=60.0)
                    self.audio.play("hit")

            # 4. Check wave completion -> transition to DRAFT
            if self.wave_spawner.is_wave_spawning_done() and len(self.creeps) == 0:
                self.economy.award_astral_shards(amount=8 + self.match_state.wave_number)
                self.draft_options = self.drafter.generate_draft_options(count=3)
                self.match_state.finish_wave_and_enter_draft()

    def handle_mouse_click(self, sx: int, sy: int, button: int) -> None:
        """Processes player tactical interaction (build, select, dock shard)."""
        gx, gy = self.viewport.screen_to_grid(sx, sy)

        if button == 1:  # Left click
            if (
                self.match_state.current_state == GameState.DRAFT
                and self.selected_draft_shard is not None
            ):
                self.place_draft_shard(gx, gy)
            elif self.match_state.current_state == GameState.PREPARATION:
                # Check if clicking existing tower
                clicked_tower = next((t for t in self.towers if t.x == gx and t.y == gy), None)
                if clicked_tower:
                    self.selected_tower = clicked_tower
                elif self.grid.is_buildable(gx, gy):
                    self.build_tower(gx, gy, self.selected_build_element)
                else:
                    self.selected_tower = None

    def draw(self, surface: pygame.Surface) -> None:
        """Full tactical frame rendering."""
        from py_aether_forge.towers.elements import ELEMENT_SPECS

        self.starfield.draw(surface)
        self.viewport.draw_grid(surface, self.grid, self.hover_tile)
        self.viewport.draw_towers(surface, self.towers, self.selected_tower)
        self.viewport.draw_creeps(surface, self.creeps)
        self.particles.draw(surface)

        # Draw range preview ghost when hovering over a buildable tile
        if (
            self.match_state.current_state in (GameState.PREPARATION, GameState.WAVE)
            and self.hover_tile
            and self.grid.is_buildable(*self.hover_tile)
        ):
            spec = ELEMENT_SPECS.get(self.selected_build_element)
            if spec:
                cx, cy = self.viewport.grid_center_to_screen(*self.hover_tile)
                range_px = int(spec.range_radius * self.viewport.tile_size)
                ghost_surf = pygame.Surface((range_px * 2 + 4, range_px * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(
                    ghost_surf, (130, 220, 255, 30), (range_px + 2, range_px + 2), range_px
                )
                pygame.draw.circle(
                    ghost_surf, (130, 220, 255, 140), (range_px + 2, range_px + 2), range_px, 1
                )
                surface.blit(ghost_surf, (cx - range_px - 2, cy - range_px - 2))

        # Draw draft preview if in draft state and shard selected
        if (
            self.match_state.current_state == GameState.DRAFT
            and self.selected_draft_shard
            and self.hover_tile
        ):
            hx, hy = self.hover_tile
            is_valid = is_valid_docking_location(self.grid, self.selected_draft_shard, hx, hy)
            preview_color = (100, 255, 140, 90) if is_valid else (255, 70, 70, 90)

            for dy, row in enumerate(self.selected_draft_shard.layout):
                for dx, ttype in enumerate(row):
                    if ttype != TileType.VOID:
                        px, py = self.viewport.grid_to_screen(hx + dx, hy + dy)
                        psurf = pygame.Surface(
                            (self.viewport.tile_size, self.viewport.tile_size), pygame.SRCALPHA
                        )
                        psurf.fill(preview_color)
                        surface.blit(psurf, (px, py))
