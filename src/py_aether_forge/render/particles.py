"""Elemental and projectile particle effects system."""

import math
import random

import pygame


class Particle:
    """An individual animated magic glow spark."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: tuple[int, int, int],
        radius: float,
        lifetime: float,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.initial_radius = radius
        self.radius = radius
        self.lifetime = lifetime
        self.age = 0.0

    @property
    def is_alive(self) -> bool:
        return self.age < self.lifetime

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        progress = self.age / self.lifetime
        self.radius = max(0.5, self.initial_radius * (1.0 - progress))


class ParticleSystem:
    """Emitter and manager for projectile impacts, auras, and sparks."""

    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def emit_burst(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        count: int = 12,
        speed: float = 90.0,
        lifetime: float = 0.45,
    ) -> None:
        """Emits an explosion of particles at (x, y)."""
        for _ in range(count):
            angle = random.uniform(0.0, 6.28)
            mag = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * mag
            vy = math.sin(angle) * mag
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    color=color,
                    radius=random.uniform(2.5, 4.5),
                    lifetime=random.uniform(lifetime * 0.7, lifetime * 1.3),
                )
            )

    def update(self, dt: float) -> None:
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (1.0 - p.age / p.lifetime))))
            # Soft glowing circle using small surface
            r = int(p.radius)
            if r > 0 and alpha > 0:
                glow_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    glow_surf,
                    (*p.color, alpha),
                    (r + 1, r + 1),
                    r,
                )
                surface.blit(glow_surf, (int(p.x - r - 1), int(p.y - r - 1)))
