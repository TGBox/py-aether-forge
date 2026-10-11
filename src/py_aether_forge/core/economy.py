"""Economy, world core health, and astral resource management."""

from py_aether_forge.config import DEFAULT_STARTING_AETHER, DEFAULT_STARTING_CORE_HEALTH


class Economy:
    """Tracks in-match currency (aether dust), core health, and meta-currency (astral shards)."""

    def __init__(
        self,
        aether_dust: int = DEFAULT_STARTING_AETHER,
        core_health: int = DEFAULT_STARTING_CORE_HEALTH,
    ) -> None:
        self.aether_dust: int = aether_dust
        self.core_health: int = core_health
        self.max_core_health: int = core_health
        self.astral_shards: int = 0

    def can_afford(self, amount: int) -> bool:
        """Checks if enough aether dust is available for a construction/upgrade."""
        return self.aether_dust >= amount

    def spend(self, amount: int) -> bool:
        """Deducts aether dust if affordable. Returns True on success, False otherwise."""
        if self.can_afford(amount):
            self.aether_dust -= amount
            return True
        return False

    def add_aether(self, amount: int) -> None:
        """Adds in-match currency from creep bounty or wave bonuses."""
        self.aether_dust += max(0, amount)

    def register_leak(self, damage: int = 1) -> None:
        """Reduces core health when a creep leaks through the defenses."""
        self.core_health = max(0, self.core_health - damage)

    def is_defeated(self) -> bool:
        """Returns True if the world core has lost all health."""
        return self.core_health <= 0

    def award_astral_shards(self, amount: int) -> None:
        """Awards permanent meta-progression currency earned during the run."""
        self.astral_shards += max(0, amount)
