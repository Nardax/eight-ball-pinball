# Copilot Instructions — Eight Ball Pinball (MPF)

This is a **Bally Eight Ball (1977) pinball machine rebuild** using Mission Pinball Framework (MPF) 0.57.4. All game logic lives in YAML config files loaded by MPF. There is no application code outside of the test suite.

---

## Commands

```bash
# Run MPF in virtual mode (simulated hardware — no physical machine needed)
.\.venv\Scripts\python.exe -m mpf machine -x

# Run all tests
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py -v

# Run a single test
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py::TestEightBall::test_rack_completion_all_8_balls -v

# Validate config loads without errors (run 15s then kill)
.\.venv\Scripts\python.exe -m mpf machine -x -t

# Syntax-check the test file
.\.venv\Scripts\python.exe -m py_compile machine/tests/test_eight_ball.py
```

Python 3.9.13 is the only Python installed on this machine. MPF 0.57.4 requires `>=3.8,<3.13`. The venv is at `.venv/`.

---

## Architecture

The game runs entirely through MPF's event bus. There is no imperative game loop — everything is declarative YAML reacting to events.

### Mode stack (priority order, highest wins)
| Mode | Priority | Active when |
|---|---|---|
| `rack_complete` | 300 | `eight_ball_rack_complete` event fires |
| `skill_shot` | 200 | `ball_started` → `ball_ended` |
| `kickback` | 150 | always during game |
| `bonus` | 130 | `ball_will_end` |
| `bonus_mult` | 120 | always during game |
| `base` | 100 | always during game |
| `attract` | 10 | no game running |

### Ball collection — odd/even player routing
Players 1 & 3 collect balls 1–8 ("solids"); players 2 & 4 collect balls 9–15 + 8-ball ("stripes"). Both sets share the same physical switches. `base.yaml` routes each switch hit to a **named per-parity event**:

```
s_lane_1 + (player 1 or 3)  →  ball_1_collected_p_odd
s_lane_1 + (player 2 or 4)  →  ball_1_collected_p_even
```

Both events write the same player variable (`ball_1_collected = true`). A `{not player.ball_1_collected}` guard in `variable_player` prevents double-scoring.

### Rack completion flow
```
s_eight_ball_target{all 7 balls collected}
  → ball_8_collected_ready        (intermediate signal, no redundant condition needed)
  → eight_ball_rack_complete
  → rack_complete mode starts     (locks 24K bonus, resets flags, increments rack_count)
```

### Bonus formula
`(balls_collected × 3,000) × bonus_multiplier + base_bonus_locked`

- `balls_collected` resets to 0 on each rack completion
- `base_bonus_locked` accumulates across all racks and balls (never resets during the game)
- `bonus_multiplier` resets to 1 after each ball's payout (`keep_multiplier: false` in bonus plugin)

---

## Key YAML Conventions

**`#config_version=6`** is required at the top of every config file. Shows use `#show_version=6`.

**`player.variable_name`** — correct syntax in event conditions. `current_player.variable_name` silently fails in mode-level event_player conditions (see ADR-005).

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
  ball_1_collected_p_odd{not player.ball_1_collected}:
    score: 3000
    ball_1_collected: true
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
self.hit_switch_and_run("s_lane_1", 0.1)    # hold for 0.1s
self.release_switch_and_run("s_lane_1", 0)  # release
self.advance_time_and_run(10)               # let events settle
self.assertEventCalled("eight_ball_rack_complete")
```

Raw `process_switch()` leaves switches stuck active and will break subsequent test assertions.

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
