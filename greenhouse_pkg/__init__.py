"""The :mod:`greenhouse_pkg` package — automatic greenhouse simulation.

Public API
----------
- :class:`Plant`           — a single plant
- :class:`Environment`     — the physical state of the greenhouse
- :class:`Equipment`       — actuators and climate-control algorithm
- :class:`Greenhouse`      — orchestrator (plants + environment + equipment)
- :class:`TUI`             — curses-based dashboard
- :func:`run_headless`     — script-friendly runner
- :func:`main`             — CLI entry point
"""

#from __future__ import annotations

from . import constants
from .environment import Environment
from .equipment import Equipment
from .greenhouse import Greenhouse
from .headless import run_headless
from .plant import Plant
from .tui import TUI

__all__ = [
    "constants",
    "Plant",
    "Environment",
    "Equipment",
    "Greenhouse",
    "TUI",
    "run_headless",
    "main",
]

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Parse command-line arguments and launch the requested run mode."""
    import argparse
    import curses

    parser = argparse.ArgumentParser(description="Greenhouse simulation")
    parser.add_argument("--auto", action="store_true",
                        help="start in auto-run mode")
    parser.add_argument("--headless", type=int, default=0,
                        help="run N ticks without TUI and exit")
    parser.add_argument("--delay", type=float, default=constants.DEFAULT_DELAY,
                        help="seconds between auto-ticks")
    args = parser.parse_args()

    if args.headless > 0:
        run_headless(args.headless)
        return

    gh = Greenhouse()
    for _ in range(constants.INITIAL_PLANTS):
        gh.add_plant()
    tui = TUI(gh, auto=args.auto, delay=args.delay)
    try:
        curses.wrapper(tui.run)
    except KeyboardInterrupt:
        pass
