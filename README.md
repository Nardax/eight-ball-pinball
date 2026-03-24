# eight-ball-pinball

A ground-up rebuild of the Bally Eight Ball (1977) pinball machine using modern hardware and software.

## Overview

This project rebuilds the Eight Ball using:
- **Mission Pinball Framework (MPF)** for all game software
- **FAST Pinball Neuron Modern Platform** electronics (Phase 6+)
- **CPR reproduction playfield** (Phase 6+)
- **Full RGB LED lighting** throughout
- **Original chimebox** with MPF-controlled coil pulses
- **New replacement mechanisms** from Marco Specialties

See [`docs/plan.md`](docs/plan.md) for the full implementation plan.

---

## Software-First Development (Phases 1–5)

All game logic is built and tested in MPF's **virtual platform** before any hardware is purchased. MPF simulates switches, coils, LEDs, and displays entirely in software.

### Requirements

- **Python 3.12.x** — required for MPF 0.57.4 (`Requires-Python: >=3.8,<3.13`)
- **MPF 0.57.4** — installed in `.venv`

> **Note on MPF versions:** The original plan targeted MPF 0.80, which requires Python 3.10+
> and uses the Godot GMC media controller. This repo uses MPF 0.57.4 (supports Python 3.8–3.12,
> uses Kivy MC). All game YAML configs are compatible with both versions. See
> [`docs/adr.md`](docs/adr.md) (ADR-002) for the full rationale.

### Setup

```bash
# Create and activate virtual environment (requires Python 3.12.x)
py -3.12 -m venv .venv
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate     # Mac/Linux

# Install MPF 0.57.4 and dependencies
pip install mpf==0.57.4 mpf-monitor pytest pytest-timeout

# To use MPF 0.80 instead (requires Python 3.10+):
# pip install mpf --pre
```

### Running MPF in Virtual Mode

```bash
# From the repo root:
.\.venv\Scripts\python.exe -m mpf machine -x
```

### Keyboard Controls (Virtual Play-Testing)

| Key | Switch |
|-----|--------|
| Z | Left flipper |
| / | Right flipper |
| 1 | Start button |
| 5 | Coin insert |
| Space | Plunger lane |
| Q W E R | Top lanes 1–4 |
| T Y | Stand-up targets 5, 6 |
| U | Right return lane (ball 7) |
| I | 8-ball pad target |
| O | Spinner |
| P | Star rollover (candy cane) |
| A S D | Pop bumpers (left, right, top) |
| F G | Slingshots (left, right) |
| H J | Left outlane, Kickback lane |
| K | Drain |
| L | Tilt |

### MPF Monitor (Interactive Playfield UI)

MPF Monitor provides a graphical view of your playfield with clickable switches, lights, and coils — useful for visual play-testing without physical hardware.

```bash
# Install MPF Monitor (one time)
.\.venv\Scripts\pip.exe install mpf-monitor

# Terminal 1 — start MPF in virtual mode
.\.venv\Scripts\python.exe -m mpf machine -x

# Terminal 2 — start the monitor (connects to the running MPF instance)
.\.venv\Scripts\python.exe -m mpf monitor machine
```

> Both terminals must be running simultaneously. Start MPF first, then launch the monitor in a second terminal.

### Running Tests

```bash
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py -v
```

---

## Machine Folder Structure

```
machine/
├── config/
│   ├── config.yaml       # Main machine config (hardware: virtual)
│   ├── switches.yaml     # All 26 switch definitions
│   ├── coils.yaml        # All 15 coil/driver definitions
│   ├── lights.yaml       # All RGB LED definitions
│   ├── displays.yaml     # Display config
│   └── sound.yaml        # Audio config
├── modes/
│   ├── attract/          # Attract mode (light show, press start)
│   ├── base/             # Base game (scoring, ball collection, chimes)
│   ├── skill_shot/       # Skill shot (active on ball launch)
│   ├── bonus/            # End-of-ball bonus count-up
│   ├── rack_complete/    # Rack completion (all 8 balls)
│   ├── kickback/         # Kickback / spinner lit state
│   └── bonus_mult/       # Star rollover multiplier progression
├── shows/
│   ├── attract_lights.yaml    # Attract cycling color show
│   ├── rack_complete_show.yaml
│   └── bonus_collect.yaml
├── sounds/               # Audio assets (placeholder — add WAV files)
├── tests/
│   └── test_eight_ball.py    # 25 automated MPF unit tests
└── keyboard.yaml         # Keyboard-to-switch mappings
```

---

## Game Rules Summary

Based on original Bally Eight Ball (1977) rules:

- **4 players**, 3 balls each
- **Pool ball collection:** Players 1 & 3 collect balls 1–8; Players 2 & 4 collect balls 9–15 + 8-ball
- **3,000 points** per ball collected
- **8-ball** only collectable after balls 1–7 are all collected
- **Rack completion:** All 8 balls → 24,000 base bonus locked in for remaining balls; ball tracking resets
- **Kickback:** Hit 8-ball pad to light kickback + spinner. Kickback saves ball from left outlane (turns off both)
- **Spinner:** 1,000/spin when lit, 100/spin when unlit
- **Star rollover (candy cane):** Hits 1–2 = score; hit 3 = 2X; hit 4 = 3X; hit 5 = 5X; hit 6 = Extra Ball; hit 7+ = 5,000 each
- **End-of-ball bonus:** (balls × 3,000) × multiplier + locked base bonus. Multiplier resets each ball.
- **Skill shot:** Ball 1 → hit lane 4. Subsequent balls → hit uncollected lane. Awards 5,000 pts.

---

## Hardware (Phase 6+)

See [`docs/plan.md`](docs/plan.md) — Phase 6 onwards covers:
- CPR reproduction playfield
- FAST Pinball Neuron electronics
- Marco Specialties mechanisms
- Original Bally chimebox
- RGB LED installation and wiring

**To switch from virtual to real hardware:** Change one line in `machine/config/config.yaml`:
```yaml
# Change:
platform: virtual
# To:
platform: fast
```
Then add FAST physical addresses to all switches, coils, and lights.
