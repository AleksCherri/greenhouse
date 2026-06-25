"""
Набор констант (настройки симуляции)
"""

DEFAULT_DELAY: float = 0.6          # Секунд между обновлением тиками
INITIAL_PLANTS: int = 3             # Кол-во растений при старте
SIM_HOURS_PER_DAY: int = 24

HEALTH_RECOVERY_IN_ZONE: float = 0.8     # Восстановление здоровья растений
HEALTH_TEMP_PENALTY: float = 0.6         # Потери за неправильно температуру
HEALTH_SLEEP_DISRUPTION: float = 1.5     # Потери за нарушение сна
HEALTH_HUMIDITY_OK: float = 0.2          # Восстановление за правильную влажность
HEALTH_HUMIDITY_EXTREME: float = 0.4     # Потеря за неправильную влажность
HEALTH_WATERING: float = 0.5             # Восстановление за полив
HEALTH_GROWTH_THRESHOLD: float = 60.0    # Минимальное здоровье для продолжения роста

HUMIDITY_LOW: float = 30.0
HUMIDITY_HIGH: float = 85.0
HUMIDITY_TARGET_LOW: float = 45.0
HUMIDITY_TARGET_HIGH: float = 75.0
HUMIDITY_SPRINKLER: float = 55.0
SPRINKLER_HEALTH_TRIGGER: float = 65.0

HEATER_POWER: float = 1.5
COOLER_POWER: float = 1.8
HUMIDIFIER_POWER: float = 4.0
DEHUMIDIFIER_POWER: float = 4.0
LIGHT_POWER: float = 60.0
LIGHT_DIM_THRESHOLD: float = 40.0
SPRINKLER_HUMIDITY: float = 6.0
TEMP_DEAD_BAND: float = 0.5

LEAK_TEMPERATURE: float = 0.15
LEAK_HUMIDITY: float = 0.05
LEAK_LIGHT: float = 0.5
CO2_ABSORPTION: float = 1.5
CO2_FLOOR: float = 380.0
