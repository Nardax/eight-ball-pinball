# Copilot Instructions — Eight Ball Pinball (MPF)

This is a **Bally Eight Ball (1977) pinball machine rebuild** using Mission Pinball Framework (MPF) 0.57.4. All game logic lives in YAML config files loaded by MPF. There is no application code outside of the test suite.

---

## Versions

[Non Negotiable]
The latest and greatest stable version of MFP must be used at all times.

[Non Negotiable]
The system should be built using the most recent stable version of Python that is supported by the most recent stable version of MFP.

Use the configuration documentation as a resource for understanding how to set up and configure the MPF machine. The documentation provides detailed instructions on how to create and manage the configuration files necessary for running the pinball machine simulation. It covers topics such as defining game modes, setting up player variables, and configuring event handling. Refer to the documentation to ensure that your configuration files are correctly structured and that you are utilizing the features of MPF effectively to create an engaging pinball machine experience. 

Read the manual - Don't guess. The manual is your friend. It contains a wealth of information about the features and capabilities of MPF, as well as best practices for configuring and running your pinball machine simulation. By familiarizing yourself with the manual, you can gain a deeper understanding of how MPF works and how to leverage its features to create a more immersive and enjoyable pinball experience.
https://missionpinball.org/latest/reference/

**Skill reference files** are available in `.github/skills/` — consult these before implementing any MPF feature:
- `event-system.md` — Event types, conditional events, placeholders
- `config-players.md` — All config players and show equivalents
- `shots-and-profiles.md` — Shots, profiles, groups, lane change
- `logic-blocks.md` — Counters, accruals, sequences, state machines
- `mode-design.md` — Mode lifecycle, layering, selection, priority
- `ball-lifecycle.md` — Game/ball start/end flowcharts
- `bonus-and-scoring.md` — Built-in bonus mode, variable_player patterns
- `shows.md` — Show format, show_player, show_tokens
- `mechs-reference.md` — Ball devices, flippers, autofires, mechanisms
- `testing-patterns.md` — MpfTestCase methods, TDD approach
- `cookbook-patterns.md` — Lane change, mode qualification, skillshots

---

## Commands

```bash
# Run MPF in virtual mode (simulated hardware — no physical machine needed)
.\.venv\Scripts\python.exe -m mpf machine -X

# Run all tests
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py -v

# Run a single test
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py::TestEightBall::test_rack_completion_all_8_balls -v

# Validate config loads without errors (run 15s then kill)
.\.venv\Scripts\python.exe -m mpf machine -X -t

# Syntax-check the test file
.\.venv\Scripts\python.exe -m py_compile machine/tests/test_eight_ball.py
```

Python 3.9.13 is the only Python installed on this machine. MPF 0.57.4 requires `>=3.8,<3.13`. The venv is at `.venv/`.

---

## MPF Core Concepts

### Event-Driven Architecture
MPF has **no imperative game loop**. Everything is declarative YAML reacting to events on MPF's event bus. When something happens (switch hit, timer expires, mode starts), an event is posted. Other components (config players, modes, devices) listen for those events and react.

### Event Types
| Type | Behavior | Example |
|---|---|---|
| **Standard** | Fire-and-forget | `ball_started`, `mode_base_started` |
| **Boolean/Request** | Handlers can approve or deny | `request_to_start_game` (credits can deny) |
| **Queue** | Processing waits until all handlers release | `ball_starting`, `ball_ending`, `game_starting` |
| **Relay** | Handlers can modify event parameters | `ball_drain` (ball save removes a ball from drain count) |

### Config Players
Config players make things happen in response to events. In config files they use `(type)_player:` syntax; in show steps they use `(type)s:` syntax:

| Config File | Show Step | Purpose |
|---|---|---|
| `variable_player:` | `variables:` | Scoring and player/machine variables |
| `event_player:` | `events:` | Post additional events |
| `show_player:` | `shows:` | Play/stop shows |
| `light_player:` | `lights:` | Control lights/LEDs |
| `slide_player:` | `slides:` | Display slides |
| `sound_player:` | `sounds:` | Play sounds |
| `coil_player:` | `coils:` | Fire coils |
| `queue_event_player:` | N/A | Post queue events |
| `random_event_player:` | N/A | Post random events |

### Conditional Events
Append `{condition}` to any event name to make it conditional:
```yaml
event_player:
  s_lane_1_active{current_player.number==1 or current_player.number==3}:
    - ball_1_collected_p_odd
  s_target_active{device.shots.my_shot.state_name=='lit'}:
    - start_multiball
```

