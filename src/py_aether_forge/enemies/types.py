"""Creep archetypes and factory functions."""

from py_aether_forge.enemies.creep import Creep, CreepArmorType


def create_swarm_runner(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Fast, frail scout creep."""
    hp = 42.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=3.4,
        base_speed=3.4,
        bounty=8,
        armor_type=CreepArmorType.UNARMORED,
        name="Astral-Flitzer",
        color=(255, 110, 160),
        secondary_color=(255, 200, 220),
        size_multiplier=0.75,
        weaknesses_text="⚡ Schwach gegen: Eis & Natur (Verlangsamung stoppt den Sprint)",
        resistances_text="Resistenz: Keine",
    )


def create_chaos_golem(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Heavy armored brute."""
    hp = 200.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=1.4,
        base_speed=1.4,
        bounty=25,
        armor_type=CreepArmorType.ARMORED,
        name="Chaos-Golem",
        color=(175, 85, 45),
        secondary_color=(235, 160, 95),
        size_multiplier=1.35,
        weaknesses_text="⚡ Schwach gegen: Arkan & Plasma (+40% Schaden)",
        resistances_text="🛡 Resistenz: Feuer & Physisch (-25% Schaden)",
    )


def create_void_wisp(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Shielded ethereal wisp."""
    hp = 100.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=2.3,
        base_speed=2.3,
        bounty=16,
        armor_type=CreepArmorType.VOID_SHIELD,
        name="Leeren-Geist",
        color=(145, 65, 245),
        secondary_color=(215, 160, 255),
        size_multiplier=0.95,
        weaknesses_text="⚡ Schwach gegen: Feuer & Natur (+35% Schaden)",
        resistances_text="🔮 Resistenz: Arkan (-30% Magieschild)",
    )


def create_aether_mite(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Tiny, rapid insectoid swarmer."""
    hp = 28.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=3.6,
        base_speed=3.6,
        bounty=6,
        armor_type=CreepArmorType.UNARMORED,
        name="Äther-Schwärmer",
        color=(245, 195, 55),
        secondary_color=(255, 235, 130),
        size_multiplier=0.6,
        weaknesses_text="⚡ Schwach gegen: Flächenschaden (AOE Feuer & Dampf)",
        resistances_text="Resistenz: Keine (Geringe Gesundheit)",
    )


def create_life_drainer(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Regenerating astral hydra."""
    hp = 170.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=1.8,
        base_speed=1.8,
        bounty=24,
        armor_type=CreepArmorType.UNARMORED,
        name="Lebensverschlinger",
        color=(45, 185, 110),
        secondary_color=(150, 245, 180),
        size_multiplier=1.2,
        regen_per_second=16.0 * wave_multiplier,
        weaknesses_text="⚡ Schwach gegen: Feuer-DoT (Verbrennen unterbricht Regeneration!)",
        resistances_text="💚 Heilt sich kontinuierlich um 16 HP/s",
    )


def create_frost_breaker(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Ice-hardened yeti resistant to slows."""
    hp = 160.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=2.1,
        base_speed=2.1,
        bounty=20,
        armor_type=CreepArmorType.ARMORED,
        name="Frost-Bannbrecher",
        color=(75, 215, 250),
        secondary_color=(205, 245, 255),
        size_multiplier=1.25,
        weaknesses_text="⚡ Schwach gegen: Feuer & Frostfeuer (+50% Schaden)",
        resistances_text="❄ Immun / Extrem resistent gegen Verlangsamung",
    )


def create_astral_titan(x: float, y: float, wave_multiplier: float = 1.0) -> Creep:
    """Colossal boss creep for milestone waves."""
    hp = 850.0 * wave_multiplier
    return Creep(
        x=x,
        y=y,
        hp=hp,
        max_hp=hp,
        speed=1.0,
        base_speed=1.0,
        bounty=120,
        armor_type=CreepArmorType.ARMORED,
        name="Astral-Titan (Boss)",
        color=(255, 50, 65),
        secondary_color=(255, 215, 70),
        size_multiplier=1.85,
        is_boss=True,
        weaknesses_text="⚡ Schwach gegen: Geballte Fokus-Verteidigung & Hybrid-Monumente",
        resistances_text="👑 Boss-Rüstung: Hohe Zähigkeit gegen alle Elemente",
    )
