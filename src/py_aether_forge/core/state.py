"""Game and match state machines."""

from enum import Enum, auto


class GameState(Enum):
    """Overall phases of an active battle match."""

    PREPARATION = auto()  # Building & upgrading towers before wave
    WAVE = auto()  # Active combat: Creeps spawning, towers firing
    DRAFT = auto()  # Post-wave platform shard drafting
    GAME_OVER = auto()  # World core destroyed
    VICTORY = auto()  # All waves survived


class MatchState:
    """Manages the phase transitions and current wave index of a run."""

    def __init__(self) -> None:
        self._state: GameState = GameState.PREPARATION
        self._wave_number: int = 0

    @property
    def current_state(self) -> GameState:
        return self._state

    @property
    def wave_number(self) -> int:
        return self._wave_number

    def start_wave(self, wave_index: int) -> None:
        """Transitions into the active combat phase for the given wave."""
        self._wave_number = wave_index
        self._state = GameState.WAVE

    def finish_wave_and_enter_draft(self) -> None:
        """Transitions to the platform shard drafting phase upon wave completion."""
        self._state = GameState.DRAFT

    def complete_draft(self) -> None:
        """Transitions back to tower preparation once a platform shard is placed."""
        self._state = GameState.PREPARATION

    def set_game_over(self) -> None:
        """Sets the game over state when the world core health reaches zero."""
        self._state = GameState.GAME_OVER

    def set_victory(self) -> None:
        """Sets the victory state when all encounters have been overcome."""
        self._state = GameState.VICTORY
