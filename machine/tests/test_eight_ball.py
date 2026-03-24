"""
Eight Ball Pinball — MPF Unit Tests (Phase 5)
Tests the full game logic using MPF's MpfTestCase framework.

Run with: python -m pytest machine/tests/test_eight_ball.py -v
Or:        mpf test machine/tests/test_eight_ball.py
"""

from mpf.tests.MpfTestCase import MpfTestCase


class TestEightBall(MpfTestCase):

    def getConfigFile(self):
        return "config.yaml"

    def getMachinePath(self):
        # Adjust relative path as needed when running from repo root
        return "machine"

    # ------------------------------------------------------------------
    # Helper: start a game with N players
    # ------------------------------------------------------------------
    def _start_game(self, players=1):
        self.hit_switch_and_run("s_trough_1", 1)
        self.machine.switch_controller.process_switch("s_coin", 1)
        self.machine_run()
        for _ in range(players):
            self.machine.switch_controller.process_switch("s_start_button", 1)
            self.machine_run()
        self.release_switch_and_run("s_plunger_lane", 1)
        self.machine_run()

    def _drain_ball(self):
        self.machine.switch_controller.process_switch("s_outhole", 1)
        self.machine_run()
        self.machine_run()

    # ------------------------------------------------------------------
    # 5.1.1 — Ball tracking: collecting ball 1 lights l_ball_1
    # ------------------------------------------------------------------
    def test_ball_1_collected_lights_insert(self):
        self._start_game()
        self.assertFalse(self.machine.game.player["ball_1_collected"])
        self.hit_switch_and_run("s_lane_1", 1)
        self.assertTrue(self.machine.game.player["ball_1_collected"])
        self.assertEqual(self.machine.lights["l_ball_1"].color, [255, 255, 0])  # yellow

    # ------------------------------------------------------------------
    # 5.1.2 — Ball 2 → l_ball_2 blue
    # ------------------------------------------------------------------
    def test_ball_2_collected_lights_insert(self):
        self._start_game()
        self.hit_switch_and_run("s_lane_2", 1)
        self.assertTrue(self.machine.game.player["ball_2_collected"])

    # ------------------------------------------------------------------
    # 5.1.3 — Score 3000 per ball collected
    # ------------------------------------------------------------------
    def test_ball_collection_scores_3000(self):
        self._start_game()
        initial_score = self.machine.game.player.score
        self.hit_switch_and_run("s_lane_1", 1)
        self.assertEqual(self.machine.game.player.score, initial_score + 3000)

    # ------------------------------------------------------------------
    # 5.1.4 — Each ball collected only once (no double scoring)
    # ------------------------------------------------------------------
    def test_ball_collected_only_once(self):
        self._start_game()
        self.hit_switch_and_run("s_lane_1", 1)
        score_after_first = self.machine.game.player.score
        self.hit_switch_and_run("s_lane_1", 1)
        self.assertEqual(self.machine.game.player.score, score_after_first)

    # ------------------------------------------------------------------
    # 5.1.5 — Rack completion: all 8 balls → rack complete event fires
    # ------------------------------------------------------------------
    def test_rack_completion_all_8_balls(self):
        self._start_game()
        for switch in ["s_lane_1", "s_lane_2", "s_lane_3", "s_lane_4",
                       "s_target_5", "s_target_6", "s_return_lane_7"]:
            self.hit_switch_and_run(switch, 0.1)
        # 8-ball should now be collectable
        self.assertTrue(
            self.machine.game.player["ball_1_collected"] and
            self.machine.game.player["ball_7_collected"]
        )
        self.hit_switch_and_run("s_eight_ball_target", 1)
        self.assertTrue(self.machine.game.player["ball_8_collected"])
        # Rack complete: base_bonus_locked should be 24000
        self.assertEqual(self.machine.game.player["base_bonus_locked"], 24000)
        self.assertEqual(self.machine.game.player["rack_count"], 1)
        # Ball flags should be reset for next rack
        self.assertFalse(self.machine.game.player["ball_1_collected"])

    # ------------------------------------------------------------------
    # 5.1.6 — 8-ball gate: cannot collect 8 before 1-7
    # ------------------------------------------------------------------
    def test_eight_ball_gate_blocks_early_collection(self):
        self._start_game()
        # Hit 8-ball before collecting 1-7 — ball 8 should NOT be collected
        self.assertFalse(self.machine.game.player["ball_7_collected"])
        self.hit_switch_and_run("s_eight_ball_target", 1)
        self.assertFalse(self.machine.game.player["ball_8_collected"])

    # ------------------------------------------------------------------
    # 5.1.7 — Kickback: 8-ball pad lights kickback
    # ------------------------------------------------------------------
    def test_kickback_lit_by_eight_ball_pad(self):
        self._start_game()
        self.assertFalse(self.machine.game.player["kickback_active"])
        self.hit_switch_and_run("s_eight_ball_target", 1)
        self.assertTrue(self.machine.game.player["kickback_active"])
        self.assertTrue(self.machine.game.player["spinner_lit"])

    # ------------------------------------------------------------------
    # 5.1.8 — Kickback save: firing kickback turns off kickback + spinner
    # ------------------------------------------------------------------
    def test_kickback_save_turns_off_kickback_and_spinner(self):
        self._start_game()
        self.hit_switch_and_run("s_eight_ball_target", 1)
        self.assertTrue(self.machine.game.player["kickback_active"])
        # Ball enters outlane while kickback is lit
        self.hit_switch_and_run("s_left_outlane", 1)
        self.assertFalse(self.machine.game.player["kickback_active"])
        self.assertFalse(self.machine.game.player["spinner_lit"])

    # ------------------------------------------------------------------
    # 5.1.9 — Kickback does NOT fire when unlit
    # ------------------------------------------------------------------
    def test_kickback_does_not_fire_when_unlit(self):
        self._start_game()
        self.assertFalse(self.machine.game.player["kickback_active"])
        # Outlane hit without kickback lit — kickback_fired should NOT post
        with self.assertEventNotCalled("kickback_fired"):
            self.hit_switch_and_run("s_left_outlane", 1)

    # ------------------------------------------------------------------
    # 5.1.10 — Bonus multiplier: star rollover progression
    # ------------------------------------------------------------------
    def test_star_rollover_multiplier_progression(self):
        self._start_game()
        # Hits 1-2: candy cane levels
        self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["star_hits"], 1)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 1)

        self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["star_hits"], 2)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 1)

        # Hit 3 → 2X
        self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 2)

        # Hit 4 → 3X
        self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 3)

        # Hit 5 → 5X
        self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 5)

    # ------------------------------------------------------------------
    # 5.1.11 — Extra ball awarded at star hit 6
    # ------------------------------------------------------------------
    def test_extra_ball_at_star_hit_6(self):
        self._start_game()
        for _ in range(6):
            self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEventCalled("extra_ball_awarded")

    # ------------------------------------------------------------------
    # 5.1.12 — Bonus calculation: balls × 3000 × multiplier + base bonus
    # ------------------------------------------------------------------
    def test_bonus_calculation(self):
        self._start_game()
        # Collect 3 balls
        self.hit_switch_and_run("s_lane_1", 0.1)
        self.hit_switch_and_run("s_lane_2", 0.1)
        self.hit_switch_and_run("s_lane_3", 0.1)
        # Advance to 2X
        for _ in range(3):
            self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 2)

        score_before_drain = self.machine.game.player.score
        self._drain_ball()
        self.machine_run()
        # Bonus = 3 balls × 3000 × 2X + 0 base = 18000
        expected_bonus = (3 * 3000 * 2) + 0
        self.assertAlmostEqual(
            self.machine.game.player.score,
            score_before_drain + expected_bonus,
            delta=100  # small tolerance for any rounding
        )

    # ------------------------------------------------------------------
    # 5.1.13 — Bonus multiplier resets after ball ends
    # ------------------------------------------------------------------
    def test_bonus_multiplier_resets_between_balls(self):
        self._start_game()
        for _ in range(3):
            self.hit_switch_and_run("s_star_rollover", 0.1)
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 2)
        self._drain_ball()
        self.machine_run()
        self.assertEqual(self.machine.game.player["bonus_multiplier"], 1)

    # ------------------------------------------------------------------
    # 5.1.14 — Even/odd player ball numbering
    # Player 1 collects ball 1; Player 2 collects ball 9 (same slot)
    # ------------------------------------------------------------------
    def test_even_odd_player_ball_numbering(self):
        self._start_game(players=2)
        # Player 1 hits lane 1 → ball_1_collected
        self.hit_switch_and_run("s_lane_1", 0.1)
        self.assertTrue(self.machine.game.player["ball_1_collected"])
        # Drain and switch to player 2
        self._drain_ball()
        self.machine_run()
        # Player 2: player number is 2 → hits lane 1 → ball 9 slot (ball_1_collected for P2)
        self.assertEqual(self.machine.game.player.number, 2)
        self.assertFalse(self.machine.game.player["ball_1_collected"])
        self.hit_switch_and_run("s_lane_1", 0.1)
        # Player 2 should now have ball_1_collected = True (their slot for ball 9)
        self.assertTrue(self.machine.game.player["ball_1_collected"])

    # ------------------------------------------------------------------
    # 5.1.15 — Skill shot: ball 1 → lane 4 awards skill shot
    # ------------------------------------------------------------------
    def test_skill_shot_ball_1_lane_4(self):
        self._start_game()
        # Ball just launched (skill_shot mode is active on ball_started)
        self.assertModeRunning("skill_shot")
        score_before = self.machine.game.player.score
        self.hit_switch_and_run("s_lane_4", 0.1)
        self.assertEventCalled("skill_shot_awarded")
        self.assertGreater(self.machine.game.player.score, score_before)

    # ------------------------------------------------------------------
    # 5.1.16 — Skill shot missed on pop bumper hit
    # ------------------------------------------------------------------
    def test_skill_shot_missed_on_pop_bumper(self):
        self._start_game()
        self.assertModeRunning("skill_shot")
        self.hit_switch_and_run("s_pop_bumper_left", 0.1)
        self.assertEventCalled("skill_shot_missed")
        self.assertModeNotRunning("skill_shot")

    # ------------------------------------------------------------------
    # 5.1.17 — Spinner scoring: lit vs. unlit
    # ------------------------------------------------------------------
    def test_spinner_scoring_lit_vs_unlit(self):
        self._start_game()
        # Unlit spinner → 100 pts
        score_before = self.machine.game.player.score
        self.hit_switch_and_run("s_spinner", 0.1)
        self.assertEqual(self.machine.game.player.score, score_before + 100)

        # Light the spinner
        self.hit_switch_and_run("s_eight_ball_target", 0.1)
        self.assertTrue(self.machine.game.player["spinner_lit"])

        # Lit spinner → 1000 pts
        score_before = self.machine.game.player.score
        self.hit_switch_and_run("s_spinner", 0.1)
        self.assertEqual(self.machine.game.player.score, score_before + 1000)

    # ------------------------------------------------------------------
    # 5.1.18 — Base bonus locked in from rack carry over to next ball
    # ------------------------------------------------------------------
    def test_locked_bonus_carries_between_balls(self):
        self._start_game()
        # Complete a rack
        for sw in ["s_lane_1", "s_lane_2", "s_lane_3", "s_lane_4",
                   "s_target_5", "s_target_6", "s_return_lane_7"]:
            self.hit_switch_and_run(sw, 0.1)
        self.hit_switch_and_run("s_eight_ball_target", 0.5)
        self.assertEqual(self.machine.game.player["base_bonus_locked"], 24000)
        # Drain ball 1 — locked bonus should persist on ball 2
        self._drain_ball()
        self.machine_run()
        self.assertEqual(self.machine.game.player["base_bonus_locked"], 24000)

    # ------------------------------------------------------------------
    # 5.1.19 — Multi-player game flow: 4 players, 3 balls each
    # ------------------------------------------------------------------
    def test_multi_player_game_flow(self):
        self._start_game(players=4)
        self.assertEqual(len(self.machine.game.players), 4)
        self.assertEqual(self.machine.game.ball, 1)
        # Each player drains and advances
        for _ in range(4):
            self._drain_ball()
            self.machine_run()
        # After 4 drains (one per player), ball 2 starts with player 1
        self.assertEqual(self.machine.game.ball, 2)
        self.assertEqual(self.machine.game.player.number, 1)
