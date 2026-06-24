#!/usr/bin/env python3
"""
Automatic Greenhouse Management - Simulation
============================================

A text-based (TUI) simulation of an automated greenhouse.

Classes
-------
    Plant        - a single plant with health, comfort zone, sleep cycle, growth
    Environment  - the physical state inside the greenhouse
    Equipment    - actuators (heater, cooler, humidifier, lights, sprinkler)
    Greenhouse   - orchestrates plants, environment and equipment

Key algorithms
--------------
    1. Climate control  - Equipment.auto_regulate() picks the most conservative
                          comfort band of all alive plants and drives the
                          actuators so the environment stays inside it.
    2. Health update    - Plant.update(env) penalises temperature deviation,
                          sleep disruption by light, and extreme humidity.
    3. Growth           - Plant.tick(env) advances growth_time when the plant
                          is comfortable, marking it mature when growth_time
                          reaches the species' threshold.

Run
---
    python greenhouse.py                 # interactive TUI (paused, press S)
    python greenhouse.py --auto          # TUI auto-runs every 0.6s
    python greenhouse.py --headless 100  # run 100 ticks, print summary, exit
"""

from __future__ import annotations

import argparse
import curses
import random
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Plant
# ---------------------------------------------------------------------------
class Plant:
    """A single plant living in the greenhouse.

    Attributes
    ----------
    name                : species / label
    health              : float in 0..100
    comfort_temperature : (low, high) in Celsius
    sleep_cycle         : (start_hour, end_hour) - the hours during which the
                          plant should be left in the dark. Wraps midnight.
    growth_time         : accumulated growth (in simulation hours)
    mature_at           : growth_time at which the plant is harvest-ready.
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
        return self.growth_time >= self.mature_at

    def is_alive(self) -> bool:
        return self.health > 0

    def is_sleeping(self, hour: int) -> bool:
        start, end = self.sleep_cycle
        if start <= end:
            return start <= hour < end
        # wraps midnight, e.g. (22, 6)
        return hour >= start or hour < end

    def status_label(self) -> str:
        if not self.is_alive():
            return "DEAD"
        if self.is_mature():
            return "MATURE"
        if self.health > 70:
            return "HEALTHY"
        if self.health > 30:
            return "STRESSED"
        return "CRITICAL"

    # -- behaviour ---------------------------------------------------------
    def update(self, env: "Environment") -> None:
        """Algorithm 2 - update health based on the current environment."""
        if not self.is_alive():
            return

        lo, hi = self.comfort_temperature
        t = env.temperature
        delta = 0.0

        # temperature comfort
        if lo <= t <= hi:
            delta += 0.8                       # in the zone -> recover
        elif t < lo:
            delta -= (lo - t) * 0.6            # too cold
        else:
            delta -= (t - hi) * 0.6            # too hot

        # sleep disruption - lights on during sleep cycle hurts
        if self.is_sleeping(env.hour) and env.light > 30:
            delta -= 1.5

        # humidity
        if env.humidity < 30:
            delta -= 0.4
        elif env.humidity > 85:
            delta -= 0.4
        else:
            delta += 0.2

        # water
        if self.watered_this_tick:
            delta += 0.5
            self.watered_this_tick = False

        self.health = max(0.0, min(100.0, self.health + delta))

    def tick(self, env: "Environment") -> None:
        """Algorithm 3 - advance growth when the plant is comfortable."""
        if not self.is_alive() or self.is_mature():
            return
        lo, hi = self.comfort_temperature
        if lo <= env.temperature <= hi and self.health > 60:
            self.growth_time += 1

    def __repr__(self) -> str:
        return (
            f"Plant({self.name}, health={self.health:.1f}, "
            f"growth={self.growth_time}/{self.mature_at}, "
            f"status={self.status_label()})"
        )


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
@dataclass
class Environment:
    """The physical state inside the greenhouse."""

    temperature: float = 22.0      # Celsius
    humidity: float = 60.0         # %
    light: float = 50.0            # % (0=dark, 100=full sun)
    co2: float = 400.0             # ppm
    hour: int = 6                  # 0..23, simulation clock

    # external climate (what is outside the glass)
    outside_temp: float = 18.0
    outside_light: float = 0.0

    def tick(self) -> None:
        """Advance one simulated hour: day/night, heat leak, humidity drift."""
        self.hour = (self.hour + 1) % 24

        # outside light follows the sun (peak at noon)
        if 6 <= self.hour < 18:
            self.outside_light = 80.0 * max(
                0.0, 1.0 - abs(self.hour - 12) / 6.0
            )
        else:
            self.outside_light = 0.0

        # outside temperature peaks mid-afternoon, drops at night
        self.outside_temp = (
            18.0 + 6.0 * (1.0 - abs(self.hour - 14) / 8.0)
            - (4.0 if self.hour < 6 or self.hour >= 20 else 0.0)
        )

        # greenhouse slowly leaks toward outside conditions
        self.temperature += (self.outside_temp - self.temperature) * 0.15
        # humidity drifts toward 50 %
        self.humidity += (50.0 - self.humidity) * 0.05
        # light follows the sun, modulated by the glass
        self.light += (self.outside_light - self.light) * 0.5
        # CO2 slowly absorbed by plants (very simplified)
        self.co2 = max(380.0, self.co2 - 1.5)


# ---------------------------------------------------------------------------
# Equipment
# ---------------------------------------------------------------------------
@dataclass
class Equipment:
    """Actuators driven by the climate-control algorithm."""

    heater: bool = False
    cooler: bool = False
    humidifier: bool = False
    dehumidifier: bool = False
    lights: bool = False
    sprinkler: bool = False

    # strengths - how much each actuator changes env per tick
    HEATER_POWER: float = 1.5
    COOLER_POWER: float = 1.8
    HUMIDIFIER_POWER: float = 4.0
    DEHUMIDIFIER_POWER: float = 4.0
    LIGHT_POWER: float = 60.0
    SPRINKLER_HUMIDITY: float = 6.0

    def apply(self, env: Environment) -> None:
        """Push the actuators' effect onto the environment."""
        if self.heater:
            env.temperature += self.HEATER_POWER
        if self.cooler:
            env.temperature -= self.COOLER_POWER
        if self.humidifier:
            env.humidity += self.HUMIDIFIER_POWER
        if self.dehumidifier:
            env.humidity -= self.DEHUMIDIFIER_POWER
        if self.lights:
            env.light = max(env.light, self.LIGHT_POWER)
        if self.sprinkler:
            env.humidity += self.SPRINKLER_HUMIDITY
            self.sprinkler = False      # one-shot per tick

    # ----- Algorithm 1: climate control ----------------------------------
    def auto_regulate(self, env: Environment, plants: List[Plant]) -> None:
        """Pick the most conservative comfort band of all alive plants and
        drive the actuators so the environment stays inside it.
        """
        alive = [p for p in plants if p.is_alive()]
        if not alive:
            self.heater = self.cooler = False
            self.humidifier = self.dehumidifier = False
            self.lights = False
            return

        # 1. intersection of all comfort bands (most conservative)
        low = max(p.comfort_temperature[0] for p in alive)
        high = min(p.comfort_temperature[1] for p in alive)
        if low > high:                       # bands don't intersect -> average
            low = sum(p.comfort_temperature[0] for p in alive) / len(alive)
            high = sum(p.comfort_temperature[1] for p in alive) / len(alive)

        # 2. temperature control (dead-band of 0.5 C)
        if env.temperature < low - 0.5:
            self.heater, self.cooler = True, False
        elif env.temperature > high + 0.5:
            self.heater, self.cooler = False, True
        else:
            self.heater = self.cooler = False

        # 3. humidity control (target 45..75 %)
        if env.humidity < 45:
            self.humidifier, self.dehumidifier = True, False
        elif env.humidity > 75:
            self.humidifier, self.dehumidifier = False, True
        else:
            self.humidifier = self.dehumidifier = False

        # 4. lights: on if any plant is awake AND outside is dim
        any_awake = any(not p.is_sleeping(env.hour) for p in alive)
        if any_awake and env.light < 40:
            self.lights = True
        else:
            self.lights = False

        # 5. sprinkler: water any plant whose health is < 65 and humidity low
        if env.humidity < 55:
            for p in alive:
                if p.health < 65:
                    p.watered_this_tick = True
            self.sprinkler = True

    def status_line(self) -> str:
        def flag(b: bool) -> str:
            return "ON " if b else "off"
        return (
            f"heater:{flag(self.heater)} cooler:{flag(self.cooler)} "
            f"humid:{flag(self.humidifier)} dehum:{flag(self.dehumidifier)} "
            f"lights:{flag(self.lights)} sprinkler:{flag(self.sprinkler)}"
        )


