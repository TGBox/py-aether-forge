"""Global game configuration, palettes, and constants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowConfig:
    title: str = "Die Äther-Schmiede"
    default_width: int = 1280
    default_height: int = 720
    min_width: int = 1024
    min_height: int = 600
    fps: int = 60


@dataclass(frozen=True)
class GridConfig:
    tile_size: int = 48
    initial_cols: int = 15
    initial_rows: int = 11


@dataclass(frozen=True)
class ColorPalette:
    # Deep astral space
    void_dark: tuple[int, int, int] = (11, 14, 28)
    void_light: tuple[int, int, int] = (19, 24, 46)

    # Platforms
    platform_base: tuple[int, int, int] = (38, 45, 74)
    platform_walk: tuple[int, int, int] = (52, 63, 102)
    platform_border: tuple[int, int, int] = (84, 102, 158)
    platform_build_slot: tuple[int, int, int] = (70, 85, 135)

    # Core & Portals
    core_glow: tuple[int, int, int] = (130, 220, 255)
    core_core: tuple[int, int, int] = (255, 255, 255)
    portal_purple: tuple[int, int, int] = (200, 75, 255)

    # Elements
    element_fire: tuple[int, int, int] = (255, 95, 45)
    element_ice: tuple[int, int, int] = (80, 210, 255)
    element_arcane: tuple[int, int, int] = (185, 95, 255)
    element_nature: tuple[int, int, int] = (75, 225, 120)

    # Hybrids
    hybrid_frostfire: tuple[int, int, int] = (255, 160, 230)
    hybrid_plasma: tuple[int, int, int] = (240, 110, 255)
    hybrid_steam: tuple[int, int, int] = (220, 230, 245)
    hybrid_glacier_root: tuple[int, int, int] = (100, 240, 200)

    # UI & Status
    text_primary: tuple[int, int, int] = (240, 245, 255)
    text_muted: tuple[int, int, int] = (145, 160, 195)
    accent_gold: tuple[int, int, int] = (255, 205, 60)
    health_red: tuple[int, int, int] = (255, 65, 80)


WINDOW_CONFIG = WindowConfig()
GRID_CONFIG = GridConfig()
COLORS = ColorPalette()
DEFAULT_STARTING_AETHER = 150
DEFAULT_STARTING_CORE_HEALTH = 20
