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

- **Python 3.9–3.12** — required for MPF 0.57.4 (`Requires-Python: >=3.8,<3.13`; 3.9+ recommended on Windows for audio support)
- **MPF 0.57.4** — installed in `.venv`
- **MPF Monitor 0.57.2** — optional graphical playfield UI (requires PyQt6)
- **Pillow 10.4.0** — required by MPF Monitor (see [Pillow version conflict](#pillow-version-conflict) below)

> **Note on MPF versions:** The original plan targeted MPF 0.80, which requires Python 3.10+
> and uses the Godot GMC media controller. This repo uses MPF 0.57.4 (supports Python 3.8–3.12,
> uses Kivy MC). All game YAML configs are compatible with both versions. See
> [`docs/adr.md`](docs/adr.md) (ADR-002) for the full rationale.

### Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate     # Mac/Linux

# Install MPF 0.57.4
pip install mpf==0.57.4

# Install MPF Monitor (graphical playfield UI)
pip install mpf-monitor

# Fix the Pillow version conflict (see note below)
pip install Pillow==10.4.0

# To use MPF 0.80 instead (requires Python 3.10+):
# pip install mpf --pre
```

#### Pillow Version Conflict

MPF 0.57.4 pins `Pillow==9.5.0` (exact match), but MPF Monitor 0.57.2 requires `Pillow>=10.4.0`.
These constraints are mutually exclusive. The fix is to install `Pillow==10.4.0` and then relax
MPF's metadata so `pkg_resources` doesn't reject the version at runtime:

```bash
# After installing all packages, patch MPF's metadata to accept Pillow 10.4.0:
# Find the METADATA file (adjust path for your OS):
#   Windows: .venv\Lib\site-packages\mpf-0.57.4.dist-info\METADATA
#   Linux/Mac: .venv/lib/python3.X/site-packages/mpf-0.57.4.dist-info/METADATA
#
# Change this line:
#   Requires-Dist: Pillow==9.5.0
# To:
#   Requires-Dist: Pillow>=9.5.0
```

On Windows, you can do this from the repo root with PowerShell:

```powershell
(Get-Content .\.venv\Lib\site-packages\mpf-0.57.4.dist-info\METADATA) -replace 'Requires-Dist: Pillow==9\.5\.0', 'Requires-Dist: Pillow>=9.5.0' | Set-Content .\.venv\Lib\site-packages\mpf-0.57.4.dist-info\METADATA
```

> **⚠️ This patch must be re-applied any time MPF is reinstalled or upgraded.**
> MPF works correctly with Pillow 10.4.0 in virtual mode — the `==9.5.0` pin is an upstream
> packaging issue between `mpf` and `mpf-monitor`.

### Running MPF in Virtual Mode

```bash
# From the repo root (smart virtual simulates ball movement):
.\.venv\Scripts\python.exe -m mpf machine -X -b
```

> **Flag reference:**
> - **`-X`** (uppercase) — enables the **smart virtual** platform, which simulates balls moving
>   through trough, plunger, and drain devices automatically. Lowercase `-x` is the basic
>   virtual platform where switches are completely manual — the trough won't have balls,
>   so the game can't start unless you manually toggle every switch yourself.
> - **`-b`** — skips the outbound BCP connection to the Media Controller (MPF-MC), which we
>   don't use. Without `-b`, MPF blocks waiting for a connection on port 5050. The BCP
>   **server** on port 5051 still starts regardless of `-b`, so the MPF Monitor can connect.

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

MPF Monitor provides a graphical view of your playfield with clickable switches, lights, and coils — useful for visual play-testing without physical hardware. It connects to a running MPF instance via BCP (Backbox Control Protocol).

> **Prerequisites:** MPF Monitor must be installed and the [Pillow version conflict](#pillow-version-conflict) resolved before first use. See [Setup](#setup) above.

```bash
# Terminal 1 — start MPF in smart virtual mode (from the repo root)
.\.venv\Scripts\python.exe -m mpf machine -X -b

# Terminal 2 — start the monitor (also from the repo root)
.\.venv\Scripts\python.exe -m mpf monitor machine
```

> **Important:** Both terminals must be running simultaneously. Start MPF first, then launch
> the monitor in a second terminal. Both commands must be run from the **repo root**
> (`eight-ball-pinball/`), not from inside the `machine/` folder. The `machine` argument
> tells MPF where to find the config — without it, MPF looks in the current directory and fails.
> The `-b` flag only disables the outbound MC connection; the BCP server on port 5051 still
> starts and the monitor connects to it.

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
