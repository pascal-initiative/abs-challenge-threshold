# Article 2 research report — What makes a batter challenge?

Research evidence for review; **not an article draft**. Frozen 2026-03-25–2026-09-09 snapshot. No new acquisition, no reconstruction changes, no causal interpretation.

## Population and provenance

The existing `src.sprint3.build_population` independently reproduces **10,755 legal incorrect-called-strike opportunities**, **2,112 challenges**, and **19.64%** observed challenging. Every outcome is whether the batter challenged; official overturn success is not used as the outcome. This matters because one reconstructed opportunity was officially confirmed.

Frozen validation reproduces 9,482/9,485 official decisions. The population comes from processed pitch records, not from filtering successful challenges. Exclusions:

| group | n |
| --- | --- |
| incorrect_called_strikes | 11704 |
| legal_recognition_opportunities | 10755 |
| recognized | 2112 |
| not_recognized | 8643 |
| resource_constrained | 789 |
| position_player_pitching | 160 |
| unknown | 0 |
| other_exclusions | 0 |


All 10,755 rows enter description and the temporal partitions; none are silently dropped for feature missingness. Missing numeric pitch characteristics are median-imputed with indicators inside training folds. Empty runner identifiers indicate unoccupied bases per existing parser. Missingness for every source/derived column is in `tables/missingness.csv`; predictor-specific counts and package versions are in the manifest. No validated public pre-pitch leverage index was found in these processed data, so this sprint uses transparent situation variables and does **not** manufacture a leverage index.

`manifest.json` records SHA-256 hashes of processed inputs, frozen publication-validation artifacts and source modules before and after analysis. They match. Raw response receipts and the existing run manifest retain original retrieval dates and raw hashes. Exact raw-byte regeneration requires the repository's archived objects; endpoint re-downloads can change. Reproduction of this sprint is offline from accepted processed inputs.

## Feature definitions and decision timing

- Absolute miss is the original signed circle/rectangle boundary distance in feet ×12, positive for these reconstructed balls. No revised geometry is used.
- Horizontal/vertical distances are positive center-to-rectangle components in inches, **not independently radius-adjusted misses**. The actual miss distance incorporates the 1.45-inch ball radius and rounded corners. `miss_side` distinguishes above/below, inside/outside and corners using actual batting stance; signed plate side is catcher's perspective. Hand/location combinations allow handedness differences.
- Count, outs, runners and home/away scores come from Statcast pre-pitch state, confirmed by the source parser and `state_timing == PRE_PITCH`. Offense score differential reverses home-minus-away for the top half.
- Late-close: inning ≥7 and absolute batting-team margin ≤2. Potential plate-appearance ending: two strikes. Potential inning ending: two strikes and two outs. Potential game ending: also bottom 9+ with batting team behind. These mean a strikeout could end play, without using what happened afterward; dropped-third-strike and unusual-event exceptions prevent calling them certain endings.
- Inventory is the existing sequential reconstruction, recorded **before** processing the current challenge. Both teams start with two; official confirmed challenges decrement inventory, overturned challenges retain it. At each extra inning, a team at zero receives one. Unknown/conflicting history propagates uncertainty, and position-player pitching blocks availability. We reuse `affected_team_challenges_remaining`, never recount from successful challenges or assume all rows start with two. One-left interacts with inning and late-close. No true leverage interaction can be estimated here.
- Velocity, movement, spin, extension, release position and pitch family describe the pitch already seen when a batter decides. They are physical covariates, not a claim the batter sees tracking-system numerical measurements. Official results, subsequent counts/scores, eventual winners, future inventory, identities and challenge outcome never enter model predictors.

## Model and validation design

Fixed L2 logistic regression, C=1, no class reweighting, 5-quantile-knot cubic spline for absolute distance, training-only preprocessing, seed 20260915. Sparse categories use one-hot encoding, unknown categories map to zero. Continuous features are scaled; no hyperparameter search. Distance is not constrained to be monotone.

Stages are cumulative: A geometry; B A+count; C B+game context; D C+inventory and its interactions. E adds the single prespecified pitch block to the selected A–D baseline. This ordering isolates context beyond count and inventory beyond both. It differs from earlier sprints' A/B/C labels; compare definitions, not letters.

