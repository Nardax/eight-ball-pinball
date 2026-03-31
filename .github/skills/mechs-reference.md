# Mechanisms — Complete Reference

> **MPF 0.57.4 deep-reference guide.**
> Covers ball devices, flippers, autofire coils, and key mechanisms for EM/SS pinball machines.

---

## Ball Devices

Ball devices are containers that hold and eject balls. They are the
backbone of ball routing in MPF.

### Trough (Home Device)

```yaml
ball_devices:
  bd_trough:
    ball_switches: s_trough_1, s_trough_2, s_trough_3
    eject_coil: c_trough_eject
    tags: home, trough, drain
    eject_targets: bd_plunger
    confirm_eject_switch: s_plunger_lane
    eject_timeouts: 5s
```

### Plunger Lane

```yaml
ball_devices:
  bd_plunger:
    ball_switches: s_plunger_lane
    mechanical_eject: true         # player manually plunges
    eject_timeouts: 3s
    tags: plunger
```

### Scoop / VUK (Vertical Up Kicker)

```yaml
ball_devices:
  bd_scoop:
    ball_switches: s_scoop
    eject_coil: c_scoop_eject
    eject_targets: playfield
    eject_timeouts: 2s
```

### Tags Reference

| Tag | Meaning |
|-----|---------|
| `home` | Where balls live when not in play. MPF tracks expected ball count here. |
| `trough` | The trough — balls queue here after draining. |
| `drain` | Ball drain — entering this device triggers `ball_drain`. |
| `plunger` | Plunger lane — the launch position. |

### Key Settings

| Setting | Type | Description |
|---------|------|-------------|
| `ball_switches` | list | Switches that detect balls in the device (one per position). |
| `eject_coil` | str | Coil that ejects balls from the device. |
| `eject_targets` | str | Where ejected balls go (another ball device or `playfield`). |
| `confirm_eject_switch` | str | Switch that confirms a ball arrived at the target. |
| `mechanical_eject` | bool | `true` if player manually ejects (e.g., manual plunger). |
| `eject_timeouts` | str | How long to wait for eject confirmation before retrying. |
| `ball_capacity` | int | Max balls the device can hold (auto-calculated from `ball_switches` if not set). |
| `entrance_count_delay` | str | Delay before counting a new ball (debounce for fast-draining). |

### Ball Device Events

| Event | When |
|-------|------|
| `balldevice_(name)_ball_enter` | A ball enters the device. |
| `balldevice_(name)_ball_eject_success` | A ball was successfully ejected. |
| `balldevice_(name)_ball_eject_failed` | Eject timed out or failed. |
| `balldevice_(name)_ball_eject_attempt` | An eject attempt is starting. |

---

## Flippers

### Single-Wound Coil

```yaml
flippers:
  left_flipper:
    main_coil: c_flipper_left
    activation_switch: s_flipper_left
    enable_events: ball_started        # default
    disable_events: ball_ended         # default
  
  right_flipper:
    main_coil: c_flipper_right
    activation_switch: s_flipper_right
```

### Dual-Wound Coil (Power + Hold)

Older machines use two coil windings — a powerful winding for the initial
flip and a weaker hold winding to maintain position.

```yaml
flippers:
  left_flipper:
    main_coil: c_flipper_left_main     # power winding
    hold_coil: c_flipper_left_hold     # hold winding
    activation_switch: s_flipper_left
```

### Flipper Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `main_coil` | str | *(required)* | Primary coil (or power winding for dual-wound). |
| `hold_coil` | str | `None` | Hold winding (dual-wound only). |
| `activation_switch` | str | *(required)* | Switch that activates the flipper. |
| `enable_events` | list | `ball_started` | Events that enable flipper response. |
| `disable_events` | list | `ball_ended` | Events that disable flipper response. |
| `eos_switch` | str | `None` | End-of-stroke switch (for EOS cutoff on older machines). |
| `use_eos` | bool | `false` | Whether to use EOS switch for hold power reduction. |

---

## Autofire Coils

Autofire coils fire automatically when their switch is hit. Used for pop
bumpers, slingshots, and similar mechanisms that don't need game logic.

### Pop Bumpers

```yaml
autofire_coils:
  ac_pop_bumper_upper:
    coil: c_pop_bumper_upper
    switch: s_pop_bumper_upper
  
  ac_pop_bumper_lower:
    coil: c_pop_bumper_lower
    switch: s_pop_bumper_lower
```

### Slingshots

```yaml
autofire_coils:
  ac_slingshot_left:
    coil: c_slingshot_left
    switch: s_slingshot_left
  
  ac_slingshot_right:
    coil: c_slingshot_right
    switch: s_slingshot_right
```

