# Testing Patterns — Complete Reference

> **MPF 0.57.4 deep-reference guide.**
> Covers test class setup, switch simulation, event testing, helpers, and TDD workflow.

---

## Test Class Setup

```python
from mpf.tests.MpfTestCase import MpfTestCase
import os

class TestMyGame(MpfTestCase):
    def get_machine_path(self):
        """MUST return an absolute path to the machine folder."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    def get_config_file(self):
        """Return just the config filename (not a path)."""
        return "config.yaml"
```

### Critical Rules

| Rule | Detail |
|------|--------|
| `get_machine_path()` | **MUST** return an absolute path. Relative paths resolve against MPF's package root, not your repo. |
| `get_config_file()` | Returns just the filename. MPF looks in `(machine_path)/config/` for it. |
| Method names | Must be **snake_case**. `getMachinePath` / `getConfigFile` (camelCase) are silently ignored — MPF never calls them. |

---

## Switch Simulation

### Momentary Hit (Hit + Release)

```python
self.hit_and_release_switch("s_target")
```

This hits the switch and immediately releases it. Use for targets, bumpers,
standup targets — any switch that the ball activates briefly.

### Hold a Switch

```python
self.hit_switch_and_run("s_lane_1", 0.1)   # hold for 0.1 seconds
```

**WARNING:** This does NOT auto-release the switch. The switch stays active
until you explicitly release it:

```python
self.release_switch_and_run("s_lane_1", 0)
```

Use hold + release for switches that detect ball presence (trough switches,
ball devices, plunger lane).

### Never Use `process_switch()`

```python
# WRONG — leaves the switch stuck active
self.machine.switch_controller.process_switch("s_target", 1)

# RIGHT — properly hits and releases
self.hit_and_release_switch("s_target")
```

Raw `process_switch()` does not release the switch and will break
subsequent test assertions.

---

## Time Control

```python
# Advance the virtual clock by N seconds
self.advance_time_and_run(10)
```

**Always call this after switch hits** to let MPF process events, timers,
and state changes. Common patterns:

```python
# After starting a game
self.hit_and_release_switch("s_start")
self.advance_time_and_run(1)

# After draining
self.hit_and_release_switch("s_outhole")
self.advance_time_and_run(10)    # enough for bonus + ball_end

# After completing a sequence
self.hit_and_release_switch("s_target_8")
self.advance_time_and_run(5)     # let events propagate
```

### How Much Time to Advance?

| Situation | Recommended | Why |
|-----------|-------------|-----|
| After a switch hit | `0.1` – `1` | Let event handlers fire |
| After starting a game | `1` – `10` | Ball ejects, modes start |
| After draining | `10` | Bonus mode runs, ball_ending queue clears |
| After completing a sequence | `3` – `5` | Delayed events may fire |
| Waiting for a timer | Exact timer value | Match the timer duration |

---

## Event Testing

### Mocking Events

```python
# MUST be called BEFORE the event fires
self.mock_event("eight_ball_rack_complete")

# ... do something that fires the event ...
self.hit_and_release_switch("s_eight_ball_target")
self.advance_time_and_run(1)

# Assert the event was posted
self.assertEventCalled("eight_ball_rack_complete")

# Assert it was NOT posted
self.assertEventNotCalled("some_other_event")
```

### Critical: `mock_event()` Timing

`mock_event()` **MUST** be called **BEFORE** the event fires. If you call
it after, the mock won't have captured the event and `assertEventCalled()`
will fail even though the event did fire.

```python
# WRONG — mock set up too late
self.hit_and_release_switch("s_target")
self.advance_time_and_run(1)
self.mock_event("target_hit")          # too late!
self.assertEventCalled("target_hit")   # FAILS

# RIGHT — mock set up first
self.mock_event("target_hit")          # before the event
self.hit_and_release_switch("s_target")
self.advance_time_and_run(1)
self.assertEventCalled("target_hit")   # PASSES
```

### Event Call Count

```python
self.mock_event("scoring_event")

# Hit three times
for _ in range(3):
    self.hit_and_release_switch("s_target")
    self.advance_time_and_run(0.5)

# Check exact count
self.assertEventCalledWith("scoring_event")
# Or check the call count directly:
self.assertEqual(self._events.get("scoring_event", 0), 3)
```

---

## Mode Testing

```python
# Assert a mode is currently running
self.assertModeRunning("base")
self.assertModeRunning("skill_shot")

# Assert a mode is NOT running
self.assertModeNotRunning("multiball")
```

---

## Player Variables

