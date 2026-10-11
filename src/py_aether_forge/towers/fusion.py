"""Elemental fusion matrix and recipe checks."""

from py_aether_forge.towers.elements import ElementType


class FusionRegistry:
    """Manages the two-element combination recipes and unlock status."""

    def __init__(self) -> None:
        self._recipes: dict[frozenset[ElementType], ElementType] = {
            frozenset({ElementType.FIRE, ElementType.ICE}): ElementType.FROSTFIRE,
            frozenset({ElementType.FIRE, ElementType.ARCANE}): ElementType.PLASMA,
            frozenset({ElementType.FIRE, ElementType.NATURE}): ElementType.STEAM,
            frozenset({ElementType.ICE, ElementType.NATURE}): ElementType.GLACIER_ROOT,
            frozenset({ElementType.ARCANE, ElementType.NATURE}): ElementType.ASTRAL_SPORE,
            frozenset({ElementType.ICE, ElementType.ARCANE}): ElementType.VOID_CHILL,
        }

    def get_recipe(self, elem1: ElementType, elem2: ElementType) -> ElementType | None:
        """Returns the hybrid result of combining two elements, or None if invalid."""
        if elem1 == elem2:
            return None
        return self._recipes.get(frozenset({elem1, elem2}))

    def can_fuse(
        self,
        elem1: ElementType,
        elem2: ElementType,
        unlocked_hybrids: set[ElementType],
    ) -> bool:
        """Checks if a fusion recipe is valid and has been unlocked in meta-progression."""
        hybrid = self.get_recipe(elem1, elem2)
        if hybrid is None:
            return False
        return hybrid in unlocked_hybrids
