# MPF 0.57.4 Logic Blocks — Deep Reference

## What Are Logic Blocks?

Logic blocks are the "glue" that ties game logic together. They perform logic based
on events and post their own events when conditions are met. They live inside mode
config files (or the machine-wide config) under their own top-level key.

MPF provides four types of logic blocks:

| Type | Purpose |
|---|---|
| **Counter** | Count event occurrences up or down to a target |
| **Accrual** | Track multiple different events in any order |
| **Sequence** | Track multiple events that must occur in order |
| **State Machine** | Arbitrary states with custom transitions |

All logic blocks share a common set of enable/disable/reset/persist settings
described in [Common Settings](#common-settings-all-logic-blocks).

---

## 1. Counters

Count event occurrences. When a target count is reached, post a "complete" event.

```yaml
#config_version=6

counters:
  ramp_counter:
    count_events: left_ramp_hit
    starting_count: 0
    count_complete_value: 3
    events_when_complete: start_ramp_mode
    direction: up           # or 'down'
    persist_state: true     # remember count between balls
    reset_on_complete: true # reset to starting_count on complete
    enable_events: ball_started
    disable_events: ball_ended
    restart_events: some_reset_event
    reset_events: mode_my_mode_started
    events_when_hit: ramp_counter_advanced  # posted each count
    start_enabled: true
```

### Key counter settings

| Setting | Default | Description |
|---|---|---|
| `count_events` | *(required)* | Event(s) that increment/decrement the counter |
| `starting_count` | `0` | Initial value |
| `count_complete_value` | *(required)* | Target value that triggers completion |
| `direction` | `up` | `up` increments, `down` decrements |
| `events_when_complete` | — | Custom event(s) posted on completion |
| `events_when_hit` | — | Custom event(s) posted on each count change |
| `reset_on_complete` | `true` | Reset to `starting_count` when complete |
| `persist_state` | `false` | Save count in player variable between balls |
| `start_enabled` | `true` | Whether the counter is enabled when the mode starts |

### Counter events

Every counter automatically posts these built-in events (no configuration needed):

- **`logicblock_(name)_complete`** — when count reaches target
- **`logicblock_(name)_hit`** — each time the count changes
- **`logicblock_(name)_updated`** — when the value changes (includes the value)

Custom events configured via `events_when_complete` and `events_when_hit` are
posted **in addition to** the built-in events, not instead of them.

### Monitorable property

```
device.counters.(name).value
```

Use this in text widgets, conditional events, or slide_player to show the current
count to the player.

### Count by more than 1

You can add a `count` parameter to the count event to change the counter by more
than 1 per hit:

```yaml
counters:
  multi_counter:
    count_events: my_event
    starting_count: 0
    count_complete_value: 10
```

Then post the event with a parameter: `my_event{count:5}` to add 5 at once.

---

## 2. Accruals

Watch for multiple different events (any order). Complete when **ALL** have occurred.

```yaml
#config_version=6

accruals:
  my_accrual:
    events:
      - event1_happened
      - event2_happened
      - event3_happened
    events_when_complete: all_three_done
    reset_on_complete: true
    persist_state: true
    enable_events: ball_started
    disable_events: ball_ended
    start_enabled: true
```

### Key accrual settings

| Setting | Default | Description |
|---|---|---|
| `events` | *(required)* | List of events to track (all must occur) |
| `events_when_complete` | — | Custom event(s) posted when all steps are done |
| `events_when_hit` | — | Custom event(s) posted when any step completes |
| `reset_on_complete` | `true` | Reset all steps when complete |
| `persist_state` | `false` | Save step states between balls |

### Accrual events

- **`logicblock_(name)_complete`** — when all events have occurred
- **`logicblock_(name)_hit`** — each time a new step is satisfied
- **`logicblock_(name)_updated`** — when the state changes

### Use cases

- Track when all targets in a bank are hit (regardless of order)
- Track when multiple objectives are completed
- "Collect all items" mechanics (e.g., hit all 4 martians in Attack from Mars)
- Multiball lock qualification (hit 3 different shots to light lock)

### Important behavior

- Each step in the `events:` list can only be satisfied **once** per cycle.
  Hitting the same event again after it is already satisfied does nothing.
- Steps can be completed in **any order**.
- If `persist_state: true`, the satisfied/unsatisfied state of each step
  survives ball drains and is stored per-player.

---

## 3. Sequences

Like accruals but events must occur **in order**. If an event fires out of order,
it is ignored (it does not reset the sequence).

```yaml
#config_version=6

sequences:
  my_sequence:
    events:
      - step1_event
      - step2_event
      - step3_event
    events_when_complete: sequence_done
    reset_on_complete: true
    persist_state: false
    enable_events: ball_started
    disable_events: ball_ended
    start_enabled: true
```

### Key sequence settings

| Setting | Default | Description |
|---|---|---|
| `events` | *(required)* | Ordered list of events (must occur in this order) |
| `events_when_complete` | — | Custom event(s) posted when sequence finishes |
| `events_when_hit` | — | Custom event(s) posted when each step is advanced |
| `reset_on_complete` | `true` | Reset to step 1 when complete |

### Sequence events

- **`logicblock_(name)_complete`** — when all steps occur in order
- **`logicblock_(name)_hit`** — each time the next expected step fires
- **`logicblock_(name)_updated`** — when the current step changes

### Use cases

- Combo tracking (hit ramp → loop → target in exact order)
- Progressive objectives (complete phase 1 before phase 2 unlocks)
- Skill shot sequences (hit specific targets in order during ball launch)
- Lane change combos

### Important behavior

- Only the **next** expected event is watched. Other events are ignored.
- Out-of-order events do **not** reset progress (the sequence just waits).
- Use `reset_events` if you want an explicit event to restart the sequence.

---

## 4. State Machines

Define arbitrary states with custom transitions between them. State machines are
the most flexible logic block — use them when counter/accrual/sequence patterns
don't fit.

```yaml
#config_version=6

state_machines:
  my_machine:
    states:
      start:
        label: Start
      step1:
        label: Step 1
        events_when_started: step1_started
        events_when_stopped: step1_stopped
      step2:
        label: Step 2
        events_when_started: step2_started
        events_when_stopped: step2_stopped
      final:
        label: Final
        events_when_started: final_reached
    transitions:
      - source: start
        target: step1
        events: begin_event
      - source: step1
        target: step2
        events: advance_event
      - source: step2
        target: final
        events: finish_event
      - source: step2
        target: start
        events: reset_event
      - source: final
        target: start
        events: reset_event
    persist_state: true
```

### State settings

Each state supports:

| Setting | Description |
|---|---|
| `label` | Human-readable name (used in logs and service mode) |
| `events_when_started` | Event(s) posted when this state becomes active |
| `events_when_stopped` | Event(s) posted when this state is left |
| `show_when_active` | Show to play while in this state |

### Transition settings

Each transition requires:

| Setting | Description |
|---|---|
| `source` | State to transition **from** |
| `target` | State to transition **to** |
| `events` | Event(s) that trigger this transition |
| `events_when_transitioning` | *(optional)* Event(s) posted during the transition |

### State machine events

- **`logicblock_(name)_updated`** — when the state changes
- Per-state events via `events_when_started` / `events_when_stopped`
- Per-transition events via `events_when_transitioning`

### Use cases

- Complex mode progression that doesn't fit counter/accrual patterns
- Multi-phase modes with different behaviors per phase
- Wizard mode qualification tracking
- Lock mechanisms with distinct states (idle → qualified → lit → locked)

---

## Common Settings (All Logic Blocks)

These settings are available on **all four** logic block types:

| Setting | Default | Description |
|---|---|---|
| `persist_state` | `false` | Save state in a player variable between balls. The variable is per-player and survives ball drains. |
| `reset_on_complete` | `true` | Automatically reset to initial state when the block completes. |
| `enable_events` | — | Event(s) that enable (activate) the logic block. |
| `disable_events` | — | Event(s) that disable (deactivate) the logic block. While disabled, count/step events are ignored. |
| `reset_events` | — | Event(s) that reset the logic block to its initial state (but do **not** re-enable it if disabled). |
| `restart_events` | — | Event(s) that reset **and** re-enable the logic block in one step. |
| `start_enabled` | `true` | Whether the logic block is enabled when its parent mode starts. Set to `false` if you want to gate it behind an `enable_events` trigger. |
| `events_when_complete` | — | Custom event(s) posted when the block completes. |
| `events_when_hit` | — | Custom event(s) posted on each incremental change (counter hit, accrual/sequence step). |

### Enable / disable lifecycle

```
Mode starts
  ├─ start_enabled: true  → block is active immediately
  └─ start_enabled: false → block is inactive, waiting for enable_events

enable_events fires  → block starts watching for count/step events
disable_events fires → block stops watching (state is preserved)
reset_events fires   → state resets to initial (enabled state unchanged)
restart_events fires → state resets AND block is re-enabled
```

### persist_state details

When `persist_state: true`:
- The logic block's state is stored in a **player variable** named
  `logicblock_(name)_state`.
- Each player has their own independent state.
- State survives ball drains and is restored when the mode restarts on the
  next ball.
- State does **not** survive across games (resets on game start).

---

## Integrating Logic Blocks with Shows

Logic blocks post events that you can use in `show_player:` to drive visual
feedback on playfield lights, flashers, or the display:

```yaml
#config_version=6

show_player:
  logicblock_ramp_counter_hit:
    flash:
      loops: 3
      speed: 4
      show_tokens:
        lights: l_ramp
  logicblock_ramp_counter_complete:
    on:
      show_tokens:
        lights: l_ramp
```

This flashes the ramp light 3 times on each counter hit, then turns it solid
when the counter completes.

### Driving scoring from logic blocks

Combine logic block events with `variable_player:` for scoring:

```yaml
#config_version=6

variable_player:
  logicblock_ramp_counter_hit:
    score: 5000
  logicblock_ramp_counter_complete:
    score: 50000
```

---

## Real-World Pattern: Mode Qualification

Use counters to qualify modes. This pattern is common in modern pinball designs
where the player must hit a shot N times before a mode becomes available:

```yaml
#config_version=6

counters:
  left_ramp_qualify:
    count_events: left_ramp_hit
    starting_count: 0
    count_complete_value: 3
    events_when_complete: start_left_ramp_mode, disable_qualify
    enable_events: enable_qualify
    disable_events: disable_qualify
    start_enabled: true
    persist_state: true
    reset_on_complete: false
```

Key design decisions in this pattern:

- **`reset_on_complete: false`** — the counter stays at its completed value.
  This prevents the mode from being re-qualified immediately after it ends.
  Use a separate `reset_events` to re-arm it when appropriate.
- **`persist_state: true`** — progress toward qualification survives ball drains.
  The player keeps their ramp hits across balls.
- **`disable_qualify`** in `events_when_complete` — the counter disables itself
  once the mode is qualified, preventing double-triggers.

### Re-qualifying after mode ends

To let the player re-qualify after the mode finishes:

```yaml
counters:
  left_ramp_qualify:
    count_events: left_ramp_hit
    starting_count: 0
    count_complete_value: 3
    events_when_complete: start_left_ramp_mode
    restart_events: left_ramp_mode_ended
    persist_state: true
```

Here `restart_events` resets the count **and** re-enables the counter when the
mode ends, so the player can work toward qualifying it again.

---

## Real-World Pattern: Target Bank Completion

Use an accrual to track a bank of drop targets or standup targets:

```yaml
#config_version=6

accruals:
  target_bank:
    events:
      - s_target_1_active
      - s_target_2_active
      - s_target_3_active
    events_when_complete: target_bank_complete
    reset_on_complete: true
    persist_state: true
    enable_events: ball_started
```

Each target only needs to be hit once, in any order. When all three are hit,
`target_bank_complete` fires and the accrual resets for the next cycle.

---

## Real-World Pattern: Combo Shots

Use a sequence to reward the player for hitting shots in a specific order:

```yaml
#config_version=6

sequences:
  super_combo:
    events:
      - left_ramp_hit
      - center_loop_hit
      - right_ramp_hit
    events_when_complete: super_combo_complete
    reset_on_complete: true
    enable_events: ball_started
    disable_events: ball_ended

variable_player:
  super_combo_complete:
    score: 100000
```

The player must hit left ramp → center loop → right ramp in exact order.
Hitting them out of order does nothing (the sequence waits at its current step).

---

## Tips and Gotchas

1. **Built-in events are always posted.** Even if you set `events_when_complete`,
   the `logicblock_(name)_complete` event still fires. Your custom event is
   posted *in addition to* the built-in one.

2. **`persist_state` is per-player.** In a multiplayer game, each player has
   their own independent logic block state.

3. **Logic blocks belong to modes.** When a mode stops, its logic blocks are
   deactivated. When the mode restarts, blocks with `persist_state: true`
   restore their saved state.

4. **`reset_on_complete` vs `reset_events`.** Use `reset_on_complete: true` for
   repeating objectives (hit 3 ramps, score, repeat). Use `reset_on_complete: false`
   with explicit `reset_events` for one-time qualifications.

5. **Counter direction matters.** A `direction: down` counter starts at
   `starting_count` and decrements. It completes when it reaches
   `count_complete_value` (which should be less than `starting_count`).

6. **State machines have no built-in "complete" concept.** Unlike the other three
   types, state machines don't have a `count_complete_value` or implicit
   completion. Use `events_when_started` on a final state to signal completion.

7. **No duplicate top-level keys.** If your mode file already has a `counters:`
   section, add new counters to the existing block — do not create a second
   `counters:` key (YAML will error or silently drop one).
