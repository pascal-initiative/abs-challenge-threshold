# Sprint 4 — Batter Recognition Skill

## 1. Executive summary

The immutable Sprint 3 population was verified before analysis. Historical batter recognition information improved the final future holdout beyond the accepted opportunity-only model (log loss -0.0128, Brier -0.0046, ROC AUC +0.0189). Adjusted effects showed supported ordered-half stability. The evidence supports an adjusted leaderboard for publication validation, but point ranks with overlapping uncertainty are not distinct and bottom rankings require caution. No causal mechanism is identified.

## 2. Inherited Sprint 3 snapshot/hash verification

Status: **VERIFIED**. Manifest `58abbfabb9318692e14199dcd6099fe847ae6497ef27e84e22cea45f9b5561d0`; feature table `b6f7c91b9d6ee2dee0d28bfff643c78688661cad631bf69c6a5c906253a9ccd0`; population audit `a396972176c2ff38fb829bf59daee37650320fdcfcd454e6309ae75bf1fe3fc8`. All 43 declared Sprint 3 outputs were rehashed successfully before Sprint 4 ran.

## 3. Population counts

The frozen 2026-03-25 through 2026-09-09 population contains 10,755 legal incorrect-called-strike opportunities, 2,112 recognized, 8,643 not recognized, and 602 observed batters. Recognition remains the batter's challenge action; outcome is unused.

## 4. Baseline opportunity-model specification

The baseline is accepted Sprint 3 Model C (`C_SITUATION`): geometry (`abs_distance`, horizontal/vertical distance, corner proximity, miss axis/side), pitch family/shape and handedness, plus inning, offense score differential, count, outs, base state, and challenges remaining. Numeric imputation/scaling, categorical imputation/one-hot encoding, and L2 logistic regression with C=1 are unchanged. No batter field is included.

## 5. Batter-history construction

The batter model adds one empirical-Bayes batter log-odds effect estimated only from opportunities strictly before the prediction period. A batter effect is applied only after 20 prior opportunities; otherwise it is zero. No held-out outcome, future challenge, full-season retrospective aggregate, challenge outcome, or post-decision field enters a future prediction.

## 6. Temporal evaluation design

Development ends 2026-06-30, validation is July, and the final untouched holdout is 2026-08-01 through 2026-09-09. The final model and batter histories are refit through July only. Expanding monthly results and alternative July/August/September cutoffs remain sensitivity evidence.

## 7. Baseline versus batter-model metrics

| Metric | Baseline opportunity model | Batter-information model | Difference |
|---|---:|---:|---:|
| Log loss | 0.430328 | 0.417568 | -0.012760 |
| Brier score | 0.135983 | 0.131420 | -0.004563 |
| ROC AUC | 0.753994 | 0.772862 | +0.018869 |
| Calibration intercept | 0.063076 | 0.124836 | +0.061760 |
| Calibration slope | 0.979364 | 1.034066 | +0.054701 |

## 8. Adjusted-recognition methodology

For each batter, expected recognized opportunities are the sum of baseline probabilities. The descriptive residual is observed minus expected. The adjusted estimate is the mean change in recognition probability after adding the posterior batter log-odds effect to each opportunity's baseline logit.

## 9. Shrinkage and small-sample protection

The random effect follows Normal(0, tau²); empirical-Bayes maximum marginal likelihood estimated tau=0.761. Posterior means and 95% intervals use deterministic quadrature/grid calculations. Sparse records shrink more toward zero and retain wider intervals; well-supported records are driven more by their observations.

## 10. Support-tier methodology

All 602 batters remain members of the `ALL_OBSERVED_BATTERS` research universe. The exclusive highest attained tier is `ALL_OBSERVED_BATTERS`, `PUBLICATION_ELIGIBLE`, or `RANKING_ELIGIBLE`. Publication requires 20+ opportunities (243 batters); ranking requires 30+ (123). These inherited thresholds are retained because the support-sensitivity table shows the uncertainty/stability tradeoff rather than because they create a preferred leaderboard.

## 11. Complete batter results

`complete_batter_results.csv/json` retain every batter, raw and expected counts/rates, residuals, adjusted estimates, intervals, temporal support, and eligibility.

## 12. Publication-eligible results

`publication_eligible_results.csv/json` contain 243 batters while preserving all lower-support records in the complete table.

## 13. Ranking-eligible leaderboard

