"""Elemental types, status effects, and color mappings."""

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
