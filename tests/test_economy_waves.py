"""Tests for core economy, game state, and wave spawner."""

from py_aether_forge.core.economy import Economy
from py_aether_forge.core.state import GameState, MatchState
from py_aether_forge.core.wave_spawner import WaveSpawner


def test_economy_initial_values() -> None:
    eco = Economy(aether_dust=120, core_health=20)
    assert eco.aether_dust == 120
    assert eco.core_health == 20
    assert eco.max_core_health == 20
    assert eco.astral_shards == 0
    assert not eco.is_defeated()


def test_economy_spend_and_earn() -> None:
    eco = Economy(aether_dust=100)
    assert eco.can_afford(60)
    assert eco.spend(60)
    assert eco.aether_dust == 40
    assert not eco.can_afford(50)
    assert not eco.spend(50)
    assert eco.aether_dust == 40

    eco.add_aether(35)
    assert eco.aether_dust == 75


def test_economy_leak_penalty_and_game_over() -> None:
    eco = Economy(core_health=3)
    eco.register_leak(damage=2)
    assert eco.core_health == 1
    assert not eco.is_defeated()

    eco.register_leak(damage=1)
    assert eco.core_health == 0
    assert eco.is_defeated()


def test_economy_astral_shards() -> None:
    eco = Economy()
    eco.award_astral_shards(5)
    assert eco.astral_shards == 5


def test_match_state_transitions() -> None:
    state = MatchState()
    assert state.current_state == GameState.PREPARATION
    assert state.wave_number == 0

    state.start_wave(wave_index=1)
    assert state.current_state == GameState.WAVE
    assert state.wave_number == 1

    state.finish_wave_and_enter_draft()
    assert state.current_state == GameState.DRAFT

    state.complete_draft()
    assert state.current_state == GameState.PREPARATION

    state.set_game_over()
    assert state.current_state == GameState.GAME_OVER


def test_wave_spawner_queue_and_scaling() -> None:
    spawner = WaveSpawner()
    spawner.start_wave(wave_number=1)
    assert not spawner.is_wave_spawning_done()
    assert len(spawner.spawn_queue) > 0

    # Advance time to spawn creeps
    spawned = spawner.update(dt=1.0, portal_pos=(0.0, 0.0))
    assert len(spawned) >= 1
    assert spawned[0].x == 0.0
    assert spawned[0].y == 0.0

    # Test scaling on wave 10
    spawner.start_wave(wave_number=10)
    # Boss wave should have higher HP than wave 1
    boss_entry = spawner.spawn_queue[0]
    boss = boss_entry.factory(0.0, 0.0, 1.12**9)
    assert boss.hp > 750.0