### Autofire Coil Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `coil` | str | *(required)* | Coil to fire. |
| `switch` | str | *(required)* | Switch that triggers the coil. |
| `enable_events` | list | `ball_started` | Events that enable the autofire. |
| `disable_events` | list | `ball_ended` | Events that disable the autofire. |
| `reverse_switch` | bool | `false` | If `true`, fire when switch deactivates (rare). |

---

## Kickbacks

Kickbacks are coils that fire to save the ball from draining down an
outlane. They are typically controlled by game logic (not autofire).

```yaml
# Define the coil
coils:
  c_kickback_left:
    number: c_kickback_left
    default_pulse_ms: 30

# Use event_player + coil_player to fire on demand
coil_player:
  kickback_fire:
    c_kickback_left:
      action: pulse
```

Or use autofire with enable/disable logic:

```yaml
autofire_coils:
  ac_kickback:
    coil: c_kickback_left
    switch: s_left_outlane
    enable_events: kickback_enabled
    disable_events: kickback_disabled, ball_ended
```

---

## Drop Targets

### Individual Drop Targets

```yaml
drop_targets:
  dt_1:
    switch: s_drop_1
    reset_coil: c_drop_reset     # shared reset coil for the bank
  dt_2:
    switch: s_drop_2
    reset_coil: c_drop_reset
  dt_3:
    switch: s_drop_3
    reset_coil: c_drop_reset
```

### Drop Target Banks

```yaml
drop_target_banks:
  dtb_top:
    drop_targets: dt_1, dt_2, dt_3
    reset_coil: c_drop_reset
    reset_events:
      dtb_top_down: 1s          # reset 1s after all targets are down
```

### Drop Target Events

| Event | When |
|-------|------|
| `drop_target_(name)_down` | Individual target drops. |
| `drop_target_(name)_up` | Individual target resets. |
| `drop_target_bank_(name)_down` | All targets in the bank are down. |
| `drop_target_bank_(name)_up` | All targets in the bank are up (after reset). |
| `drop_target_bank_(name)_mixed` | Some up, some down. |

---

## Standup Targets

Standup targets are just switches. Scoring is handled via `variable_player:`.

```yaml
switches:
  s_standup_1:
    number: s_standup_1
  s_standup_2:
    number: s_standup_2

# Score on hit
variable_player:
  s_standup_1_active:
    score: 500
  s_standup_2_active:
    score: 500
```

---

## Spinners

Spinners generate rapid switch hits as the ball passes through.

```yaml
switches:
  s_spinner:
    number: s_spinner

variable_player:
  s_spinner_active:
    score: 100
    spinner_count:
      int: 1
      action: add
```

---

## Diverters

Diverters route balls to different paths on the playfield.

```yaml
diverters:
  d_ramp_diverter:
    activation_coil: c_ramp_diverter
    type: hold                         # hold coil energised while active
    activate_events: diverter_activate
    deactivate_events: diverter_deactivate
    deactivation_switches: s_ramp_entry  # auto-deactivate when ball passes
    enable_events: ball_started
    disable_events: ball_ended
```

### Diverter Settings

| Setting | Type | Description |
|---------|------|-------------|
| `activation_coil` | str | Coil that moves the diverter. |
| `type` | str | `hold` (keep energised) or `pulse` (momentary). |
| `activate_events` | list | Events that activate the diverter. |
| `deactivate_events` | list | Events that deactivate the diverter. |
| `deactivation_switches` | list | Switches that auto-deactivate the diverter (ball has passed). |

---

## Playfield

The playfield is a special ball device that represents the playing surface.

```yaml
playfields:
  playfield:
    default_source_device: bd_trough
    tags: default
```

- `default_source_device` tells MPF where to get balls for auto-launch.
- The playfield tracks `balls_in_play`.

---

## Hardware Numbers

In **virtual mode**, `number:` can be any arbitrary string:

```yaml
switches:
  s_lane_1:
    number: s_lane_1

coils:
  c_trough_eject:
    number: c_trough_eject
```

For **physical hardware** (e.g., FAST Pinball Neuron), replace with board
addresses:

```yaml
switches:
  s_lane_1:
    number: "0-0"       # board 0, input 0

coils:
  c_trough_eject:
    number: "0-0"       # board 0, output 0
```

---

## Common Pitfalls

1. **Missing `number:` on devices** — even in virtual mode, every switch and coil needs a `number:` field.
2. **Forgetting `eject_targets:`** — MPF needs to know where balls go after ejection to track ball counts.
3. **Using `autofire_coils` for logic-controlled mechanisms** — autofire bypasses game logic. Use `coil_player:` if you need conditional firing.
4. **Not setting `eject_timeouts:`** — without a timeout, a failed eject is never retried.
5. **Forgetting `tags: home, trough, drain`** on the trough — MPF uses these tags to manage the ball lifecycle.
