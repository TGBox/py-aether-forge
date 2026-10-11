"""Elemental types, status effects, specs, and color mappings."""

from dataclasses import dataclass
from enum import Enum, auto


class ElementType(Enum):
    """Base elements and advanced hybrid rune combinations."""

    # Base elements
    FIRE = auto()
    ICE = auto()
    ARCANE = auto()
    NATURE = auto()

    # Hybrids (unlocked in the Astral Forge)
    FROSTFIRE = auto()  # FIRE + ICE
    PLASMA = auto()  # FIRE + ARCANE
    STEAM = auto()  # FIRE + NATURE
    GLACIER_ROOT = auto()  # ICE + NATURE
    ASTRAL_SPORE = auto()  # ARCANE + NATURE
    VOID_CHILL = auto()  # ICE + ARCANE


BASE_ELEMENTS = {
    ElementType.FIRE,
    ElementType.ICE,
    ElementType.ARCANE,
    ElementType.NATURE,
}

HYBRID_ELEMENTS = {
    ElementType.FROSTFIRE,
    ElementType.PLASMA,
    ElementType.STEAM,
    ElementType.GLACIER_ROOT,
    ElementType.ASTRAL_SPORE,
    ElementType.VOID_CHILL,
}


ELEMENT_NAMES_DE = {
    ElementType.FIRE: "Feuer",
    ElementType.ICE: "Eis",
    ElementType.ARCANE: "Arkan",
    ElementType.NATURE: "Natur",
    ElementType.FROSTFIRE: "Frostfeuer",
    ElementType.PLASMA: "Plasma",
    ElementType.STEAM: "Dampf",
    ElementType.GLACIER_ROOT: "Gletscherwurzel",
    ElementType.ASTRAL_SPORE: "Astralspore",
    ElementType.VOID_CHILL: "Leerenfrost",
}


@dataclass(frozen=True)
class TowerSpec:
    """Detailed specifications and descriptions for player reference."""

    element: ElementType
    name_de: str
    cost: int
    damage: float
    fire_rate: float
    range_radius: float
    effect_name_de: str
    description_de: str
    color_hex: str


ELEMENT_SPECS: dict[ElementType, TowerSpec] = {
    ElementType.FIRE: TowerSpec(
        element=ElementType.FIRE,
        name_de="Feuer-Monolith",
        cost=80,
        damage=35.0,
        fire_rate=1.0,
        range_radius=3.0,
        effect_name_de="Brand (7 DPS für 3s)",
        description_de="Schlägt mit flammender Wucht ein. Verursacht hohen Einzeltrefferschaden und Brandschaden über Zeit.",
        color_hex="#FF5F2D",
    ),
    ElementType.ICE: TowerSpec(
        element=ElementType.ICE,
        name_de="Frost-Pfeiler",
        cost=80,
        damage=18.0,
        fire_rate=1.2,
        range_radius=3.2,
        effect_name_de="Verlangsamung (-40% Tempo)",
        description_de="Hüllt anrückende Schwärme in klirrende Kälte und verlangsamt ihre Bewegung drastisch.",
        color_hex="#50D2FF",
    ),
    ElementType.ARCANE: TowerSpec(
        element=ElementType.ARCANE,
        name_de="Arkan-Obelisk",
        cost=80,
        damage=22.0,
        fire_rate=2.2,
        range_radius=4.0,
        effect_name_de="Schnellfeuer (Schild-Durchdringung)",
        description_de="Feuert in rascher Kadenz konzentrierte arkane Strahlen über hohe Distanz ab.",
        color_hex="#B95FFF",
    ),
    ElementType.NATURE: TowerSpec(
        element=ElementType.NATURE,
        name_de="Lebensbaum-Wurzel",
        cost=80,
        damage=20.0,
        fire_rate=1.1,
        range_radius=3.0,
        effect_name_de="Gift-DoT (Stapelbar über 4s)",
        description_de="Injiziert zehrendes Pflanzengift, das Creeps über längere Zeit zersetzt.",
        color_hex="#4BE178",
    ),
    ElementType.FROSTFIRE: TowerSpec(
        element=ElementType.FROSTFIRE,
        name_de="Frostfeuer-Monument",
        cost=120,
        damage=55.0,
        fire_rate=1.3,
        range_radius=3.5,
        effect_name_de="Frostbrand (-50% Tempo + 16 DPS)",
        description_de="Kombiniert sengende Flammen mit lähmender Kälte für verheerende Effekte.",
        color_hex="#FFA0E6",
    ),
    ElementType.PLASMA: TowerSpec(
        element=ElementType.PLASMA,
        name_de="Plasma-Obelisk",
        cost=120,
        damage=70.0,
        fire_rate=1.8,
        range_radius=4.2,
        effect_name_de="Plasmastrahl (Hoher Durchschlag)",
        description_de="Reißt Lücken in die stärksten Chaos-Golems mit ionisierter Sternenenergie.",
        color_hex="#F06EFF",
    ),
    ElementType.STEAM: TowerSpec(
        element=ElementType.STEAM,
        name_de="Dampf-Geysir",
        cost=120,
        damage=48.0,
        fire_rate=1.5,
        range_radius=3.2,
        effect_name_de="Druckwelle (Flächenbrand)",
        description_de="Entlässt überhitzten Ätherdampf, der Gruppen schwer zusetzt.",
        color_hex="#DCE6F5",
    ),
    ElementType.GLACIER_ROOT: TowerSpec(
        element=ElementType.GLACIER_ROOT,
        name_de="Gletscherwurzel-Monument",
        cost=120,
        damage=44.0,
        fire_rate=1.2,
        range_radius=3.4,
        effect_name_de="Eiswurzel (-60% Verlangsamung)",
        description_de="Verwurzelt feindliche Schwärme in ewigem Permafrost und hemmt deren Fortbewegung massiv.",
        color_hex="#6EF5D2",
    ),
    ElementType.ASTRAL_SPORE: TowerSpec(
        element=ElementType.ASTRAL_SPORE,
        name_de="Astralsporen-Nest",
        cost=120,
        damage=50.0,
        fire_rate=1.6,
        range_radius=3.8,
        effect_name_de="Astral-Spore (20 DPS über 4s)",
        description_de="Verbreitet kosmische Giftsporen, die selbst schwere Rüstungen kontinuierlich zersetzen.",
        color_hex="#C864FF",
    ),
    ElementType.VOID_CHILL: TowerSpec(
        element=ElementType.VOID_CHILL,
        name_de="Leerenfrost-Säule",
        cost=120,
        damage=52.0,
        fire_rate=1.4,
        range_radius=3.6,
        effect_name_de="Leeren-Schüttelfrost (-50% Tempo + Magie-Bruch)",
        description_de="Entzieht dem Äther jegliche Wärme und zwingt Chaos-Wesen in eisige Starre.",
        color_hex="#A0D2FF",
    ),
}
