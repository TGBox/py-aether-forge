"""Parallax starfield and celestial nebula rendering."""

import math
import random

import pygame


class Star:
    """An individual shimmering star in astral space."""

    def __init__(self, x: float, y: float, depth: float, brightness: float) -> None:
        self.x: float = x
        self.y: float = y
        self.depth: float = depth  # 0.2 (distant) to 1.0 (near)
        self.brightness: float = brightness
        self.twinkle_phase: float = random.uniform(0.0, 6.28)

    def update(self, dt: float, bounds_w: int, bounds_h: int) -> None:
        # Subtle celestial drift
        self.x -= 4.0 * self.depth * dt
        self.y += 2.0 * self.depth * dt
        self.twinkle_phase += 2.5 * dt

        if self.x < 0:
            self.x = float(bounds_w)
        if self.y > bounds_h:
            self.y = 0.0


class Starfield:
    """Manages multi-layered shimmering stars and ambient background glow."""

    def __init__(self, width: int = 1280, height: int = 720, count: int = 120) -> None:
        self.width = width
        self.height = height
        self.stars: list[Star] = []

        rng = random.Random(42)
        for _ in range(count):
            self.stars.append(
                Star(
                    x=rng.uniform(0, width),
                    y=rng.uniform(0, height),
                    depth=rng.uniform(0.3, 1.0),
                    brightness=rng.uniform(140, 255),
                )
            )

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def update(self, dt: float) -> None:
        for star in self.stars:
            star.update(dt, self.width, self.height)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((11, 14, 28))  # Void dark

        for star in self.stars:
            twinkle = 0.7 + 0.3 * math.sin(star.twinkle_phase)
            alpha_brightness = int(star.brightness * twinkle)
            color = (
                min(255, int(alpha_brightness * 0.9)),
                min(255, int(alpha_brightness * 0.95)),
                min(255, alpha_brightness),
            )
            size = 1 if star.depth < 0.6 else 2
            pygame.draw.circle(surface, color, (int(star.x), int(star.y)), size)
