# Ball Lifecycle — Complete Reference

> **MPF 0.57.4 deep-reference guide.**
> Covers every event from start-button press through game-over.

---

## Game Start Flow

```
Player pushes start button
        │
        ▼
request_to_start_game          ◄── boolean event; credits mode or
        │                           ball controller can DENY
        │  (approved)
        ▼
    game_start                  ◄── standard event
        │
        ▼
   game_starting                ◄── QUEUE event
        │                           • score reels reset
        │                           • auditor enables
        │                           • wait for all handlers to clear
        ▼
  First player created
  (player_added, player_1)
        │
        ▼
   game_started                 ◄── standard event; game is now live
        │
        ▼
  player_turn_start()           ◄── internal call → begins first ball
```

### Detail

| Step | What happens |
|------|-------------|
| `request_to_start_game` | Posted when the start button is pressed. This is a **boolean event**: any handler can return `False` to block the game from starting (e.g., not enough credits, ball device not ready). |
| `game_start` | Fired only if the boolean event was approved. The game mode itself begins. |
| `game_starting` | A **queue event**. Handlers add themselves to the queue, do their setup work (reset score reels, enable auditor, etc.), then clear. The flow pauses until every handler clears. |
| Player creation | MPF creates the first `Player` object. Posts `player_added` and `player_1`. |
| `game_started` | Standard event indicating the game object is fully initialised and ready. |
| `player_turn_start()` | Internal method call that kicks off the first ball sequence (see below). |

---

## Ball Start Flow

```
player_turn_starting            ◄── queue event
        │
        ▼
player_turn_started             ◄── standard event
        │
        ▼
  Ball count incremented
  (player.ball increments)
        │
        ▼
   ball_starting                ◄── QUEUE event
        │                           • modes can hook in for per-ball setup
        │                           • e.g. skill-shot mode starts here
        ▼
  ball drain handlers added
  balls_in_play = 1
        │
        ▼
    ball_started                ◄── standard event
        │                           • flippers enabled
        │                           • shots enabled
        │                           • autofire coils enabled
        ▼
  Ball ejected from trough
  to plunger lane
```

### Detail

| Step | What happens |
|------|-------------|
| `player_turn_starting` | Queue event. Lets modes prepare before the ball is live. |
| `player_turn_started` | Standard event confirming the player's turn has begun. |
| Ball count increment | `player.ball` is incremented (1-indexed). |
| `ball_starting` | **Queue event.** This is the main hook for modes that need to set up before the ball is live. Skill-shot mode typically starts here. Handlers must clear the queue when done. |
| Drain handlers / `balls_in_play` | The game registers its drain handler and sets `balls_in_play = 1`. |
| `ball_started` | Standard event. MPF enables flippers, shots, and autofire coils at this point. The ball is now fully in play. |
| Ball ejection | The trough ejects a ball toward the plunger lane (or auto-launches if configured). |

---

## Ball End Flow

```
Ball enters device tagged "drain"
        │
        ▼
    ball_drain                  ◄── RELAY event
        │                           • ball save can "remove" balls
        │                           • if balls removed, balls_in_play
        │                             stays > 0 and flow stops here
        ▼
  balls_in_play decremented
        │
        ▼
  balls_in_play == 0 ?
        │
   ┌────┴────┐
   │ NO      │ YES
   │ (multi- │
   │  ball)  │
   ▼         ▼
 (wait)   ball_will_end         ◄── standard event
             │
             ▼
          ball_ending           ◄── QUEUE event
             │                       • bonus mode hooks here
             │                       • use_wait_queue: true
             ▼
          ball_ended            ◄── standard event
             │
             ▼
       Extra balls?
        ┌────┴────┐
        │ YES     │ NO
        ▼         ▼
  shoot_again()   Last ball of last player?
                     ┌────┴────┐
                     │ YES     │ NO
                     ▼         ▼
              game_ending    player_rotate()
                  │              │
                  ▼              ▼
              game_ended     Next player's
                             player_turn_start()
```

