"""Animated elemental projectiles and weapon FX."""

from __future__ import annotations

from dataclasses import dataclass, field

from py_aether_forge.enemies.creep import Creep
from py_aether_forge.towers.elements import ElementType
from py_aether_forge.towers.tower import Tower

PROJECTILE_COLORS: dict[ElementType, tuple[int, int, int]] = {
    ElementType.FIRE: (255, 95, 30),
    ElementType.ICE: (100, 220, 255),
    ElementType.ARCANE: (210, 80, 255),
    ElementType.NATURE: (60, 230, 110),
    ElementType.FROSTFIRE: (255, 140, 230),
    ElementType.PLASMA: (245, 100, 255),
    ElementType.STEAM: (220, 235, 250),
    ElementType.GLACIER_ROOT: (110, 245, 210),
    ElementType.ASTRAL_SPORE: (180, 255, 100),
    ElementType.VOID_CHILL: (180, 150, 255),
}


@dataclass
class Projectile:
    """An active elemental missile traveling from a tower towards an enemy."""

    start_x: float
    start_y: float
    target_x: float
    target_y: float
    current_x: float
    current_y: float
    element: ElementType
    color: tuple[int, int, int]
    target_creep: Creep | None = None
    progress: float = 0.0
    speed: float = 6.0  # Normalized progress speed per second
    size: float = 6.0
    tail_points: list[tuple[float, float]] = field(default_factory=list)

    @property
    def is_finished(self) -> bool:
        return self.progress >= 1.0

    def update(self, dt: float) -> None:
        """Advances projectile position and records motion trail."""
        # Update target coordinate if creep is still alive
        if self.target_creep is not None and self.target_creep.is_alive:
            self.target_x = self.target_creep.x
            self.target_y = self.target_creep.y

        self.progress = min(1.0, self.progress + self.speed * dt)

        # Record trail
        self.tail_points.append((self.current_x, self.current_y))
        if len(self.tail_points) > 5:
            self.tail_points.pop(0)

        # Interpolate position
        self.current_x = self.start_x + (self.target_x - self.start_x) * self.progress
        self.current_y = self.start_y + (self.target_y - self.start_y) * self.progress


def spawn_tower_projectile(tower: Tower, target: Creep) -> Projectile:
    """Constructs an elemental projectile for a tower attack."""
    color = PROJECTILE_COLORS.get(tower.element, (255, 255, 255))
    size = 7.0 if tower.is_hybrid else 5.5

    # Arcane and Plasma travel faster like laser pulses
    speed = 8.5 if tower.element in (ElementType.ARCANE, ElementType.PLASMA) else 6.0

    return Projectile(
        start_x=float(tower.x),
        start_y=float(tower.y),
        target_x=float(target.x),
        target_y=float(target.y),
        current_x=float(tower.x),
        current_y=float(tower.y),
        element=tower.element,
        color=color,
        target_creep=target,
        progress=0.0,
        speed=speed,
        size=size,
    )
