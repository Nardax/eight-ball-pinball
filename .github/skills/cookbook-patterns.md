# Cookbook Patterns — Proven Recipes

> **MPF 0.57.4 deep-reference guide.**
> Ready-to-use YAML patterns for common pinball game features.

---

## Lane Change with Shot Groups

Rotate lit lanes using flipper buttons. Classic top-lane or orbit-lane
pattern used in nearly every modern pinball machine.

```yaml
# Mode config (e.g., modes/base/config/base.yaml)
#config_version=6

shots:
  lane_1:
    switch: s_lane_1
    show_tokens:
      light: l_lane_1
  lane_2:
    switch: s_lane_2
    show_tokens:
      light: l_lane_2
  lane_3:
    switch: s_lane_3
    show_tokens:
      light: l_lane_3

shot_groups:
  top_lanes:
    shots: lane_1, lane_2, lane_3
    rotate_left_events: s_left_flipper_active
    rotate_right_events: s_right_flipper_active
    reset_events:
      top_lanes_lit_complete: 1s    # reset 1s after all lanes completed
```

### How It Works

1. Each shot has two profiles (default): `unlit` and `lit`.
2. The shot group starts with one lane lit.
3. Flipper button presses rotate which lane is lit.
4. Hitting a lit lane advances it (completes it).
5. When all lanes are complete, `top_lanes_lit_complete` fires.
6. The group resets after 1 second.

### Shot Profiles (Default)

MPF provides default shot profiles: `unlit` → `lit`. You can define
custom profiles:

```yaml
shot_profiles:
  lane_profile:
    states:
      - name: unlit
        show: off
      - name: lit
        show: flash
      - name: complete
        show: on
    loop: false

shots:
  lane_1:
    switch: s_lane_1
    profile: lane_profile
    show_tokens:
      light: l_lane_1
```

---

## Counter-Based Mode Qualification

Use a counter to track hits and start a mode when the threshold is met.

```yaml
counters:
  ramp_counter:
    count_events: ramp_made
    starting_count: 0
    count_complete_value: 5
    direction: up
    reset_on_complete: true
    events_when_complete: qualify_multiball
    persist_state: true           # remember count across balls

event_player:
  qualify_multiball:
    - start_mode_multiball        # start multiball mode
```

### Counter Settings

| Setting | Description |
|---------|-------------|
| `count_events` | Events that increment the counter. |
| `starting_count` | Initial value (default `0`). |
| `count_complete_value` | Target value to trigger completion. |
| `direction` | `up` or `down`. |
| `reset_on_complete` | Reset counter when complete? |
| `persist_state` | Keep count across balls (within same game). |
| `events_when_complete` | Event(s) posted when target reached. |
| `events_when_hit` | Event(s) posted on every count increment. |

---

## Top Lanes with Multiplier

Complete top lanes → increment bonus multiplier. A classic pattern.

```yaml
shots:
  top_lane_1:
    switch: s_top_lane_1
    show_tokens:
      light: l_top_1
  top_lane_2:
    switch: s_top_lane_2
    show_tokens:
      light: l_top_2
  top_lane_3:
    switch: s_top_lane_3
    show_tokens:
      light: l_top_3

shot_groups:
  top_lanes:
    shots: top_lane_1, top_lane_2, top_lane_3
    rotate_left_events: s_left_flipper_active
    rotate_right_events: s_right_flipper_active
    reset_events:
      top_lanes_lit_complete: 1s

variable_player:
  top_lane_1_lit_hit:
    score: 1000
  top_lane_2_lit_hit:
    score: 1000
  top_lane_3_lit_hit:
    score: 1000
  top_lanes_lit_complete{player.bonus_multiplier < 5}:
    bonus_multiplier:
      int: 1
      action: add
  top_lanes_lit_complete:
    score: 10000
```

### Event Naming Convention

When a shot in a shot group is hit, MPF posts events in this format:

```
(shot_name)_(profile_state)_hit
```

For example: `top_lane_1_lit_hit` means shot `top_lane_1` was hit while
in the `lit` state.

When all shots in a group complete:

```
(group_name)_(profile_state)_complete
```

For example: `top_lanes_lit_complete`.

---

