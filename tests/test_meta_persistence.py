"""Tests for meta-progression persistence and research tree."""

from pathlib import Path

from py_aether_forge.meta.research import ResearchTree
from py_aether_forge.meta.save_system import SaveSystem
from py_aether_forge.towers.elements import ElementType


def test_save_system_defaults_and_roundtrip(tmp_path: Path) -> None:
    save_file = tmp_path / "test_save.json"
    system = SaveSystem(save_path=save_file)

    # Initially file does not exist, loads default data
    data = system.load()
    assert data.total_astral_shards == 0
    assert ElementType.FROSTFIRE.name not in data.unlocked_hybrids
    assert data.highest_wave == 0

    # Modify and save
    data.total_astral_shards = 150
    data.unlocked_hybrids.add(ElementType.FROSTFIRE.name)
    data.highest_wave = 12
    system.save(data)

    assert save_file.exists()

    # Re-read
    loaded_data = system.load()
    assert loaded_data.total_astral_shards == 150
    assert ElementType.FROSTFIRE.name in loaded_data.unlocked_hybrids
    assert loaded_data.highest_wave == 12


def test_research_tree_unlock_hierarchy() -> None:
    tree = ResearchTree()

    # Root node: Base affinity (cost 20)
    root = tree.get_node("root_affinity")
    assert root is not None
    assert root.is_unlocked

    # Child node: Frostfire Monument (cost 50, requires root)
    frostfire_node = tree.get_node("unlock_frostfire")
    assert frostfire_node is not None
    assert not frostfire_node.is_unlocked

    # Plasma node (cost 80, requires unlock_frostfire)
    plasma_node = tree.get_node("unlock_plasma")
    assert plasma_node is not None
    assert not plasma_node.is_unlocked

    # Try unlocking plasma without parent -> fails
    assert not tree.can_unlock("unlock_plasma", available_shards=100)

    # Unlock frostfire with enough shards
    assert tree.can_unlock("unlock_frostfire", available_shards=50)
    spent = tree.unlock("unlock_frostfire", available_shards=50)
    assert spent == 50
    assert frostfire_node.is_unlocked

    # Now plasma can be unlocked if enough shards
    assert tree.can_unlock("unlock_plasma", available_shards=80)
    assert not tree.can_unlock("unlock_plasma", available_shards=30)
