# Shots & Shot Profiles — MPF 0.57.4 Deep Reference

> Skill reference for the Mission Pinball Framework shots system.
> Covers `shots:`, `shot_profiles:`, `shot_groups:`, events, show tokens, and common patterns.

---

## What Are Shots?

A **shot** is a switch (or sequence of switches) that the player shoots for. Shots have **states**, **profiles**, and can be **grouped** for collective behavior.

Shots are the backbone of pinball game logic — drop targets, standups, lanes, ramps, orbits, and spinners are all modeled as shots. Each shot tracks its own state (e.g., unlit → flashing → lit), advances through a profile on each hit, and posts events that the rest of the game can react to.

---

## `shots:`

Define shots in a mode config file under the `shots:` top-level key.

### Simple single-switch shot

```yaml
shots:
  my_standup:
    switch: s_standup_1
    show_tokens:
      light: l_standup_1
```

### Sequence shot (must hit switches in order within time)

```yaml
shots:
  left_orbit:
    switches: s_orbit_left, s_orbit_center, s_orbit_right
    sequence: true
    time: 3s
```

When `sequence: true`, the player must activate the switches in the listed order within `time:`. If the sequence times out or a switch is hit out of order, the sequence resets.

### Shot with custom profile

```yaml
shots:
  my_ramp:
    switch: s_ramp_made
    profile: my_profile
    show_tokens:
      light: l_ramp_indicator
```

### Full settings reference

| Setting | Type | Default | Description |
|---|---|---|---|
| `switch:` | string | — | Single switch that triggers this shot. |
| `switches:` | list | — | Multiple switches (use with `sequence:`). |
| `sequence:` | bool | `false` | If `true`, switches must be hit in listed order. |
| `time:` | time string | `0` | Time window for completing a sequence (`0` = no limit). |
| `profile:` | string | `default` | Which `shot_profile` to use. |
| `show_tokens:` | map | — | Key/value pairs passed into the show (see below). |
| `advance_events:` | event list | — | Events that advance the shot state (besides a hit). |
| `reset_events:` | event list | — | Events that reset the shot to state 0. |
| `restart_events:` | event list | — | Events that restart the shot (reset + enable). |
| `enable_events:` | event list | — | Events that enable the shot. |
| `disable_events:` | event list | — | Events that disable the shot. |
| `start_enabled:` | bool | `true` | Whether the shot is enabled when the mode starts. |
| `block:` | bool | `true` | If `true`, lower-priority modes won't process this switch as a shot hit. |
| `delay_switch:` | time string | — | Debounce delay applied to the switch activation. |

---

## `shot_profiles:`

A **shot profile** defines the list of states a shot cycles through on each hit.

```yaml
shot_profiles:
  my_profile:
    states:
      - name: unlit
        show: off
      - name: flashing
        show: flash
      - name: lit
        show: on
    loop: true  # returns to first state after last
```

Each hit advances the shot to the next state. When the last state is reached:
- If `loop: true`, the shot wraps back to the first state.
- If `loop: false` (default), the shot stays on the last state.

### Profile settings reference

| Setting | Type | Default | Description |
|---|---|---|---|
| `states:` | list | — | Ordered list of state definitions. |
| `loop:` | bool | `false` | Wrap to first state after last is reached. |
| `show_when_disabled:` | bool | `true` | Continue showing the current state show when shot is disabled. |
| `advance_on_hit:` | bool | `true` | Automatically advance state on each hit. |
| `block:` | bool | `true` | Block lower-priority profiles from processing. |

### State definition

Each entry in `states:` accepts:

| Setting | Type | Default | Description |
|---|---|---|---|
| `name:` | string | **required** | Name of this state (used in events). |
| `show:` | string | `None` | Show to play when the shot is in this state. |
| `speed:` | number | `1` | Playback speed of the show. |
| `manual_advance:` | bool | `false` | If `true`, the shot does not auto-advance on hit from this state. |

### Default profile

MPF has a **built-in "default" profile** with two states:

| Index | Name | Show |
|---|---|---|
| 0 | `unlit` | `off` |
| 1 | `lit` | `on` |

`loop: false` — once lit, it stays lit until explicitly reset.

If you don't specify `profile:` on a shot, it uses this default.

### Built-in shows

MPF ships with several built-in shows you can reference by name:

