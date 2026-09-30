import unittest
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.sprint3 import SUPPORT_PUBLISH, SUPPORT_RANK, run, temporal_folds


ROOT = Path(__file__).resolve().parents[1]


class TemporalValidationTests(unittest.TestCase):
    def test_expanding_windows_have_no_future_leakage_and_keep_games_intact(self):
        rows=[]
        for month in range(4,9):
            for game in range(3):
                for outcome in (0,1):
                    rows.append(dict(game_date=f"2026-{month:02d}-{game+1:02d}",game_pk=month*10+game,recognized=outcome))
        frame=pd.DataFrame(rows)
        for _,train,test in temporal_folds(frame):
            self.assertLess(frame.iloc[train].game_date.max(),frame.iloc[test].game_date.min())
            self.assertTrue(set(frame.iloc[train].game_pk).isdisjoint(frame.iloc[test].game_pk))

    def test_support_thresholds_are_preregistered(self):
        self.assertEqual(SUPPORT_PUBLISH,20)
        self.assertEqual(SUPPORT_RANK,30)


class Sprint3OutputTests(unittest.TestCase):
    def test_acquisition_is_complete_if_snapshot_exists(self):
        receipts=ROOT/"data/full_season/raw/receipts.jsonl"
        if not receipts.exists(): self.skipTest("Sprint 3 acquisition has not run")
        rows=[json.loads(x) for x in receipts.read_text().splitlines()]
        self.assertFalse(any(not x["ok"] for x in rows))
        self.assertEqual(sum(x["kind"]=="schedule" for x in rows),1)
        self.assertGreaterEqual(sum(x["kind"]=="feed" for x in rows),2200)

    def test_processed_games_are_unique_and_final_if_snapshot_exists(self):
        path=ROOT/"data/full_season/processed/game_manifest.csv"
        if not path.exists(): self.skipTest("Sprint 3 processing has not run")
        with path.open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),len({r["game_pk"] for r in rows}))
        self.assertTrue(all(r["status"] in ("Final","Completed Early") and r["processed"]=="True" for r in rows))

    def test_outputs_if_analysis_has_run(self):
        base=ROOT/"data/analysis/sprint3"
        if not base.exists(): self.skipTest("Sprint 3 analysis has not run")
        required=["offensive_recognition_features.csv","offensive_recognition_population_audit.json",
                  "offensive_recognition_descriptive.csv","offensive_recognition_predictions.csv",
                  "offensive_recognition_model_metrics.csv","monthly_recognition_summary.csv",
                  "replication_results.csv","identity_support.csv","resource_constrained_summary.csv",
                  "defensive_population_summary.csv","data_quality_report.json"]
        self.assertTrue(all((base/x).is_file() for x in required))
        pred=pd.read_csv(base/"offensive_recognition_predictions.csv")
        self.assertTrue(pred.predicted_probability.between(0,1).all())
        self.assertTrue(pred.groupby(["pitch_key","model"]).size().eq(1).all())

    def test_twelve_core_figures_if_analysis_has_run(self):
        base=ROOT/"artifacts/sprint3"
        if not base.exists(): self.skipTest("Sprint 3 analysis has not run")
        self.assertGreaterEqual(len(list(base.glob("*.png"))),12)

    def test_population_and_recognition_labels(self):
        base=ROOT/"data/analysis/sprint3"
        if not base.exists(): self.skipTest("Sprint 3 analysis has not run")
        audit=json.loads((base/"offensive_recognition_population_audit.json").read_text())
        self.assertTrue(audit["population_identity_holds"])
        self.assertEqual(audit["legal_recognition_opportunities"],audit["recognized"]+audit["not_recognized"])
        f=pd.read_csv(base/"offensive_recognition_features.csv",low_memory=False)
        self.assertTrue(f.affected_team_challenges_remaining.isin([1,2]).all())
        self.assertTrue((f.recognized==f.challenged.astype(str).str.lower().eq("true").astype(int)).all())
        self.assertFalse(f.survival_class.isin(["SURVIVED_RESOURCE","UNKNOWN"]).any())

    def test_unsupported_entities_cannot_rank(self):
        path=ROOT/"artifacts/sprint3/identity_effects.csv"
        if not path.exists(): self.skipTest("Sprint 3 analysis has not run")
        effects=pd.read_csv(path)
        self.assertFalse(effects.loc[effects.opportunities<SUPPORT_RANK,"rank_eligible"].any())
        self.assertFalse(effects.loc[~effects.identity_model_supported,"rank_eligible"].any())

    def test_full_analysis_is_byte_deterministic(self):
        if not (ROOT/"data/analysis/sprint3").exists(): self.skipTest("Sprint 3 analysis has not run")
        bases=[ROOT/"data/analysis/sprint3",ROOT/"artifacts/sprint3",ROOT/"docs/sprint3"]
        def digest():
            h=hashlib.sha256()
            for base in bases:
                for path in sorted(x for x in base.rglob("*") if x.is_file()):
                    h.update(str(path.relative_to(ROOT)).encode());h.update(path.read_bytes())
            return h.hexdigest()
        before=digest();run(ROOT,"2026-03-25","2026-09-09");self.assertEqual(before,digest())


if __name__=="__main__": unittest.main()