## Skill Shot with Lane Change

Skill shot mode runs during ball start, using shots with rotation.

```yaml
# modes/skill_shot/config/skill_shot.yaml
#config_version=6

mode:
  start_events: ball_started
  stop_events: skill_shot_miss, skill_shot_hit, ball_ended
  priority: 200

shots:
  skill_lane_1:
    switch: s_lane_1
    show_tokens:
      light: l_lane_1
  skill_lane_2:
    switch: s_lane_2
    show_tokens:
      light: l_lane_2
  skill_lane_3:
    switch: s_lane_3
    show_tokens:
      light: l_lane_3

shot_groups:
  skill_lanes:
    shots: skill_lane_1, skill_lane_2, skill_lane_3
    rotate_left_events: s_left_flipper_active
    rotate_right_events: s_right_flipper_active

variable_player:
  skill_lane_1_lit_hit:
    score: 25000
  skill_lane_2_lit_hit:
    score: 25000
  skill_lane_3_lit_hit:
    score: 25000

event_player:
  skill_lane_1_lit_hit:
    - skill_shot_hit
  skill_lane_2_lit_hit:
    - skill_shot_hit
  skill_lane_3_lit_hit:
    - skill_shot_hit
  # Miss — any lane hit while unlit
  skill_lane_1_unlit_hit:
    - skill_shot_miss
  skill_lane_2_unlit_hit:
    - skill_shot_miss
  skill_lane_3_unlit_hit:
    - skill_shot_miss
```

---

## Sequential Drop Target Banks

Track drop target completions with a counter.

```yaml
drop_targets:
  dt_1:
    switch: s_drop_1
  dt_2:
    switch: s_drop_2
  dt_3:
    switch: s_drop_3

drop_target_banks:
  dtb_main:
    drop_targets: dt_1, dt_2, dt_3
    reset_coil: c_drop_reset
    reset_events:
      dtb_main_down: 1s           # reset 1s after all targets down

counters:
  drop_bank_counter:
    count_events: dtb_main_down    # fires when all targets in bank are down
    starting_count: 0
    count_complete_value: 3        # complete 3 times for reward
    direction: up
    events_when_complete: drop_bank_award

variable_player:
  dtb_main_down:
    score: 5000
  drop_bank_award:
    score: 50000
```

---

## Carousel Mode Selection

MPF's built-in carousel mode lets players select modes using flipper
buttons. Commonly used for "choose your mode" features.

```yaml
# modes/mode_select/config/mode_select.yaml
#config_version=6

mode:
  start_events: mode_select_ready
  stop_events: mode_selected
  priority: 200
  game_mode: false

carousel:
  mode_carousel:
    selectable_items: mode_a, mode_b, mode_c
    select_item_events: s_start_active
    next_item_events: s_right_flipper_active
    previous_item_events: s_left_flipper_active

event_player:
  carousel_mode_carousel_mode_a_highlighted:
    - highlight_mode_a
  carousel_mode_carousel_mode_b_highlighted:
    - highlight_mode_b
  carousel_mode_carousel_mode_c_highlighted:
    - highlight_mode_c
  carousel_mode_carousel_mode_a_selected:
    - start_mode_a
    - mode_selected
  carousel_mode_carousel_mode_b_selected:
    - start_mode_b
    - mode_selected
  carousel_mode_carousel_mode_c_selected:
    - start_mode_c
    - mode_selected
```

### How It Works

1. Flipper buttons cycle through selectable items.
2. `(carousel_name)_(item)_highlighted` fires as each item is shown.
3. Start button (or configured event) selects the current item.
4. `(carousel_name)_(item)_selected` fires for the chosen item.

---

## Mystery Awards

Random event selection for mystery award features.

```yaml
# Use random_event_player for weighted random selection
random_event_player:
  mystery_award_triggered:
    event_list:
      - event: mystery_points
        weight: 40
      - event: mystery_extra_ball
        weight: 10
      - event: mystery_multiball
        weight: 5
      - event: mystery_multiplier
        weight: 25
      - event: mystery_special
        weight: 20

variable_player:
  mystery_points:
    score: 100000
  mystery_multiplier{player.bonus_multiplier < 5}:
    bonus_multiplier:
      int: 1
      action: add

event_player:
  mystery_extra_ball:
    - award_extra_ball
```

