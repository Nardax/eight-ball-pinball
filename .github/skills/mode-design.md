# MPF 0.57.4 — Mode Design Reference

## Mode Basics

Modes are self-contained units of game logic. Each mode has its own config, shows, and sounds. Everything in a mode config is only active when that mode is running.

### Folder structure

```
modes/
  my_mode/
    config/
      my_mode.yaml        # required — mode config (must match folder name)
    shows/                 # optional — mode-specific shows
      my_show.yaml
    sounds/                # optional — mode-specific sounds
      my_sound.ogg
```

- The config filename **must** match the mode folder name.
- There is no limit on concurrent modes — dozens running at once is normal.
- Modes **must** be listed in the `modes:` section of the machine config to be loaded:

```yaml
# config/config.yaml
modes:
  - base
  - attract
  - bonus
  - skill_shot
```

---

## Mode Configuration

Every mode config begins with a `mode:` section that controls when and how the mode starts and stops.

```yaml
#config_version=6

mode:
  start_events: ball_started       # event(s) that start this mode
  stop_events: ball_ended           # optional — auto-stops on ball end if omitted
  priority: 100                     # higher number = takes precedence over lower
  game_mode: true                   # true (default) = requires active game; false = can run outside game
  use_wait_queue: true              # delays ball ending until this mode stops itself
  events_when_started: my_mode_type_started    # custom event posted when mode starts
  events_when_stopped: my_mode_type_stopped    # custom event posted when mode stops
```

### Key fields

| Field | Default | Purpose |
|---|---|---|
| `start_events` | *(none)* | Event(s) that cause this mode to start |
| `stop_events` | *(none)* | Event(s) that cause this mode to stop. Modes auto-stop on `ball_ended` unless `game_mode: false` |
| `priority` | `0` | Determines which mode wins conflicts (display, scoring, lights) |
| `game_mode` | `true` | If `true`, mode can only run during an active game |
| `use_wait_queue` | `false` | If `true`, ball ending is delayed until this mode posts its stop event |
| `events_when_started` | *(none)* | Custom event(s) posted when the mode starts |
| `events_when_stopped` | *(none)* | Custom event(s) posted when the mode stops |
| `restart_on_next_ball` | `false` | If `true`, mode restarts automatically on the next ball |

---

## Priority System

Priority determines which mode's configuration wins when multiple modes define the same thing (e.g., competing slide players, light shows, scoring blocks).

| Layer | Priority | Examples |
|---|---|---|
| Machine-wide config | 0 | Hardware definitions, switch/coil mappings |
| Attract mode | 10 | Attract show, high score display |
| Game mode | 20 | Core game logic |
| User gameplay modes | 100–1,000,000 | Base, skill shot, bonus, wizard modes |

- **Higher priority modes override lower ones** for display, lights, and scoring.
- Multiple modes at different priorities can all run simultaneously — priority only matters when they conflict.
- Use `block: true` in `variable_player:` to prevent lower-priority modes from scoring.

---

## Mode Lifecycle Events

For a mode named `base`, MPF posts these events in order:

### Start sequence

1. **`mode_base_will_start`** — mode is about to start; last chance to prevent it
2. **`mode_base_starting`** — mode is initializing its config
3. **`mode_base_started`** — mode is now fully active and ready

### Stop sequence

4. **`mode_base_will_stop`** — mode is about to stop; clean up here
5. **`mode_base_stopping`** — mode is tearing down its config
6. **`mode_base_stopped`** — mode is fully stopped and removed

### Critical timing rule

> **Use `mode_<name>_started` in your mode config to trigger initial actions.**
>
> Do **NOT** use `ball_starting` inside the mode config to trigger slides/shows/events. If the mode starts from `ball_started`, then `ball_starting` has already fired *before* the mode was running — the mode will never see it.

```yaml
# CORRECT — triggers when the mode is actually active
event_player:
  mode_skill_shot_started:
    - show_skill_shot_display

# WRONG — ball_starting fires before the mode starts
event_player:
  ball_starting:            # mode misses this event entirely
    - show_skill_shot_display
```

---

## Mode Layering Pattern (Field / Mission / Wizard)

Complex games organize modes into three categories that replace each other in a controlled hierarchy.

### Field Modes (lowest priority)

- Non-intrusive gameplay running on the open playfield.
- Accruals, multipliers, qualification shots, combos.
- All field modes run together simultaneously.
- Typically implemented as config imports consolidated in a single field mode.

```yaml
# modes/field/config/field.yaml
#config_version=6

mode:
  start_events: start_mode_field
  stop_events: stop_mode_field
  priority: 200
  events_when_started: mode_type_field_started
  events_when_stopped: mode_type_field_stopped
```

### Mission Modes (medium priority)

- "Partial takeover" — demand player attention but don't stop everything.
- Replace field modes when active; field modes resume when mission ends.
- Multiple missions should not overlap (use `achievement_groups:` to enforce).

```yaml
# modes/mission_a/config/mission_a.yaml
#config_version=6

mode:
  start_events: start_mode_mission_a
  stop_events: stop_mode_mission_a, ball_ended
  priority: 500
  events_when_started: mode_type_mission_started
  events_when_stopped: mode_type_mission_stopped
```

### Wizard Modes (highest priority)

- "Complete takeover" — stop nearly all other gameplay.
- Includes multiballs, video modes, end-game wizard modes.
- Replace global + field modes when active.

