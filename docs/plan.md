# Eight Ball Pinball Rebuild — Implementation Plan

## Overview

Rebuild a Bally Eight Ball (1977) pinball machine using a **CPR reproduction playfield**, **FAST Pinball Neuron Modern Platform** electronics, **Mission Pinball Framework (MPF)** software, **full RGB LED lighting**, **modern RGB 7-segment displays**, an **original chimebox with supplemental electronic audio**, and **new replacement mechanisms** sourced from Marco Specialties.

This is NOT a restoration with original parts. This is a ground-up rebuild using the original game's rules, layout, and aesthetics with modern hardware throughout.

### Strategy: Software-First Development

**Build and fully test the complete game software in MPF's virtual environment on your PC before purchasing any hardware.** MPF supports a "virtual" hardware platform that simulates switches, coils, LEDs, and displays entirely in software. Combined with keyboard mappings and MPF Monitor, you can play-test and debug the entire game without a physical machine. This approach:
- Validates all game rules and logic before spending money on hardware
- Lets you iterate quickly on modes, shows, and scoring
- Produces a complete, tested MPF config ready to drop onto real hardware when you build
- Uses MPF Monitor for visual switch/device state and the keyboard for simulated play

---

## Phase 1: MPF Project Setup & Virtual Environment

### 1.1 — Install MPF on Development PC
- Install Python 3.14
- Create a Python virtual environment for the project
- Install MPF 0.80 (latest): `pip install mpf --pre`
- Install MPF Monitor 0.57.2 for visual debugging
- Install Godot Editor 4.6 + MPF-GMC 0.1.6 for media controller

### 1.2 — Create Machine Folder Structure
Create the MPF machine folder structure in this repository:

```
eight-ball-pinball/
├── machine/                    # MPF machine root
│   ├── config/
│   │   ├── config.yaml         # Main machine config
│   │   ├── switches.yaml       # All switch definitions
│   │   ├── coils.yaml          # All coil/driver definitions
│   │   ├── lights.yaml         # All LED definitions
│   │   ├── displays.yaml       # Display configuration
│   │   └── sound.yaml          # Audio configuration
│   ├── modes/
│   │   ├── attract/
│   │   │   └── config/attract.yaml
│   │   ├── base/
│   │   │   └── config/base.yaml
│   │   ├── skill_shot/
│   │   │   └── config/skill_shot.yaml
│   │   ├── bonus/
│   │   │   └── config/bonus.yaml
│   │   └── ...
│   ├── shows/
│   │   ├── attract_lights.yaml
│   │   ├── bonus_collect.yaml
│   │   └── ...
│   ├── sounds/
│   ├── tests/
│   │   └── test_eight_ball.py
│   └── keyboard.yaml           # Keyboard-to-switch mappings for virtual play
├── manuals/
│   └── eight-ball-rules.md
├── docs/
└── README.md
```

### 1.3 — Configure Virtual Hardware Platform
- Set `hardware: platform: virtual` in config.yaml for development
- Later swap to `platform: fast` when connecting real hardware (one-line change)
- Define all switches, coils, and lights with descriptive names (physical addresses added later)

