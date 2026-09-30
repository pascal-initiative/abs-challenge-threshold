# Sprint 2 methodology — offensive recognition

## Fixed scope and population

Sprint 2 reads the accepted Sprint 1 `data/processed/pitches.csv` and `challenges.csv`. It performs no acquisition. The entry point fixes the date range to August 24–30, 2026 and rejects any other range or input dates. Before and after analysis it hashes every Sprint 1 processed artifact and fails if any hash changes.

The candidate population is every row with `original_call=STRIKE` and `derived_abs_call=BALL`. Legal recognition opportunities additionally require `challenge_available=True` and exclude `SURVIVED_RESOURCE`, `UNKNOWN`, and all position-player-pitching cases. A challenged eligible pitch must match a Savant challenge whose challenger role is BATTER. `recognized` is one exactly when that batter challenged and zero otherwise. Challenge success is retained but never used to construct the outcome.

Analysis stops unless the population is 509 incorrect called strikes, 484 legal opportunities, 96 recognized, 388 not recognized, 15 resource exclusions, 10 unknown legal-restriction exclusions, and zero other exclusions. It also stops for missing model fields, ambiguous challenge roles, non-pilot data, or a failed Sprint 1 validation gate.

## Features

All Sprint 1 source values remain unchanged. New features live in `data/analysis/offensive_recognition_features.csv`.

`abs_distance` is the absolute value of the signed Sprint 1 ball-to-zone boundary distance. The `_inches` version multiplies feet by 12. Geometry components first measure the ball center beyond the unexpanded 17-inch rectangle: horizontal excess is `max(abs(plate_x) - 17/24, 0)` and vertical excess is the distance above `abs_zone_top` or below `abs_zone_bot`. `corner_proximity` is Euclidean center distance when both components are positive and zero otherwise. These center-to-rectangle components accompany, rather than replace, the ball-edge `abs_distance`.

`miss_axis` is HORIZONTAL when only horizontal excess is positive, VERTICAL when only vertical excess is positive, and CORNER when both are positive. Statcast `plate_x` is interpreted from the catcher's perspective. A negative horizontal miss is inside to a right-handed batter; a positive miss is inside to a left-handed batter. Corner `miss_side` retains both labels, such as `ABOVE_INSIDE`, because collapsing either component would discard information.

Pitch codes map before modeling to FOUR_SEAM, SINKER, CUTTER, SLIDER, SWEEPER, CURVEBALL, CHANGEUP, SPLITTER, or OTHER. Raw pitch type remains present. Spin axis is encoded as sine and cosine to respect circularity. Source pitch measurements are never overwritten.

`count` is pre-pitch balls-strikes. `base_state` is three occupancy bits in 1B/2B/3B order. `two_strike_count` and `strike_three_call` are both YES when the pre-pitch strike count is two; they are preserved as separately requested features but only the full count enters Model C to avoid deterministic duplication. Inning groups are EARLY (1–3), MIDDLE (4–6), and LATE (7+). The source `score_diff` remains home minus away. `offense_score_diff` reverses that sign in the top half so positive always means the batting team is ahead; `score_state` categorizes this value. The model uses offense score difference and raw inning; grouped representations remain descriptive to avoid duplicating the same signal.

## Descriptive analysis

The descriptive table reports opportunities, recognized, not recognized, recognition rate, and a 95% Wilson interval. Rates with fewer than 20 opportunities remain machine-readable but `display_rate` is suppressed with a warning. Distance bins are 0–0.25, 0.25–0.5, 0.5–1, 1–2, and 2+ inches. Velocity bins are <85, 85–<90, 90–<95, and 95+ mph. Movement bins are empirical quartiles. No identity rates or rankings are produced.

## Models and evaluation

The fixed sequence is DISTANCE, A_GEOMETRY, B_PITCH, C_SITUATION, followed by separate batter, pitcher, catcher, umpire, and combined identity additions. Distance uses only boundary distance. Model A adds geometry components, miss axis, and miss side. Model B adds pitch family, velocity, movement, spin, extension, release position, pitch hand, and batter side. Model C adds count, outs, bases, inning, score difference, and remaining challenges.

The initial unpenalized expanded design was singular because sparse categories and redundant pilot geometry produce an unstable Hessian. Per the stop condition, that fit was rejected rather than interpreted. All predictive models therefore use the same L2 logistic penalty with fixed `C=1`; there is no hyperparameter search. Continuous variables are median-imputed and standardized within each training fold. Categoricals are most-frequent-imputed and fully one-hot encoded within each fold; the L2 penalty resolves redundant intercept coding, and held-out unseen levels are encoded as all zero. The population currently has no missing required predictors, so imputation is a pipeline safeguard rather than an unexplained modeling choice.

The stable unpenalized one-variable distance model supplies its per-inch coefficient, standard error, 95% interval, p-value, AIC, and BIC. Expanded models publish standardized penalized coefficients without classical intervals or p-values. This avoids presenting invalid uncertainty after the singular-fit finding.

Evaluation uses 10 repeats of five-fold stratified group cross-validation. The group is `game_pk`, so all opportunities in a game remain together. Each pitch receives exactly 10 out-of-fold predictions, averaged for the published prediction. Metrics are ROC AUC, PR AUC, log loss, Brier score, calibration intercept and slope, and five-bin expected calibration error. Fold means and standard deviations are also retained. Repeats are correlated and their standard deviations are descriptive, not formal confidence intervals.

Incremental value is the expanded minus baseline metric. Positive ROC/PR changes and negative log-loss/Brier changes favor the expansion. Mixed directions are recorded without selecting a preferred metric after seeing results.

## Secondary analyses

Pitch-family summaries include opportunity count, raw mean boundary distance, raw recognition rate, and a Model B average marginal prediction formed by setting each row's pitch family to the target while preserving its other values. Families below 20 opportunities are marked unsupported.

Model C marginal predictions compare representative innings 2, 5, and 8 and challenge inventories 1 and 2 while preserving other observed covariates. These are model summaries, not causal contrasts. Movement remains continuous in Model B/C; plots add quartile summaries only to make patterns visible. No interaction search is performed because the pilot is too small.

Identity models add one categorical identity at a time to Model C, followed by a combined exploratory model. Individual coefficients are not reported as rankings. Support distributions include the number of groups, quartiles, maximum, and counts above five and ten opportunities. Batter or pitcher analyses with median support below five or fewer than ten groups at five opportunities are labeled insufficient sample. Other labels depend on fixed predictive-improvement rules and remain exploratory. Catcher comparisons omit batter/pitcher identities because their support already fails that threshold; adding poorly supported controls would increase sparsity without a defensible pilot estimate.

## Interpretation limits

This one-week sample cannot support causal effects, player quality, optimal challenge strategy, or definitive identity effects. Challenge decisions within games and players are correlated. Grouping games prevents within-game leakage but does not create an independent season. Results may depend on reasonable fixed encoding and regularization choices. No feature selection, interaction fishing, leverage model, run-expectancy model, WPA model, or player leaderboard is included. Null and adverse model transitions are preserved.

Any full-season analysis belongs to a later, separately authorized sprint. Sprint 2 remains pilot-only even if its report recommends hypotheses for later validation.