Training uses March–June; July selects the simplest A–D model within .001 log loss of the best. The selected baseline is **D**. Every stage is refitted on March–July and evaluated once on August–September 9. E is an incremental test, not allowed to redefine the non-pitch baseline after seeing final test scores.

| split | start | end | opportunities | challenges | batters |
| --- | --- | --- | --- | --- | --- |
| test | 2026-08-01 | 2026-09-09 | 2830 | 567 | 457 |
| train | 2026-03-25 | 2026-06-30 | 6131 | 1186 | 536 |
| validation | 2026-07-01 | 2026-07-31 | 1794 | 359 | 399 |


| model | period | n | challenges | log_loss | brier | auc | calibration_intercept | calibration_slope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | test | 2830 | 567 | 0.47702 | 0.15257 | 0.66392 | 0.23348 | 1.128 |
| B | test | 2830 | 567 | 0.43747 | 0.13796 | 0.74073 | 0.06959 | 1.0035 |
| C | test | 2830 | 567 | 0.43263 | 0.13688 | 0.75201 | 0.055685 | 0.98672 |
| D | test | 2830 | 567 | 0.43137 | 0.13634 | 0.75314 | 0.057399 | 0.9862 |
| E | test | 2830 | 567 | 0.43181 | 0.13653 | 0.75325 | 0.020504 | 0.94724 |
| intercept | test | 2830 | 567 | 0.50098 | 0.16024 | 0.5 | nan | nan |


The test period is held out from this sprint's fitting and selection, but the same frozen season has appeared in earlier exploratory sprints. This is temporal validation of a specified analysis, **not a pristine never-seen external replication**. More-season validation remains needed. The same batters can occur on both sides of a boundary; no batter identity enters the model, but persistent team/player characteristics can still induce dependence. Game- and batter-cluster paired bootstrap intervals address test-loss dependence conditionally on the fitted models; they do not include retraining uncertainty.

### Incremental held-out performance

Negative change means improvement. Material improvement was defined before score inspection as ≥.001 lower log loss, with confidence and stability considered separately.

| baseline | added | cluster | n | challenges | delta_log_loss | ci95_low | ci95_high | delta_brier | total_log_likelihood_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | B | game_pk | 2830 | 567 | -0.039546 | -0.050377 | -0.02836 | -0.014611 | 111.92 |
| B | C | game_pk | 2830 | 567 | -0.0048369 | -0.0093191 | -0.00031866 | -0.0010815 | 13.689 |
| C | D | game_pk | 2830 | 567 | -0.0012592 | -0.003599 | 0.0013023 | -0.00054436 | 3.5636 |
| D | E | game_pk | 2830 | 567 | 0.0004346 | -0.0026698 | 0.0036606 | 0.00019176 | -1.2299 |


Full metrics include Brier, ROC AUC, calibration intercept/slope and summed out-of-sample log-likelihood gain. Classification accuracy is not used. E tests the complete pitch block once; a null result is not proof that every physical pitch attribute has zero effect.

## Descriptive geometry and count

Eight equal-frequency distance bins were constructed without reference to outcomes, providing about 1,344 opportunities per bin instead of sparse arbitrary tail bins. Wilson intervals describe binomial sampling uncertainty only; repeated-observation robustness uses cluster-based analyses below.

| distance_group | opportunities | challenges | challenge_rate | ci95_low | ci95_high | distance_min | distance_max | distance_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 | 1345 | 162 | 0.12045 | 0.10412 | 0.13893 | 0.00020746 | 0.16214 | 0.078868 |
| Q2 | 1344 | 196 | 0.14583 | 0.12797 | 0.16571 | 0.1622 | 0.36058 | 0.26074 |
| Q3 | 1344 | 208 | 0.15476 | 0.13641 | 0.17508 | 0.36066 | 0.56603 | 0.46176 |
| Q4 | 1345 | 217 | 0.16134 | 0.14265 | 0.18196 | 0.56604 | 0.80015 | 0.67884 |
| Q5 | 1344 | 265 | 0.19717 | 0.17678 | 0.21929 | 0.80069 | 1.0836 | 0.93535 |
| Q6 | 1344 | 275 | 0.20461 | 0.1839 | 0.22701 | 1.0837 | 1.4546 | 1.2612 |
| Q7 | 1344 | 354 | 0.26339 | 0.24054 | 0.28759 | 1.4552 | 2.0133 | 1.7038 |
| Q8 | 1345 | 435 | 0.32342 | 0.29895 | 0.34889 | 2.0143 | 6.4469 | 2.6919 |


