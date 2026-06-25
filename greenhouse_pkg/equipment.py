"""Класс Equipment - алгоритмы климатического контроля."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import constants as C
from .environment import Environment
from .plant import Plant


@dataclass
class Equipment:
    """
    Каждый активатор соответствует определённому оборудованию климат-контроля.
    """

    heater: bool = False
    cooler: bool = False
    humidifier: bool = False
    dehumidifier: bool = False
    lights: bool = False
    sprinkler: bool = False

    def apply(self, env: Environment) -> None:
        """Применяет эффекты оборудования к внутренней среде теплицы."""
        if self.heater:
            env.temperature += C.HEATER_POWER
        if self.cooler:
            env.temperature -= C.COOLER_POWER
        if self.humidifier:
            env.humidity += C.HUMIDIFIER_POWER
        if self.dehumidifier:
            env.humidity -= C.DEHUMIDIFIER_POWER
        if self.lights:
            env.light = max(env.light, C.LIGHT_POWER)
        if self.sprinkler:
            env.humidity += C.SPRINKLER_HUMIDITY
            self.sprinkler = False  # one-shot per tick

    # ----- Algorithm 1: climate control ----------------------------------
    def auto_regulate(self, env: Environment, plants: List[Plant]) -> None:
        """Управление активаторами, чтобы держать климат в норме."""
        alive = [p for p in plants if p.is_alive()]
        if not alive:
            self.heater = self.cooler = False
            self.humidifier = self.dehumidifier = False
            self.lights = False
            return

        low = max(p.comfort_temperature[0] for p in alive)
        high = min(p.comfort_temperature[1] for p in alive)
        if low > high:  # no intersection -> average
            low = sum(p.comfort_temperature[0] for p in alive) / len(alive)
            high = sum(p.comfort_temperature[1] for p in alive) / len(alive)

        if env.temperature < low - C.TEMP_DEAD_BAND:
            self.heater, self.cooler = True, False
        elif env.temperature > high + C.TEMP_DEAD_BAND:
            self.heater, self.cooler = False, True
        else:
            self.heater = self.cooler = False

        if env.humidity < C.HUMIDITY_TARGET_LOW:
            self.humidifier, self.dehumidifier = True, False
        elif env.humidity > C.HUMIDITY_TARGET_HIGH:
            self.humidifier, self.dehumidifier = False, True
        else:
            self.humidifier = self.dehumidifier = False

        any_awake = any(not p.is_sleeping(env.hour) for p in alive)
        self.lights = any_awake and env.light < C.LIGHT_DIM_THRESHOLD

        self.sprinkler = env.humidity < C.HUMIDITY_SPRINKLER
        if self.sprinkler:
            for p in alive:
                if p.health < C.SPRINKLER_HEALTH_TRIGGER:
                    p.watered_this_tick = True

    def status_line(self) -> str:
        flag = lambda b: "ВКЛ " if b else "ВЫКЛ"
        return (
            f"Обогр.:{flag(self.heater)} Конд.:{flag(self.cooler)} "
            f"Увлажн.:{flag(self.humidifier)} Осуш.:{flag(self.dehumidifier)} "
            f"Свет:{flag(self.lights)} Полив:{flag(self.sprinkler)}"
        )