**Operators:** `==`, `!=`, `>`, `>=`, `<`, `<=`, `and`, `or`, `not`, `+`, `-`, `*`, `/`, `%`

### Dynamic Values / Placeholders
| Context | Syntax | Example |
|---|---|---|
| Event conditions | `current_player.variable` | `{current_player.ball_1_collected}` |
| variable_player int expressions | `current_player.variable` | `int: 25000 * current_player.ramps` |
| Slide widget text | `(variable)` for player vars | `text: (score)` |
| Slide widget text (machine) | `{machine.current_player.var}` | `text: "{machine.current_player.score}"` |
| Device state | `device.TYPE.NAME.PROP` | `device.counters.my_counter.value` |

⚠️ **CRITICAL:** Always use `current_player.variable_name` in event conditions and variable_player expressions. `player.variable_name` does NOT work — it silently resolves to nothing. See ADR-017.

---

## Architecture

The game runs entirely through MPF's event bus. There is no imperative game loop — everything is declarative YAML reacting to events.

### Ball Lifecycle Flowchart
```
Game Start: request_to_start_game (boolean) → game_starting (queue) → game_started
     ↓
Ball Start: player_turn_starting → ball_starting (queue) → ball_started
     ↓        [flippers enabled, shots enabled, ball ejected to plunger]
Ball End:   ball enters drain → ball_drain (relay, ball save can intercept)
     ↓        → balls_in_play = 0 → ball_will_end → ball_ending (queue, bonus runs here)
     ↓        → ball_ended → [next player or next ball or game_ending → game_ended]
```

### Mode Stack (priority order, highest wins)
| Mode | Priority | Active when |
|---|---|---|
| `rack_complete` | 300 | `eight_ball_rack_complete` event fires |
| `skill_shot` | 200 | `ball_started` → `ball_ended` |
| `kickback` | 150 | always during game |
| `bonus` | 130 | `ball_will_end` |
| `bonus_mult` | 120 | always during game |
| `base` | 100 | always during game |
| `attract` | 10 | no game running |

### Mode Lifecycle Events
For any mode named `X`:
1. `mode_X_will_start` → `mode_X_starting` → `mode_X_started`
2. `mode_X_will_stop` → `mode_X_stopping` → `mode_X_stopped`

**Use `mode_X_started` in your mode config** to trigger slides/shows/actions. Do NOT use the event that starts the mode (e.g., `ball_starting`) because the mode isn't active yet when that event fires.

### Ball Collection — Odd/Even Player Routing
Players 1 & 3 collect balls 1–8 ("solids"); players 2 & 4 collect balls 9–15 + 8-ball ("stripes"). Both sets share the same physical switches. `base.yaml` routes each switch hit to a **named per-parity event**:

```
s_lane_1 + (player 1 or 3)  →  ball_1_collected_p_odd
s_lane_1 + (player 2 or 4)  →  ball_1_collected_p_even
```

Both events write the same player variable (`ball_1_collected = true`). A `{not current_player.ball_1_collected}` guard in `variable_player` prevents double-scoring.

### Rack Completion Flow
```
s_eight_ball_target{all 7 balls collected}
  → ball_8_collected_ready        (intermediate signal, no redundant condition needed)
  → eight_ball_rack_complete
  → rack_complete mode starts     (locks 24K bonus, resets flags, increments rack_count)
```

### Bonus Formula
`(balls_collected × 3,000) × bonus_multiplier + base_bonus_locked`

- `balls_collected` resets to 0 on each rack completion
- `base_bonus_locked` accumulates across all racks and balls (never resets during the game)
- `bonus_multiplier` resets to 1 after each ball's payout (`keep_multiplier: false` in bonus plugin)

---

## Game Logic Toolkit

### Shots, Shot Profiles, Shot Groups
Shots track player targets with state management and light feedback:
```yaml
shots:
  my_target:
    switch: s_target_1
    show_tokens:
      light: l_target_1
    profile: my_profile       # optional, uses "default" if omitted

shot_profiles:
  my_profile:
    states:
      - name: unlit
        show: off
      - name: lit
        show: on
    loop: false               # stay in last state

shot_groups:
  top_lanes:
    shots: lane_1, lane_2, lane_3
    rotate_left_events: s_left_flipper_active
    rotate_right_events: s_right_flipper_active
    reset_events:
      top_lanes_lit_complete: 1s
```

Shot events: `(shot)_hit`, `(shot)_(profile)_hit`, `(shot)_(profile)_(state)_hit`

