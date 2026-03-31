# Bonus & Scoring — Complete Reference

> **MPF 0.57.4 deep-reference guide.**
> Covers the built-in bonus mode, `variable_player:` scoring, and advanced scoring patterns.

---

## Built-in Bonus Mode

MPF ships with a built-in bonus mode that handles end-of-ball bonus calculation,
display, and multiplier logic. You configure it entirely in YAML.

### Minimal Config

```yaml
# modes/bonus/config/bonus.yaml
#config_version=6

mode:
  start_events: ball_ending
  use_wait_queue: true        # CRITICAL — holds ball_ending queue
  priority: 500
  stop_events: bonus_complete
  game_mode: false            # not a "game" mode — runs between balls

mode_settings:
  bonus_entries:
    - event: bonus_ramps
      score: 5000
      player_score_entry: ramps_made       # player var holding the count
    - event: bonus_targets
      score: 1000
      player_score_entry: targets_hit
    - event: bonus_lanes
      score: 3000
      player_score_entry: lanes_completed
  display_delay_ms: 1500       # pause between each bonus line on display
  keep_multiplier: false       # reset bonus_multiplier to 1 after each ball
  hurry_up_event: flipper_cancel    # skip delay when flippers pressed
  end_bonus_event: flipper_cancel   # end entire bonus when flippers pressed
```

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `bonus_entries` | list | *(required)* | List of bonus items to tally |
| `display_delay_ms` | int | `2000` | Milliseconds between each bonus entry display step |
| `keep_multiplier` | bool | `true` | If `false`, resets `player.bonus_multiplier` to 1 after each ball |
| `hurry_up_event` | str | `None` | Event that skips the display delay for remaining entries |
| `end_bonus_event` | str | `None` | Event that immediately ends the bonus sequence |

### Each `bonus_entries` item:

| Key | Description |
|-----|-------------|
| `event` | Event name posted during the bonus sequence (use for slides/sounds) |
| `score` | Points per unit of the player variable |
| `player_score_entry` | Player variable whose value is multiplied by `score` |
| `reset_player_score_entry` | If `true`, resets the player var to 0 after tallying |

---

## Bonus Flow

```
ball_ending fires
    │
    ▼
bonus mode starts (holds ball_ending queue)
    │
    ▼
1. bonus_start event posted
    │
    ▼
2. For EACH bonus_entries item:
   ├── Calculate: entry_score = score × player[player_score_entry]
   ├── Post entry event with score in kwargs
   ├── Wait display_delay_ms (or skip if hurry_up_event fired)
   └── (optionally reset player_score_entry)
    │
    ▼
3. bonus_subtotal posted
   (sum of all entry scores, BEFORE multiplier)
    │
    ▼
4. IF player.bonus_multiplier > 1:
   └── bonus_multiplier event posted
    │
    ▼
5. bonus_total posted
   (subtotal × multiplier)
    │
    ▼
6. Score added to player.score
    │
    ▼
7. bonus_complete event posted
   → mode stops
   → ball_ending queue clears
   → ball_ended fires
   → next ball starts
```

### Events Posted During Bonus

| Event | Kwargs | When |
|-------|--------|------|
| `bonus_start` | — | Beginning of bonus sequence |
| *(entry event)* | `score`, `total_score` | Each bonus entry |
| `bonus_subtotal` | `score` | After all entries, before multiplier |
| `bonus_multiplier` | `multiplier` | If multiplier > 1 |
| `bonus_total` | `score` | Final total after multiplier |
| `bonus_complete` | — | Bonus is done |

---

## Multiplier

MPF's bonus mode automatically reads `player.bonus_multiplier`.

- If the variable exists and is > 1, the subtotal is multiplied.
- If `keep_multiplier: false`, the variable is reset to 1 after the bonus is paid out.
- If `keep_multiplier: true` (default), the multiplier persists across balls.

To increment the multiplier during gameplay:

```yaml
variable_player:
  bonus_mult_target_hit:
    bonus_multiplier:
      int: 1
      action: add
```

To cap the multiplier:

```yaml
variable_player:
  bonus_mult_target_hit{player.bonus_multiplier < 5}:
    bonus_multiplier:
      int: 1
      action: add
```