```python
# Dict-style access (best for custom variables)
self.machine.game.player["ball_1_collected"]
self.machine.game.player["bonus_multiplier"]

# Attribute-style access (best for built-in variables)
self.machine.game.player.score
self.machine.game.player.ball
self.machine.game.player.number         # 1-indexed player number
self.machine.game.player.extra_balls

# Assertions
self.assertEqual(self.machine.game.player.score, 3000)
self.assertEqual(self.machine.game.player["ball_1_collected"], True)
self.assertEqual(self.machine.game.player["bonus_multiplier"], 1)
```

---

## Game State Assertions

```python
# Game lifecycle
self.assertGameIsRunning()
self.assertGameIsNotRunning()

# Player info
self.assertPlayerCount(2)
self.assertBallNumber(1)

# Scores (if available)
self.assertPlayerVarEqual(0, "score")   # player 0 not available — use below
self.assertEqual(self.machine.game.player.score, 5000)
```

---

## Ball Device State

```python
# Check ball count in a device
self.assertEqual(
    self.machine.ball_devices["bd_trough"].balls, 3
)

# Check the playfield balls in play
self.assertEqual(
    self.machine.game.balls_in_play, 1
)
```

---

## Test Helpers Pattern (from Eight Ball)

Encapsulate common multi-step operations in helper methods:

### `_start_game()`

```python
def _start_game(self, players=1):
    """Insert coin, press start N times, advance time for setup."""
    self.hit_and_release_switch("s_coin")
    self.advance_time_and_run(1)
    for _ in range(players):
        self.hit_and_release_switch("s_start")
        self.advance_time_and_run(1)
    self.advance_time_and_run(10)    # let ball eject, modes start
```

### `_drain_ball()`

```python
def _drain_ball(self):
    """Drain the ball and wait for bonus + ball_end."""
    self.hit_and_release_switch("s_outhole")
    self.advance_time_and_run(10)    # bonus mode + ball_ending queue
```

### `_collect_all_balls()` (Eight Ball specific)

```python
def _collect_all_balls(self, switches):
    """Hit a list of switches to collect balls."""
    for sw in switches:
        self.hit_and_release_switch(sw)
        self.advance_time_and_run(0.5)
```

---

## Full Test Example

```python
def test_basic_scoring(self):
    """Hitting a target scores 1000 points."""
    self._start_game()
    
    self.assertEqual(self.machine.game.player.score, 0)
    
    self.hit_and_release_switch("s_target_1")
    self.advance_time_and_run(1)
    
    self.assertEqual(self.machine.game.player.score, 1000)

def test_rack_completion(self):
    """Collecting all balls fires rack_complete event."""
    self._start_game()
    
    self.mock_event("eight_ball_rack_complete")
    
    # Collect balls 1–7
    for i in range(1, 8):
        self.hit_and_release_switch(f"s_lane_{i}")
        self.advance_time_and_run(0.5)
    
    # Collect 8-ball
    self.hit_and_release_switch("s_eight_ball_target")
    self.advance_time_and_run(1)
    
    self.assertEventCalled("eight_ball_rack_complete")
```

---

## TDD Workflow

1. **Write the test first** — define expected behaviour in a test method.
2. **Run the test** — it should fail (red).
3. **Implement the YAML config** — add the mode/scoring/event logic.
4. **Run the test again** — it should pass (green).
5. **Refactor** — clean up YAML, add edge case tests.

```bash
# Run all tests
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py -v

# Run a single test
.\.venv\Scripts\python.exe -m pytest machine/tests/test_eight_ball.py::TestEightBall::test_rack_completion_all_8_balls -v
```

---

## Fuzz Testing

Automated tests that hit random switches to ensure MPF doesn't crash,
hang, or enter an invalid state.

```python
import random

def test_fuzz_random_switches(self):
    """Hit random switches rapidly — MPF should not crash."""
    self._start_game()
    
    all_switches = list(self.machine.switches.keys())
    
    for _ in range(200):
        sw = random.choice(all_switches)
        self.hit_and_release_switch(sw)
        self.advance_time_and_run(0.05)
    
    # If we get here without an exception, the test passes
    self.assertGameIsRunning()
```

---

## Critical Rules Summary

| # | Rule |
|---|------|
| 1 | `mock_event()` MUST be called BEFORE the event fires. |
| 2 | `hit_switch_and_run()` does NOT release — use `hit_and_release_switch()` for momentary. |
| 3 | Never use raw `process_switch()` — it leaves switches stuck active. |
| 4 | Always `advance_time_and_run()` after switch hits to let events settle. |
| 5 | `get_machine_path()` must return an absolute path. |
| 6 | Method names must be snake_case (`get_machine_path`, not `getMachinePath`). |
| 7 | Test files go in `machine/tests/`. |
| 8 | Always use MPF test helpers, not direct hardware simulation. |
