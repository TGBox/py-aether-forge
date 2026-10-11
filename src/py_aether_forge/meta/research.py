"""The Astral Forge research tree and unlock prerequisites."""

from dataclasses import dataclass, field

from py_aether_forge.towers.elements import ElementType


@dataclass
class ResearchNode:
    """A technology node in the Astral Forge sanctuary."""

    node_id: str
    name_de: str
    description_de: str
    cost_shards: int
    parent_ids: list[str] = field(default_factory=list)
    unlocked_element: ElementType | None = None
    core_hp_bonus: int = 0
    starting_aether_bonus: int = 0
    is_unlocked: bool = False


class ResearchTree:
    """Manages available technologies, dependencies, and purchase validations."""

    def __init__(self, unlocked_node_ids: set[str] | None = None) -> None:
        unlocked = unlocked_node_ids if unlocked_node_ids is not None else {"root_affinity"}

        self.nodes: dict[str, ResearchNode] = {
            "root_affinity": ResearchNode(
                node_id="root_affinity",
                name_de="Astrale Einstimmung",
                description_de="Das grundlegende Verständnis des Äthers und der Elementarkräfte.",
                cost_shards=0,
                parent_ids=[],
                is_unlocked=True,
            ),
            "unlock_frostfire": ResearchNode(
                node_id="unlock_frostfire",
                name_de="Frostfeuer-Monument",
                description_de="Ermöglicht die Fusion von Feuer- und Eistürmen zu Frostfeuer.",
                cost_shards=50,
                parent_ids=["root_affinity"],
                unlocked_element=ElementType.FROSTFIRE,
            ),
            "unlock_plasma": ResearchNode(
                node_id="unlock_plasma",
                name_de="Plasma-Obelisk",
                description_de="Ermöglicht die Fusion von Feuer- und Arkantürmen zu Plasma.",
                cost_shards=80,
                parent_ids=["unlock_frostfire"],
                unlocked_element=ElementType.PLASMA,
            ),
            "unlock_steam": ResearchNode(
                node_id="unlock_steam",
                name_de="Dampf-Geysir",
                description_de="Ermöglicht die Fusion von Feuer- und Naturtürmen zu Dampf.",
                cost_shards=60,
                parent_ids=["root_affinity"],
                unlocked_element=ElementType.STEAM,
            ),
            "core_vitality": ResearchNode(
                node_id="core_vitality",
                name_de="Weltenkern-Aura",
                description_de="Erhöht das maximale Leben des Weltenkerns dauerhaft um +5.",
                cost_shards=40,
                parent_ids=["root_affinity"],
                core_hp_bonus=5,
            ),
            "starting_aether": ResearchNode(
                node_id="starting_aether",
                name_de="Äther-Katalysator",
                description_de="Startet jedes Match mit +50 zusätzlichem Äther-Staub.",
                cost_shards=45,
                parent_ids=["root_affinity"],
                starting_aether_bonus=50,
            ),
        }

        # Apply unlocked status
        for nid in unlocked:
            if nid in self.nodes:
                self.nodes[nid].is_unlocked = True

    def get_node(self, node_id: str) -> ResearchNode | None:
        return self.nodes.get(node_id)

    def can_unlock(self, node_id: str, available_shards: int) -> bool:
        """Checks if all prerequisite parents are unlocked and enough shards are available."""
        node = self.get_node(node_id)
        if node is None or node.is_unlocked:
            return False

        if available_shards < node.cost_shards:
            return False

        # Check that all parents are unlocked
        return all(self.nodes[pid].is_unlocked for pid in node.parent_ids if pid in self.nodes)

    def unlock(self, node_id: str, available_shards: int) -> int:
        """Unlocks the node if valid. Returns the shard cost deducted."""
        if not self.can_unlock(node_id, available_shards):
            return 0

        node = self.nodes[node_id]
        node.is_unlocked = True
        return node.cost_shards