# ---------------------------------------------------------------------------
# Greenhouse
# ---------------------------------------------------------------------------
class Greenhouse:
    """The orchestrator: holds plants (bedlist), environment and equipment."""

    SPECIES = [
        # name,     comfort_temp,  sleep_cycle, mature_at
        ("Tomato",   (18.0, 26.0),  (22, 6),     48),
        ("Lettuce",  (10.0, 20.0),  (20, 5),     30),
        ("Basil",    (15.0, 25.0),  (21, 6),     36),
        ("Pepper",   (20.0, 28.0),  (23, 7),     60),
        ("Cucumber", (18.0, 27.0),  (22, 6),     54),
    ]

    def __init__(self) -> None:
        self.bedlist: List[Plant] = []
        self.environment = Environment()
        self.equipment = Equipment()
        self.tick_count: int = 0

    # -- plant management --------------------------------------------------
    def add_plant(self, species: Optional[str] = None) -> Plant:
        if species is None:
            species = random.choice(self.SPECIES)[0]
        spec = next(s for s in self.SPECIES if s[0] == species)
        plant = Plant(spec[0], spec[1], spec[2], spec[3])
        self.bedlist.append(plant)
        return plant

    def remove_dead(self) -> int:
        before = len(self.bedlist)
        self.bedlist = [p for p in self.bedlist if p.is_alive()]
        return before - len(self.bedlist)

    # -- main loop step ----------------------------------------------------
    def tick(self) -> None:
        """One simulation step:
            1. equipment decides what to do based on plants + env
            2. equipment applies its effect
            3. environment evolves on its own
            4. each plant updates health and growth
        """
        self.tick_count += 1
        self.equipment.auto_regulate(self.environment, self.bedlist)
        self.equipment.apply(self.environment)
        self.environment.tick()
        for p in self.bedlist:
            p.update(self.environment)
            p.tick(self.environment)
        self.remove_dead()

    def average_health(self) -> float:
        if not self.bedlist:
            return 0.0
        return sum(p.health for p in self.bedlist) / len(self.bedlist)

    def mature_count(self) -> int:
        return sum(1 for p in self.bedlist if p.is_mature())


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------
class TUI:
    """Curses-based dashboard for the greenhouse simulation."""

    HEADER = " Automatic Greenhouse Management - Simulation "

    def __init__(self, gh: Greenhouse, auto: bool = False, delay: float = 0.6):
        self.gh = gh
        self.auto = auto
        self.delay = delay
        self.paused = not auto

    # ----- one-line helpers ----------------------------------------------
    @staticmethod
    def bar(value: float, width: int = 16) -> str:
        value = max(0.0, min(100.0, value))
        filled = int(width * value / 100.0)
        return "[" + "#" * filled + "-" * (width - filled) + "]"

    # ----- the curses main loop ------------------------------------------
    def run(self, stdscr: "curses.window") -> None:
        curses.curs_set(0)
        stdscr.nodelay(True)
        last_tick = 0.0

        while True:
            # ---- input ----
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                break
            elif key == ord(" "):
                self.paused = not self.paused
            elif key in (ord("s"), ord("S")):
                self.gh.tick()
            elif key in (ord("a"), ord("A")):
                self.gh.add_plant()
            elif key in (ord("r"), ord("R")):
                self.gh = Greenhouse()
                for _ in range(3):
                    self.gh.add_plant()
            elif key in (ord("p"), ord("P")):
                for _ in range(3):
                    self.gh.tick()

            # ---- auto step ----
            now = time.time()
            if not self.paused and now - last_tick > self.delay:
                self.gh.tick()
                last_tick = now

            # ---- draw ----
            self._draw(stdscr)
            time.sleep(0.05)

    # ----- draw -----------------------------------------------------------
    def _draw(self, stdscr: "curses.window") -> None:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        y = 0

        def put(line: str, attr: int = curses.A_NORMAL) -> None:
            nonlocal y
            if y < h - 1:
                try:
                    stdscr.addnstr(y, 0, line[: w - 1], w - 1, attr)
                except curses.error:
                    pass
                y += 1

        put(self.HEADER.center(w, "="), curses.A_REVERSE)
        if self.paused:
            put("  [ PAUSED - press SPACE to resume ]", curses.A_BOLD)
        else:
            put("  [ RUNNING ]", curses.A_BOLD)
        put("")

        env = self.gh.environment
        put(f" Tick: {self.gh.tick_count:>5}   "
            f"Sim hour: {env.hour:02d}:00   "
            f"Outside: {env.outside_temp:5.1f}C  "
            f"light {env.outside_light:4.0f}%")
        put("")
        put("  ENVIRONMENT")
        put(f"   temperature : {env.temperature:6.2f} C   "
            f"{self.bar(max(0.0, (env.temperature + 5) / 40 * 100), 20)}")
        put(f"   humidity    : {env.humidity:6.2f} %    "
            f"{self.bar(env.humidity, 20)}")
        put(f"   light       : {env.light:6.2f} %    "
            f"{self.bar(env.light, 20)}")
        put(f"   CO2         : {env.co2:6.1f} ppm")
        put("")
        put("  EQUIPMENT")
        put(f"   {self.gh.equipment.status_line()}")
        put("")
        put(f"  PLANTS ({len(self.gh.bedlist)})   "
            f"avg health: {self.gh.average_health():5.1f}   "
            f"mature: {self.gh.mature_count()}")
        put("   name       health  bar              growth      "
             "comfort  sleep  status")
        put("   " + "-" * 70)
        for p in self.gh.bedlist[: h - y - 4]:
            lo, hi = p.comfort_temperature
            ss, se = p.sleep_cycle
            put(f"   {p.name:<9}  {p.health:5.1f}  "
                f"{self.bar(p.health, 16)}  "
                f"{p.growth_time:>3}/{p.mature_at:<3}    "
                f"{lo:4.1f}-{hi:4.1f}  "
                f"{ss:02d}-{se:02d}  "
                f"{p.status_label()}")

        put("")
        put("  [SPACE] pause   [S] step   [A] add plant   "
            "[P] step x3   [R] reset   [Q] quit")


