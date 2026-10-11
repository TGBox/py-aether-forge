"""Full battle simulation engine connecting grid, towers, creeps, particles, and input."""

import math

import pygame

from py_aether_forge.config import GRID_CONFIG
from py_aether_forge.core.economy import Economy
from py_aether_forge.core.grid import Grid, TileType
from py_aether_forge.core.pathfinding import can_build_without_blocking, find_path_astar
from py_aether_forge.core.state import GameState, MatchState

BARRIER_COST: int = 20
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

        # Safely initialize fonts for rendering tactical feedback
        if not pygame.font.get_init():
            pygame.font.init()
        try:
            self._warning_font: pygame.font.Font = pygame.font.SysFont("Segoe UI", 15, bold=True)
        except (pygame.error, OSError):
            self._warning_font = pygame.font.Font(None, 20)

        # Entities
        self.towers: list[Tower] = []
        self.creeps: list[Creep] = []
        self.creep_paths: dict[int, list[tuple[int, int]]] = {}  # id(creep) -> path coordinates

        # Selections & drafting state
        self.selected_tower: Tower | None = None
        self.selected_barrier: tuple[int, int] | None = None
        self.build_mode: str = "TOWER"  # "TOWER" or "BARRIER"
        self.warning_message: str = ""
        self.warning_timer: float = 0.0
        self.hover_tile: tuple[int, int] | None = None
        self.draft_options: list[PlatformShard] = []
        self.selected_draft_shard: PlatformShard | None = None
        self.selected_build_element: ElementType = ElementType.FIRE

        self._setup_initial_arena()
        self._recalculate_swarm_path()
        self.viewport.center_on_grid(width, height, self.grid.width, self.grid.height)

    def _setup_initial_arena(self) -> None:
        """Constructs the initial floating platform with a central walkway and tower build foundations."""
        mid_y = self.grid.height // 2
        portal_x = 2
        core_x = self.grid.width - 3

        # Central direct walkway from portal to core
        for x in range(portal_x, core_x + 1):
            self.grid.set_tile(x, mid_y, TileType.PLATFORM_WALK)

        self.grid.set_tile(portal_x, mid_y, TileType.PORTAL)
        self.grid.set_tile(core_x, mid_y, TileType.CORE)

        # Tower foundation platforms above and below the central lane (2 rows on each side)
        # When unoccupied, enemy swarms can traverse these tiles freely.
        # Placing a tower or an aether wall obstructs that cell and creates a maze.
        for x in range(portal_x + 1, core_x):
            self.grid.set_tile(x, mid_y - 2, TileType.PLATFORM_BUILD)
            self.grid.set_tile(x, mid_y - 1, TileType.PLATFORM_BUILD)
            self.grid.set_tile(x, mid_y + 1, TileType.PLATFORM_BUILD)
            self.grid.set_tile(x, mid_y + 2, TileType.PLATFORM_BUILD)

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

        # Re-route all active creeps dynamically to the core
        for creep in self.creeps:
            if not creep.is_alive:
                continue
            c_grid = (round(creep.x), round(creep.y))
            new_path = find_path_astar(self.grid, start=c_grid, goal=c_pos)
            if new_path:
                self.creep_paths[id(creep)] = new_path

        return self.cached_path

    def build_barrier(self, gx: int, gy: int) -> bool:
        """Places an aether barrier wall on a walkable tile to divert swarms."""
        if not self.grid.can_place_barrier(gx, gy):
            return False
        if not self.economy.can_afford(BARRIER_COST):
            self.warning_message = "Nicht genügend Äther-Staub für Äther-Wand (20 ✨ benötigt)!"
            self.warning_timer = 2.5
            return False

        # Blockade prevention check from portal to core
        portal_pos, core_pos = self._get_portal_and_core_positions()
        if not can_build_without_blocking(
            self.grid, start=portal_pos, goal=core_pos, target_tile=(gx, gy)
        ):
            self.warning_message = (
                "Aktion verweigert: Der Pfad zum Weltenkern darf nicht komplett versperrt werden!"
            )
            self.warning_timer = 3.0
            self.audio.play("leak")
            return False

        # Check that active creeps won't be trapped
        for creep in self.creeps:
            if not creep.is_alive:
                continue
            creep_pos = (round(creep.x), round(creep.y))
            if creep_pos == (gx, gy):
                self.warning_message = (
                    "Aktion verweigert: Eine Kreatur befindet sich auf diesem Feld!"
                )
                self.warning_timer = 2.0
                return False
            c_path = find_path_astar(
                self.grid, start=creep_pos, goal=core_pos, blocked_tile=(gx, gy)
            )
            if c_path is None:
                self.warning_message = (
                    "Aktion verweigert: Eine aktive Kreatur würde eingesperrt werden!"
                )
                self.warning_timer = 3.0
                self.audio.play("leak")
                return False

        self.economy.spend(BARRIER_COST)
        tile = self.grid.get_tile(gx, gy)
        tile.has_barrier = True
        self.warning_message = ""
        self.warning_timer = 0.0

        cx, cy = self.viewport.grid_center_to_screen(gx, gy)
        self.particles.emit_burst(cx, cy, (79, 195, 247), count=14, speed=80.0)
        self.audio.play("shoot")

        self._recalculate_swarm_path()
        return True

    def remove_barrier(self, gx: int, gy: int) -> bool:
        """Demolishes an aether barrier wall and refunds 100% of dust cost (20 ✨)."""
        if not self.grid.in_bounds(gx, gy):
            return False
        tile = self.grid.get_tile(gx, gy)
        if not tile.has_barrier:
            return False

        tile.has_barrier = False
        self.economy.add_aether(BARRIER_COST)

        cx, cy = self.viewport.grid_center_to_screen(gx, gy)
        self.particles.emit_burst(cx, cy, (255, 205, 60), count=12, speed=70.0)
        self.audio.play("hit")

        self._recalculate_swarm_path()
        return True

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

        if not self.grid.is_buildable(gx, gy):
            return False
        if not self.economy.can_afford(cost):
            self.warning_message = "Nicht genügend Äther-Staub für diesen Turm!"
            self.warning_timer = 2.5
            return False

        # Blockade prevention check: placing a tower obstructs this cell for swarms
        portal_pos, core_pos = self._get_portal_and_core_positions()
        if not can_build_without_blocking(
            self.grid, start=portal_pos, goal=core_pos, target_tile=(gx, gy)
        ):
            self.warning_message = (
                "Aktion verweigert: Der Pfad zum Weltenkern darf nicht komplett versperrt werden!"
            )
            self.warning_timer = 3.0
            self.audio.play("leak")
            return False

        # Check that active creeps won't be trapped
        for creep in self.creeps:
            if not creep.is_alive:
                continue
            creep_pos = (round(creep.x), round(creep.y))
            if creep_pos == (gx, gy):
                self.warning_message = (
                    "Aktion verweigert: Eine Kreatur befindet sich auf diesem Feld!"
                )
                self.warning_timer = 2.0
                return False
            c_path = find_path_astar(
                self.grid, start=creep_pos, goal=core_pos, blocked_tile=(gx, gy)
            )
            if c_path is None:
                self.warning_message = (
                    "Aktion verweigert: Eine aktive Kreatur würde eingesperrt werden!"
                )
                self.warning_timer = 3.0
                self.audio.play("leak")
                return False

        self.economy.spend(cost)
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
        self.warning_message = ""
        self.warning_timer = 0.0

        cx, cy = self.viewport.grid_center_to_screen(gx, gy)
        self.particles.emit_burst(cx, cy, (130, 220, 255), count=16, speed=90.0)
        self.audio.play("shoot")

        # Dynamically recalculate paths for swarm and alive creeps around the new tower
        self._recalculate_swarm_path()
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
        self._recalculate_swarm_path()
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

    def rotate_selected_draft_shard(self, clockwise: bool = True) -> bool:
        """Rotates the currently selected platform shard by 90 degrees."""
        if self.selected_draft_shard is not None:
            self.selected_draft_shard.rotate(clockwise)
            self.audio.play("build")
            return True
        return False

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
        if self.warning_timer > 0:
            self.warning_timer = max(0.0, self.warning_timer - dt)
            if self.warning_timer == 0:
                self.warning_message = ""

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
        """Processes player tactical interaction (build, select, dock shard, barrier)."""
        gx, gy = self.viewport.screen_to_grid(sx, sy)

        if button == 1:  # Left click
            if (
                self.match_state.current_state == GameState.DRAFT
                and self.selected_draft_shard is not None
            ):
                self.place_draft_shard(gx, gy)
                return

            if self.match_state.current_state in (GameState.PREPARATION, GameState.WAVE):
                tile = self.grid.get_tile(gx, gy)

                # 1. Click on existing tower
                clicked_tower = next((t for t in self.towers if t.x == gx and t.y == gy), None)
                if clicked_tower:
                    self.selected_tower = clicked_tower
                    self.selected_barrier = None
                    return

                # 2. Click on existing barrier
                if tile.has_barrier:
                    self.selected_barrier = (gx, gy)
                    self.selected_tower = None
                    return

                # 3. Build barrier if in BARRIER mode
                if self.build_mode == "BARRIER":
                    if self.grid.can_place_barrier(gx, gy):
                        self.build_barrier(gx, gy)
                    elif self.grid.is_buildable(gx, gy):
                        self.warning_message = (
                            "Äther-Wände können nur auf Gehwegen errichtet werden!"
                        )
                        self.warning_timer = 2.5
                    return

                # 4. Build tower if in TOWER mode
                if self.grid.is_buildable(gx, gy):
                    self.build_tower(gx, gy, self.selected_build_element)
                elif self.grid.can_place_barrier(gx, gy):
                    self.warning_message = (
                        "Wähle 'Äther-Wand' in der Bauleiste, um Gehwege zu blockieren!"
                    )
                    self.warning_timer = 2.5
                else:
                    self.selected_tower = None
                    self.selected_barrier = None

        elif button == 3:  # Right click: Quick demolish barrier or rotate draft shard / deselect
            if self.match_state.current_state == GameState.DRAFT and self.selected_draft_shard:
                self.rotate_selected_draft_shard()
                return

            tile = self.grid.get_tile(gx, gy)
            if tile.has_barrier:
                self.remove_barrier(gx, gy)
                self.selected_barrier = None
            else:
                self.selected_tower = None
                self.selected_barrier = None

    def draw(self, surface: pygame.Surface) -> None:
        """Full tactical frame rendering."""
        from py_aether_forge.towers.elements import ELEMENT_SPECS

        self.starfield.draw(surface)
        self.viewport.draw_grid(surface, self.grid, self.hover_tile)
        self.viewport.draw_path_telegraph(surface, self.cached_path)
        self.viewport.draw_towers(surface, self.towers, self.selected_tower)
        self.viewport.draw_creeps(surface, self.creeps)
        self.particles.draw(surface)

        # Draw barrier ghost when hovering in BARRIER mode
        if (
            self.match_state.current_state in (GameState.PREPARATION, GameState.WAVE)
            and self.hover_tile
            and self.build_mode == "BARRIER"
            and self.grid.can_place_barrier(*self.hover_tile)
        ):
            cx, cy = self.viewport.grid_center_to_screen(*self.hover_tile)
            r = self.viewport.tile_size // 3
            barrier_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
            ghost_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.rect(
                ghost_surf, (79, 195, 247, 100), ghost_surf.get_rect(), border_radius=4
            )
            pygame.draw.rect(
                ghost_surf, (130, 220, 255, 200), ghost_surf.get_rect(), 2, border_radius=4
            )
            surface.blit(ghost_surf, barrier_rect)

        # Draw range preview ghost when hovering over a buildable tile in TOWER mode
        if (
            self.match_state.current_state in (GameState.PREPARATION, GameState.WAVE)
            and self.hover_tile
            and self.build_mode == "TOWER"
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

        # Draw tactical warning banner if set
        if self.warning_message:
            txt_surf = self._warning_font.render(self.warning_message, True, (255, 100, 100))
            bg_rect = txt_surf.get_rect(center=(self.width // 2, 75))
            pad_rect = bg_rect.inflate(36, 16)
            pill = pygame.Surface((pad_rect.width, pad_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(pill, (24, 12, 30, 230), pill.get_rect(), border_radius=8)
            pygame.draw.rect(pill, (255, 80, 80), pill.get_rect(), 2, border_radius=8)
            surface.blit(pill, pad_rect)
            surface.blit(txt_surf, bg_rect)

        # Draw rich draft preview if in draft state and shard selected
        if (
            self.match_state.current_state == GameState.DRAFT
            and self.selected_draft_shard
            and self.hover_tile
        ):
            self.viewport.draw_draft_preview(
                surface, self.grid, self.selected_draft_shard, self.hover_tile
            )
