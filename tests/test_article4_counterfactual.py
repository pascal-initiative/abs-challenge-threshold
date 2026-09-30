import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research/article4"))
from counterfactual import Movement, State, reconstruct  # noqa: E402

BATTER = 1


def mv(runner, start, end, out=False, event="Walk", reason=None, idx=5):
    return Movement(runner, start, end, out, event, reason, idx, runner == BATTER)


class CounterfactualRules(unittest.TestCase):
    def test_count_only(self):
        r = reconstruct(1, 1, 0, set(), "STRIKE", "BALL", [])
        self.assertEqual(r.rule, "R1_NO_RUNNER_ACTION")
        self.assertEqual((r.actual.balls, r.actual.strikes), (1, 2))
        self.assertEqual((r.counterfactual.balls, r.counterfactual.strikes), (2, 1))

    def test_full_count_ball_four_should_be_strikeout(self):
        moves = [mv(BATTER, None, "1B"), mv(2, "1B", "2B", reason="r_adv_force")]
        r = reconstruct(3, 2, 1, {"1B"}, "BALL", "STRIKE", moves)
        self.assertEqual(r.confidence, "EXACT")
        self.assertEqual(r.actual.pa_status, "WALK")
        self.assertEqual(r.actual.base_state, "110")
        self.assertEqual(r.counterfactual.pa_status, "STRIKEOUT")
        self.assertEqual((r.counterfactual.outs, r.counterfactual.base_state), (2, "100"))

    def test_bases_loaded_walk_scores_forced_run(self):
        moves = [mv(BATTER, None, "1B"), mv(2, "1B", "2B", reason="r_adv_force"),
                 mv(3, "2B", "3B", reason="r_adv_force"), mv(4, "3B", "score", reason="r_adv_force")]
        r = reconstruct(3, 1, 0, {"1B", "2B", "3B"}, "BALL", "STRIKE", moves)
        self.assertEqual(r.actual.runs, 1)
        self.assertEqual((r.counterfactual.balls, r.counterfactual.strikes, r.counterfactual.runs), (3, 2, 0))

    def test_third_out_strikeout_ends_inning(self):
        r = reconstruct(1, 2, 2, {"2B"}, "STRIKE", "BALL", [mv(BATTER, None, None, True, "Strikeout")])
        self.assertTrue(r.actual.inning_ended)
        self.assertEqual((r.counterfactual.balls, r.counterfactual.strikes, r.counterfactual.outs), (2, 2, 2))

    def test_stolen_base_on_count_change_stands(self):
        moves = [mv(2, "1B", "2B", event="Stolen Base 2B", reason="r_stolen_base_2b", idx=6)]
        r = reconstruct(1, 0, 0, {"1B"}, "STRIKE", "BALL", moves)
        self.assertEqual(r.rule, "R2_RUNNER_OUTCOME_STANDS")
        self.assertEqual(r.counterfactual.base_state, "010")
        self.assertEqual((r.counterfactual.balls, r.counterfactual.strikes), (2, 0))

    def test_caught_stealing_on_terminal_change_is_ambiguous(self):
        moves = [mv(BATTER, None, None, True, "Strikeout"),
                 mv(2, "1B", None, True, "Strikeout Double Play", None)]
        r = reconstruct(2, 2, 0, {"1B"}, "STRIKE", "BALL", moves)
        self.assertEqual(r.actual.outs, 2)
        self.assertEqual(r.confidence, "AMBIGUOUS")
        stands = r.alternatives["RUNNER_RESULT_STANDS"]
        returned = r.alternatives["RUNNERS_RETURNED_TO_TIME_OF_PITCH_BASES"]
        self.assertEqual((stands.outs, stands.base_state, stands.balls), (1, "000", 3))
        self.assertEqual((returned.outs, returned.base_state), (0, "100"))
        self.assertIsNone(r.counterfactual)

    def test_uncaught_strike_three_is_ambiguous(self):
        moves = [mv(2, "2B", "3B", event="Wild Pitch", reason="r_adv_play", idx=6)]
        r = reconstruct(1, 2, 0, {"2B"}, "BALL", "STRIKE", moves)
        self.assertEqual(r.rule, "R4_UNCAUGHT_THIRD_STRIKE")
        self.assertIn("RUNNER_RESULT_STANDS|BATTER_REACHES_FIRST", r.alternatives)

    def test_inconsistent_movement_flagged(self):
        r = reconstruct(0, 0, 0, set(), "BALL", "STRIKE", [mv(2, "2B", "3B", event="Wild Pitch", idx=6)])
        self.assertEqual(r.rule, "R5_UNSUPPORTED_MOVEMENT")

    def test_states_valid(self):
        for b in range(4):
            for s in range(3):
                for o in range(3):
                    for call, other in (("BALL", "STRIKE"), ("STRIKE", "BALL")):
                        r = reconstruct(b, s, o, {"1B", "3B"}, call, other, [
                            mv(BATTER, None, "1B") if call == "BALL" and b == 3 else
                            mv(BATTER, None, None, True, "Strikeout") if call == "STRIKE" and s == 2 else None
                        ] if (call == "BALL" and b == 3) or (call == "STRIKE" and s == 2) else [])
                        if call == "BALL" and b == 3:
                            r = reconstruct(b, s, o, {"1B", "3B"}, call, other, [
                                mv(BATTER, None, "1B"), mv(2, "1B", "2B", reason="r_adv_force")])
                        self.assertTrue(r.actual.valid(), (b, s, o, call))
                        self.assertTrue(r.counterfactual.valid(), (b, s, o, call))
                        self.assertEqual(r.actual_consistency, "CONSISTENT")


if __name__ == "__main__":
    unittest.main()
