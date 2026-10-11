"""Tower entity with stats, upgrades, and attack triggers."""

from dataclasses import dataclass

from py_aether_forge.enemies.creep import Creep, StatusEffect
from py_aether_forge.towers.elements import HYBRID_ELEMENTS, ElementType
from py_aether_forge.towers.targeting import TargetMode, select_target


@dataclass
class Tower:
    """An elemental defense tower positioned on a grid slot."""

    x: int
    y: int
    element: ElementType
    damage: float
    fire_rate: float  # Attacks per second
    range_radius: float  # In tiles
    level: int = 1
    cost: int = 100
    target_mode: TargetMode = TargetMode.FIRST
    cooldown_timer: float = 0.0

    @property
    def is_hybrid(self) -> bool:
        return self.element in HYBRID_ELEMENTS

    def can_attack(self) -> bool:
        return self.cooldown_timer <= 0.0

    def reset_cooldown(self) -> None:
        if self.fire_rate > 0.0:
            self.cooldown_timer = 1.0 / self.fire_rate

    def update(self, dt: float) -> None:
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)

    def upgrade(self) -> None:
        """Upgrades tower rank, scaling stats."""
        self.level += 1
        self.damage *= 1.35
        self.range_radius *= 1.05

    def fuse(self, new_element: ElementType) -> None:
        """Transforms the tower into an advanced hybrid."""
        self.element = new_element
        self.damage *= 1.6
        self.range_radius *= 1.15
        self.cost += 120

    def attack_target(self, target: Creep) -> None:
        """Applies direct damage and elemental status debuffs."""
        target.take_damage(self.damage)

        # Apply elemental effects
        if self.element == ElementType.FIRE:
            target.apply_effect(
                StatusEffect(
                    name="Burn",
                    duration_remaining=3.0,
                    dps=self.damage * 0.2,
                    icon="🔥",
                    color=(255, 100, 30),
                )
            )
        elif self.element == ElementType.ICE:
            target.apply_effect(
                StatusEffect(
                    name="Chill",
                    duration_remaining=2.5,
                    slow_multiplier=0.6,
                    icon="❄️",
                    color=(100, 220, 255),
                )
            )
        elif self.element == ElementType.NATURE:
            target.apply_effect(
                StatusEffect(
                    name="Poison",
                    duration_remaining=4.0,
                    dps=self.damage * 0.15,
                    icon="🌿",
                    color=(60, 230, 110),
                )
            )
        elif self.element == ElementType.FROSTFIRE:
            target.apply_effect(
                StatusEffect(
                    name="Frostfire",
                    duration_remaining=3.0,
                    dps=self.damage * 0.3,
                    slow_multiplier=0.5,
                    icon="💠",
                    color=(255, 140, 230),
                )
            )
        elif self.element == ElementType.PLASMA:
            target.apply_effect(
                StatusEffect(
                    name="Plasma-Brand",
                    duration_remaining=3.5,
                    dps=self.damage * 0.35,
                    icon="⚡",
                    color=(240, 110, 255),
                )
            )
        elif self.element == ElementType.STEAM:
            target.apply_effect(
                StatusEffect(
                    name="Dampf-Verbrühung",
                    duration_remaining=3.0,
                    dps=self.damage * 0.25,
                    slow_multiplier=0.75,
                    icon="💨",
                    color=(220, 235, 250),
                )
            )
        elif self.element == ElementType.GLACIER_ROOT:
            target.apply_effect(
                StatusEffect(
                    name="Eiswurzel-Starre",
                    duration_remaining=2.5,
                    slow_multiplier=0.4,
                    icon="🌿",
                    color=(110, 245, 210),
                )
            )
        elif self.element == ElementType.ASTRAL_SPORE:
            target.apply_effect(
                StatusEffect(
                    name="Astral-Zersetzung",
                    duration_remaining=4.0,
                    dps=self.damage * 0.25,
                    icon="✨",
                    color=(200, 100, 255),
                )
            )
        elif self.element == ElementType.VOID_CHILL:
            target.apply_effect(
                StatusEffect(
                    name="Leerenfrost",
                    duration_remaining=3.0,
                    slow_multiplier=0.5,
                    dps=self.damage * 0.15,
                    icon="❄️",
                    color=(160, 210, 255),
                )
            )

        self.reset_cooldown()

    def acquire_and_fire(self, creeps: list[Creep]) -> Creep | None:
        """Acquires target according to priority mode and attacks if cooldown is ready."""
        if not self.can_attack():
            return None

        target = select_target(
            (float(self.x), float(self.y)), self.range_radius, creeps, self.target_mode
        )
        if target is not None:
            self.attack_target(target)
            return target
        return None
