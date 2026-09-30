import hashlib
import json
import unittest
from pathlib import Path

import pandas as pd

from src.sprint4 import PUBLISH_N, RANK_N, run
from src.sprint4_evidence import (
    ACCEPTED_FEATURE_SHA256,
    ACCEPTED_SPRINT3_MANIFEST_SHA256,
    BOUNDARY_THRESHOLDS,
    deterministic_rank,
)

ROOT=Path(__file__).resolve().parents[1]


class Sprint4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=ROOT/"data/analysis/sprint4";cls.art=ROOT/"artifacts/sprint4"
        if not cls.data.exists(): raise unittest.SkipTest("Sprint 4 has not run")

    def test_required_outputs_and_figures(self):
        data="batter_recognition_opportunities.csv batter_recognition_summary.csv batter_recognition_rankings.csv batter_recognition_temporal.csv batter_opportunity_difficulty.csv batter_recognition_accuracy_matrix.csv batter_team_summary.csv".split()
        art="batter_model_metrics.csv batter_adjusted_effects.csv batter_temporal_validation.csv batter_stability.csv raw_vs_adjusted_rank.csv support_analysis.csv sensitivity_analysis.csv negative_controls.csv run_manifest.json".split()
        self.assertTrue(all((self.data/x).is_file() for x in data))
        self.assertTrue(all((self.art/x).is_file() for x in art))
        self.assertEqual(len(list(self.art.glob("*.png"))),8)
        evidence="sprint3_snapshot_verification.csv temporal_holdout_metrics.csv split_half_stability_statistics.csv minimum_support_sensitivity.csv boundary_uncertainty_sensitivity.csv opportunity_difficulty_sensitivity.csv accepted_control_sensitivity.csv claims_matrix.csv adversarial_validation.csv decision_gates.json artifact_hashes.sha256".split()
        self.assertTrue(all((self.art/x).is_file() for x in evidence))

    def test_population_and_expected_probabilities(self):
        o=pd.read_csv(self.data/"batter_recognition_opportunities.csv")
        self.assertEqual(len(o),10755);self.assertEqual(o.recognized.sum(),2112)
        self.assertEqual(o.pitch_key.nunique(),10755)
        self.assertTrue(o.expected_probability.between(0,1).all())
        s=pd.read_csv(self.data/"batter_recognition_summary.csv")
        self.assertEqual(len(s),602);self.assertEqual(s.opportunities.sum(),10755)
        self.assertEqual(s.recognized.sum(),2112)

    def test_thresholds_and_uncertainty_gate_rankings(self):
        self.assertEqual((PUBLISH_N,RANK_N),(20,30))
        r=pd.read_csv(self.data/"batter_recognition_rankings.csv")
        self.assertTrue((r.opportunities>=RANK_N).all())
        self.assertTrue(r.rank_eligible.all())
        self.assertTrue((r.uncertainty_lower<=r.adjusted_effect).all())
        self.assertTrue((r.adjusted_effect<=r.uncertainty_upper).all())

    def test_temporal_validation_has_no_leakage(self):
        f=pd.read_csv(self.art/"batter_temporal_validation.csv")
        f=f[f.fold.ne("POOLED")]
        self.assertTrue((pd.to_datetime(f.train_end)<pd.to_datetime(f.test_start)).all())
        self.assertEqual(set(f.minimum_prior_opportunities),{10,20,30})
        holdout=pd.read_csv(self.art/"temporal_holdout_metrics.csv")
        self.assertTrue((pd.to_datetime(holdout.train_end)<pd.to_datetime(holdout.test_start)).all())
        predictions=pd.read_csv(self.data/"temporal_holdout_predictions.csv")
        self.assertTrue((predictions.prior_opportunities>=0).all())
        self.assertTrue((predictions.loc[predictions.prior_opportunities<20,"historical_effect_applied"]==0).all())

    def test_negative_controls_and_stability(self):
        controls=pd.read_csv(self.art/"negative_controls.csv")
        self.assertTrue(controls.pass_check.all())
        effects=pd.read_csv(self.art/"batter_adjusted_effects.csv")
        self.assertGreater(effects[effects.opportunities<20].uncertainty_width.mean(),effects[effects.opportunities>=50].uncertainty_width.mean())

    def test_sprint3_inputs_match_manifest(self):
        m=json.loads((self.art/"run_manifest.json").read_text())
        for rel,expected in m["input_artifact_hashes"].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),expected)
        self.assertEqual(m["accepted_sprint3"]["accepted_manifest_sha256"],ACCEPTED_SPRINT3_MANIFEST_SHA256)
        self.assertEqual(m["accepted_sprint3"]["accepted_feature_sha256"],ACCEPTED_FEATURE_SHA256)

    def test_expected_recognition_and_support_classification(self):
        s=pd.read_csv(self.data/"complete_batter_results.csv")
        self.assertAlmostEqual(s.expected_recognized.sum(),pd.read_csv(self.data/"batter_recognition_opportunities.csv").expected_probability.sum(),places=8)
        self.assertTrue(s.loc[s.opportunities<PUBLISH_N,"support_classification"].eq("ALL_OBSERVED_BATTERS").all())
        self.assertTrue(s.loc[s.opportunities>=RANK_N,"support_classification"].eq("RANKING_ELIGIBLE").all())
        self.assertTrue(s.loc[s.opportunities.between(PUBLISH_N,RANK_N-1),"support_classification"].eq("PUBLICATION_ELIGIBLE").all())

    def test_shrinkage_and_deterministic_ties(self):
        effects=pd.read_csv(self.art/"batter_adjusted_effects.csv")
        self.assertGreater(effects[effects.opportunities<20].uncertainty_width.mean(),effects[effects.opportunities>=50].uncertainty_width.mean())
        frame=pd.DataFrame({"batter_id":[3,1,2],"effect":[.2,.2,.1]})
        self.assertEqual(deterministic_rank(frame,"effect").tolist(),[1,1,3])

    def test_boundary_and_figure_reconciliation(self):
        boundary=pd.read_csv(self.art/"boundary_uncertainty_sensitivity.csv")
        self.assertEqual(boundary.excluded_boundary_band_inches.tolist(),list(BOUNDARY_THRESHOLDS))
        self.assertTrue(boundary.opportunities.is_monotonic_decreasing)
        figure1=pd.read_csv(self.art/"figure1_raw_vs_adjusted.csv")
        publication=pd.read_csv(self.data/"publication_eligible_results.csv")
        self.assertEqual(set(figure1.batter_id),set(publication.batter_id))
        figure3=pd.read_csv(self.art/"figure3_adjusted_leaderboard.csv")
        leaderboard=pd.read_csv(self.data/"ranking_eligible_leaderboard.csv")
        self.assertEqual(figure3.batter_id.tolist(),leaderboard.head(len(figure3)).batter_id.tolist())

    def test_artifact_hash_reproducibility(self):
        for line in (self.art/"artifact_hashes.sha256").read_text().splitlines():
            expected,rel=line.split("  ",1)
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),expected)

    def test_analysis_is_byte_deterministic(self):
        bases=[self.data,self.art,ROOT/"docs/sprint4"]
        def digest():
            h=hashlib.sha256()
            for base in bases:
                for path in sorted(p for p in base.rglob("*") if p.is_file()):h.update(str(path.relative_to(ROOT)).encode());h.update(path.read_bytes())
            return h.hexdigest()
        before=digest();run(ROOT);self.assertEqual(before,digest())


if __name__=="__main__": unittest.main()
