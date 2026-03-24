# Architecture Decision Records

**Project:** Bally Eight Ball (1977) Pinball Rebuild  
**Framework:** Mission Pinball Framework (MPF)  
**Hardware target:** FAST Pinball Neuron Modern Platform

Each record documents a significant decision made during the software build phases (1–5). Records are numbered in the order they were made and do not change once accepted — superseded decisions get a new record.

---

## ADR-001: Software-First Development Strategy

**Status:** Accepted

**Context:**  
Rebuilding a physical pinball machine requires significant hardware investment (CPR playfield, FAST Neuron electronics, mechanisms, wiring). Defects in game logic discovered after hardware is assembled are expensive and time-consuming to fix.

**Decision:**  
Build and fully test all game software in MPF's virtual platform before purchasing any hardware. MPF's `platform: virtual` simulates switches, coils, LEDs, and displays entirely in software. Physical hardware platform (`platform: fast`) is a single config-line change.

**Consequences:**
- All 7 modes and 25 unit tests validated in software before any spending
- Hardware integration (Phase 6+) starts from a tested, working codebase
- No need for hardware to iterate on rules, scoring, or mode logic
- Keyboard mappings (`keyboard.yaml`) enable manual play-testing without hardware
- MPF Monitor provides a visual playfield overlay for virtual debugging

---

## ADR-002: MPF Version Selection (0.57.4 instead of 0.80)

**Status:** Accepted — supersedes original plan target of MPF 0.80

**Context:**  
The original plan specified MPF 0.80 with the Godot GMC media controller. MPF 0.80 requires Python 3.10 or higher.

**Constraint:** Only **Python 3.9.13** is installed on the development machine. The `py` launcher confirms this is the only available Python installation. MPF 0.57.4's official metadata specifies `Requires-Python: >=3.8,<3.13`, making 3.9.13 fully supported.

**Decision:**  
Install **MPF 0.57.4** (the latest stable release in the 0.57.x line) using the existing Python 3.9.13. Do not install a new Python version during the software build phases.

**Consequences:**
- MPF 0.57.4 uses the **Kivy MC** (not Godot GMC) for the media controller
- All game YAML config syntax is compatible between 0.57.4 and 0.80 (core game logic is the same)
- To upgrade to MPF 0.80 later: install Python 3.10+, create a new venv, `pip install mpf --pre`
- `#config_version=6` and `#show_version=6` are correct for MPF 0.57.4
- The `platform: virtual` and `platform: fast` targets work identically in both versions

> ⚠️ **Python version note:** MPF 0.57.4 supports Python 3.8 through 3.12 (not just 3.9). If any Python in the 3.8–3.12 range is available, MPF 0.57.4 will install and run on it. The plan's original Python 3.14 target does not exist as a stable release and was not pursued.

---

## ADR-003: Config File Version (config_version=6)

**Status:** Accepted

**Context:**  
MPF uses a `#config_version=N` header to validate config files and reject stale configs.

**Decision:**  
All machine config files use `#config_version=6`. All show files use `#show_version=6`. These are the correct values for MPF 0.57.4.

**Consequences:**
- MPF will refuse to load files with `#config_version=5` (the 0.56.x value)
- If upgrading to MPF 0.80, config version may need to change — check MPF release notes

---

## ADR-004: Odd/Even Player Ball Numbering Event Architecture

**Status:** Accepted

**Context:**  
The original Bally Eight Ball rules give players 1 & 3 the "solids" (balls 1–8) and players 2 & 4 the "stripes" (balls 9–15 + 8-ball). Both sets of players share the same physical switches. The game must route the same physical switch hit to the correct ball slot depending on which player is active.

**Attempted approach (rejected):** Parameterized events (`eight_ball_collect_ball{number=1}`) — MPF 0.57.4 does not support parameterized event names in conditions; they fail Python AST parsing silently.

**Decision:**  
Use **named per-ball events** with player parity in the event name:
- `ball_1_collected_p_odd` — posted when `s_lane_1` fires and current player is 1 or 3
- `ball_1_collected_p_even` — posted when `s_lane_1` fires and current player is 2 or 4
- Both events set the same player variable: `ball_1_collected = true`