There are **0 downward steps among seven adjacent observed-bin comparisons**, and **0 downward steps on the 100-point adjusted spline grid**. This directly checks monotonicity rather than assuming it; smooth monotonic association is not established by a positive linear coefficient alone. The plotted spline stops at the 99th percentile to avoid tail extrapolation claims. Full tail observations remain in every model.

Pre-pitch two-strike counts: **580/1,202 (48.25%)**, versus **1,532/9,553 (16.04%)** for other counts.

| count | opportunities | challenges | challenge_rate | ci95_low | ci95_high | standardized_probability | standardization_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-0 | 4514 | 462 | 0.10235 | 0.093841 | 0.11153 | 0.10483 | 10755 |
| 0-1 | 881 | 202 | 0.22928 | 0.20274 | 0.25818 | 0.23582 | 10755 |
| 0-2 | 207 | 97 | 0.4686 | 0.40181 | 0.53653 | 0.47351 | 10755 |
| 1-0 | 1587 | 257 | 0.16194 | 0.14464 | 0.18088 | 0.15906 | 10755 |
| 1-1 | 862 | 231 | 0.26798 | 0.23949 | 0.29853 | 0.26385 | 10755 |
| 1-2 | 365 | 150 | 0.41096 | 0.36167 | 0.46211 | 0.42448 | 10755 |
| 2-0 | 617 | 115 | 0.18639 | 0.15763 | 0.21902 | 0.17461 | 10755 |
| 2-1 | 482 | 140 | 0.29046 | 0.25171 | 0.33251 | 0.27767 | 10755 |
| 2-2 | 350 | 165 | 0.47143 | 0.41973 | 0.52375 | 0.46861 | 10755 |
| 3-0 | 314 | 28 | 0.089172 | 0.062415 | 0.12586 | 0.088523 | 10755 |
| 3-1 | 296 | 97 | 0.3277 | 0.27674 | 0.38308 | 0.32269 | 10755 |
| 3-2 | 280 | 168 | 0.6 | 0.54164 | 0.65565 | 0.57985 | 10755 |


Geometry-adjusted probabilities average predictions after replacing count over the same observed geometry distribution; they are descriptive standardizations, not interventions. `geometry_count_associations.csv` contains odds ratios and batter-cluster robust intervals from an unpenalized spline model. Coefficients for count compare with 0-0. Correlated geometry columns are omitted from this inference model to avoid redundant radius/component terms; its coefficients are not the regularized prediction model's coefficients. Direction ablation compares distance+hand with full geometry:

| model | n | challenges | log_loss | brier | auc | calibration_intercept | calibration_slope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| distance_and_hand_only | 2830 | 567 | 0.48567 | 0.15511 | 0.63234 | 0.20619 | 1.1261 |
| A_full_geometry | 2830 | 567 | 0.47702 | 0.15257 | 0.66392 | 0.23348 | 1.128 |


The conditional below-versus-above miss odds ratio is 1.74 (batter-cluster 95% CI 1.44–2.10; full sample n=10,755), controlling distance, count and hand/plate side in the association model. This supports directional asymmetry; corner and inside/outside coefficients require their individual support and intervals. Location tables and the zone map show substantial location mix differences. Use held-out ablation plus conditional coefficient intervals when discussing direction beyond distance; do not interpret raw heatmap colors as adjusted effects. Hand/location estimates can have limited support in rare corner cells.

## Situation and inventory

| late_close | opportunities | challenges | challenge_rate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| 0 | 9054 | 1658 | 0.18312 | 0.17529 | 0.19122 |
| 1 | 1701 | 454 | 0.2669 | 0.24642 | 0.28843 |


| affected_team_challenges_remaining | opportunities | challenges | challenge_rate | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| 1 | 3168 | 612 | 0.19318 | 0.17981 | 0.2073 |
| 2 | 7587 | 1500 | 0.19771 | 0.1889 | 0.20682 |


