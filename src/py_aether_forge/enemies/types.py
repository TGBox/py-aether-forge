"""Creep archetypes and factory functions."""

from py_aether_forge.enemies.creep import Creep, CreepArmorType


def create_swarm_runner(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Fast, frail scout creep."""
    hp = 45.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=3.2,
        base_speed=3.2,
        bounty=8,
        armor_type=CreepArmorType.UNARMORED,
    )


def create_chaos_golem(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Heavy armored brute."""
    hp = 180.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=1.5,
        base_speed=1.5,
        bounty=22,
        armor_type=CreepArmorType.ARMORED,
    )


def create_void_wisp(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Shielded ethereal wisp."""
    hp = 90.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=2.4,
        base_speed=2.4,
        bounty=15,
        armor_type=CreepArmorType.VOID_SHIELD,
    )


def create_astral_titan(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Boss creep for milestone waves."""
    hp = 750.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=1.1,
        base_speed=1.1,
        bounty=100,
        armor_type=CreepArmorType.ARMORED,
    )