### Logic Blocks
| Type | Purpose | Key Setting |
|---|---|---|
| `counters:` | Count events, complete at threshold | `count_complete_value`, `persist_state` |
| `accruals:` | Multiple events, any order | `events:` list |
| `sequences:` | Multiple events, specific order | `events:` list |
| `state_machines:` | Arbitrary state transitions | `states:`, `transitions:` |

### Achievements
Track mode completion for wizard mode qualification:
```yaml
achievements:
  left_ramp:
    show_when_enabled: off
    show_when_selected: flash
    show_when_completed: on
    complete_events: left_ramp_mode_done
    events_when_started: start_left_ramp

achievement_groups:
  all_modes:
    achievements: left_ramp, right_ramp, center_target
    auto_select: true
    start_selected_events: hit_scoop
    rotate_right_events: s_action_button_active
```

---

## Key YAML Conventions

**`#config_version=6`** is required at the top of every config file. Shows use `#show_version=6`.

**`current_player.variable_name`** — correct syntax in event conditions and variable_player int expressions (see ADR-017). `player.variable_name` silently fails — it resolves to nothing because MPF's PlaceholderManager only registers `current_player` as a global parameter.

**No duplicate top-level keys.** `ruamel.yaml` raises `DuplicateKeyError`. Every mode file has exactly one `event_player:` block, one `variable_player:` block, etc. Always extend the existing section.

**Delayed events use pipe syntax:**
```yaml
event_player:
  eight_ball_rack_complete|2s:
    - rack_complete_done
```
A nested `delay:` key does not work in MPF 0.57.4 event_player.

**Scoring uses `variable_player:`, not `scoring:`** (which doesn't exist in 0.57.4):
```yaml
variable_player:
  ball_1_collected_p_odd{not current_player.ball_1_collected}:
    score: 3000
    ball_1_collected: true
```

**Blocking lower-priority mode scoring:**
```yaml
variable_player:
  jackpot_hit:
    score:
      int: 50000
      block: true    # prevents base mode from also scoring this event
```

**All devices need `number:`** even in `platform: virtual`:
```yaml
switches:
  s_lane_1:
    number: s_lane_1   # arbitrary string in virtual mode; replace with FAST address for hardware
```

**Sound system** must nest tracks under `sound_system:`:
```yaml
sound_system:
  tracks:
    sfx:
      type: standard
```
A flat `sound_tracks:` key is not valid.

**Show files** use `#show_version=6` and list steps with dashes:
```yaml
#show_version=6
- duration: 3s
  lights:
    l_led1: red
- duration: 2s
  lights:
    l_led1: off
```

**Mode configs** are only active when the mode is running. Machine-wide configs are always active.

**Ball-end modes** use `use_wait_queue: true` to delay ball ending:
```yaml
mode:
  start_events: ball_ending
  use_wait_queue: true
  priority: 500
  stop_events: bonus_complete
```

---

## Test Conventions

Tests extend `mpf.tests.MpfTestCase`. Two methods must use **snake_case** (camelCase overrides are never called by MPF):

```python
def get_machine_path(self):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_config_file(self):
    return "config.yaml"
```

`get_machine_path()` must return an absolute path — relative paths resolve against MPF's package root, not the repo.

**Always use MPF test helpers** (never raw `process_switch()`):
```python
self.hit_and_release_switch("s_coin")       # momentary — hit then release
self.hit_switch_and_run("s_lane_1", 0.1)    # hold for 0.1s (does NOT release!)
self.release_switch_and_run("s_lane_1", 0)  # release held switch
self.advance_time_and_run(10)               # let events settle
self.assertEventCalled("eight_ball_rack_complete")
```

Raw `process_switch()` leaves switches stuck active and will break subsequent test assertions.

**Mock events before asserting:**
```python
self.mock_event("my_event")                  # MUST be called BEFORE the event fires
# ... do something that posts the event ...
self.assertEventCalled("my_event")
```

**Test helpers** (defined in the test class):
- `_start_game(players=1)` — inserts coin, presses start N times, advances 10s
- `_drain_ball()` — hits + releases outhole, advances 10s for bonus + ball_end

**Player variable access:**
```python
self.machine.game.player["ball_1_collected"]   # dict-style
self.machine.game.player.score                  # attribute-style
self.machine.game.player.number                 # 1-indexed
```

---

## Hardware Transition (Phase 6+)

To switch from virtual to FAST Pinball Neuron hardware, change one line in `machine/config/config.yaml`:
```yaml
platform: fast   # was: virtual
```
Then replace all `number:` values with physical FAST board addresses (e.g., `0-0`, `0-1`).

All architecture decisions are documented in [`docs/adr.md`](../docs/adr.md).