Each of the 7 ball switches generates two named events (one per player parity). The `event_player` conditions use `player.number==1 or player.number==3` and `player.number==2 or player.number==4`.

**Consequences:**
- Event names are verbose but completely unambiguous
- Double-collection is prevented by a `{not player.ball_X_collected}` guard in `variable_player`
- This pattern handles 2-player, 3-player, and 4-player games correctly
- 14 named events total (7 balls × 2 parities) defined in `base.yaml`

---

## ADR-005: Player Variable References in Event Conditions

**Status:** Accepted

**Context:**  
MPF provides multiple ways to reference the current player's variables. Two syntaxes appear similar but behave differently inside event condition strings:

- `player.variable_name` — correct in mode-level `event_player` conditions
- `current_player.variable_name` — valid at machine-level widget display text but **fails silently** in mode event conditions

**Decision:**  
Always use `player.variable_name` in event_player condition strings. Never use `current_player.variable_name` in conditions.

**Consequences:**
- `skill_shot.yaml` had 7 occurrences of `current_player.ball` that caused skill shot conditions to silently fail on balls 2 and 3. All were fixed to `player.ball`.
- This is a runtime silent failure — MPF does not log a warning; the condition simply never matches.
- `machine.current_player` IS correct for display widget text interpolation (not conditions)

---

## ADR-006: No Duplicate Top-Level YAML Keys

**Status:** Accepted

**Context:**  
MPF config files are parsed by `ruamel.yaml`, which raises `DuplicateKeyError` if the same top-level key appears more than once in a file (e.g., two `variable_player:` blocks).

**Decision:**  
Each YAML section type (`event_player:`, `variable_player:`, `light_player:`, `sound_player:`, `coil_player:`) appears **exactly once** per file. All entries for that section type are merged into that single block.

**Consequences:**
- All mode files have a single `event_player:` block, a single `variable_player:` block, etc.
- When adding new entries, always find and extend the existing section rather than adding a new top-level key
- This is enforced at parse time — violations fail immediately and loudly

---

## ADR-007: Delayed Events Use Pipe Syntax

**Status:** Accepted

**Context:**  
MPF 0.57.4 event_player supports delayed event posting. Two syntaxes exist:

- `event_name|2s:` — pipe-delimited delay suffix (correct)
- Nested `- event:\n  delay: 2s` — **not valid** in MPF 0.57.4 event_player

**Decision:**  
Use pipe syntax for all delayed event posts: `event_name|2s:` as the YAML key.

**Consequences:**
- Rack complete celebration delay: `eight_ball_rack_complete|2s:`
- Bonus mode start delay: `ball_will_end|1s:`
- Delays are expressed in the event name string, not as a nested property

---

## ADR-008: Scoring via variable_player, Not scoring:

**Status:** Accepted

**Context:**  
MPF 0.57.4 does not have a `scoring:` top-level config section. Earlier MPF documentation (and the original plan) referenced this section.

**Decision:**  
All point scoring is done via `variable_player:` targeting `score:`:
```yaml
variable_player:
  ball_1_collected_p_odd{not player.ball_1_collected}:
    score: 3000
```

**Consequences:**
- `score` is a built-in player variable in MPF; `variable_player` can add to it directly
- Conditional scoring uses the `{condition}` suffix on the event key
- This is compatible with both MPF 0.57.4 and 0.80

---

## ADR-009: Sound System Nesting

**Status:** Accepted

**Context:**  
MPF 0.57.4 requires sound track configuration nested inside `sound_system:`. A flat `sound_tracks:` top-level key is not valid.

**Decision:**  
```yaml
sound_system:
  tracks:
    sfx:
      type: standard
    music:
      type: standard
      simultaneous_sounds: 1
```

**Consequences:**
- All audio references in mode files use track names `sfx` and `music`
- `sound_player:` entries specify `track: sfx` or `track: music`

---

## ADR-010: Attract Mode as a Regular Mode

**Status:** Accepted