# ---------------------------------------------------------------------------
# headless runner (for smoke tests / scripting)
# ---------------------------------------------------------------------------
def run_headless(ticks: int) -> None:
    gh = Greenhouse()
    for _ in range(3):
        gh.add_plant()
    for _ in range(ticks):
        gh.tick()

    print(f"=== Headless run after {ticks} ticks ===")
    print(f"Plants alive : {len(gh.bedlist)}")
    print(f"Average health: {gh.average_health():.2f}")
    print(f"Mature       : {gh.mature_count()}")
    print(f"Environment  : T={gh.environment.temperature:.2f}C  "
          f"H={gh.environment.humidity:.1f}%  "
          f"L={gh.environment.light:.1f}%  "
          f"hour={gh.environment.hour:02d}")
    print(f"Equipment    : {gh.equipment.status_line()}")
    print("Plants:")
    for p in gh.bedlist:
        print("  ", p)


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Greenhouse simulation")
    parser.add_argument("--auto", action="store_true",
                        help="start in auto-run mode")
    parser.add_argument("--headless", type=int, default=0,
                        help="run N ticks without TUI and exit")
    parser.add_argument("--delay", type=float, default=0.6,
                        help="seconds between auto-ticks")
    args = parser.parse_args()

    if args.headless > 0:
        run_headless(args.headless)
        return

    gh = Greenhouse()
    for _ in range(3):
        gh.add_plant()
    tui = TUI(gh, auto=args.auto, delay=args.delay)
    try:
        curses.wrapper(tui.run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
