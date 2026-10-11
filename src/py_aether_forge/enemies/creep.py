"""Chaos swarm creep entities and debuff mechanics."""

import math
from dataclasses import dataclass, field
from enum import Enum, auto


class CreepArmorType(Enum):
    """Armor types with varying elemental affinities."""

    UNARMORED = auto()  # Standard swarm
    ARMORED = auto()  # Heavy golem, resists physical/fire, weak to arcane
    VOID_SHIELD = auto()  # Fast ethereal, resists arcane, weak to fire/nature


@dataclass
class StatusEffect:
    """Ongoing elemental debuff on a creep."""

    name: str
    duration_remaining: float
    dps: float = 0.0
    slow_multiplier: float = 1.0  # 0.7 = 30% slow
    icon: str = "🔥"
    color: tuple[int, int, int] = (255, 100, 30)


@dataclass
class Creep:
    """An individual enemy entity traveling along the path towards the world core."""

    x: float
    y: float
    hp: float
    max_hp: float
    speed: float = 2.0  # Tiles per second
    base_speed: float = 2.0
    bounty: int = 10
    armor_type: CreepArmorType = CreepArmorType.UNARMORED
    path_progress: float = 0.0  # Distance along waypoint path
    active_effects: list[StatusEffect] = field(default_factory=list)
    name: str = "Chaos-Kreatur"
    color: tuple[int, int, int] = (220, 60, 85)
    secondary_color: tuple[int, int, int] = (255, 180, 195)
    size_multiplier: float = 1.0
    regen_per_second: float = 0.0
    weaknesses_text: str = "Schwach gegen: Direkten Elementarschaden"
    resistances_text: str = "Resistenz: Standard"
    is_boss: bool = False

    @property
    def is_alive(self) -> bool:
        return self.hp > 0.0

    @property
    def is_burning(self) -> bool:
        """Returns True if the creep is currently taking burn DoT."""
        return any(e.dps > 0.0 for e in self.active_effects)

    @property
    def is_slowed(self) -> bool:
        """Returns True if movement speed is reduced by frost or nature."""
        return any(e.slow_multiplier < 0.99 for e in self.active_effects)

    def take_damage(self, amount: float) -> None:
        """Applies damage and clamps HP at 0."""
        self.hp = max(0.0, self.hp - amount)

    def apply_effect(self, effect: StatusEffect) -> None:
        """Applies or refreshes a status effect."""
        # Refresh if existing effect of same name
        for existing in self.active_effects:
            if existing.name == effect.name:
                existing.duration_remaining = max(
                    existing.duration_remaining, effect.duration_remaining
                )
                existing.dps = max(existing.dps, effect.dps)
                existing.slow_multiplier = min(existing.slow_multiplier, effect.slow_multiplier)
                return
        self.active_effects.append(effect)

    def update(self, dt: float) -> None:
        """Updates status effects, health regeneration, DoT damage, and speed adjustments."""
        current_slow = 1.0
        remaining_effects: list[StatusEffect] = []

        for effect in self.active_effects:
            # Apply DoT
            if effect.dps > 0.0:
                self.take_damage(effect.dps * dt)

            current_slow = min(current_slow, effect.slow_multiplier)
            effect.duration_remaining -= dt

            if effect.duration_remaining > 0.0:
                remaining_effects.append(effect)

        self.active_effects = remaining_effects
        self.speed = self.base_speed * current_slow

        # Health regeneration (suppressed while burning)
        if self.regen_per_second > 0.0 and not self.is_burning and self.is_alive:
            self.hp = min(self.max_hp, self.hp + self.regen_per_second * dt)

    def distance_to(self, target_x: float, target_y: float) -> float:
        """Euclidean distance to a coordinate."""
        return math.hypot(self.x - target_x, self.y - target_y)