| Show name | Behavior |
|---|---|
| `on` | Light on solid. |
| `off` | Light off. |
| `flash` | Light flashing (default 1s cycle — 0.5s on, 0.5s off). |
| `led_color` | Set an LED to a specific color (use with `show_tokens`). |

---

## `shot_groups:`

Group multiple shots for **collective behavior**: rotation (lane change), completion detection, and batch reset.

```yaml
shot_groups:
  top_lanes:
    shots: lane_1, lane_2, lane_3, lane_4
    rotate_left_events: s_left_flipper_active
    rotate_right_events: s_right_flipper_active
    reset_events:
      top_lanes_lit_complete: 1s  # reset 1s after all lit
```

### Shot group settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `shots:` | list | **required** | Comma-separated list of shot names in this group. |
| `rotate_left_events:` | event list | — | Events that rotate shot states left. |
| `rotate_right_events:` | event list | — | Events that rotate shot states right. |
| `reset_events:` | event list | — | Events that reset all shots in the group. |
| `enable_events:` | event list | — | Events that enable all shots in the group. |
| `disable_events:` | event list | — | Events that disable all shots in the group. |
| `restart_events:` | event list | — | Events that restart all shots in the group. |
| `enable_rotation_events:` | event list | — | Events that enable shot rotation. |
| `disable_rotation_events:` | event list | — | Events that disable shot rotation. |

### Rotation mechanics

When a rotate event fires, the **state values** of the shots shift left or right within the group. The shots themselves don't move — their states do. This is the classic **lane change** mechanic.

Example with 4 lanes (states before rotate-right): `[lit, unlit, unlit, lit]`
After rotate-right: `[lit, lit, unlit, unlit]`

### Events posted by `shot_groups:`

Shot groups automatically post events when all shots reach the same state:

| Event | When |
|---|---|
| `(group_name)_(state)_complete` | All shots in the group reach `(state)`. |
| `(group_name)_(profile)_(state)_complete` | Same, but includes the profile name. |
| `(group_name)_hit` | Any shot in the group is hit. |
| `(group_name)_(profile)_hit` | Any shot in the group is hit (with profile). |
| `(group_name)_(profile)_(state)_hit` | Any shot in the group is hit (with profile and state). |

**Common completion events:**

- `(group_name)_lit_complete` — all shots reached `lit` state.
- `(group_name)_unlit_complete` — all shots reset to `unlit` state.

---

## Events Posted by Shots

Every shot hit posts **multiple events**, from general to specific:

1. **`(shot_name)_hit`** — always posted on every hit.
2. **`(shot_name)_(profile)_hit`** — includes the active profile name.
3. **`(shot_name)_(profile)_(state)_hit`** — includes both profile and the state the shot was in *before* advancing.
4. **`(shot_name)_(state)_hit`** — state without profile name.

### Example event sequence

Given a shot `my_shot` using profile `my_profile` with states `[unlit, flashing, lit]`:

**First hit** (shot was in `unlit`):
```
my_shot_hit
my_shot_my_profile_hit
my_shot_my_profile_unlit_hit
my_shot_unlit_hit
```

**Second hit** (shot was in `flashing`):
```
my_shot_hit
my_shot_my_profile_hit
my_shot_my_profile_flashing_hit
my_shot_flashing_hit
```

**Third hit** (shot was in `lit`):
```
my_shot_hit
my_shot_my_profile_hit
my_shot_my_profile_lit_hit
my_shot_lit_hit
```

> **Important:** The state name in the event is the state the shot was in *before* advancing, not the state it advances *to*.

---

## `show_tokens:`

Show tokens let you **dynamically bind lights/LEDs to shows** without hardcoding light names inside shows. This makes shots reusable across different physical locations.

```yaml
shots:
  lane_1:
    switch: s_lane_1
    show_tokens:
      light: l_lane_1  # 'light' token is passed to the show

  lane_2:
    switch: s_lane_2
    show_tokens:
      light: l_lane_2  # same show, different light
```

Inside a show file, the token is referenced with parentheses:

```yaml
#show_version=6
- duration: -1
  lights:
    (light): white  # replaced at runtime with l_lane_1 or l_lane_2
```

Multiple tokens can be passed:

```yaml
show_tokens:
  light: l_my_light
  color: red
```

---

## Per-Mode Shot Definitions

Shots should be defined **per-mode**, NOT machine-wide. The same physical switch can be defined as different shots in different modes with different profiles and scoring.

This is a key architectural principle:

