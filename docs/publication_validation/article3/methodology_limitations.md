# Methodology Disclosure and Limitations Notes

## Required methodology box

- Snapshot: accepted Sprint 4, covering 2026-03-25 through 2026-09-09.
- Population: 10,755 legal incorrect-called-strike opportunities; 2,112 recognized; 602 batters.
- Outcome: `recognized = 1` only when the batter challenged the eligible opportunity; challenge success and outcome are not used.
- Baseline: accepted Sprint 3 situation model with approved non-batter geometry and context features.
- Batter information: only prior recognition history available before each opportunity; minimum 20 prior opportunities in the primary predictive model.
- Temporal test: train through July 31; final holdout August 1–September 9; 2,830 holdout opportunities.
- Adjustment: empirical-Bayes normal random effect with shrinkage; publication threshold 20 opportunities and ranking threshold 30.
- Held-out result: log loss 0.43033 to 0.41757; Brier 0.13598 to 0.13142; ROC AUC 0.75399 to 0.77286.
- Stability: 168 batters with at least 10 opportunities in each ordered half; Spearman 0.474 (0.333–0.592).

## Required limitations

The analysis covers one partial MLB season and cannot establish multi-season persistence. Challenge action is a behavioral outcome, not a direct perception test. Batter identity may proxy coaching, team policy, confidence, timing, communication, or unmeasured pitch and game context. The baseline controls only accepted measured features. Intervals quantify estimate uncertainty under the accepted model but do not exhaust model uncertainty. The moderate-miss result is a subgroup sensitivity; the obvious-miss subgroup has only seven supported batters. Adjacent leaderboard ranks usually overlap and must not be narrated as distinct tiers. Results describe the accepted snapshot and should not be projected automatically to a different ABS zone, rule set, or season.
