"""Tests for elemental towers, targeting priorities, and fusion matrix."""

from py_aether_forge.enemies.creep import Creep
from py_aether_forge.towers.elements import ElementType
from py_aether_forge.towers.fusion import FusionRegistry
from py_aether_forge.towers.targeting import TargetMode, select_target
from py_aether_forge.towers.tower import Tower


def test_fusion_matrix_symmetry_and_recipes() -> None:
    registry = FusionRegistry()

    # Frostfire recipe: FIRE + ICE
    assert registry.get_recipe(ElementType.FIRE, ElementType.ICE) == ElementType.FROSTFIRE
    assert registry.get_recipe(ElementType.ICE, ElementType.FIRE) == ElementType.FROSTFIRE

    # Plasma recipe: FIRE + ARCANE
    assert registry.get_recipe(ElementType.FIRE, ElementType.ARCANE) == ElementType.PLASMA
    assert registry.get_recipe(ElementType.ARCANE, ElementType.FIRE) == ElementType.PLASMA

    # Steam recipe: FIRE + NATURE
    assert registry.get_recipe(ElementType.FIRE, ElementType.NATURE) == ElementType.STEAM

    # Same elements cannot fuse into hybrid
    assert registry.get_recipe(ElementType.FIRE, ElementType.FIRE) is None


def test_fusion_with_unlock_status() -> None:
    registry = FusionRegistry()
    unlocked = {ElementType.FROSTFIRE}

    # Frostfire is unlocked
    assert registry.can_fuse(ElementType.FIRE, ElementType.ICE, unlocked_hybrids=unlocked)
    # Plasma is not unlocked
    assert not registry.can_fuse(ElementType.FIRE, ElementType.ARCANE, unlocked_hybrids=unlocked)


def test_tower_upgrade_and_fusion() -> None:
    tower = Tower(x=2, y=2, element=ElementType.FIRE, damage=20.0, fire_rate=1.0, range_radius=3.0)
    assert tower.damage == 20.0
    assert tower.level == 1

    tower.upgrade()
    assert tower.level == 2
    assert tower.damage > 20.0

    tower.fuse(ElementType.FROSTFIRE)
    assert tower.element == ElementType.FROSTFIRE
    assert tower.is_hybrid


def test_targeting_modes() -> None:
    tower_pos = (0.0, 0.0)
    tower_range = 10.0

    # Create dummy creeps at various positions and progress
    c_close = Creep(x=2.0, y=0.0, hp=100.0, max_hp=100.0, path_progress=5.0)
    c_lead = Creep(x=8.0, y=0.0, hp=50.0, max_hp=50.0, path_progress=20.0)
    c_strong = Creep(x=4.0, y=0.0, hp=500.0, max_hp=500.0, path_progress=10.0)
    c_weak = Creep(x=5.0, y=0.0, hp=20.0, max_hp=20.0, path_progress=12.0)
    c_out_of_range = Creep(x=15.0, y=0.0, hp=30.0, max_hp=30.0, path_progress=25.0)

    creeps = [c_close, c_lead, c_strong, c_weak, c_out_of_range]

    # FIRST: Highest path progress within range
    target_first = select_target(tower_pos, tower_range, creeps, mode=TargetMode.FIRST)
    assert target_first == c_lead

    # LAST: Lowest path progress within range
    target_last = select_target(tower_pos, tower_range, creeps, mode=TargetMode.LAST)
    assert target_last == c_close

    # CLOSEST: Minimal Euclidean distance
    target_closest = select_target(tower_pos, tower_range, creeps, mode=TargetMode.CLOSEST)
    assert target_closest == c_close

    # STRONGEST: Highest current HP
    target_strong = select_target(tower_pos, tower_range, creeps, mode=TargetMode.STRONGEST)
    assert target_strong == c_strong

    # WEAKEST: Lowest current HP
    target_weak = select_target(tower_pos, tower_range, creeps, mode=TargetMode.WEAKEST)
    assert target_weak == c_weak
