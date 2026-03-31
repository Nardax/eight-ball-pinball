# MPF 0.57.4 — Config Players Reference

> **Source:** [missionpinball.org/latest/config_players](https://missionpinball.org/latest/config_players/)
>
> Config players have nothing to do with human pinball players.
> They are MPF's mechanism for **making things happen in response to events**.

---

## What Are Config Players?

Config players are the primary way you connect events to actions in MPF.
When an event fires, config players "play" a response — score points, fire a
coil, start a show, play a sound, post another event, etc.

They work in two places with slightly different naming:

| Context | Section name | Triggered by |
|---|---|---|
| Config file (machine or mode) | `(type)_player:` | An event you specify |
| Show step | `(type)s:` | The show step itself (no event needed) |

**Config file example:**

```yaml
sound_player:
  ball_starting:
    snd_ball_launch: play
```

**Show step equivalent:**

```yaml
- duration: 2s
  sounds:
    snd_ball_launch: play
```

### Scope Rules

- **Mode-level** config players are **only active while that mode is running**.
  When the mode stops, all effects started by its config players are
  automatically undone (shows stop, lights release, etc.).
- **Machine-level** config players are **always active** regardless of mode
  state.  Use these sparingly — typically only for hardware-level reactions.

---

## Complete Config Players Reference

| Config Section | Show Section | Purpose |
|---|---|---|
| `variable_player:` | `variables:` | Add/set player or machine variables (**scoring**) |
| `event_player:` | `events:` | Post additional events when an event occurs |
| `show_player:` | `shows:` | Start / stop / pause / resume shows |
| `light_player:` | `lights:` | Set light / LED colors |
| `coil_player:` | `coils:` | Pulse / enable / disable coils |
| `flasher_player:` | `flashers:` | Flash flasher devices |
| `sound_player:` | `sounds:` | Play sounds |
| `slide_player:` | `slides:` | Show slides on displays |
| `widget_player:` | `widgets:` | Add / remove / update display widgets |
| `segment_display_player:` | `segment_displays:` | Update segment displays |
| `playlist_player:` | `playlists:` | Control audio playlists |
| `track_player:` | `tracks:` | Control audio tracks |
| `queue_event_player:` | `queue_events:` | Post queue events (block until handlers finish) |
| `random_event_player:` | `random_events:` | Post a random event from a weighted list |
| `queue_relay_player:` | N/A | Relay and transform queue events |
| `blinkenlight_player:` | `blinkenlights:` | Control blinkenlight effects |
| `hardware_sound_player:` | `hardware_sounds:` | Trigger sounds on hardware sound boards |
| `gi_player:` | `gis:` | Control general illumination |

---

## variable_player (Scoring) — Deep Dive

> **Docs:** [config/variable_player](https://missionpinball.org/latest/config/variable_player/)

This is the most important config player for game logic.  It adds to,
sets, or replaces player variables and machine variables in response to
events.  "Scoring" in MPF is just adding to the `score` player variable.

> **Important:** `variable_player:` entries that target player variables can
> only be used in **mode** config files.  Entries that target machine
> variables (`add_machine` / `set_machine`) may also appear in the
> machine-wide config.

### Simple add (most common)

```yaml
variable_player:
  target_1_hit:
    score: 1000
```

Adds 1000 to `player.score`.

### Multiple variables at once

```yaml
variable_player:
  ramp_hit:
    score: 10000
    ramps: 1
```

### Set (replace) instead of add

```yaml
variable_player:
  ramp_timeout:
    ramps:
      int: 0
      action: set
```

### Math expression with player variable

```yaml
variable_player:
  ramp_complete:
    score:
      int: 25000 * current_player.ramps
```

### Block lower-priority modes

Prevents the same event from also being handled by a lower-priority mode's
`variable_player:`.

```yaml
# Full syntax
variable_player:
  jackpot_hit:
    score:
      int: 5000
      block: true

# Shorthand (pipe) syntax
variable_player:
  jackpot_hit:
    score: 5000|block
```

### String variable

```yaml
variable_player:
  player_album_value{value==1}:
    album_name:
      string: SILVER
```

### Machine variable

Machine variables require an explicit `action:` — no shorthand.

```yaml
variable_player:
  game_ended:
    total_games:
      int: 1
      action: add_machine
```

### Score to a specific player

```yaml
variable_player:
  add_to_player_2:
    score:
      int: 1000
      player: 2
```

### Float variable

```yaml
variable_player:
  some_event:
    multiplier:
      float: 1.5
      action: set
```

### Actions

| Action | Meaning |
|---|---|
| `add` | *(default)* Add value to existing player variable |
| `set` | Replace the player variable with the given value |
| `add_machine` | Add value to a machine variable |
| `set_machine` | Replace a machine variable with the given value |

### Expanded vs. shorthand syntax

```yaml
# Shorthand — equivalent to action: add
variable_player:
  some_event:
    score: 1000
    aliens: 1

# Expanded — required for set, block, machine vars, player targeting
variable_player:
  some_event:
    score:
      int: 1000
      action: add
    aliens:
      int: 1
      action: add
```

---

## event_player

> **Docs:** [config/event_player](https://missionpinball.org/latest/config/event_player/)

Posts one or more events when a triggering event fires.  Think of it as
simple if-then game logic wiring.

### Basic usage

```yaml
event_player:
  ball_starting:
    - show_ball_start_animation
    - play_start_sound
    - start_first_mode
  ball_ending:
    - show_ball_ending_animation
```

### With delay (pipe syntax)

```yaml
event_player:
  some_event|2s:
    - delayed_event
```

The `delayed_event` fires 2 seconds after `some_event`.

### With conditions

```yaml
event_player:
  s_target_active{current_player.mode_active}:
    - start_special_mode
```

### In a show step

```yaml
- duration: 1s
  events: my_custom_event
```

---

## show_player

> **Docs:** [config/show_player](https://missionpinball.org/latest/config/show_player/)

Starts, stops, pauses, resumes, or advances shows.

### Express syntax

```yaml
show_player:
  some_event: my_show_name
```

### Full syntax

```yaml
show_player:
  mode_base_started:
    my_show:
      action: play
      loops: -1        # infinite
      speed: 1
      priority: 0
      show_tokens:
        lights: l_my_light

  mode_base_stopped:
    my_show:
      action: stop
```

### Actions

| Action | Meaning |
|---|---|
| `play` | *(default)* Start the show |
| `stop` | Stop the show, undo its effects |
| `pause` | Freeze on current step |
| `resume` | Continue a paused show |
| `advance` | Manually move to next step |
| `step_back` | Manually move to previous step |
| `queue` | Queue show to play after the current one |

### Key settings

| Setting | Default | Notes |
|---|---|---|
| `loops:` | `-1` (infinite) | `0` = play once; `1` = play twice (loops once) |
| `speed:` | `1` | `2` = double speed; `0.5` = half speed |
| `start_step:` | `1` | Which step to begin on |
| `manual_advance:` | `false` | If true, show won't auto-advance by time |
| `sync_ms:` | *(empty)* | Sync multiple shows to a ms boundary |
| `block_queue:` | `false` | Block a queue event until the show finishes |
| `show_tokens:` | *(empty)* | Key-value pairs to replace tokens in the show |

### In a show step

```yaml
- duration: 2s
  shows:
    nested_show:
      action: play
      loops: 0
```

---

## light_player

> **Docs:** [config/light_player](https://missionpinball.org/latest/config/light_player/)

Sets light / LED colors.

### Basic usage

```yaml
light_player:
  some_event:
    l_led1: red
    l_led2:
      color: blue
      fade: 200ms
    l_led3: off
```

### Color values

Colors can be: named (`red`, `turquoise`), hex (`22FFCC`), hex with
brightness (`22FFCC%60`), or brightness only (`AA`).

### Special color directives

| Directive | Meaning |
|---|---|
| `on` | Use the light's `default_on_color` (or white) |
| `off` | Actively hold the light at zero power |
| `stop` | Release control — let lower-priority shows through |

### Tags and wildcards

```yaml
light_player:
  # By tag
  some_event:
    my_light_tag: red

  # Wildcard — all lights
  panic_event:
    "*": off
```

### Subscription syntax

Automatically applies when condition becomes true, and removes when false:

```yaml
light_player:
  "{current_player.score > 1000000}":
    l_score_1M: white
```

### Fade

```yaml
light_player:
  some_event:
    l_led1:
      color: red
      fade: 500ms
```

### In a show step

```yaml
- duration: 1s
  lights:
    l_led1: green
- duration: 1s
  lights:
    l_led1: red
```

---

## coil_player

> **Docs:** [config/coil_player](https://missionpinball.org/latest/config/coil_player/)

Pulses, enables, or disables coils / solenoids / drivers.

### Express syntax

```yaml
coil_player:
  some_event: c_slingshot     # pulses by default
```

### Full syntax

```yaml
coil_player:
  some_event:
    c_slingshot:
      action: pulse
      pulse_ms: 30

  hold_event:
    c_magnet:
      action: enable
      hold_power: 0.5    # 50% duty cycle

  release_event:
    c_magnet:
      action: disable
```

### Actions

| Action | Meaning |
|---|---|
| `pulse` | *(default)* Fire for `pulse_ms` then turn off |
| `enable` / `on` | Hold the coil on (use `hold_power` to limit) |
| `disable` / `off` | Turn the coil off |

### In a show step

```yaml
- duration: 1s
  coils:
    c_flasher: pulse
```

---

## flasher_player

> **Docs:** [config/flasher_player](https://missionpinball.org/latest/config/flasher_player/)

Flashes flasher devices (a convenience layer over coil_player for
flasher-type coils).

```yaml
flasher_player:
  some_event:
    fl_flasher_1:
      ms: 100    # flash duration in ms
```

### In a show step

```yaml
- duration: 500ms
  flashers:
    fl_flasher_1: 100ms
```

---

## sound_player

> **Docs:** [config/sound_player](https://missionpinball.org/latest/config/sound_player/)

Plays, stops, or loops sound assets.

```yaml
sound_player:
  ball_starting:
    snd_ball_launch:
      action: play
      volume: 0.8
      loops: 0           # play once

  mode_stopped:
    snd_background:
      action: stop
```

### In a show step

```yaml
- duration: 2s
  sounds:
    snd_chime: play
```

---

## slide_player

> **Docs:** [config/slide_player](https://missionpinball.org/latest/config/slide_player/)

Shows slides on displays (MPF-MC).

```yaml
slide_player:
  ball_started:
    ball_start_slide:
      expire: 3s
      target: default

  ball_ended:
    ball_start_slide:
      action: remove
```

### In a show step

```yaml
- duration: 3s
  slides:
    my_slide_name:
      expire: 3s
```

---

## widget_player

> **Docs:** [config/widget_player](https://missionpinball.org/latest/config/widget_player/)

Adds, removes, or updates widgets on existing slides.

```yaml
widget_player:
  score_updated:
    score_widget:
      action: update
      slide: main_slide

  mode_started:
    mode_widget:
      action: add
      slide: main_slide
```

### In a show step

```yaml
- duration: 2s
  widgets:
    my_widget:
      action: add
      slide: main_slide
```

---

## segment_display_player

> **Docs:** [config/segment_display_player](https://missionpinball.org/latest/config/segment_display_player/)

Updates segment displays (score reels, DMDs acting as segment displays).

```yaml
segment_display_player:
  ball_started:
    my_segment:
      text: "{machine.credits_string}"
      expire: 3s
```

### In a show step

```yaml
- duration: 2s
  segment_displays:
    my_segment:
      text: "HELLO"
```

---

## playlist_player

> **Docs:** [config/playlist_player](https://missionpinball.org/latest/config/playlist_player/)

Controls audio playlists (background music sequences).

```yaml
playlist_player:
  mode_started:
    my_playlist:
      action: play
      shuffle: true
      crossfade_time: 2s
```

### In a show step

```yaml
- duration: 1s
  playlists:
    my_playlist:
      action: play
```

---

## track_player

> **Docs:** [config/track_player](https://missionpinball.org/latest/config/track_player/)

Controls audio tracks (volume, play, stop).

```yaml
track_player:
  mode_started:
    sfx:
      action: play
      volume: 0.5
```

---

## queue_event_player

> **Docs:** [config/queue_event_player](https://missionpinball.org/latest/config/queue_event_player/)

Posts **queue events** — events that wait for all handlers to finish before
continuing.  No show equivalent.

```yaml
queue_event_player:
  some_event:
    queue_event: my_queue
    events_when_finished: my_queue_done
```

When `some_event` fires, `my_queue` is posted as a queue event.
After **all** handlers of `my_queue` are done (including any that blocked),
`my_queue_done` fires.

### Use case

Mode-stopping events are queue events.  Use `queue_event_player` with
`show_player` and `block_queue: true` to play an "outro" show before a
mode fully stops.

---

## random_event_player

> **Docs:** [config/random_event_player](https://missionpinball.org/latest/config/random_event_player/)

Posts a randomly selected event from a list — great for mystery awards or
randomized callouts.

### Equal probability

```yaml
random_event_player:
  trigger_event:
    events:
      - event_a
      - event_b
      - event_c
```

### Weighted probability

```yaml
random_event_player:
  trigger_event:
    events:
      rare_event: 5
      common_event: 45
      another_common: 50
```

### With conditions and fallback

```yaml
random_event_player:
  trigger_event:
    events:
      event1{current_player.level > 3}: 25
      event2{current_player.level <= 3}: 75
    fallback_event: default_event
```

### Key settings

| Setting | Default | Notes |
|---|---|---|
| `force_all:` | `true` | Every event plays once before any repeats |
| `force_different:` | `true` | Same event never appears twice in a row |
| `scope:` | `player` | `player` or `machine` — per-player or global tracking |

---

## Common Patterns

### Conditional events

All config players support **conditional events** using `{expression}`:

```yaml
variable_player:
  s_target_hit{current_player.multiball_active}:
    score: 50000
```

The condition is evaluated when the event fires.  If false, the entry is
skipped.

### Delayed events (pipe syntax)

Add `|<time>` after the event name to delay execution:

```yaml
event_player:
  my_event|3s:
    - delayed_event
```

### Subscription (dynamic) syntax

Some config players support **subscription** entries that auto-activate
when a condition becomes true and auto-deactivate when it becomes false:

```yaml
light_player:
  "{current_player.jackpot_lit}":
    l_jackpot: red
```

### Express config

Many config players support a one-line "express" format for the most
common action:

```yaml
# Express — pulse coil
coil_player:
  some_event: c_my_coil

# Express — play show
show_player:
  some_event: my_show

# Express — play sound
sound_player:
  some_event: snd_chime
```

---

## Config vs. Show Syntax Comparison

Here is a side-by-side example showing the same actions in a config file
versus a show file:

**Config file** (event-triggered):

```yaml
# In a mode config
event_player:
  ball_started:
    - enable_flippers

light_player:
  ball_started:
    l_shoot_again: green

sound_player:
  ball_started:
    snd_launch: play

variable_player:
  ball_started:
    balls_played: 1
```

**Show file** (step-triggered):

```yaml
#show_version=6
- duration: 2s
  events: enable_flippers
  lights:
    l_shoot_again: green
  sounds:
    snd_launch: play
  variables:
    balls_played: 1
```

Note how each `(type)_player:` becomes `(type)s:` in the show, and the
event is omitted because the show step itself is the trigger.

---

## Eight Ball Project Notes

In this project's `base.yaml` mode, the key config players in use are:

- **`variable_player:`** — Routes switch hits to score and ball-collected
  flags via odd/even parity events. Uses `{not player.ball_X_collected}`
  guards to prevent double-scoring.
- **`event_player:`** — Chains intermediate events like
  `ball_8_collected_ready` → `eight_ball_rack_complete`. Uses pipe syntax
  for delays (e.g., `eight_ball_rack_complete|2s:`).
- **`show_player:`** — Controls lamp shows for playfield inserts.
- **`coil_player:`** — Fires the kickback coil on drain-save events.

---

*Generated for the Eight Ball Pinball project. Based on MPF 0.57.4 official
documentation at [missionpinball.org](https://missionpinball.org/latest/).*
