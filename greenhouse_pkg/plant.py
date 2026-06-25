"""The :class:`Plant` model — a single plant living in the greenhouse."""

#from __future__ import annotations

from typing import Tuple

from . import constants as C
from .environment import Environment


class Plant:
    """A single plant living in the greenhouse.

    Each plant is described by its species' ecological profile (comfort
    temperature band, photoperiod and maturation threshold) and by its current
    biological state (health and accumulated growth time).

    Attributes
    ----------
    name : str
        Species / display label.
    health : float
        Current vitality in the range ``0..100``; zero means the plant is dead.
    comfort_temperature : tuple[float, float]
        ``(low, high)`` ambient temperatures, in Celsius, within which the
        plant thrives.
    sleep_cycle : tuple[int, int]
        ``(start_hour, end_hour)`` during which the plant should be kept in
        the dark. The window wraps midnight, so ``(22, 6)`` means 22:00–06:00.
    growth_time : int
        Accumulated growth, measured in simulation hours.
    mature_at : int
        ``growth_time`` at which the plant becomes harvest-ready.
    """

    def __init__(
        self,
        name: str,
        comfort_temperature: Tuple[float, float],
        sleep_cycle: Tuple[int, int],
        mature_at: int = 48,
    ) -> None:
        self.name: str = name
        self.health: float = 100.0
        self.comfort_temperature: Tuple[float, float] = comfort_temperature
        self.sleep_cycle: Tuple[int, int] = sleep_cycle
        self.growth_time: int = 0
        self.mature_at: int = mature_at
        self.watered_this_tick: bool = False

    # -- queries -----------------------------------------------------------
    def is_mature(self) -> bool:
        """Return ``True`` once the plant has accumulated enough growth."""
        return self.growth_time >= self.mature_at

    def is_alive(self) -> bool:
        """Return ``True`` while the plant still has health."""
        return self.health > 0

    def is_sleeping(self, hour: int) -> bool:
        """Return ``True`` if ``hour`` falls inside the plant's sleep window.

        Handles windows that wrap around midnight (e.g. ``(22, 6)``).
        """
        start, end = self.sleep_cycle
        if start <= end:
            return start <= hour < end
        return hour >= start or hour < end

    def status_label(self) -> str:
        """Return a short human-readable status string."""
        if not self.is_alive():
            return "МЁРТВ"
        if self.is_mature():
            return "ВЫРОС"
        if self.health > 70:
            return "ЗДОРОВ"
        if self.health > 30:
            return "БОЛЕЕТ"
        return "КРИТИЧНО"

    # -- behaviour ---------------------------------------------------------
    def update(self, env: Environment) -> None:
        """Recalculate the plant's health for the current tick.

        The model is additive: staying inside the comfort zone and within the
        healthy humidity band restores health, while temperature deviation,
        night-time light exposure, extreme humidity and drought reduce it.
        The result is clamped to ``0..100``.
        """
        if not self.is_alive():
            return

        low, high = self.comfort_temperature
        t = env.temperature
        delta = 0.0

        # Temperature comfort.
        if low <= t <= high:
            delta += C.HEALTH_RECOVERY_IN_ZONE
        else:
            delta -= abs(t - (low if t < low else high)) * C.HEALTH_TEMP_PENALTY

        # Photoperiod disruption: light during the sleep window hurts.
        if self.is_sleeping(env.hour) and env.light > C.LIGHT_DIM_THRESHOLD:
            delta -= C.HEALTH_SLEEP_DISRUPTION

        # Humidity.
        if env.humidity < C.HUMIDITY_LOW or env.humidity > C.HUMIDITY_HIGH:
            delta -= C.HEALTH_HUMIDITY_EXTREME
        else:
            delta += C.HEALTH_HUMIDITY_OK

        # One-shot watering boost.
        if self.watered_this_tick:
            delta += C.HEALTH_WATERING
            self.watered_this_tick = False

        self.health = max(0.0, min(100.0, self.health + delta))

    def tick(self, env: Environment) -> None:
        """Advance growth when the plant is comfortable and vigorous enough.

        Growth only happens if the plant is alive, not yet mature, sitting in
        its comfort temperature and above the :data:`HEALTH_GROWTH_THRESHOLD`.
        """
        if not self.is_alive() or self.is_mature():
            return
        low, high = self.comfort_temperature
        if low <= env.temperature <= high and self.health > C.HEALTH_GROWTH_THRESHOLD:
            self.growth_time += 1

    def __repr__(self) -> str:
        return (
            f"Plant({self.name}, health={self.health:.1f}, "
            f"growth={self.growth_time}/{self.mature_at}, "
            f"status={self.status_label()})"
        )
