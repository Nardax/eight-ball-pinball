# MPF Event System — Deep Reference

> **MPF 0.57.4** · All config files require `#config_version=6` at the top.

---

## 1. Event Types

MPF has four distinct event types. Understanding which type an event uses is critical
for knowing how handlers interact with it.

### Standard Events

Posted and forgotten. Handlers run but cannot influence the event or its caller.
This is the most common type — the vast majority of events are standard.

```
ball_started          # ball is live
mode_base_started     # a mode finished starting
player_added          # new player joined
```

### Boolean / Request Events

Allow handlers to **approve or deny** an action. Any single handler returning `False`
causes the entire request to be denied.

```
request_to_start_game     # credits module denies if no credits
request_to_add_player     # can deny adding a player (e.g., max players reached)
```

The originator checks the combined result and decides whether to proceed.

### Queue Events

Processing **waits** until every handler explicitly releases its hold. Handlers call
`queue.wait()` to pause the pipeline and `queue.clear()` when their work is done.
This lets modes/devices perform setup or teardown before the framework continues.

```
ball_starting       # modes hook in to prepare before ball is served
ball_ending         # bonus mode hooks in to display/calculate bonus
game_starting       # game-level setup (reset scores, etc.)
game_ending         # game-level teardown
mode_<name>_starting   # per-mode startup work
mode_<name>_stopping   # per-mode shutdown work
```

### Relay Events

Can **modify event parameters** as they pass through the handler chain. Each handler
receives the current kwargs, may alter them, and passes them to the next handler.

```
ball_drain          # ball save can decrement the "balls" count to "save" a ball
```

A ball save handler receiving `balls: 2` can change it to `balls: 1`, effectively
saving one ball from draining.

---

## 2. Conditional Events

Conditions are appended to event names inside `{}` in YAML config. The event only
triggers its action when the condition evaluates to `True`.

```yaml
event_name{condition}: action
```

### Variables Available in Conditions

| Syntax | Description |
|---|---|
| `current_player.variable_name` | Player variables (score, custom vars, etc.) |
| `machine.variable_name` | Machine-wide variables |
| `device.TYPE.NAME.PLACEHOLDER` | Device state values |
| `settings.setting_name` | Operator settings |
| `game.attribute` | Game object attributes (e.g., `game.num_players`) |
| `players[x].variable` | Any player's variables by 0-based index |
| `mode["mode_name"].stopping` | Whether a mode is in the process of stopping |

> **⚠️ CRITICAL:** In mode-level config (event_player, variable_player, etc.),
> use **`current_player.`** to access player variables. The shorthand **`player.`**
> does NOT work — it silently resolves to nothing and your condition will never
> match. This is the single most common config bug.

#### Device state examples

```yaml
# Counter value
event{device.counters.my_counter.value == 5}: do_something

# Shot state name
event{device.shots.my_shot.state_name == 'lit'}: collect_award

# Sequence current step
event{device.sequences.my_seq.value == 3}: almost_done
```

### Operators

| Category | Operators |
|---|---|
| Comparison | `==` `!=` `>` `>=` `<` `<=` |
| Boolean | `and` `or` `not` |
| Math | `+` `-` `*` `/` `//` (floor div) `%` (mod) `**` (power) |
| Grouping | `(` `)` |

### Examples

```yaml
event_player:
  # Simple equality
  ball_started{ball==1}:
    - first_ball_slide

  # Multiple conditions
  ball_started{ball==3 and current_player.score < 10000}:
    - you_stink_slide

  # Device state check
  s_target_active{device.shots.my_shot.state_name=='lit'}:
    - start_multiball

  # Math expression
  ball_started{ball > 1 and current_player.score < ((ball - 1) * 10000)}:
    - uh_oh_slide

  # Player number routing (odd/even parity)
  s_lane_1_active{current_player.number==1 or current_player.number==3}:
    - ball_1_collected_p_odd
  s_lane_1_active{current_player.number==2 or current_player.number==4}:
    - ball_1_collected_p_even

  # Negation guard — prevent double-collection
  ball_1_collected_p_odd{not current_player.ball_1_collected}:
    - award_ball_1
```

---

## 3. Subscription Syntax (Config Players)

Certain config players (notably `light_player`, `widget_player`, `slide_player`)
support **subscription conditions** — wrapped entirely in `""` with `{}`. These
automatically apply when the condition becomes true and revert when it becomes false.

```yaml
light_player:
  # Fires whenever machine var equals 23; reverts when it doesn't
  "{machine.test_machine_var == 23}":
    led4: red

  # Fires whenever current player var equals 42
  "{current_player.test_player_var == 42}":
    led5: red
```

This is fundamentally different from conditional events. A conditional event only
checks the condition at the moment the event fires. A subscription **continuously
monitors** the variable and re-evaluates whenever it changes.

---

## 4. Event Parameters (kwargs)

Events carry keyword arguments that handlers can read. These same kwargs are
available inside `{}` conditions.

| Event | Key Parameters |
|---|---|
| `ball_started` | `ball`, `player_num` |
| `ball_drain` | `balls` (count of balls that drained) |
| `player_added` | `player`, `num` |
| `ball_will_end` | _(none — use player vars)_ |
| `timer_(name)_tick` | `ticks`, `ticks_remaining` |
| `timer_(name)_complete` | _(none)_ |
| Switch events | `switch_name`, `state` |
| Shot events | `profile`, `state` |

Parameters are accessed directly by name in conditions:

```yaml
event_player:
  ball_started{ball == 3}: third_ball_event
```

---

## 5. Dynamic Values / Placeholders

