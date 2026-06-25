#from __future__ import annotations

import curses
import time
from typing import List

from . import constants as C
from .greenhouse import Greenhouse


def bar(value: float, width: int = 16) -> str:
    value = max(0.0, min(100.0, value))
    filled = int(width * value / 100.0)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _put(stdscr, y: int, w: int, line: str, attr: int = curses.A_NORMAL) -> int:
    if y < stdscr.getmaxyx()[0] - 1:
        try:
            stdscr.addnstr(y, 0, line[: w - 1], w - 1, attr)
        except curses.error:
            pass
        return y + 1
    return y


class TUI:
    HEADER = " СИМУЛЯЦИЯ ТЕПЛИЦЫ "

    def __init__(self, gh: Greenhouse, auto: bool = False, delay: float = C.DEFAULT_DELAY):
        self.gh = gh
        self.auto = auto
        self.delay = delay
        self.paused = not auto
        self.choosing_plant = False

    def run(self, stdscr: "curses.window") -> None:
        """Main curses event loop: input → auto-step → draw."""
        curses.curs_set(0)
        stdscr.nodelay(True)
        last_tick = 0.0

        while True:
            if self.choosing_plant:
                self._index_choosing(stdscr.getch())
            else:
                self._handle_key(stdscr.getch())

            now = time.time()
            if not self.paused and now - last_tick > self.delay:
                self.gh.tick()
                last_tick = now

            self._draw(stdscr)
            time.sleep(0.05)

    def _handle_key(self, key: int) -> None:
        if key in (ord("q"), ord("Q")):
            raise KeyboardInterrupt
        elif key == ord(" "):
            self.paused = not self.paused
        elif key in (ord("s"), ord("S")):
            self.gh.tick()
        elif key in (ord("a"), ord("A")):
            self.choosing_plant = True
        elif key in (ord("r"), ord("R")):
            self.gh = Greenhouse()
            for _ in range(C.INITIAL_PLANTS):
                self.gh.add_plant()
        elif key in (ord("p"), ord("P")):
            for _ in range(3):
                self.gh.tick()

    def _index_choosing(self, key: int) -> None:
        if key in (ord("q"), ord("Q")):
            self.choosing_plant = False
        elif key in (ord("a"), ord("A")):
            self.gh.add_plant('Томат')
            self.choosing_plant = False
        elif key in (ord("s"), ord("S")):
            self.gh.add_plant('Латук')
            self.choosing_plant = False
        elif key in (ord("d"), ord("D")):
            self.gh.add_plant('Базилик')
            self.choosing_plant = False
        elif key in (ord("f"), ord("F")):
            self.gh.add_plant('Перец')
            self.choosing_plant = False
        elif key in (ord("g"), ord("G")):
            self.gh.add_plant('Огурец')
            self.choosing_plant = False

    def _draw(self, stdscr: "curses.window") -> None:
        """Render the full dashboard once."""
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        y = 0

        y = _put(stdscr, y, w, self.HEADER.center(w, "="), curses.A_REVERSE)
        if self.paused:
            y = _put(stdscr, y, w, "  [ ПАУЗА - нажимите SPACE для продолжения ]", curses.A_BOLD)
        else:
            y = _put(stdscr, y, w, "  [ В ПРОЦЕССЕ ]", curses.A_BOLD)
        y = _put(stdscr, y, w, "")

        env = self.gh.environment
        y = _put(stdscr, y, w,
                 f" Шаг: {self.gh.tick_count:>5}   "
                 f"Время: {env.hour:02d}:00   "
                 f"Внеш. темп.: {env.outside_temp:5.1f}C  "
                 f"Внеш. свет: {env.outside_light:4.0f}%")
        y = _put(stdscr, y, w, "")

        y = _put(stdscr, y, w, "  СРЕДА")
        y = _put(stdscr, y, w,
                 f"   Температура : {env.temperature:6.2f} C   "
                 f"{bar(max(0.0, (env.temperature + 5) / 40 * 100), 20)}")
        y = _put(stdscr, y, w,
                 f"   Влажность   : {env.humidity:6.2f} %    "
                 f"{bar(env.humidity, 20)}")
        y = _put(stdscr, y, w,
                 f"   Свет        : {env.light:6.2f} %    "
                 f"{bar(env.light, 20)}")
        y = _put(stdscr, y, w, f"   CO2         : {env.co2:6.1f} ppm")
        y = _put(stdscr, y, w, "")

        y = _put(stdscr, y, w, "  ОБОРУДОВАНИЕ")
        y = _put(stdscr, y, w, f"   {self.gh.equipment.status_line()}")
        y = _put(stdscr, y, w, "")

        y = _put(stdscr, y, w,
                 f"  РАСТЕНИЯ ({len(self.gh.bedlist)})   "
                 f"Ср. здоровье: {self.gh.average_health():5.1f}   "
                 f"Всего собрано: {self.gh.total_harvested}")
        y = _put(stdscr, y, w,
                 "   Название           Здоровье             Рост    "
                 "Комф. темп. Сон    Статус")
        y = _put(stdscr, y, w, "   " + "-" * 70)

        # Show as many plants as still fit on the screen.
        for p in self.gh.bedlist[: max(0, h - y - 4)]:
            lo, hi = p.comfort_temperature
            ss, se = p.sleep_cycle
            y = _put(stdscr, y, w,
                     f"   {p.name:<9}  {p.health:5.1f}  "
                     f"{bar(p.health, 16)}  "
                     f"{p.growth_time:>3}/{p.mature_at:<3}    "
                     f"{lo:4.1f}-{hi:4.1f}  "
                     f"{ss:02d}-{se:02d}  "
                     f"{p.status_label()}")

        y = _put(stdscr, y, w, "")
        if self.choosing_plant:
            y = _put(stdscr, y, w, "  [Q] ОТМЕНА")
            _put(stdscr, y, w, "  [A] Томат   [S] Латук   [D] Базилик   [F] Перец   [G] Огурец")
        else:
            _put(stdscr, y, w,
                 "  [SPACE] пауза   [S] шаг   [A] доб. растение   "
                 "[P] шаг x3   [R] рестарт   [Q] выйти")
