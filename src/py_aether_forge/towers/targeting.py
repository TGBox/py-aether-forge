"""Tower targeting priorities and enemy selection."""

from collections.abc import Sequence
from enum import Enum, auto

from py_aether_forge.enemies.creep import Creep


class TargetMode(Enum):
    """Priority mode for tower target acquisition."""

    FIRST = auto()  # Furthest along path (standard leak defense)
    LAST = auto()  # Least path progress (guards entrance)
    CLOSEST = auto()  # Minimum Euclidean distance to tower
    STRONGEST = auto()  # Highest current HP (tanks)
    WEAKEST = auto()  # Lowest current HP (secure last-hits)


def select_target(
    tower_pos: tuple[float, float],
    tower_range: float,
    creeps: Sequence[Creep],
    mode: TargetMode = TargetMode.FIRST,
) -> Creep | None:
    """Filters alive creeps within tower range and selects one based on the target mode."""
    tx, ty = tower_pos
    in_range = [c for c in creeps if c.is_alive and c.distance_to(tx, ty) <= tower_range]

    if not in_range:
        return None

    if mode == TargetMode.FIRST:
        return max(in_range, key=lambda c: c.path_progress)
    elif mode == TargetMode.LAST:
        return min(in_range, key=lambda c: c.path_progress)
    elif mode == TargetMode.CLOSEST:
        return min(in_range, key=lambda c: c.distance_to(tx, ty))
    elif mode == TargetMode.STRONGEST:
        return max(in_range, key=lambda c: c.hp)
    elif mode == TargetMode.WEAKEST:
        return min(in_range, key=lambda c: c.hp)

    return in_range[0]