### 1.4 — Set Up Keyboard Mappings
Map keyboard keys to simulate every switch for virtual play-testing:
- Flipper buttons (e.g., Left Shift / Right Shift)
- Start button, coin insert
- Top lane rollovers (1-4 keys)
- Stand-up targets (5, 6 keys)
- 8-ball pad target, spinner, star rollover
- Pop bumper, slingshot triggers
- Return lane (#7), outlane, kickback lane
- Trough/drain, plunger launch

---

## Phase 2: Machine Configuration (Virtual)

### 2.1 — Define All Switches
Map every switch in the game (names only for virtual mode; FAST addresses added in Phase 6):
- **Top lanes:** `s_lane_1`, `s_lane_2`, `s_lane_3`, `s_lane_4`
- **Stand-up targets:** `s_target_5`, `s_target_6`
- **Return lane:** `s_return_lane_7`
- **8-ball pad:** `s_eight_ball_target`
- **Spinner:** `s_spinner`
- **Star rollover:** `s_star_rollover` (candy cane top)
- **Pop bumpers:** `s_pop_bumper_left`, `s_pop_bumper_right`, `s_pop_bumper_top`
- **Slingshots:** `s_slingshot_left`, `s_slingshot_right`
- **Outlane:** `s_left_outlane`
- **Kickback lane:** `s_kickback_lane`
- **Trough:** `s_trough_1` (single ball trough)
- **Outhole:** `s_outhole`
- **Plunger lane:** `s_plunger_lane`
- **Cabinet:** `s_start_button`, `s_coin`, `s_tilt`, `s_slam_tilt`

### 2.2 — Define All Coils/Drivers
- **Flippers:** `c_flipper_left`, `c_flipper_right`
- **Pop bumpers:** `c_pop_bumper_left`, `c_pop_bumper_right`, `c_pop_bumper_top`
- **Slingshots:** `c_slingshot_left`, `c_slingshot_right`
- **Kickback:** `c_kickback`
- **Trough/drain:** `c_outhole_eject`, `c_trough_eject`
- **Chimebox:** `c_chime_high`, `c_chime_mid`, `c_chime_low` (+ optional `c_chime_extra`)
- **Knocker:** `c_knocker`

### 2.3 — Define All LEDs
- **Pool ball inserts:** `l_ball_1` through `l_ball_8` (or `l_ball_9` through `l_ball_15` for even players — same physical LEDs, aliased)
- **Kickback indicator:** `l_kickback`
- **Spinner indicator:** `l_spinner_lit`
- **Bonus multiplier indicators:** `l_mult_2x`, `l_mult_3x`, `l_mult_5x`
- **Extra ball indicator:** `l_extra_ball`
- **Candy cane value indicators:** `l_candy_1`, `l_candy_2`
- **Top lane lit indicators:** `l_lane_2_lit`, `l_lane_3_lit`
- **Pop bumper LEDs:** `l_pop_left`, `l_pop_right`, `l_pop_top`
- **GI zones:** `l_gi_playfield`, `l_gi_backbox` (groups of LEDs)

### 2.4 — Configure Machine Devices
- **Flippers:** Hardware rules for instant flipper response
- **Pop bumpers:** Autofire coils (switch → coil, no software delay)
- **Slingshots:** Autofire coils
- **Kickback:** Software-controlled coil (only fires when enabled)
- **Trough:** Ball device with opto switches, eject coil
- **Plunger lane:** Ball device for skill shot detection
- **Ball count:** 3 balls per game (original spec)

### 2.5 — Configure Displays (Virtual)
- Virtual display window showing simulated RGB 7-segment scores
- 4-player score displays + credit/ball-in-play display
- Will map to FAST RGB 7-segment hardware later

### 2.6 — Configure Sound (Virtual)
- MPF sound system with virtual audio output to PC speakers
- Multi-track: background music, SFX, voice
- Chimebox events logged/simulated (actual chime coils fire on real hardware)
- Source or create sound effects for: spinner, pop bumpers, slingshots, targets, scoring, bonus

---

## Phase 3: Game Logic & Modes (The Core Software Work)

### 3.1 — Attract Mode
- Light show cycling through RGB colors on all LEDs
- Score display cycling / animation
- "Press Start" prompt on display
- Start game on `s_start_button` + coin credit

### 3.2 — Base Game Mode
- 4-player support
- Players 1&3 use pool balls 1-8; players 2&4 use pool balls 9-15 + 8-ball
- Per-player tracking of which pool balls have been collected (player variables)
- Ball tracking: 3000 points per ball collected
- Bonus tracking: accumulated bonus = (balls collected × 3000) × multiplier
- Base locked-in bonus from completed racks (persists across balls)

### 3.3 — Skill Shot Mode
- Activate on ball launch (ball leaves plunger lane)
- Ball 1: target is lane 4
- Subsequent balls: target is whichever lane number still needed
- If all 4 top lanes collected: target is whichever of lane 2 or 3 is lit for multiplier advance
- Award bonus points for successful skill shot
- Deactivate when ball hits any playfield switch (not a top lane)

### 3.4 — Pool Ball Collection Logic
- Top lanes 1-4 → collect corresponding ball (or 9-12 for even players)
- Stand-up target left → ball 5 (or 13)
- Stand-up target right → ball 6 (or 14)
- Right return lane → ball 7 (or 15)
- 8-ball pad target → ball 8 ONLY if balls 1-7 all collected
- Each ball collected: score 3000, light corresponding insert LED

### 3.5 — Rack Completion Mode
- Monitor when all 8 balls collected
- On rack completion:
  - Score bonus (rack value)
  - Lock in 24,000 base bonus for remaining balls in game
  - Reset ball tracking for next rack
  - Increment rack counter
- Multiple racks can be completed across balls in a game

### 3.6 — Spinner & 8-Ball Pad Mode
- 8-ball pad target hit:
  - Lights kickback (`l_kickback` on)
  - Lights spinner (`l_spinner_lit` on)
  - Also handles ball 8 collection when rack conditions met
- Spinner scoring:
  - When lit: higher point value per spin
  - When unlit: lower point value per spin

### 3.7 — Kickback Mode
- Kickback state: lit or unlit (per-player)
- When ball enters left outlane AND kickback is lit:
  - Fire `c_kickback` coil to save the ball
  - Turn OFF kickback (`l_kickback` off)
  - Turn OFF spinner lit (`l_spinner_lit` off)
- Must hit 8-ball pad target again to relight both

### 3.8 — Bonus Multiplier Mode
- Track candy cane star rollover hits (per-player):
  - Hit 1: Advance candy cane score value (level 1)
  - Hit 2: Advance candy cane score value (level 2)
  - Hit 3: Multiplier → **2X**
  - Hit 4: Multiplier → **3X**
  - Hit 5: Multiplier → **5X**
  - Hit 6: **Extra Ball**
  - Hit 7+: Score 5000 points each
- Alternative advance: ball through lit lane 2 or 3 (after all 4 top lanes completed)
- Lane change: which of lane 2/3 is lit alternates on any switch hit

### 3.9 — End-of-Ball Bonus Mode
- On ball drain:
  - Count up collected balls × 3000
  - Multiply by bonus multiplier
  - Add locked-in base bonus from completed racks
  - Animate bonus count-up on display with LED show
  - Fire chimebox chimes during count-up
- Bonus multiplier does NOT carry over between balls (resets to 1X)
- Collected balls within current rack DO carry over between balls

### 3.10 — Extra Ball & Match
- Extra ball logic when awarded via bonus multiplier progression
- End-of-game match number display

### 3.11 — Chimebox Event Mapping
- Define MPF events that trigger chimebox coil pulses:
  - `c_chime_high`: 1,000-point scoring events
  - `c_chime_mid`: 100-point scoring events
  - `c_chime_low`: 10-point scoring events
  - Bonus count-up: rapid chime sequence
  - Game start: chime pattern
- In virtual mode: log chime events; on real hardware: fire coil pulses

---

## Phase 4: LED Shows & Audio (Virtual Testing)

### 4.1 — LED Shows
- **Attract mode:** Cycling color patterns across all LEDs
- **Ball collection:** Flash corresponding insert LED when ball collected
- **Kickback lit:** Pulsing glow on kickback LED
- **Spinner lit:** Steady glow on spinner indicator
- **Bonus countdown:** Sequential LED flash during bonus collection
- **Rack completion:** Celebration show (all LEDs flash)
- **Multiplier advance:** Flash multiplier indicator LEDs
- **GI themes:** Ambient color schemes for different game states

### 4.2 — Sound Design
- Source/create sound effects:
  - Spinner clicks (per revolution)
  - Pop bumper hits
  - Slingshot hits
  - Target hits (stand-up, 8-ball pad)
  - Rollover switches
  - Ball drain
  - Bonus count-up tones
  - Extra ball awarded
  - Rack completion fanfare
- Background music tracks (if desired)
- Sound pools for variety (multiple sounds per event)

### 4.3 — Display Slides & Widgets
- Score display formatting for 7-segment style
- Player-up indicators
- Ball-in-play display
- Bonus count-up animation
- Match number display
- Tilt warning / tilt display

---

## Phase 5: Automated Testing

### 5.1 — MPF Unit Tests
Write automated tests using MPF's test framework (`test_eight_ball.py`):
- Test ball tracking: collecting each ball lights correct insert
- Test rack completion: all 8 balls → rack complete → bonus locked in
- Test 8-ball gate: cannot collect 8 before 1-7
- Test kickback state: 8-ball pad lights kickback; kickback save turns off kickback + spinner
- Test bonus multiplier progression: star rollover advances correctly
- Test bonus calculation: balls × 3000 × multiplier + base bonus
- Test even/odd player ball numbering
- Test skill shot: correct target detection
- Test spinner scoring: lit vs. unlit values
- Test extra ball award at correct multiplier stage
- Test multi-player game flow

### 5.2 — Virtual Play Testing
- Play full games using keyboard controls + MPF Monitor
- Verify scoring matches original rules document
- Test edge cases (multiple racks, all multiplier stages, tilt)
- Validate LED shows and audio timing

---

## Phase 6: Hardware Acquisition & Physical Build

> **Only begin this phase after software is fully tested and working in virtual mode.**

### 6.1 — Acquire Reproduction Playfield
- **Source:** [Classic Playfield Reproductions (CPR)](https://classicplayfields.com/shop/pinball-playfields/eightball-playfield/) — $699 USD
- 5-layer polyurethane clearcoated, made in USA
- Currently out of stock — join waitlist
- Consider ordering matching **backglass, plastics set, and/or topper** for bundle discounts

### 6.2 — Cabinet & Backbox
- Source a donor Bally cabinet/backbox (any Bally -17 or -35 era) OR build new to Bally standard dimensions
- Strip all original electronics; keep only the wood shell
- Sand, repaint, and apply new decals/artwork if desired

### 6.3 — Acquire Original Chimebox
- Source an original Bally chimebox unit (eBay, pinball parts dealers, swap meets)
- Test chime coils and replace any worn strikers/coils as needed

### 6.4 — FAST Pinball Electronics
Purchase from [FAST Pinball](https://fastpinball.com/products/):
- **FAST Neuron Controller** (FP-CPU-2000) — central hub
- **Raspberry Pi 5** — mounts directly on Neuron (recommended host computer for final machine; use dev PC for development)
- **FAST I/O 3208** (32 switches, 8 drivers)
- **FAST I/O 1616** (16 switches, 16 drivers)
- **FAST Cabinet I/O Board** (cabinet switches, coin door)
- **FP-EXP-0071** Expansion Board (128 LEDs, 4 servos) — playfield lighting
- **FP-EXP-0081** Expansion Board (256 LEDs) — additional LEDs if needed
- **FAST RGB 7-Segment Displays** via Display Bus
- **FAST Smart Power Filter Board** (Neuron version)
- **FAST Smart Fuse Block**
- **FAST Audio Interface**
- **FAST RGB Playfield Insert LEDs**
- **FAST Trough IR Board**
- 48V power supply, 12V power supply

### 6.5 — Playfield Mechanisms (New from Marco Specialties)
Purchase from [Marco Specialties](https://www.marcospecialties.com/control/main):
- 2× flipper assemblies (Bally/Williams style, 3" bats) + coils, EOS switches
- 3× pop bumper assemblies (complete) — replace lamp holders with RGB LED holders
- 2× slingshot assemblies (note: left slingshot has wider/flatter angle unique to Eight Ball)
- 1× kickback assembly + coil
- 1× spinner assembly + switch
- 1× large 8-ball pad target
- 2× stand-up targets (#5, #6)
- 4× top lane rollover switches
- 1× star rollover switch (candy cane top)
- 1× return lane rollover switch (right side)
- Wire guides / lane guides for candy cane horseshoe
- Trough assembly with opto sensors
- Manual plunger assembly (shooter rod, barrel spring, housing, tip)
- Complete rubber ring kit
- Post assemblies, screws, nuts, spacers
- Playfield legs, levelers, leg bolts

### 6.6 — RGB LED Components
- FAST RGB Insert LEDs for all playfield insert positions
- RGB LEDs for pop bumper caps
- RGB LED strips for GI replacement
- Backbox RGB LEDs (Neuron supports 128 built-in)

---

## Phase 7: Wiring & Assembly

### 7.1 — Update MPF Config for Real Hardware
- Change `platform: virtual` → `platform: fast` in config.yaml
- Add FAST board/port physical addresses to all switches, coils, and LEDs
- Configure FAST I/O Loop, Expansion Bus, and Display Bus
- Configure FAST Audio Interface

### 7.2 — Cabinet Wiring
- Mount FAST Neuron in backbox
- Mount Raspberry Pi 5 on Neuron header
- Mount Smart Power Filter Board and Smart Fuse Block
- Wire 48V and 12V power supplies
- Wire Cabinet I/O Board (start button, coin switches, tilt)
- Wire FAST Audio Interface and speakers
- Mount and wire RGB 7-segment displays
- Mount chimebox, wire chime coils to FAST I/O driver outputs

### 7.3 — Playfield Wiring
- Install all mechanisms on CPR reproduction playfield
- Mount FAST I/O boards under playfield
- Wire all switches to I/O board inputs
- Wire all coils/solenoids to I/O board driver outputs
- Mount FAST Expansion board(s) under playfield
- Wire all RGB LEDs to expansion board LED ports
- Complete FAST I/O Loop (CAT-5 ring: Neuron → boards → back to Neuron)
- Connect expansion boards via CAT-5 to expansion bus
- Install rubber rings and posts

### 7.4 — Final Assembly
- Install playfield in cabinet
- Connect playfield to cabinet wiring via playfield interchange connector
- Install plunger, coin door, legs

---

## Phase 8: Hardware Testing & Calibration

### 8.1 — Hardware Verification
- Use MPF's switch test mode to verify every switch
- Test every coil/driver individually (flipper, pop bumper, slingshot, kickback, chimebox)
- Verify LED addressing (every LED lights correct color)
- Test RGB 7-segment display segments
- Test chimebox chime firing
- Test audio output through speakers

### 8.2 — Integration Testing
- Run the same automated test suite from Phase 5 against real hardware
- Use MPF Monitor connected to real machine to visualize game state

### 8.3 — Play Testing & Tuning
- Play full games on the physical machine
- Verify scoring accuracy against original rules
- Tune coil strengths (flipper power, pop bumper force, kickback force)
- Tune LED brightness and color schemes
- Adjust rubber and post positioning for proper ball flow
- Fine-tune chimebox chime timing and coil pulse durations

---

## Parts & Vendor Summary

| Category | Source | Key Items |
|----------|--------|-----------|
| Playfield | [CPR](https://classicplayfields.com/shop/pinball-playfields/eightball-playfield/) | Reproduction Eight Ball playfield ($699) |
| Electronics | [FAST Pinball](https://fastpinball.com/products/) | Neuron Controller, I/O Boards (3208, 1616, Cabinet), Expansion Boards (0071, 0081), Smart Power Filter, Smart Fuse Block, Audio Interface, RGB 7-Segment Displays, RGB Insert LEDs, Trough IR Board |
| Mechanisms | [Marco Specialties](https://www.marcospecialties.com/control/main) | Flippers, pop bumpers, slingshots, kickback, spinner, targets, rollover switches, trough, plunger, rubber kit, posts, hardware |
| Software | [Mission Pinball](https://missionpinball.org/latest/) | MPF 0.80 + MPF-GMC (Godot) — free & open source |
| Chimebox | eBay / pinball swap meets | Original Bally chimebox unit |
| Host Computer | Various | Raspberry Pi 5 (mounts on Neuron) for final machine; dev PC for development |

---

## Notes & Considerations

- **Software-first approach:** All game rules, modes, shows, and audio are developed and tested in MPF virtual mode on your PC. No hardware purchase needed until Phase 6.
- **One-line hardware swap:** Moving from virtual to real hardware is a single config change (`platform: virtual` → `platform: fast`) plus adding physical switch/coil/LED addresses.
- **CPR Playfield is currently out of stock** — join the waitlist early; they may do another run if demand exists.
- **FAST Neuron + Raspberry Pi 5** is the recommended combination for the final machine. The Pi seats directly into the Neuron for power, fan control, and soft shutdown.
- **Chimebox coils** need 25-50V pulse power — verify the 48V supply and FAST driver output can handle the chime coil specs (check coil resistance).
- **MPF 0.80** is the latest version using Godot-based media controller (GMC).
- **The 7-ball problem:** The #7 ball (right return lane) cannot be reliably aimed for — this is by design. The MPF config faithfully replicates this.
- **Even/odd player ball numbering:** Players 1&3 use balls 1-8, players 2&4 use balls 9-15 + 8-ball. MPF player variables handle this per-player.
- **MPF Monitor** is invaluable during development — it shows real-time switch states, device states, player variables, events, and more in a visual GUI.
