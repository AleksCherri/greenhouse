from . import constants as C
from .greenhouse import Greenhouse

def run_headless(ticks: int) -> None:
    gh = Greenhouse()
    for _ in range(C.INITIAL_PLANTS):
        gh.add_plant()
    for _ in range(ticks):
        gh.tick()

    env = gh.environment
    print(f"=== Быстрая симуляция за {ticks} шагов ===")
    print(f"Всего раст.: {len(gh.bedlist)}")
    print(f"Ср. здоровье: {gh.average_health():.2f}")
    print(f"Собрано: {gh.total_harvested}")
    print(f"Среда: Темп={env.temperature:.2f}C  "
          f"Вл={env.humidity:.1f}%  "
          f"Св={env.light:.1f}%  "
          f"Время={env.hour:02d}")
    print(f"Оборудование: {gh.equipment.status_line()}")
    print("Растения:")
    for p in gh.bedlist:
        print("  ", p)
