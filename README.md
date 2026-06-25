# Automatic Greenhouse Management — Simulation

A text-based (TUI) simulation of an automated greenhouse, written in Python 3.

## Project Structure

The code is split into a reusable package plus a small launcher:

```
.
├── main.py                    # CLI launcher (run this file)
├── greenhouse_pkg/            # the package
│   ├── __init__.py            # public API + main() entry point
│   ├── constants.py           # all tunable parameters
│   ├── plant.py               # Plant class (health, growth, sleep)
│   ├── environment.py         # Environment class (climate state)
│   ├── equipment.py           # Equipment class + climate-control algorithm
│   ├── greenhouse.py          # Greenhouse orchestrator (the control loop)
│   ├── headless.py            # script-friendly headless runner
│   └── tui.py                 # curses-based dashboard
└── README.md
```

## Run Modes

```bash
python main.py                 # interactive TUI (paused, press S to step)
python main.py --auto          # TUI auto-runs every 0.6s
python main.py --headless 100  # run 100 ticks, print summary, exit
python main.py --delay 1.0     # custom delay between auto-ticks
```

## TUI Key Bindings

| Key   | Action                  |
|-------|-------------------------|
| SPACE | pause / resume auto-run |
| S     | single step             |
| P     | step three ticks        |
| A     | add a random plant      |
| R     | reset the greenhouse    |
| Q     | quit                    |

## Architecture

Three loosely-coupled subsystems interact on every simulated hour (tick):

- **Plant** — biology: health, comfort zone, photoperiod, growth
- **Environment** — physics: temperature, humidity, light, CO₂, day/night
- **Equipment** — actuators: heater, cooler, humidifier, lights, sprinkler

The `Greenhouse` orchestrator wires them into a closed control loop:

1. equipment decides what to do (based on plants + environment)
2. equipment applies its effect to the environment
3. environment evolves on its own
4. each plant updates its health and growth
5. dead plants are removed

## Tuning

All magic numbers live in `greenhouse_pkg/constants.py`. Editing that single
file is enough to retune the simulation.