Full inning, half-inning, score, outs, runner-state and potential-ending distributions are supplied separately. Raw inventory/context rates are confounded by count, geometry, game history and team/player behavior. C versus B and D versus C are the primary incremental checks, with game and batter bootstrap intervals. None establishes that conserving a challenge causes a change in behavior. Potential game-ending samples are explicitly reported in `situation_game_ending.csv`; avoid strong conclusions from rare cells.

## Batter actual versus expected behavior

Expected probabilities use expanding monthly fits (April–September), always trained on earlier dates without batter identity. March supplies the initial training set and has no honest prior-date prediction; its 391 opportunities remain in the primary population but are explicitly excluded from residual aggregation. Thus batter residuals cover 10,364 opportunities. The baseline specification was selected on July; earlier rolling residuals are retrospective descriptive diagnostics, not a fully prospective validation of that selection procedure. Early models train on few opportunities and can be miscalibrated.

The main candidate threshold is **50 predicted opportunities**: at p=.20, binomial sampling alone gives an approximate 95% halfwidth of 11 percentage points, so even this is only a candidate screen. Thresholds 30/50/75/100 are shown below. Actual-minus-summed-expected challenges measure challenge frequency conditional on modeled opportunities, **not recognition skill, optimal decisions, or challenge accuracy**.

| minimum_n | qualifying_batters | opportunities | challenges | median_conditional_rate_halfwidth | above_simultaneous | below_simultaneous |
| --- | --- | --- | --- | --- | --- | --- |
| 30 | 117 | 4517 | 906 | 0.11428 | 4 | 0 |
| 50 | 9 | 501 | 81 | 0.091913 | 0 | 1 |
| 75 | 0 | 0 | 0 | nan | 0 | 0 |
| 100 | 0 | 0 | 0 | nan | 0 | 0 |


`batter_actual_expected.csv` contains actual/expected counts/rates, above-expected counts, conditional normal intervals using sum p(1-p), whole-game within-batter bootstrap residual-rate intervals (1,000 resamples), and simultaneous Bonferroni intervals for the qualifying set. Normal intervals assume conditional independence and fixed predictions. The game bootstrap allows within-game dependence but not arbitrary season-long within-batter dependence. Both omit fitted-baseline uncertainty and may understate total uncertainty. They must not be presented as definitive talent intervals. The additional residual shrinkage divides above-expected counts by n+50 (a fixed 50-opportunity zero-effect prior equivalent), providing transparent descriptive stabilization, **not a fitted hierarchical talent model**. Adjusted rates are additive reference-rate summaries and are not guaranteed probabilities outside the observed range.

Qualified batter summary:

| batter_name | opportunities | actual | expected | above_expected | conditional_ci95_low | conditional_ci95_high |
| --- | --- | --- | --- | --- | --- | --- |
| Xander Bogaerts | 55 | 18 | 10.431 | 7.5694 | 2.1189 | 13.02 |
| Geraldo Perdomo | 53 | 16 | 11.09 | 4.9103 | -0.39824 | 10.219 |
| Alex Bregman | 52 | 12 | 7.3247 | 4.6753 | -0.016555 | 9.3671 |
| Seiya Suzuki | 51 | 11 | 9.2381 | 1.7619 | -3.3727 | 6.8965 |
| Otto Lopez | 51 | 8 | 9.2805 | -1.2805 | -6.2606 | 3.6995 |
| Chase Meidroth | 60 | 4 | 6.8791 | -2.8791 | -7.5673 | 1.809 |
| Pete Alonso | 62 | 7 | 11.285 | -4.2849 | -9.8357 | 1.2659 |
| Yandy Díaz | 50 | 0 | 7.3958 | -7.3958 | -11.991 | -2.8001 |
| Mike Trout | 67 | 5 | 13.228 | -8.2277 | -14.062 | -2.3935 |


