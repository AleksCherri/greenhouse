"""Класс Greenhouse - оркестратор, связывает классы Plant, Environment и Equipment."""

import random

from .environment import Environment
from .equipment import Equipment
from .plant import Plant

class Greenhouse:
    # Характеристики растений: Имя: (комфотная темп. (мин, макс), цикл сна (старт, конец), время роста)
    SPECIES: dict[str: tuple[tuple[int | float] | int]] = {
        'Томат': ((18.0, 26.0), (22, 6), 48),
        'Латук': ((10.0, 20.0), (20, 5), 30),
        'Базилик': ((15.0, 25.0), (21, 6), 36),
        'Перец': ((20.0, 28.0), (23, 7), 60),
        'Огурец': ((18.0, 27.0), (22, 6), 54),
    }

    def __init__(self):
        self.bedlist: list[Plant] = []
        self.environment: Environment = Environment()
        self.equipment: Equipment = Equipment()
        self.tick_count: int = 0
        self.total_harvested: int = 0

    # Управление посевами:
    def add_plant(self, spec: str = None) -> Plant:
        """Добавляет растение. Если тип не указан, добавляется произвольное растение"""
        spec = spec if spec else random.choice(tuple(self.SPECIES.keys()))
        props = self.SPECIES[spec]
        plant = Plant(spec, props[0], props[1], props[2])
        self.bedlist.append(plant)
        return plant

    def remove_dead(self) -> int:
        """Удаляет умершие растение и возвращает их количество"""
        before = len(self.bedlist)
        self.bedlist = [p for p in self.bedlist if p.is_alive()]
        return before - len(self.bedlist)

    def harvest_mature(self) -> int:
        """Собирает созревшие растения и возвращает их количество"""
        before = len(self.bedlist)
        self.bedlist = [p for p in self.bedlist if not p.is_mature()]
        return before - len(self.bedlist)

    # Основной цикл
    def tick(self) -> None:
        self.tick_count += 1
        self.equipment.auto_regulate(self.environment, self.bedlist)
        self.equipment.apply(self.environment)
        self.environment.tick()
        for p in self.bedlist:
            p.update(self.environment)
            p.tick(self.environment)
        self.remove_dead()
        self.total_harvested += self.harvest_mature()

    # Подсчёт метрик
    def average_health(self) -> float:
        """Возвращает среднее значение здоровья растений, 0 если их нет"""
        if not self.bedlist:
            return 0.0
        return sum(p.health for p in self.bedlist) / len(self.bedlist)

    def mature_count(self) -> int:
        """Возвращает количество взрослых растений"""
        return sum(1 for p in self.bedlist if p.is_mature())
