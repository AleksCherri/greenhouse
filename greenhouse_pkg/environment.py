"""Класс Environment - внутреннее физическое состояние теплицы."""

#from __future__ import annotations

from dataclasses import dataclass

from . import constants as C

@dataclass
class Environment:
    """Внутреннее и внешнее состояние теплицы.

    Все значения обновляются каждый тик, имитируя обмен
    смену дня и ночи, а так же перемешивание внутреннего и внешнего климатов.
    """

    # Внутренний климат
    temperature: float = 22.0       # Цельсия, тепличная температура
    humidity: float = 60.0      # %, относительная влажность
    light: float = 50.0     # %, тепличная освещённость
    co2: float = 400.0      # ppm, количество углекислого газа
    hour: int = 6       # 0..23, часы симуляции

    # Внешний климат.
    outside_temp: float = 18.0      # Цельсия, внешняя температура
    outside_light: float = 0.0      # %, яркость солнца

    def tick(self) -> None:
        """Просчитывает один тик (час) симуляции.
        Обновляет часы симуляции и просчитывает смешивание внутреннего климата с внешним.
        (Теплообмен и т.д.)
        """
        self.hour = (self.hour + 1) % C.SIM_HOURS_PER_DAY

        # Внешнее освещение максимально в полдень, минимально ночью.
        if 6 <= self.hour < 18:
            self.outside_light = 80.0 * max(0.0, 1.0 - abs(self.hour - 12) / 6.0)
        else:
            self.outside_light = 0.0

        # Внешняя температура максимально после полудня, затем падает к ночи.
        self.outside_temp = (
            18.0 + 6.0 * (1.0 - abs(self.hour - 14) / 8.0)
            - (4.0 if self.hour < 6 or self.hour >= 20 else 0.0)
        )

        # Внутренний климат постепенно стремится сравняться с внешним.
        self.temperature += (self.outside_temp - self.temperature) * C.LEAK_TEMPERATURE
        self.humidity += (50.0 - self.humidity) * C.LEAK_HUMIDITY
        self.light += (self.outside_light - self.light) * C.LEAK_LIGHT
        self.co2 = max(C.CO2_FLOOR, self.co2 - C.CO2_ABSORPTION)
