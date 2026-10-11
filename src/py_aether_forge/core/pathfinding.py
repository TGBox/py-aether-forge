"""A* pathfinding algorithm for chaos swarms and blockade prevention."""

import heapq

from py_aether_forge.core.grid import Grid


def manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Manhattan distance heuristic for grid-based pathfinding."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path_astar(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
    blocked_tile: tuple[int, int] | None = None,
) -> list[tuple[int, int]] | None:
    """Computes the shortest path from start to goal over walkable tiles using A*.

    Returns a list of (x, y) coordinates from start to goal inclusive, or None if unreachable.
    """
    if start == goal:
        return [start]

    # Priority queue stores: (f_score, cost_so_far, current_pos)
    frontier: list[tuple[int, int, tuple[int, int]]] = []
    heapq.heappush(frontier, (0, 0, start))

    came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    cost_so_far: dict[tuple[int, int], int] = {start: 0}

    while frontier:
        _, current_cost, current = heapq.heappop(frontier)

        if current == goal:
            # Reconstruct path
            path: list[tuple[int, int]] = []
            curr: tuple[int, int] | None = current
            while curr is not None:
                path.append(curr)
                curr = came_from[curr]
            path.reverse()
            return path

        cx, cy = current
        for neighbor in grid.get_neighbors(cx, cy):
            npos = (neighbor.x, neighbor.y)

            # Check if tile is blocked or not walkable
            if npos == blocked_tile:
                continue
            if not grid.is_walkable(npos[0], npos[1]):
                continue

            new_cost = current_cost + 1
            if npos not in cost_so_far or new_cost < cost_so_far[npos]:
                cost_so_far[npos] = new_cost
                priority = new_cost + manhattan_distance(npos, goal)
                heapq.heappush(frontier, (priority, new_cost, npos))
                came_from[npos] = current

    return None


def can_build_without_blocking(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
    target_tile: tuple[int, int],
) -> bool:
    """Validates whether placing an obstacle/tower on target_tile would sever the swarm path."""
    path = find_path_astar(grid, start=start, goal=goal, blocked_tile=target_tile)
    return path is not None