**Context:**  
`attract_mode:` is not a valid top-level machine config key in MPF 0.57.4. Attract is treated as a regular game mode.

**Decision:**  
Attract behavior lives in `machine/modes/attract/config/attract.yaml` as a standard mode. It starts automatically because MPF's game controller starts attract by default when no game is running.

**Consequences:**
- Attract mode config: `mode: priority: 10, start_events: machine_reset_phase_3`
- Light shows, music, and slide displays all use standard mode YAML sections
- No special attract-specific config key is needed or valid

---

## ADR-011: End-of-Ball Bonus via MPF Bonus Plugin

**Status:** Accepted

**Context:**  
The Eight Ball bonus formula is: `(balls_collected × 3,000 + base_bonus_locked) × bonus_multiplier`. This requires counting variable-length player variables and applying a multiplier.

**Decision:**  
Use MPF's built-in **bonus plugin** (`mode_settings:` structure in `bonus.yaml`):
```yaml
mode_settings:
  keep_multiplier: false
  bonus_entries:
    - event: bonus_start
      score: 3000
      player_score_entry: balls_collected
    - event: bonus_start
      score: 1
      player_score_entry: base_bonus_locked
```

**Consequences:**
- `keep_multiplier: false` resets bonus_multiplier to 1 after each ball's bonus
- `base_bonus_locked` accumulates across balls and racks — it is never reset by the bonus plugin
- The bonus plugin handles its own count-up animation and event sequencing
- `balls_collected` resets to 0 on rack completion; `base_bonus_locked` does not

---

## ADR-012: Rack Complete Logic — Intermediate Event Pattern

**Status:** Accepted

**Context:**  
The 8-ball target (`s_eight_ball_target`) should only collect the 8-ball (completing the rack) when all 7 prior balls are collected. MPF event conditions can guard this, but the multi-condition string becomes unwieldy when embedded directly in a coil_player or rack_complete mode start event.

**Decision:**  
Use an intermediate event `ball_8_collected_ready` as a signal that passes the 7-ball guard. The switch fires this event only when all 7 are collected. Downstream listeners respond to `ball_8_collected_ready` without needing to re-check the condition:
```
s_eight_ball_target{all 7 collected} → ball_8_collected_ready
ball_8_collected_ready → eight_ball_rack_complete
eight_ball_rack_complete → rack_complete mode starts
```

**Consequences:**
- `rack_complete.yaml` resets all 7 ball flags, locks in 24,000 base bonus, increments `rack_count`
- The intermediate event is an internal signal — nothing outside the base mode posts it
- A previously redundant 7-ball condition on `ball_8_collected_ready → eight_ball_rack_complete` was removed (ADR applies the guard upstream)

---

## ADR-013: Kickback Architecture — Flag-Based State

**Status:** Accepted

**Context:**  
The kickback mechanism saves the ball from the left outlane when active. It must track two related states: `kickback_active` (coil can fire) and `spinner_lit` (spinner scores 1,000 instead of 100). Both activate together and deactivate together.

**Decision:**  
Use **player variable flags** rather than MPF's built-in enable/disable logic:
- `kickback_active: false` and `spinner_lit: false` are player variable defaults
- Hit `s_eight_ball_target` (8-ball pad) → sets both to `true`, lights LEDs
- Hit `s_left_outlane` when `kickback_active==true` → fires `c_kickback` coil via `coil_player:`, posts `kickback_fired`, sets both flags back to `false`
- Hit `s_left_outlane` when `kickback_active==false` → normal drain (no coil fire)

**Consequences:**
- State survives mode restarts within the same ball (flags are player variables)
- `kickback_fired` event is the canonical signal that the kickback coil fired — used in tests via `assertEventCalled("kickback_fired")`
- Spinner scoring reads `player.spinner_lit` in `base.yaml` variable_player conditions

---

## ADR-014: MPF Test Framework Configuration

**Status:** Accepted

**Context:**  
MPF's `MpfTestCase` uses Python snake_case method names (`get_machine_path`, `get_config_file`) to locate the machine folder. The original test file used camelCase overrides (`getMachinePath`, `getConfigFile`) which Python never dispatched — the framework silently fell back to its own defaults, loading a null test machine instead of the actual game machine.