```
modes/
  base/
    config/
      base.yaml        # defines lane shots for base scoring
  multiball/
    config/
      multiball.yaml   # redefines same switches as jackpot shots
  skill_shot/
    config/
      skill_shot.yaml  # redefines same switches for skill shot logic
```

When multiple modes define shots on the same switch, the **highest-priority mode wins** (controlled by `block:` setting). Lower-priority shot definitions are suppressed unless `block: false`.

---

## Monitorable Properties

For use in conditional events and `variable_player:` conditions:

| Property | Type | Description |
|---|---|---|
| `device.shots.(name).state` | int | Numeric index of current state (0, 1, 2…). |
| `device.shots.(name).state_name` | string | String name of current state (`'lit'`, `'unlit'`, etc.). |
| `device.shots.(name).enabled` | bool | Whether the shot is currently enabled. |

### Example: conditional scoring

```yaml
variable_player:
  my_shot_hit{device.shots.my_shot.state_name=="lit"}:
    score: 50000
```

---

## Key Pattern: Lane Change

The classic **lane change** pattern uses `shot_groups:` with rotate events tied to flipper buttons.

### Full working example

```yaml
#config_version=6

shots:
  lane_j:
    switch: s_lane_j
    show_tokens:
      light: l_lane_j
  lane_a:
    switch: s_lane_a
    show_tokens:
      light: l_lane_a
  lane_m:
    switch: s_lane_m
    show_tokens:
      light: l_lane_m

shot_profiles:
  default:
    states:
      - name: unlit
        show: off
      - name: lit
        show: on

shot_groups:
  top_lanes:
    shots: lane_j, lane_a, lane_m
    rotate_left_events: s_left_flipper_active
    rotate_right_events: s_right_flipper_active
    reset_events:
      top_lanes_lit_complete: 1s

variable_player:
  top_lanes_lit_complete:
    score: 25000
```

**How it works:**

1. Each lane starts `unlit`.
2. Rolling through a lane advances it to `lit`.
3. Pressing flippers rotates which lanes are lit/unlit.
4. When all three are `lit`, `top_lanes_lit_complete` fires.
5. After 1 second, all lanes reset to `unlit`.
6. Scoring awards 25,000 points on completion.

---

## Key Pattern: Drop Targets

Drop targets use shots with `reset_events:` to handle target resets:

```yaml
shots:
  drop_1:
    switch: s_drop_1
    reset_events: reset_drop_bank
  drop_2:
    switch: s_drop_2
    reset_events: reset_drop_bank
  drop_3:
    switch: s_drop_3
    reset_events: reset_drop_bank

shot_groups:
  drop_bank:
    shots: drop_1, drop_2, drop_3
    reset_events:
      drop_bank_lit_complete: 500ms

variable_player:
  drop_bank_lit_complete:
    score: 50000
```

---

## Key Pattern: Progressive Scoring with Multi-State Profile

Use a multi-state profile to increase value on repeated hits:

```yaml
shot_profiles:
  progressive:
    states:
      - name: base
        show: off
      - name: silver
        show: flash
      - name: gold
        show: on
    loop: false

shots:
  center_target:
    switch: s_center_target
    profile: progressive
    show_tokens:
      light: l_center

variable_player:
  center_target_base_hit:
    score: 10000
  center_target_silver_hit:
    score: 25000
  center_target_gold_hit:
    score: 50000
```

---

## Common Pitfalls

| Mistake | Fix |
|---|---|
| Defining shots in `config.yaml` (machine-wide) | Define shots inside mode configs instead. |
| Forgetting `show_tokens:` | Shots with no `show_tokens` won't control any lights. |
| Using `current_player.` in mode conditions | Use `player.` — see ADR-005 in this project. |
| Not specifying `#config_version=6` | Required at the top of every MPF config file. |
| Expecting state in event to be the *new* state | Events report the state *before* advancing. |
| Duplicate `shots:` keys in one file | YAML forbids duplicate top-level keys — merge into one block. |

---

## Quick Reference: Event Naming

```
Shot hit:           (shot)_hit
Profile hit:        (shot)_(profile)_hit
Profile+state hit:  (shot)_(profile)_(state)_hit
State hit:          (shot)_(state)_hit
Group complete:     (group)_(state)_complete
Group profile hit:  (group)_(profile)_(state)_complete
```

---

*Reference: [MPF Shots Documentation](https://missionpinball.org/latest/reference/)*
*MPF version: 0.57.4 · Config version: 6 · Show version: 6*