### Detail

| Step | What happens |
|------|-------------|
| `ball_drain` | **Relay event.** Any handler (typically ball save) can modify the event kwargs to "remove" drained balls, effectively telling MPF the ball wasn't really lost. If a ball is removed, `balls_in_play` is not decremented and the flow stops. |
| `balls_in_play` decrement | Decremented by the number of balls that actually drained (after relay handlers). |
| `balls_in_play == 0` check | If balls remain in play (multiball), nothing further happens. |
| `ball_will_end` | Standard event. Signals that the ball is about to end. Useful for modes that need to do cleanup before bonus. |
| `ball_ending` | **Queue event.** This is where the bonus mode runs. The bonus mode sets `use_wait_queue: true` so it can hold the queue while it tallies and displays the bonus. The flow pauses until all handlers clear. |
| `ball_ended` | Standard event. The ball is now officially over. |
| Extra balls | If `player.extra_balls > 0`, `shoot_again()` is called — the player gets another ball without incrementing `player.ball`. |
| Last ball check | If this was the last ball for the last player, the game ends. |
| `game_ending` | Standard event posted just before game teardown. |
| `game_ended` | Standard event. The game object is destroyed. Attract mode typically restarts. |
| `player_rotate()` | If not the last player, rotate to the next player and call `player_turn_start()`. |

---

## Key Events Table

| Event | Type | When | Notes |
|-------|------|------|-------|
| `request_to_start_game` | boolean | Start button pressed | Can be denied by credits or ball controller |
| `game_starting` | queue | Game initialising | Score reels reset, auditor enables; pauses until all handlers clear |
| `game_started` | standard | Game ready | Game object fully initialised |
| `player_turn_starting` | queue | Player turn beginning | Before ball count increment |
| `player_turn_started` | standard | Player turn begun | After queue clears |
| `ball_starting` | queue | Ball being set up | Modes hook in here (e.g. skill shot) |
| `ball_started` | standard | Ball in play | Flippers, shots, autofire enabled |
| `ball_drain` | relay | Ball enters drain device | Ball save can intercept |
| `ball_will_end` | standard | Ball about to end | Pre-bonus cleanup |
| `ball_ending` | queue | Ball ending | Bonus mode runs here (`use_wait_queue: true`) |
| `ball_ended` | standard | Ball is over | Modes stop, flippers disabled |
| `game_ending` | standard | Game about to end | Last ball of last player just ended |
| `game_ended` | standard | Game over | Game object destroyed, attract mode restarts |

---

## Event Types Explained

| Type | Behaviour |
|------|-----------|
| **standard** | Fire-and-forget. All handlers run, no return value. |
| **boolean** | Handlers can return `False` to deny/block the action. |
| **queue** | Handlers call `queue.wait()` to pause the flow, then `queue.clear()` when done. Flow resumes only when every handler has cleared. |
| **relay** | Handlers receive kwargs, can modify them, and pass them along. Used for `ball_drain` so ball save can change the drained ball count. |

---

## Multiplayer Turn Order

```
Player 1, Ball 1
Player 2, Ball 1      ◄── player_rotate()
Player 1, Ball 2
Player 2, Ball 2
Player 1, Ball 3
Player 2, Ball 3
game_ending → game_ended
```

Each `player_rotate()` posts `player_turn_will_start` for the next player, then the full ball-start sequence repeats.

---

## Common Pitfalls

1. **Hooking `ball_ending` without `use_wait_queue: true`** — the ball will end before your mode finishes. Always use the queue if you need to display bonus or do async work.
2. **Starting modes on `ball_started` but not stopping on `ball_will_end` or `ball_ending`** — modes can bleed into the next ball.
3. **Forgetting that `ball_drain` is a relay** — if you handle it, you must pass the kwargs through or you'll break ball save.
4. **Not advancing time in tests** — events are processed asynchronously. Always call `self.advance_time_and_run()` after triggering a drain or start.