Additionally, `get_machine_path()` must return an **absolute path**. Relative paths resolve against MPF's own package root, not the repo root.

**Decision:**
```python
def get_machine_path(self):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_config_file(self):
    return "config.yaml"
```
`__file__` is `machine/tests/test_eight_ball.py`; `..` resolves to `machine/` — the MPF machine root.

**Consequences:**
- All 25 tests now load and test the actual Eight Ball machine config
- `hit_and_release_switch()`, `advance_time_and_run()`, and `assertEventCalled()` are the canonical test helpers — raw `process_switch()` calls leave switches stuck active and must not be used
- `_start_game(players=N)` and `_drain_ball()` helpers use these correctly

---

## ADR-015: Number Fields Required on All Devices (Virtual Platform)

**Status:** Accepted

**Context:**  
MPF 0.57.4 validates that all switches, coils, and lights have a `number:` field, even when `platform: virtual` is set and no real hardware addresses are needed.

**Decision:**  
All switch, coil, and light definitions include a `number:` field. For virtual mode, the value is an arbitrary string (matching the device name is a readable convention):
```yaml
switches:
  s_lane_1:
    number: s_lane_1
```

**Consequences:**
- When transitioning to hardware (Phase 6), replace each `number:` value with the physical FAST Neuron board address (e.g., `0-0`, `0-1`, etc.)
- Virtual mode accepts any string value for `number:` without validation

---

---

## ADR-016: MPF 0.57.4 Is the Latest Stable Release — ADR-002 Framing Superseded

**Status:** Accepted — supersedes the *rationale* (not the conclusion) of ADR-002

**Context:**  
ADR-002 documented choosing MPF 0.57.4 as a *constraint-driven fallback* because Python 3.9.13
was the only available Python and MPF 0.80 required 3.10+. This framing implied 0.57.4 was a
temporary workaround until 0.80 was reachable.

As of January 19, 2026, **MPF 0.57.4 is the latest stable release on PyPI**. MPF 0.80 remains
in beta. Per non-negotiable project constraints, the latest stable MPF must always be used.
MPF 0.57.4 satisfies this constraint — it is not a workaround.

The Python constraint remains real but must be reframed: `>=3.8,<3.13` means the *most recent
stable Python supported* is **Python 3.12.x**. Python 3.9.13 (currently installed) satisfies the
lower bound but not the non-negotiable requirement to use the *most recent stable* supported
Python. Python must be upgraded to 3.12.x.

**Decision:**
- Confirm MPF 0.57.4 as the correct version selection — it IS the latest stable, not a fallback
- Python 3.9.13 must be upgraded to **Python 3.12.x** before the next venv rebuild to satisfy
  the non-negotiable "most recent stable Python" constraint
- After upgrade: delete `.venv`, recreate with Python 3.12, reinstall `mpf==0.57.4`
- Kivy MC remains the media controller for 0.57.4 (Godot GMC applies only to 0.80 beta)
- When MPF 0.80 reaches stable, open a new ADR for the upgrade decision

**Consequences:**
- ADR-002's *conclusion* (use 0.57.4) is correct and unchanged
- ADR-002's *framing* (0.57.4 as a workaround) is obsolete — do not use it as justification
- All existing YAML config files remain valid — no syntax changes needed for this ADR
- All 25 automated tests remain valid
- The Python upgrade is a prerequisite for the next venv rebuild; existing `.venv` (3.9.13)
  may be used for current development until a rebuild is needed

---

## Future Decisions Pending (Phase 6+)

| Decision | Status |
|---|---|
| FAST Neuron board layout and switch/coil address mapping | Pending hardware procurement |
| Godot GMC vs Kivy MC for display on hardware | Pending Python upgrade to 3.10+ |
| Audio file format (WAV vs OGG) and chimebox MIDI interface | Pending hardware |
| RGB LED chain topology (number of segments, FAST LED controller) | Pending hardware |
| MPF version upgrade to 0.80 | Blocked on Python 3.10+ installation |
