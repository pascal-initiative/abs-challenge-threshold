import importlib.util
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/acquire_ct_s1.py"
SPEC = importlib.util.spec_from_file_location("article5_ct_s1_acquisition", MODULE_PATH)
acquire = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = acquire
SPEC.loader.exec_module(acquire)


def game(
    game_pk,
    official_date="2026-09-11",
    state="Final",
    detailed_state="Final",
    teams=(1, 2),
):
    return {
        "gamePk": game_pk,
        "officialDate": official_date,
        "gameType": "R",
        "link": f"/api/v1.1/game/{game_pk}/feed/live",
        "status": {"abstractGameState": state, "detailedState": detailed_state},
        "teams": {
            "home": {"team": {"id": teams[0]}},
            "away": {"team": {"id": teams[1]}},
        },
    }


class CTS1AcquisitionTests(unittest.TestCase):
    def test_dry_plan_is_network_free_and_frozen(self):
        plan = acquire.dry_plan()
        self.assertEqual(plan["status"], "DRY_RUN_NO_NETWORK")
        self.assertEqual(plan["window"], {"start": "2026-09-11", "end": "2026-09-27"})
        self.assertEqual(plan["limits"]["unique_requests"], 326)
        self.assertEqual(plan["external_service_calls"]["odds_api"], 0)

    def test_final_games_rejects_nonfinal_holdout_game(self):
        schedule = {"dates": [{"games": [game(1, state="Preview")]}]}
        with self.assertRaises(acquire.AcquisitionError):
            acquire.final_games(schedule)

    def test_postponed_and_final_schedule_listings_collapse_to_completed_game(self):
        postponed = game(824785, official_date="2026-09-23", detailed_state="Postponed")
        completed = game(824785, official_date="2026-09-23", detailed_state="Final")
        schedule = {"dates": [{"games": [postponed]}, {"games": [completed]}]}
        games = acquire.final_games(schedule)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["status"]["detailedState"], "Final")

    def test_conflicting_duplicate_schedule_listings_fail_closed(self):
        first = game(824785, official_date="2026-09-23", detailed_state="Postponed")
        conflict = game(824785, official_date="2026-09-24", detailed_state="Final")
        schedule = {"dates": [{"games": [first]}, {"games": [conflict]}]}
        with self.assertRaisesRegex(acquire.AcquisitionError, "conflicting duplicate"):
            acquire.final_games(schedule)

    def test_ambiguous_duplicate_schedule_listings_fail_closed(self):
        first = game(824785, official_date="2026-09-23", detailed_state="Final")
        second = game(824785, official_date="2026-09-23", detailed_state="Final")
        schedule = {"dates": [{"games": [first]}, {"games": [second]}]}
        with self.assertRaisesRegex(acquire.AcquisitionError, "ambiguous duplicate"):
            acquire.final_games(schedule)

    def test_jobs_obey_frozen_request_cap(self):
        games = []
        for index in range(15):
            teams = (2 * index + 1, 2 * index + 2)
            games.append(game(index + 1, teams=teams))
        jobs = acquire.fixed_jobs(games)
        self.assertEqual(len([kind for _, kind in jobs if kind == "feed"]), 15)
        self.assertEqual(len([kind for _, kind in jobs if kind == "abs"]), 30)
        self.assertEqual(len([kind for _, kind in jobs if kind == "statcast"]), 17)
        self.assertLessEqual(1 + len(jobs), acquire.UNIQUE_REQUEST_LIMIT)

    def test_schedule_game_cap_fails_closed(self):
        games = [game(index + 1) for index in range(acquire.GAME_FEED_LIMIT + 1)]
        with self.assertRaises(acquire.AcquisitionError):
            acquire.fixed_jobs(games)

    def test_execution_date_gate_prevents_early_network(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(acquire.AcquisitionError):
                acquire.acquire(ROOT, Path(temp), date(2026, 9, 25))
            self.assertEqual(list(Path(temp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