---

## Scoring with `variable_player:`

MPF 0.57.4 uses `variable_player:` for ALL scoring. There is **no** `scoring:` section.

### Basic Scoring

```yaml
variable_player:
  # Simple — add fixed points
  target_hit:
    score: 1000

  # With condition guard
  special_hit{player.special_lit}:
    score: 50000
```

### Player Variables

Any key under an event that is NOT `score` creates/modifies a player variable:

```yaml
variable_player:
  ramp_made:
    score: 5000
    ramps_made:              # player.ramps_made
      int: 1
      action: add            # add (default), set, add_machine, set_machine
  
  ball_1_collected_p_odd{not player.ball_1_collected}:
    score: 3000
    ball_1_collected:
      int: 1                 # treated as truthy
      action: set
```

### Dynamic (Calculated) Scoring

Use `int:` with an expression for dynamic scores:

```yaml
variable_player:
  # Score based on a player variable
  ramp_complete:
    score:
      int: 25000 * current_player.ramps
  
  # Score based on event kwargs
  combo_scored:
    score:
      int: 10000 * (combo_count + 1)
  
  # Fixed value
  mode_started:
    counter:
      int: 5
      action: set
```

### `action:` Values

| Action | Behaviour |
|--------|-----------|
| `add` | Add value to existing (default) |
| `set` | Replace existing value |
| `add_machine` | Add to a machine-wide variable (persists across games) |
| `set_machine` | Set a machine-wide variable |

### `block:` — Prevent Lower-Priority Modes from Scoring

```yaml
variable_player:
  jackpot_hit:
    score:
      int: 50000
      block: true     # lower-priority modes won't score on this event
```

When `block: true`, the event is consumed by this mode and not passed to
modes with lower priority. Useful for jackpot modes that override base scoring.

### `float:` — For Non-Integer Values

```yaml
variable_player:
  timer_tick:
    time_remaining:
      float: 0.5
      action: add
```

### `string:` — For String Variables

```yaml
variable_player:
  mode_selected:
    current_mode:
      string: "multiball"
      action: set
```

---

## Condition Syntax

Conditions go in curly braces after the event name:

```yaml
variable_player:
  # Boolean check
  target_hit{player.target_lit}:
    score: 5000

  # Negation
  target_hit{not player.already_collected}:
    score: 3000

  # Numeric comparison
  ramp_hit{player.ramps >= 3}:
    score: 25000

  # Player number (parity for odd/even routing)
  s_lane_1_active{current_player.number % 2 == 1}:
    score: 3000

  # Compound conditions
  target_hit{player.target_lit and player.ball >= 2}:
    score: 10000
```

### Important Condition Notes

- Use `player.variable_name` in conditions (NOT `current_player.variable_name`
  in mode-level `event_player:` — see ADR-005).
- `current_player.variable_name` works in `variable_player:` expressions
  for the `int:` / `float:` value calculation.
- Conditions are Python-like expressions evaluated by MPF's config validator.

---

## Eight Ball Bonus Formula

The Eight Ball pinball machine uses this bonus formula:

```
bonus = (balls_collected × 3,000) × bonus_multiplier + base_bonus_locked
```

| Variable | Resets when |
|----------|------------|
| `balls_collected` | Each rack completion (not each ball) |
| `base_bonus_locked` | Never during the game (accumulates across racks and balls) |
| `bonus_multiplier` | After each ball's bonus payout (`keep_multiplier: false`) |

---

## Common Pitfalls

1. **Using `scoring:` instead of `variable_player:`** — `scoring:` does not exist in MPF 0.57.4. Use `variable_player:` for all scoring.
2. **Forgetting `use_wait_queue: true` in bonus mode** — without it, the ball ends before bonus is displayed.
3. **Duplicate `variable_player:` blocks** — YAML does not allow duplicate top-level keys. Extend the existing block.
4. **Missing condition guard on collectibles** — without `{not player.ball_1_collected}`, re-hitting a switch scores again.
5. **`keep_multiplier: true` when you want per-ball reset** — set to `false` if the multiplier should reset after each ball.
