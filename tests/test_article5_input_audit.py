import importlib.util
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/audit_inputs.py"
SPEC = importlib.util.spec_from_file_location("article5_audit_inputs", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class Article5InputAuditTests(unittest.TestCase):
    def fixture(self):
        return pd.DataFrame([
            dict(pitch_key="1", game_pk=1, game_date="2026-04-01",
                 original_call="STRIKE", derived_abs_call="BALL",
                 official_abs_call="BALL", challenged=True,
                 challenge_outcome="OVERTURNED", position_player_pitching=False,
                 affected_team_challenges_remaining=2),
            dict(pitch_key="2", game_pk=1, game_date="2026-04-01",
                 original_call="BALL", derived_abs_call="BALL",
                 official_abs_call="BALL", challenged=True,
                 challenge_outcome="CONFIRMED", position_player_pitching=False,
                 affected_team_challenges_remaining=1),
            dict(pitch_key="3", game_pk=1, game_date="2026-04-01",
                 original_call="BALL", derived_abs_call="STRIKE",
                 official_abs_call=None, challenged=False,
                 challenge_outcome=None, position_player_pitching=True,
                 affected_team_challenges_remaining=2),
        ])

    def test_legal_population_excludes_position_player(self):
        self.assertEqual(audit.legal_decision_mask(self.fixture()).tolist(), [True, True, False])

    def test_label_fidelity_uses_all_challenges(self):
        result = audit.challenge_label_audit(self.fixture())
        self.assertEqual(result["challenges"], 2)
        self.assertEqual(result["agreement_rate"], 1.0)
        self.assertEqual(result["disagreements"], 0)

    def test_allowlist_and_blacklist_do_not_overlap(self):
        self.assertFalse(audit.DECISION_FEATURE_ALLOWLIST & audit.LEAKAGE_BLACKLIST)

    def test_signed_margin_is_blacklisted(self):
        self.assertIn("wrong_way_margin_inches", audit.LEAKAGE_BLACKLIST)


if __name__ == "__main__":
    unittest.main()