```yaml
# modes/wizard/config/wizard.yaml
#config_version=6

mode:
  start_events: start_mode_wizard
  stop_events: stop_mode_wizard, ball_ended
  priority: 800
  events_when_started: mode_type_wizard_started
  events_when_stopped: mode_type_wizard_stopped
```

### Helper Modes

These structural modes manage transitions between field, mission, and wizard layers:

| Mode | Role |
|---|---|
| **Base** | Always running during game. Manages global ↔ wizard transitions. Tracks persistent player state. |
| **Global** | Manages field ↔ mission transitions. Runs persistent gameplay (pop bumpers, multiball locking). |
| **Field** | Consolidates all field mode configs via imports. Stopped/started by global mode. |

### Event flow for mode transitions

```yaml
# base.yaml — manages global ↔ wizard transitions
event_player:
  mode_base_started: start_mode_global
  mode_base_will_stop: stop_mode_global
  mode_type_wizard_started: stop_mode_global
  mode_type_wizard_stopped{not mode["base"].stopping}: start_mode_global
```

```yaml
# global.yaml — manages field ↔ mission transitions
event_player:
  mode_global_started: start_mode_field
  mode_global_will_stop:
    - stop_mode_field
    - stop_missions
  mode_type_mission_started: stop_mode_field
  mode_type_mission_stopped{not mode["global"].stopping}: start_mode_field
```

The `{not mode["base"].stopping}` and `{not mode["global"].stopping}` conditions prevent modes from restarting during shutdown cascades.

---

## Mode Selection / Qualification

### By hitting shots X times

Use counters in a qualification mode to track progress and start game modes when thresholds are met.

```yaml
counters:
  qualify_mission_counter:
    count_events: s_target_hit
    starting_count: 0
    count_complete_value: 5
    events_when_complete: mission_qualified
    reset_on_complete: true
    persist_state: true
```

### By carousel selection

Use MPF's built-in `carousel` mode code for mode selection:

```yaml
mode:
  code: mpf.modes.carousel.code.carousel.Carousel
  start_events: modes_qualified
  stop_events: carousel_item_selected

carousel:
  selectable_items: mission_a, mission_b, mission_c
  select_item_events: s_start_active
  next_item_events: s_right_flipper_active
  previous_item_events: s_left_flipper_active
```

When the player makes a selection, `carousel_mission_a_highlighted` (or whichever item is active) is posted.

### Using achievements

Track mode completion with `achievements:` and `achievement_groups:`:

```yaml
achievements:
  mission_a:
    enable_events: mission_a_qualified
    start_events: start_mode_mission_a
    complete_events: mission_a_complete
    events_when_started: start_mode_mission_a
    events_when_completed: mission_a_done

achievement_groups:
  all_missions:
    achievements: mission_a, mission_b, mission_c
    events_when_all_completed: wizard_ready
```

Achievement states flow: **disabled → enabled → started → stopped → completed**.

---

## Ball-End Modes

To delay ball ending for bonus display, animations, or other end-of-ball sequences:

```yaml
#config_version=6

mode:
  start_events: ball_ending        # triggered when the ball drains
  use_wait_queue: true             # prevents ball from ending until mode stops
  priority: 500                    # high enough to control display
  stop_events: stop_my_bonus_mode  # MUST eventually stop or game hangs forever
```

> **WARNING:** If `use_wait_queue: true` is set, the mode **must** eventually stop itself. If it doesn't, the game will hang permanently waiting for the mode to release the ball-end queue.

Common pattern for a timed ball-end mode:

```yaml
mode:
  start_events: ball_ending
  use_wait_queue: true
  priority: 500
  stop_events: bonus_display_complete

event_player:
  mode_bonus_started:
    - start_bonus_show
  bonus_show_ended:
    - bonus_display_complete
```

---

## Key Patterns and Best Practices

### Running modes outside of a game

Use `game_mode: false` for modes that should run when no game is active (e.g., attract mode enhancements, service menu extensions).

```yaml
mode:
  start_events: machine_reset_phase_3
  game_mode: false
  priority: 15
```

### Auto-stop on ball end

Modes auto-stop on `ball_ended` by default when `game_mode: true`. You can explicitly set `stop_events: ball_ended` for clarity, but it is not required.

### Blocking lower-priority scoring

Use `block: true` in `variable_player:` to prevent lower-priority modes from awarding points for the same event:

```yaml
# wizard mode (priority 800)
variable_player:
  s_target_hit:
    score: 50000
    block: true     # base mode's s_target_hit scoring is suppressed
```

### Preventing restart during shutdown

When a mode posts events on stop that could re-trigger another mode, guard against it:

```yaml
event_player:
  mode_type_wizard_stopped{not mode["base"].stopping}: start_mode_global
```

Without the guard, stopping the base mode would cascade: base stops → wizard stops → global restarts → global starts field → but base is gone, causing errors.

### Delayed events in event_player

Use pipe syntax for delays:

```yaml
event_player:
  some_event|2s:
    - delayed_event
```

A nested `delay:` key does **not** work in MPF 0.57.4 `event_player`.

### Mode-scoped devices

Devices defined inside a mode config (shots, shot groups, counters, timers, etc.) are only active while that mode is running. They are automatically created when the mode starts and destroyed when it stops.

```yaml
# Only exists while this mode is running
timers:
  hurry_up:
    start_value: 30
    end_value: 0
    direction: down
    tick_interval: 1s
    start_running: true
    control_events:
      - event: mode_my_mode_started
        action: start
```
