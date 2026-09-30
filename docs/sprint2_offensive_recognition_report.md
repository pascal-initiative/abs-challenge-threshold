# Sprint 2 — Offensive recognition analysis

This analysis is restricted to **2026-08-24 through 2026-08-30**. It did not acquire or analyze full-season data. Sprint 1 accepted outputs were read-only inputs.

## 1. Population

The population reconciles exactly: 509 incorrect called strikes, comprising 484 legal opportunities, 15 exhausted-resource exclusions, and 10 position-player-pitching exclusions. The analytical population has 96 recognized and 388 not recognized opportunities. No other rows were excluded.

## 2. Baseline recognition

Batters challenged 96 of 484 eligible incorrect strikes (19.8%). Recognition means the batter challenged; challenge outcome never defines the label.

## 3. Geometry

Boundary distance had a positive association with recognition (log-odds coefficient per inch: 0.538, 95% CI 0.279 to 0.798). The distance-only repeated out-of-fold ROC AUC was 0.617, PR AUC 0.286, log loss 0.487, and Brier score 0.155. The expanded geometry model changed ROC AUC by +0.025 and log loss by -0.001.

Miss axis and handedness-aware location are included in Model A. Corner labels retain both vertical and horizontal components, such as ABOVE_INSIDE. These results describe association and out-of-fold discrimination, not perception causality.

## 4. Pitch characteristics

The pitch block did not add reliable held-out information beyond geometry: it changed ROC AUC by -0.004, PR AUC by -0.001, log loss by +0.015, and Brier score by +0.002. Pitch family alone changed ROC AUC -0.012 and log loss +0.008; velocity/movement/release fields without pitch family changed ROC AUC +0.005 and log loss +0.007. Negative log-loss/Brier changes indicate improvement. Unsupported pitch-family rates remain present with sample warnings; they are not interpreted individually.

Supported pitch-family summaries (`n >= 20`):

| Family | Opportunities | Mean miss (in) | Raw rate | Model-adjusted rate |
|---|---:|---:|---:|---:|
| CHANGEUP | 33 | 0.98 | 18.2% | 21.9% |
| CURVEBALL | 45 | 0.98 | 17.8% | 33.1% |
| CUTTER | 48 | 0.99 | 12.5% | 14.8% |
| FOUR_SEAM | 155 | 0.95 | 21.3% | 17.6% |
| SINKER | 110 | 1.14 | 19.1% | 16.6% |
| SLIDER | 54 | 1.12 | 24.1% | 27.9% |
| SWEEPER | 28 | 1.00 | 25.0% | 29.7% |

## 5. Situation

Situation added the clearest incremental pilot signal. Adding count, outs, runners, inning, score, and remaining inventory changed ROC AUC by +0.060, PR AUC by +0.088, log loss by -0.025, and Brier score by -0.007. Average adjusted recognition was 17.6% with one challenge and 20.9% with two. The detailed coefficient table preserves standardized penalized estimates, but classical uncertainty is withheld for these expanded singular designs; no coefficient was selected for significance.

## 6. Human effects

- **Batter: insufficient sample.** 257 groups; median 2.0 opportunities, maximum 7, and 7 groups with at least five. Adding regularized identity changed ROC AUC +0.001 and log loss +0.002.
- **Pitcher: insufficient sample.** 249 groups; median 2.0 opportunities, maximum 8, and 9 groups with at least five. Adding regularized identity changed ROC AUC +0.005 and log loss -0.004.
- **Catcher: no detectable pilot signal.** 64 groups; median 7.0 opportunities, maximum 18, and 48 groups with at least five. Adding regularized identity changed ROC AUC -0.009 and log loss +0.004.
- **Umpire: no detectable pilot signal.** 61 groups; median 7.0 opportunities, maximum 20, and 48 groups with at least five. Adding regularized identity changed ROC AUC -0.014 and log loss +0.013.

Identity labels are used only as regularized model inputs. No individual coefficient table or ranking is published. Sparse groups and unseen identities in held-out games constrain these tests.

## 7. Early versus late

Early, middle, and late recognition rates are reported with Wilson intervals. The controlled situation model uses raw inning alongside geometry, pitch, count, runners, score, and inventory. Average adjusted recognition probabilities at representative innings 2, 5, and 8 were 18.2%, 19.9%, and 21.6%. These estimates are exploratory; the report does not characterize late-game behavior as optimal or suboptimal.

## 8. Limitations

This is one week and 484 opportunities. Repeated cross-validation reduces dependence on one split, but folds remain correlated across repeats and uncertainty is descriptive. Games are held together within folds to limit within-game leakage. Identity support is especially sparse. Regularized identity models do not provide classical AIC/BIC or coefficient p-values. Statcast geometry is public rounded measurement, and challenged pitches helped validate geometry in Sprint 1 but are a selected subset. Model comparisons can vary with reasonable encoding and regularization choices; only a fixed, documented specification was run. Results are predictive associations, not causal effects.

## 9. Recommendation

Do not expand the data during Sprint 2. Preserve this pilot as the fixed mechanism and pipeline check. A later, separately authorized sprint could test the primary geometry, pitch, and situation hypotheses across the full season, while identity effects should proceed only with preregistered support thresholds and grouped temporal validation. The strongest candidates for later validation are those with out-of-fold improvement in `model_comparisons.csv`; null and adverse changes are equally retained.

## Evaluation design

All models use 10 repeats of 5-fold stratified, group-by-game cross-validation. Every opportunity receives exactly 10 held-out predictions, averaged for the published row-level probability. All predictive models use the same fixed L2 penalty (C=1) because expanded unpenalized pilot models were singular; no penalty search was performed. Classical AIC/BIC and coefficient uncertainty are therefore reported only for the stable unpenalized distance baseline. Calibration reports intercept, slope, five-bin expected calibration error, and Brier score. The figures show untruncated 0–1 probability axes, group sizes, and Wilson or model intervals.

## Reproducibility and files

Run `python -m src.offensive_recognition` after installing `requirements.txt`. Required tables are under `data/analysis/`; model coefficients, comparisons, identity support, pitch-family summaries, figures, and a run manifest are under `artifacts/sprint2/`. The notebook is a read-only inspection layer. The run manifest records input and output hashes and explicitly records that no full-season expansion occurred.
