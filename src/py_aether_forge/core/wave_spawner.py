"""Wave generation and timed creep spawning queue."""

from collections.abc import Callable
from dataclasses import dataclass

from py_aether_forge.enemies.creep import Creep
from py_aether_forge.enemies.types import (
    create_astral_titan,
    create_chaos_golem,
    create_swarm_runner,
    create_void_wisp,
)


@dataclass
class SpawnEntry:
    """An individual queued creep ready to spawn."""

    factory: Callable[[float, float, float], Creep]
    delay_before_spawn: float


class WaveSpawner:
    """Manages wave progression, scaling, and timed enemy emissions at the portal."""

    def __init__(self) -> None:
        self.current_wave_number: int = 0
        self.spawn_queue: list[SpawnEntry] = []
        self.spawn_timer: float = 0.0
        self.active_creeps: list[Creep] = []

    def generate_wave(self, wave_number: int) -> list[SpawnEntry]:
        """Generates a scripted wave with geometric HP scaling (~1.12x per wave)."""
        queue: list[SpawnEntry] = []

        if wave_number % 10 == 0:
            # Boss wave
            queue.append(SpawnEntry(factory=create_astral_titan, delay_before_spawn=1.0))
            for _ in range(4):
                queue.append(SpawnEntry(factory=create_chaos_golem, delay_before_spawn=0.8))
        elif wave_number % 5 == 0:
            # Swarm rush
            for _ in range(16):
                queue.append(SpawnEntry(factory=create_swarm_runner, delay_before_spawn=0.35))
        else:
            # Standard wave mix
            runner_count = 6 + wave_number
            for _ in range(runner_count):
                queue.append(SpawnEntry(factory=create_swarm_runner, delay_before_spawn=0.6))
            if wave_number >= 3:
                golem_count = 1 + wave_number // 3
                for _ in range(golem_count):
                    queue.append(SpawnEntry(factory=create_chaos_golem, delay_before_spawn=1.2))
            if wave_number >= 4:
                wisp_count = 2 + wave_number // 2
                for _ in range(wisp_count):
                    queue.append(SpawnEntry(factory=create_void_wisp, delay_before_spawn=0.8))

        return queue

    def start_wave(self, wave_number: int) -> None:
        """Loads and primes the spawner for the requested wave."""
        self.current_wave_number = wave_number
        self.spawn_queue = self.generate_wave(wave_number)
        self.spawn_timer = 0.5  # Initial breather before first creep
        self.active_creeps.clear()

    def update(
        self,
        dt: float,
        portal_pos: tuple[float, float],
    ) -> list[Creep]:
        """Advances spawn timer and returns newly spawned creeps."""
        newly_spawned: list[Creep] = []

        if not self.spawn_queue:
            return newly_spawned

        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            next_entry = self.spawn_queue.pop(0)
            creep = next_entry.factory(
                portal_pos[0],
                portal_pos[1],
                1.12 ** (self.current_wave_number - 1),
            )
            newly_spawned.append(creep)
            self.active_creeps.append(creep)

            if self.spawn_queue:
                self.spawn_timer = self.spawn_queue[0].delay_before_spawn

        return newly_spawned

    def is_wave_spawning_done(self) -> bool:
        """Returns True when all queued creeps have spawned."""
        return len(self.spawn_queue) == 0