Candidate lists (up to ten per direction and up to ten per shrunken adjusted direction, only with the corresponding residual sign) are in `batter_candidates.csv`. Broad leaderboards and best/worst labels are not justified. The two-period stability diagnostic requires ≥20 observations in each period: {"batters_n20_both": 23, "pearson_residual_rate": 0.5555785671726143, "spearman_residual_rate": 0.5721343873517787}. It can suggest persistence but does not establish innate recognition ability. Between-player differences can reflect coaching, teammates, pitch perceptions, omitted context, and baseline calibration.

## Robustness and diagnostic limits

Across every boundary threshold, B improves on A, C improves on B, and E worsens D. Removing the top ten development-period batters or top three teams leaves this ordering intact. Linear-distance A/D improve loss slightly, so spline flexibility is not required to reproduce the principal result. Compare increments **within** each retained sample; absolute loss across boundary thresholds is not comparable because prevalence and difficulty change.

| exclude_at_or_below_inches | n | challenges | odds_ratio_per_inch | ci95_low | ci95_high |
| --- | --- | --- | --- | --- | --- |
| 0 | 10755 | 2112 | 1.7008 | 1.6011 | 1.8067 |
| 0.05 | 10308 | 2066 | 1.6864 | 1.5849 | 1.7945 |
| 0.1 | 9907 | 2017 | 1.6769 | 1.5733 | 1.7874 |
| 0.25 | 8811 | 1859 | 1.6744 | 1.5612 | 1.7959 |
| 0.5 | 7142 | 1608 | 1.6479 | 1.522 | 1.7841 |


Count improves on geometry in all six rolling months. Context improves on count in five of six; it worsens April predictions when trained on only 391 March rows. Inventory also worsens April while improving five later months, and pitch features worsen the selected baseline in all six rolling months. Rolling early-season models have limited training support. Inspect monthly rather than only pooled performance; the final test is the primary evaluation. Only nine batters reach the conservative 50-opportunity residual threshold, and none reaches 75. This is a substantive sample-size limitation, not a reason to lower the threshold until attractive rankings appear.

- Boundary sensitivity refits A–E after removing misses ≤0, .05, .10, .25 and .50 inches. Every resulting denominator is in `robustness.csv`; the primary 10,755 population is unchanged. These are sensitivity analyses, not replacement populations.
- Alternative distance specification replaces the cubic spline with a linear term for A and the selected baseline, holding other choices fixed.
- Expanding monthly results supply an additional temporal stability check (`monthly_model_performance.csv`), including small March-trained April models. These rolling tests are not an independent new dataset.
- Game and batter clustered bootstrap intervals compare final-test losses. Cluster-robust batter standard errors assess geometry/count association. They do not eliminate unmeasured confounding or establish player residual independence.
- Excluding the ten most common batters or three most common teams (selected by development-period opportunity counts) refits A–E and tests on the corresponding remaining test rows. `concentration.csv` reports retained denominators. This is a targeted influence check, not exhaustive leave-every-team-out analysis.
- No dedicated catcher, pitcher or umpire analysis is performed. Their potential confounding remains unresolved.

## Recognition versus accuracy and future decision quality

The available source supports separate future official challenge-accuracy measurement: 2,112 official overturns / 4,335 batter challenges in the frozen publication audit. That accuracy numerator is not interchangeable with the 2,112 challenges among reconstructed opportunities: one confirmed reconstructed error and one overturned reconstructed strike offset in the totals. Opportunity recognition therefore must stay separate from official success rate.

A broader decision-quality metric would require all legal decision opportunities (including correctly called strikes), calibrated pre-decision overturn probabilities, reliable inventory and timing, validated count/state values for hold versus overturn, future resource cost and uncertainty. Player comparisons would additionally need partial pooling, out-of-time calibration and replication, reliable attribution of who prompted the challenge, and a defensible utility criterion. This dataset cannot identify a batter's private certainty, signals from others, motivations, or causal decision quality.

## Reproduction and deliverables

Run the adjacent `analyze.py` with the accepted repository as `--source-root` and a new `--output` directory. See `README.md` for exact setup and command. All CSVs, Markdown tables, report, plotting data and PNG/PDF figures are generated by code. `FIGURES.md` displays the seven review figures. No Article 1 files are written.

## Research findings summary

### Strong Evidence