### Conditional Mystery Awards

Use conditions to prevent awarding things the player already has:

```yaml
random_event_player:
  mystery_award_triggered:
    event_list:
      - event: mystery_points
        weight: 40
      - event: mystery_multiplier{player.bonus_multiplier < 5}
        weight: 25
      - event: mystery_points        # fallback if multiplier maxed
        weight: 25
```

---

## Ball Save

Protect the player from early drains after ball launch.

```yaml
ball_saves:
  bs_start:
    active_time: 10s
    enable_events: ball_started
    timer_start_events: balldevice_bd_plunger_ball_eject_success
    auto_launch: true              # auto re-launch saved balls
    balls_to_save: 1               # save up to 1 ball
    early_ball_save_events: s_shooter_lane_active    # optional
```

### Ball Save Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `active_time` | str | *(required)* | How long the save is active after timer starts. |
| `enable_events` | list | — | Events that enable the ball save. |
| `timer_start_events` | list | — | Events that start the save timer (typically ball eject from plunger). |
| `auto_launch` | bool | `false` | Auto-launch saved balls? |
| `balls_to_save` | int | `1` | Max balls to save during one activation. |
| `early_ball_save_events` | list | — | Events that trigger an early save (before timer starts). |
| `disable_events` | list | — | Events that disable the ball save. |
| `hurry_up_time` | str | `None` | Time before end when "hurry up" event fires. |

### Ball Save Events

| Event | When |
|-------|------|
| `ball_save_(name)_enabled` | Ball save is active. |
| `ball_save_(name)_disabled` | Ball save expired or disabled. |
| `ball_save_(name)_saving_ball` | A ball was saved! |
| `ball_save_(name)_hurry_up` | Hurry-up time started (save about to expire). |
| `ball_save_(name)_grace_period` | Grace period active. |

---

## Timed Mode with Hurry-Up

A mode that runs for a limited time with a countdown.

```yaml
# modes/timed_mode/config/timed_mode.yaml
#config_version=6

mode:
  start_events: timed_mode_start
  stop_events: timer_mode_timer_complete, ball_ended
  priority: 200

timers:
  mode_timer:
    start_value: 30
    end_value: 0
    direction: down
    tick_interval: 1s
    start_running: true
    control_events:
      - event: add_time
        action: add
        value: 10
      - event: pause_timer
        action: pause
      - event: resume_timer
        action: resume

variable_player:
  target_hit_during_timed:
    score:
      int: 10000 * (timer_mode_timer_tick + 1)    # more points with more time left
```

### Timer Events

| Event | When |
|-------|------|
| `timer_(name)_tick` | Each tick (kwargs include `ticks`, `ticks_remaining`). |
| `timer_(name)_started` | Timer starts. |
| `timer_(name)_stopped` | Timer stopped (not complete). |
| `timer_(name)_complete` | Timer reached end value. |
| `timer_(name)_paused` | Timer paused. |
| `timer_(name)_time_added` | Time was added. |

---

## Accruals (Collect N Different Things)

Track collecting different items (like balls in Eight Ball).

```yaml
accruals:
  my_accrual:
    events:
      - target_1_hit
      - target_2_hit
      - target_3_hit
    events_when_complete: all_targets_collected
    reset_on_complete: true
    persist_state: true
```

Each event in the list is a "slot" that must be completed once.
Order doesn't matter. When all slots are filled, the completion event fires.

---

## Common Pitfalls

1. **Forgetting `reset_events:` on shot groups** — lanes stay complete forever after first completion.
2. **Not using `persist_state: true` on counters** — counter resets to 0 on every ball.
3. **Using `scoring:` instead of `variable_player:`** — `scoring:` doesn't exist in MPF 0.57.4.
4. **Not stopping modes on `ball_ended`** — modes can bleed into the next ball or even the next game.
5. **Hardcoding light names in shows** — use `show_tokens:` for reusable shows.
6. **Duplicate top-level YAML keys** — `ruamel.yaml` raises `DuplicateKeyError`. Merge into a single block.
7. **Missing `#config_version=6`** — every config file must start with this header.