- Bryce Harper: 31 opportunities, 21 recognized, adjusted effect +36.7% (+22.3% to +50.2%).
- José Caballero: 32 opportunities, 17 recognized, adjusted effect +25.9% (+12.4% to +40.1%).
- Nolan Schanuel: 39 opportunities, 20 recognized, adjusted effect +25.6% (+13.1% to +38.7%).
- Sal Stewart: 49 opportunities, 27 recognized, adjusted effect +24.2% (+12.8% to +35.8%).
- Jose Altuve: 43 opportunities, 20 recognized, adjusted effect +20.4% (+9.0% to +32.7%).
- Munetaka Murakami: 34 opportunities, 14 recognized, adjusted effect +17.2% (+4.9% to +30.9%).
- JJ Bleday: 31 opportunities, 15 recognized, adjusted effect +15.5% (+2.3% to +29.5%).
- Caleb Durbin: 38 opportunities, 15 recognized, adjusted effect +13.9% (+2.5% to +27.1%).
- Josh Bell: 30 opportunities, 12 recognized, adjusted effect +13.8% (+0.7% to +28.7%).
- Marcell Ozuna: 33 opportunities, 12 recognized, adjusted effect +13.2% (+1.9% to +26.9%).

The ordering is deterministic. `interval_overlaps_previous` explicitly marks adjacent point ranks whose intervals overlap; such ranks should not be described as meaningfully different.

## 14. Split-half stability

At 10+ opportunities in each ordered half, n=168, Spearman=0.474 (bootstrap 95% 0.333 to 0.592), Pearson=0.561 (0.417 to 0.669), directional consistency=63.7%. This is moderate repeatability, not deterministic or multi-season persistence.

## 15. Minimum-support sensitivity

Thresholds 10, 15, 20, 25, 30, 40, 50 are reported with eligible counts, primary-rank correlation, top-10 overlap, interval width, and ordered-half stability. The minimum defined ranking correlation with the primary specification is 0.941. At 50 opportunities only 14 batters remain and 6 meet balanced split-half support; that split-half estimate is explicitly treated as inconclusive low-n evidence, not as a stable contrary result.

## 16. Boundary-uncertainty sensitivity

The accepted inclusive exclusion bands 0, 0.05, 0.1, 0.25, 0.5 inches were applied without changing geometry. Minimum nonzero-band rank correlation was 0.941; all variants report future-model deltas and top-10 overlap.

## 17. Opportunity-difficulty sensitivity

Marginal (≤0.5 inch), moderate (>0.5 to 2 inches), and obvious (>2 inches) groups reuse Sprint 3 distance bins. The future improvement is concentrated in the moderate group (delta log loss -0.0119); it is not driven by obvious misses (obvious-group delta +0.0004). Marginal and obvious subgroup estimates are weak and their smaller support precludes standalone player claims.

## 18. Raw-versus-adjusted analysis

`raw_vs_adjusted_comparison.csv/json` identifies material improvements/declines after opportunity adjustment. Raw challenge rate is not treated as recognition skill, and adjusted order remains an estimate rather than ground truth.

## 19. Candidate player case studies

- Bryce Harper: 31 opportunities, raw 67.7%, expected 20.6%, adjusted +36.7%; Strongly supported high adjusted recognizer.
- Nick Kurtz: 39 opportunities, raw 23.1%, expected 26.6%, adjusted -3.0%; Standing declines materially after opportunity adjustment.
- Jonathan Aranda: 43 opportunities, raw 20.9%, expected 20.4%, adjusted +0.0%; Well-supported comparison batter near contextual expectation.

## 20. Bottom-ranking publication assessment

Gate: **SUPPORTED_WITH_CAUTION**. Several supported negative intervals exist, but public negative characterization receives the higher standard: retain intervals, context, neutral wording, and avoid implying cause or fixed ability.

## 21. Figure-ready datasets

`figure1_raw_vs_adjusted.csv/json`, `figure2_temporal_stability.csv/json`, `figure3_adjusted_leaderboard.csv/json`, and `figure4_case_studies.csv/json` are generated directly from accepted artifacts. No branded article graphics were created.

## 22. Claims matrix

`claims_matrix.csv/json` evaluates 9 claims; 6 are supported as written. Claims that recognition is innate, permanently persistent, or caused by vision/experience/approach/coaching/confidence/cognitive ability are prohibited.

## 23. Adversarial validation

Every requested challenge is recorded in `adversarial_validation.csv/json`, including failed challenges. Result: None of the preregistered adversarial challenges failed.

## 24. Limitations

This is one season-to-date observational snapshot. Challenge action is not perception or intent. Residual confounding, repeated-player/game dependence, source measurement error, unequal opportunity support, dugout communication, and model specification remain. Bootstrap intervals describe supported batters, not a superpopulation causal effect. Subgroup samples are smaller. Multi-season persistence and mechanism are untested.

## 25. Decision gates

- Batter historical predictive value: **PROCEED**
- Adjusted recognition differences: **PROCEED**
- Temporal stability: **SUPPORTED**
- Adjusted leaderboard publication: **PROCEED**
- Bottom-ranking publication: **SUPPORTED_WITH_CAUTION**
- Player case studies: **PROCEED**
- Article 3 research basis: **READY_FOR_PUBLICATION_VALIDATION**

## 26. Recommended next step

Stop at the Sprint 4 boundary and submit this evidence package for Pascal review. If approved, begin a separate publication-validation sprint; do not draft or publish from these research artifacts alone.