- **Miss distance:** observed rates rise across all eight bins, from 162/1,345 (12.04%) in the closest group to 435/1,345 (32.34%) in the farthest. The adjusted spline rises on its central-support grid. Boundary sensitivity retains a positive adjusted per-inch association; this supports a broad increasing relationship, not a mathematical monotonic law.
- **Direction beyond distance:** full geometry improves final-test loss over distance+hand alone; paired cluster intervals appear in `direction_increment.csv`. Location carries information beyond the scalar distance: log-loss gain .00866 on 2,830 test opportunities (567 challenges), game-cluster 95% interval [.00449, .01318].
- **Count:** adding count reduces test log loss by .03955 (n=2,830, 567 challenges), with both game and batter cluster intervals below zero. Count remains informative after geometry adjustment.
- **Game context:** adds a smaller .00484 loss reduction beyond count on the same test rows, with both cluster intervals below zero. This supports the context block collectively, not every individual flag or a leverage effect.
- The requested population is reproducible: 2,112 challenges / 10,755 legal reconstructed incorrect-strike opportunities (19.64%).
- Raw count and miss-distance distributions are well measured in this frozen snapshot; the tables provide denominators and uncertainty. Count's incremental evidence should be judged from B–A test loss and both clustered intervals, rather than the raw strike-three contrast alone.

### Suggestive Evidence

- Adjusted location differences and batter residual candidates warrant follow-up. Conditional residual uncertainty and prior exploratory use limit interpretation as stable player traits.
- Inventory's .00126 test loss reduction has intervals spanning zero. It was selected on July, but its separate incremental value is suggestive, not robustly established. Raw rates are 612/3,168 (19.32%) with one challenge and 1,500/7,587 (19.77%) with two. These do not measure a causal conservation effect.

### No Evidence Found

- **Pitch-characteristic predictive gain:** E worsens final-test loss by .00043 and Brier by .00019 (n=2,830, 567 challenges); its intervals span zero. It also worsens July validation and each boundary/influence-check comparison. No material incremental improvement is found for this fixed pitch block.
- **Need for spline complexity:** linear-distance sensitivity performs slightly better on final-test A and D. We retain the prespecified models, but do not claim nonlinear modeling is necessary.
- No causal effect, optimal-decision claim or ranking of intrinsic recognition skill is established by this observational sprint.
- See the numerical assessment below for incremental blocks that fail the prespecified predictive-improvement threshold. Failure to improve prediction does not prove an effect is absent.

### Cannot Determine From Available Data

- A validated numerical pre-pitch leverage index, private confidence, advice from teammates, who initiated recognition, or causal reasons for challenging.
- Whether not challenging was a mistake, whether a successful challenge was optimal, or a complete player decision-quality ranking.

### Recommended Article 2 Claims

- State the frozen dates, population definition, denominator and estimated nature of unchallenged-call classification.
- Larger reconstructed misses are challenged more often, with location contributing beyond distance; count adds substantial predictive information, and game context a smaller amount. State exact temporal test sizes and performance.
- The tested pitch-characteristic block adds no meaningful held-out gain. Inventory is a plausible smaller contributor whose incremental uncertainty remains unresolved.
- Treat batter lists as opportunity-adjusted behavior candidates for further validation.

### Claims We Should NOT Make

- “These are the best/worst challengers,” “every unchallenged miss was a bad decision,” or “a successful challenge was necessarily correct strategy.”
- “Count/context/inventory causes challenging,” “the spline proves monotonicity at every distance,” or “pitch physics has no effect.”
- “All 2026 data,” “independent external replication,” or “the 19.64% recognition rate is challenge accuracy.”

### Numerical assessment of tested information blocks

- **A → B**: Δlog loss -0.03955, 95% CI [-0.05038, -0.02836], n=2,830: meets the material improvement threshold with a game-cluster interval below zero.
- **B → C**: Δlog loss -0.00484, 95% CI [-0.00932, -0.00032], n=2,830: meets the material improvement threshold with a game-cluster interval below zero.
- **C → D**: Δlog loss -0.00126, 95% CI [-0.00360, +0.00130], n=2,830: does not establish material improvement with a game-cluster interval below zero.
- **D → E**: Δlog loss +0.00043, 95% CI [-0.00267, +0.00366], n=2,830: does not establish material improvement with a game-cluster interval below zero.