MPF supports dynamic value resolution in several contexts. The syntax varies
depending on where the placeholder appears.

### In `variable_player:` (int/float expressions)

Use bare `current_player.variable` — no braces, no parens:

```yaml
variable_player:
  collect_ramp:
    score: 25000 * current_player.ramps
```

### In slide/widget `text:` fields

Use parentheses `()` for player variables:

```yaml
slides:
  score_slide:
    widgets:
      - type: text
        text: (score)          # current player's score
```

Or use braces `{}` with the full machine path:

```yaml
widgets:
  - type: text
    text: "{machine.current_player.score}"
```

### In show tokens

```yaml
shows:
  my_show:
    - duration: 1s
      lights:
        (leds): red            # token replaced at show-play time
```

---

## 6. Delayed Events

Use **pipe syntax** to delay an event posting:

```yaml
event_player:
  eight_ball_rack_complete|2s:
    - rack_complete_done

  some_event|500ms:
    - delayed_response
```

Valid time suffixes: `ms` (milliseconds), `s` (seconds).

> **Note:** A nested `delay:` key does NOT work in MPF 0.57.4 `event_player`.
> Always use the pipe syntax.

---

## 7. Key Built-in Events Reference

### Machine Lifecycle

| Event | Type | When |
|---|---|---|
| `init_done` | Standard | All machine init complete |
| `machine_reset_phase_1` | Standard | First reset phase |
| `machine_reset_phase_2` | Standard | Second reset phase |
| `machine_reset_phase_3` | Standard | Final reset phase — modes start here |

### Game Lifecycle

| Event | Type | When |
|---|---|---|
| `game_will_start` | Standard | About to start a game |
| `game_starting` | **Queue** | Game is starting — handlers can wait |
| `game_started` | Standard | Game has started |
| `game_ending` | **Queue** | Game is ending — handlers can wait |
| `game_ended` | Standard | Game has ended |

### Ball Lifecycle

| Event | Type | When |
|---|---|---|
| `ball_will_start` | Standard | About to start a ball |
| `ball_starting` | **Queue** | Ball is starting — handlers can wait |
| `ball_started` | Standard | Ball is live (kwargs: `ball`, `player_num`) |
| `ball_will_end` | Standard | Ball is about to end (bonus runs here) |
| `ball_ending` | **Queue** | Ball is ending — handlers can wait |
| `ball_ended` | Standard | Ball has ended |
| `ball_drain` | **Relay** | Ball(s) drained (kwargs: `balls`) — ball save modifies count |

### Player Events

| Event | Type | When |
|---|---|---|
| `player_added` | Standard | New player added (kwargs: `player`, `num`) |
| `player_turn_starting` | Standard | Player turn is starting |
| `player_turn_started` | Standard | Player turn has started |
| `player_turn_will_end` | Standard | Player turn is about to end |
| `player_turn_ended` | Standard | Player turn has ended |
| `player_(var_name)` | Standard | Fires when any player variable changes |

### Mode Events

For a mode named `base`:

| Event | Type | When |
|---|---|---|
| `mode_base_will_start` | Standard | Mode is about to start |
| `mode_base_starting` | **Queue** | Mode is starting — handlers can wait |
| `mode_base_started` | Standard | Mode has started |
| `mode_base_will_stop` | Standard | Mode is about to stop |
| `mode_base_stopping` | **Queue** | Mode is stopping — handlers can wait |
| `mode_base_stopped` | Standard | Mode has stopped |

### Switch Events

For a switch named `s_lane_1`:

| Event | When |
|---|---|
| `s_lane_1_active` | Switch activated |
| `s_lane_1_inactive` | Switch deactivated |

### Shot Events

For a shot named `my_shot` with profile `my_profile` in state `lit`:

| Event | When |
|---|---|
| `my_shot_hit` | Shot hit (any profile, any state) |
| `my_shot_my_profile_hit` | Shot hit with specific profile active |
| `my_shot_my_profile_lit_hit` | Shot hit in specific profile + state |
| `my_shot_lit_hit` | Shot hit in specific state (any profile) |

### Timer Events

For a timer named `hurry_up`:

| Event | When |
|---|---|
| `timer_hurry_up_started` | Timer started |
| `timer_hurry_up_tick` | Timer ticked (kwargs: `ticks`, `ticks_remaining`) |
| `timer_hurry_up_stopped` | Timer stopped |
| `timer_hurry_up_complete` | Timer reached zero |
| `timer_hurry_up_paused` | Timer paused |

---

## 8. Quick Gotchas

1. **`player.` vs `current_player.`** — Always use `current_player.` in mode
   configs. `player.` silently fails.

2. **Duplicate top-level keys** — YAML does not allow two `event_player:` blocks
   in the same file. MPF uses `ruamel.yaml` which raises `DuplicateKeyError`.
   Merge all entries under a single block.

3. **Delayed events** — Use `event|2s:` pipe syntax. A nested `delay:` key is
   not valid in `event_player`.

4. **Queue events need clearing** — If you hook into a queue event with
   `queue.wait()`, you **must** call `queue.clear()` or the game will hang.

5. **Relay events modify kwargs** — Handlers must return the (potentially
   modified) kwargs dict. Forgetting to return it drops the data.

6. **`#config_version=6`** — Required at the top of every YAML config file.
   Show files use `#show_version=6`.

7. **Boolean conditions** — Use lowercase `and`, `or`, `not`. Python-style.
   Uppercase `AND`, `OR` will not work.

---

*Reference: [MPF Events Documentation](https://missionpinball.org/latest/events/) · MPF 0.57.4*
