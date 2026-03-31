# Shows — Complete Reference

> **MPF 0.57.4 deep-reference guide.**
> Covers show file format, `show_player:`, tokens, and built-in shows.

---

## Show File Format

```yaml
#show_version=6

- duration: 3s
  lights:
    l_led1: red
  slides:
    my_slide:
      widgets:
        - type: text
          text: "HELLO"
  sounds:
    my_sound: play

- duration: 2s
  lights:
    l_led1: blue

- duration: 1s
  lights:
    l_led1: off
```

### Key Rules

| Rule | Detail |
|------|--------|
| `#show_version=6` | **Required** at the top of every show file (for MPF 0.57.x). |
| Steps | Separated by dashes (`-`). Each step is a list item. |
| `duration:` | How long each step lasts. Supports `ms`, `s`, `m` suffixes. If omitted on the last step, it holds indefinitely. |
| Config player sections | Use **plural names WITHOUT the `_player` suffix**. In shows, you write `lights:` not `light_player:`, `slides:` not `slide_player:`, etc. |
| File location | `modes/(mode_name)/shows/(show_name).yaml` for mode shows, or `machine/shows/(show_name).yaml` for machine-wide shows. |
| Auto-loading | Shows placed in `shows/` folders are automatically loaded by MPF. No explicit registration needed. |

---

## Config Player Section Names (Show vs. Config)

In a **show file**, config player sections drop the `_player` suffix and use the plural form:

| Config File (mode YAML) | Show File |
|--------------------------|-----------|
| `light_player:` | `lights:` |
| `led_player:` | `leds:` |
| `slide_player:` | `slides:` |
| `sound_player:` | `sounds:` |
| `show_player:` | `shows:` |
| `event_player:` | `events:` |
| `widget_player:` | `widgets:` |
| `coil_player:` | `coils:` |

---

## `show_player:` — Playing Shows from Config

Use `show_player:` in your mode config to start, stop, or control shows in
response to events.

### Basic Usage

```yaml
show_player:
  # Play a show when an event fires
  mode_attract_started:
    attract_show:
      action: play
      loops: -1            # -1 = infinite loop
      speed: 1.0           # playback speed multiplier
  
  # Stop a show
  mode_attract_stopped:
    attract_show:
      action: stop
```

### All `show_player:` Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `action` | str | `play` | `play`, `stop`, `pause`, `resume`, `advance`, `step_back`, `update` |
| `loops` | int | `0` | Number of times to loop. `-1` = infinite. `0` = play once. |
| `speed` | float | `1.0` | Playback speed multiplier. `2.0` = double speed. |
| `priority` | int | `0` | Show priority (higher wins for same device). |
| `sync_ms` | int | `None` | Synchronise show start to a clock interval (ms). |
| `manual_advance` | bool | `false` | If `true`, show only advances when you post `advance` action. |
| `show_tokens` | dict | `None` | Token substitutions (see below). |
| `start_step` | int | `1` | Which step to start on (1-indexed). |
| `key` | str | show name | Unique key for controlling this show instance. |

### Multiple Shows on One Event

```yaml
show_player:
  multiball_started:
    light_show_1:
      action: play
      loops: -1
    flasher_show:
      action: play
      loops: 3
```

### Controlling a Running Show

```yaml
show_player:
  # Pause
  pause_event:
    my_show:
      action: pause
  
  # Resume
  resume_event:
    my_show:
      action: resume
  
  # Advance one step (for manual_advance shows)
  advance_event:
    my_show:
      action: advance
```

---

## `show_tokens:` — Dynamic Device Binding

Show tokens let you write generic shows that work with different devices.
Instead of hardcoding device names in the show, you use placeholders.

### In the Show File

```yaml
#show_version=6

- duration: 500ms
  lights:
    (light): on

- duration: 500ms
  lights:
    (light): off
```

### In the Config

```yaml
show_player:
  target_lit:
    flash_show:
      action: play
      loops: -1
      show_tokens:
        light: l_target_1
```

Now `(light)` in the show is replaced with `l_target_1` at runtime.

### Multiple Tokens

```yaml
# Show file
- duration: 1s
  lights:
    (left_light): red
    (right_light): blue

# Config
show_player:
  event_name:
    my_show:
      show_tokens:
        left_light: l_left
        right_light: l_right
```

### Tokens from Shot Groups

When shots use `show_tokens:`, the shot group automatically passes them
to shows:

```yaml
shots:
  lane_1:
    switch: s_lane_1
    show_tokens:
      light: l_lane_1
  lane_2:
    switch: s_lane_2
    show_tokens:
      light: l_lane_2
```

---

## Built-in Shows

MPF includes several built-in shows you can use without creating show files:

| Show Name | Behaviour |
|-----------|-----------|
| `on` | Turns lights on solid (at full brightness, white for LEDs). |
| `off` | Turns lights off. |
| `flash` | 1 second on, 1 second off — repeating flash. |
| `led_color` | Sets an LED to a specific colour (use with show tokens or colour settings). |

### Using Built-in Shows

```yaml
show_player:
  ball_started:
    flash:
      show_tokens:
        light: l_shoot_again
      loops: -1

  ball_ended:
    flash:
      action: stop
```

---

## Show Priority and Stacking

- Shows have a `priority:` setting (default `0`).
- When multiple shows target the same device, the highest priority wins.
- Mode shows automatically inherit the mode's priority.
- Use `key:` to name show instances so you can stop/control them later.

```yaml
show_player:
  # Base mode show — low priority
  base_started:
    idle_show:
      key: playfield_lights
      priority: 0
      loops: -1

  # Multiball overrides — high priority
  multiball_started:
    multiball_show:
      key: playfield_lights
      priority: 100
      loops: -1
```

When `multiball_show` stops, `idle_show` automatically takes back control
of the lights (if it's still running).

---

## Shows in Mode Folders

```
machine/
  modes/
    attract/
      config/
        attract.yaml
      shows/
        attract_light_show.yaml    ◄── auto-loaded when mode starts
        attract_flasher.yaml
    base/
      config/
        base.yaml
      shows/
        playfield_idle.yaml
```

Shows in a mode's `shows/` folder are automatically available when that
mode is running. They are referenced by filename (without `.yaml`).

---

## Show Steps in Detail

Each step can contain any combination of config player sections:

```yaml
#show_version=6

- duration: 2s
  lights:
    l_left: red
    l_right: blue
  events:
    my_custom_event            # post an event during this step
  sounds:
    sfx_swoosh: play

- duration: 1s
  lights:
    l_left: off
    l_right: off
  coils:
    c_flasher: pulse
```

### Duration Notes

- `duration: -1` means "hold forever" (useful for the last step).
- If no `duration:` on the last step, it holds until the show is stopped.
- Duration on all other steps is required.

---

## Common Pitfalls

1. **Using `light_player:` in a show file** — use `lights:` (plural, no `_player` suffix).
2. **Forgetting `#show_version=6`** — MPF will fail to parse the show.
3. **Not setting `loops: -1` for continuous shows** — without it, the show plays once and stops.
4. **Hardcoding device names when tokens would work** — tokens make shows reusable across different lights/devices.
5. **Forgetting `key:` when you need to stop a show later** — without a key, you have to reference the exact show name and event.
