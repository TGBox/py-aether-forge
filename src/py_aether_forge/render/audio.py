"""Sound synthesis and audio cues manager for towers and combat."""

import math
import struct

import pygame


class AudioManager:
    """Generates and plays synthesizer sound effects for combat events."""

    def __init__(self) -> None:
        self.enabled: bool = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.enabled = True
            self._generate_sfx()
        except (pygame.error, OSError):
            self.enabled = False

    def _create_synth_sound(
        self,
        freq_start: float,
        freq_end: float,
        duration: float,
        volume: float = 0.3,
    ) -> pygame.mixer.Sound | None:
        """Synthesizes a simple sine frequency-sweep waveform."""
        if not self.enabled:
            return None

        sample_rate = 22050
        num_samples = int(sample_rate * duration)
        buf = bytearray()

        phase = 0.0
        for i in range(num_samples):
            t = i / num_samples
            freq = freq_start + (freq_end - freq_start) * t
            phase += 2.0 * math.pi * freq / sample_rate

            # Linear fade out
            amp = (1.0 - t) * volume
            sample_val = int(32767.0 * amp * math.sin(phase))
            buf.extend(struct.pack("<h", sample_val))

        return pygame.mixer.Sound(buffer=bytes(buf))

    def _generate_sfx(self) -> None:
        # Pew / Tower attack
        s_shoot = self._create_synth_sound(580.0, 220.0, 0.12, volume=0.25)
        if s_shoot:
            self._sounds["shoot"] = s_shoot

        # Hit / Impact
        s_hit = self._create_synth_sound(260.0, 90.0, 0.08, volume=0.35)
        if s_hit:
            self._sounds["hit"] = s_hit

        # Wave start chime
        s_wave = self._create_synth_sound(340.0, 680.0, 0.35, volume=0.4)
        if s_wave:
            self._sounds["wave"] = s_wave

        # Leak warning buzzer
        s_leak = self._create_synth_sound(180.0, 110.0, 0.25, volume=0.5)
        if s_leak:
            self._sounds["leak"] = s_leak

    def play(self, sound_name: str) -> None:
        """Plays a pre-synthesized audio cue."""
        if not self.enabled:
            return
        sound = self._sounds.get(sound_name)
        if sound is not None:
            sound.play()
