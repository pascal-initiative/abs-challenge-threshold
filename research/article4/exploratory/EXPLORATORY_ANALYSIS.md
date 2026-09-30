# Article 4 exploratory analysis — what is a challenge worth?

This is exploratory research to decide what the evidence supports before an Article 4 thesis is chosen. It is not an article and does not recommend a challenge policy. Every number below comes from `output/`, which `analyze.py` regenerates byte-for-byte. Tables are named by file and section.

## Methodology

* **Data.** The validated Article 4 dataset (`research/article4/output`, version `pascal_article4_dataset_v1`), 2026-03-25 to 2026-09-09. It holds 20,164 eligible incorrect calls: 10,755 offense (incorrect called strikes; the Articles 1-3 population) and 9,409 defense (incorrect called balls). Of these, 2,112 and 2,986 were challenged. It also includes the team-game sequences with all 9,485 official challenges. The analysis checks that every input hash still matches the Article 4 manifest, and that no Articles 1-3 file or Article 4 output changes (see `VALIDATION_ANALYSIS.md`).
* **Primary value.** `correction_value_runs_pooled` is the decision-point counterfactual run-expectancy value of correcting the call, to the team entitled to challenge. It uses the pooled-count RE288 (base-out mean plus a count effect pooled across base states), which has no count-ordering violations and no negative values. Runs use Article 4's scoring-movement accounting, not Sprint 5's RBI-only sum; Sprint 5 artifacts are untouched. The Sprint 5 smoothing estimator (`correction_value_runs`) is rerun as a sensitivity (Analysis 9). The 40 AMBIGUOUS rows have no primary value and are excluded from value analyses, leaving n = 20,124. Including them at their bound midpoint is a sensitivity.
* **Realized later runs are never used as a cost.** All values are decision-time counterfactual run expectancy.
* **Models.** Interpretable binomial logistic regressions with standard errors clustered by game. Controls are defined at decision time:
  * inning bucket, side, score state (ahead/tied/behind), late-and-close (inning 7+, |score diff| ≤ 2);
  * a B-spline of boundary distance;
  * whether either call ends the plate appearance (`terminal`);
  * in one specification, count, outs and base-state fixed effects.

  Value enters per 0.25 runs (`v4`). Calibration of the main model (A) is checked by decile: every decile's observed rate is within 1.5 points of its prediction.
* **Hindsight.** Analysis 3 recomputes later-game quantities from the sequences under the primary value. Every hindsight table is labelled HINDSIGHT and none enters a model.
* **Descriptive vs associational vs causal.** Rates and distributions are descriptive. Model coefficients are adjusted associations. **No causal claim is made.** A challenge is an observed action. Its absence cannot distinguish failure to recognize the miss, deliberate conservation, team instruction, or inability to execute the challenge in time.

## 1. Distribution of challenge value (`article4_value_distribution.csv`, fig01, fig02)

| group | N | total runs | mean | median | P90 | P99 | max | ≥0.25 | ≥0.50 | ≥1.00 |
|---|---|---|---|---|---|---|---|---|---|---|
| all | 20,124 | 3,097.7 | 0.154 | 0.111 | 0.259 | 0.701 | 1.910 | 12.0% | 3.0% | 0.36% |
| offense | 10,750 | 1,608.3 | 0.150 | 0.111 | 0.257 | 0.687 | 1.910 | 10.7% | 2.5% | 0.29% |
| defense | 9,374 | 1,489.3 | 0.159 | 0.111 | 0.285 | 0.743 | 1.910 | 13.4% | 3.5% | 0.45% |
| challenged | 5,085 | 980.0 | 0.193 | 0.120 | 0.411 | 0.945 | 1.910 | 20.4% | 6.1% | 0.89% |
| unchallenged | 15,039 | 2,117.6 | 0.141 | 0.111 | 0.229 | 0.625 | 1.910 | 9.1% | 1.9% | 0.19% |

The table file also carries the SD and P10/P25/P75/P95 for every group.

* **Typical value.** A typical opportunity is worth about a tenth of a run: median 0.111, mean 0.154 (game-cluster bootstrap 95% CI 0.152–0.156). The value is set almost entirely by the count, because the correction changes a ball into a strike or vice versa.
* **Concentration is moderate, not extreme.**
  * The top 1% of opportunities hold 6.4% of total correctable value; top 5%, 20.0%; top 10%, 29.8% (CI 29.2–30.4%); top 20%, 44.0%. Gini = 0.35.
  * Opportunities under 0.25 runs are 88% of the count and 67% of the value.
  * Terminal counts (two strikes or three balls, where one call ends the plate appearance) are 19% of opportunities and 37% of value. 3-2 alone is 3.0% of opportunities and 11.4% of value.
* **Volume or selection?** Both, and the data do not support a binary answer. Most correctable value sits in large numbers of ~0.1-run early-count errors that no two-challenge budget could cover. A thin tail of terminal-count errors carries much larger value per decision. For unchallenged opportunities, 74% of the value left on the table is in opportunities worth less than 0.25 runs, which is the volume side. There are still 293 unchallenged opportunities worth ≥0.50 runs, totalling 207 runs, which is the selection side.
* **Encountered, recovered, left.** 3,097.7 runs of correctable value were encountered. 979.9 were recovered by successful challenges (31.6%), and 2,117.6 were left in unchallenged eligible opportunities. The remaining 0.1 run is the single eligible challenge that ABS confirmed although the geometry disagrees.

## 2. Challenge inventory and scarcity (`article4_inventory_analysis.csv`, fig04, fig05)

Only two inventory states occur among eligible opportunities: 2 left (14,315 with values) and 1 left (5,809 with values). Extra-inning grants appear as inventory 1.

* **Raw rates.** Offense: 19.7% with 2 left vs 19.3% with 1 left, essentially identical. Defense: 33.1% vs 28.4%.
* **Adjusted (model A: value, distance spline, side, inning bucket, score state, late-and-close, terminal).** One challenge left is associated with lower challenge odds: OR 0.66 (95% CI 0.59–0.75). Among comparable opportunities that is roughly 6.4 to 9.5 percentage points lower predicted challenge rate at values from 0.10 to 1.00 runs, a ratio of about 0.75–0.81. By side: defense OR 0.56 (0.47–0.66), offense OR 0.80 (0.67–0.95). With count, outs and base fixed effects (model B), OR 0.64 (0.57–0.72).
* **Why the raw offense gap is hidden.** Inventory-1 opportunities occur mostly late (47% in innings 7-9 vs 14% in innings 1-3), when challenge rates are higher for every inventory state. Adjusting for inning reveals the scarcity association.
* **Inventory × value.** There is no interaction on the odds scale: OR 0.99 (0.88–1.13) in model A, 1.00 in model B, 0.94 on offense, 1.05 on defense. On the probability scale the absolute gap grows slightly with value, because rates rise. **Higher immediate value does not reduce or eliminate the scarcity association.** There is no evidence of a threshold that shifts upward with scarcity by a value-dependent amount. The pattern is a roughly proportional downshift of the whole challenge curve (fig04).
* **Value itself.** Each additional 0.25 runs of value is associated with OR 1.42 (1.31–1.54), and terminal counts with OR 2.31 (2.11–2.53). When count, outs and base fixed effects are added, the separate value term goes to 1.0, because value is almost a deterministic function of that state.
* **Held-out recognition caveat.** The offense model that adds the held-out Article 3 expected-recognition probability shows no inventory association: OR 0.97 (0.81–1.16). That model is **not a valid test of inventory**. The Article 3 recognition model (Model C) uses challenges remaining, count, outs, base state, inning and score as predictors, so its output absorbs the inventory term by construction.
* **Alternative explanations for the scarcity association.**
  * Deliberate conservation.
  * Selection: teams and players at inventory 1 are those whose earlier challenge failed, and they may be more cautious or worse at recognition.
  * A behavioral response to a recent failure.
  * Unmeasured within-game dynamics.

  The data cannot separate these.

## 3. HINDSIGHT — are teams saving challenges for later? (`article4_hindsight_conservation.csv`, fig09)

**Retrospective only.** These fields use events after the decision, which the team could not know.

* **Passed opportunities overall** (15,039). 80% saw at least one later eligible opportunity (mean 2.5), and 56% saw a later one of higher value. The team used a challenge later in 72%. The first later challenge's realized value averaged 0.10 runs, counting failed challenges as 0. In 78% the game ended with inventory unused.
* **Meaningful early passes: how often did something more valuable come along?**

  | passed in innings 1-3 | n | later more valuable | ... and challenged | team used a challenge later | first later challenge value (mean) | game ended with unused inventory |
  |---|---|---|---|---|---|---|
  | value ≥ 0.25 | 585 | 24.3% | 14.4% | 88.4% | 0.108 | 74.0% |
  | value ≥ 0.50 | 126 | 8.7% | 5.6% | 88.1% | 0.109 | 73.0% |
  | value ≥ 0.75 | 31 | 0% | 0% | 83.9% | 0.105 | 74.2% |

  After passing an early opportunity worth ≥0.50 runs, a more valuable opportunity appeared later in fewer than 1 in 10 games. In nearly 9 of 10 games the team did challenge again later, recovering on average about one-seventh of the passed value. Part of this is mechanical: few opportunities exceed 0.5 runs at all, so any high-value opportunity is rarely exceeded. That is precisely the property a preservation decision must weigh.
* **Unused challenges.** 1,148 team-games passed at least one opportunity worth ≥0.25 runs; 76.9% of them ended with a challenge unused. At ≥0.50 it was 280 team-games, 79.3%; at ≥0.75, 71 team-games, 76.1%. **This matches the base rate:** 73.6% of all team-games end with inventory unused (45.5% with one left, 28.1% with two). Passing a meaningful opportunity is not associated with a notably different chance of finishing unused.
* **Challenged opportunities as a contrast.** For challenged early opportunities worth ≥0.50, 6.2% saw a more valuable later opportunity. Passed and challenged high-value opportunities have similar hindsight futures.
* **Interpretation limit.** None of this shows an earlier decision was irrational. At the time, the team faced an uncertain future. A model of the expected future value of preserving a challenge is the appropriate next step.

## 4. Team-level behavior (`article4_team_adjusted.csv`, fig08)

* **Raw.** Team challenge rates on eligible opportunities range from 19.3% to 33.5%, and value capture ratios from 0.26 to 0.43. Every team also spent many challenges on calls the geometry says were correct: 112 to 195 per team, and 46% of all 9,485 challenges league-wide.
* **Adjusted** (model A plus sum-coded team effects, game-clustered).
  * Adjusted odds ratios run from 0.64 (Cardinals) to 1.59 (Yankees).
  * Four teams differ from league average after Bonferroni correction: Cardinals low; Yankees, Twins and Rockies high.
  * The team block improves group-by-game cross-validated log loss by 0.0014, which passes the Article 3 identity threshold of −0.001.
  * Method-of-moments between-team SD is 0.19 log-odds, about ±20% in odds for one SD.
* **Meaningful adjusted team differences exist, but they are modest.** They are almost entirely a re-expression of raw rates: the correlation between raw rate and adjusted OR is 0.97. Team opportunity mixes are similar, so adjustment rarely reorders teams.
* **Value Capture Ratio** = value recovered by successful challenges ÷ correctable value encountered. It is reported with its expected counterpart under league-average behavior. It mixes recognition ability, conservation, execution, opportunity difficulty and team policy, and it ignores the cost of failed challenges. It is descriptive only and not a skill rating.
* **Early-game conservation screen** (observed minus expected rate in innings 1-3 minus the same in innings 7+).
  * χ² = 37.9 on 30 df, p = 0.15. No team is significant after Bonferroni.
  * The most extreme is Philadelphia, z = +3.0, meaning *relatively more* early challenging, the opposite of conservation.
  * **No team shows early-game behavior distinguishable from chance variation.**

## 5. Offense vs defense (`article4_offense_defense.csv`, fig06)

| | offense | defense |
|---|---|---|
| eligible opportunities (per team-game) | 10,750 (2.46) | 9,374 (2.14) |
| challenge rate | 19.6% | 31.7% |
| success rate on eligible (geometry-incorrect) calls | ~100% | 100% |
| success rate of all challenges | 48.7% (4,335) | 58.0% (5,150) |
| mean / median value | 0.150 / 0.111 | 0.159 / 0.111 |
| correctable value encountered | 1,608.3 | 1,489.3 |
| recovered | 419.3 | 560.6 |
| left unchallenged | 1,188.9 | 928.7 |
| value capture ratio | 0.26 | 0.38 |

* **Adjusted comparison.** Defense has about 2.1× the adjusted challenge odds of offense (offense OR 0.47, 0.43–0.50, in model A). Challenge rates rise with value on both sides. The offense curve is steeper (side × value OR 1.33, 1.18–1.50), so the gap narrows at high value; at ≥0.50 runs the rates are 50% vs 52%.
* **Inventory.** The scarcity association is stronger on defense (OR 0.56) than on offense (OR 0.80).
* **Inning.** Both sides challenge more as the game goes on. Offense rises from 16.4% (innings 1-3) to 24.0% (7-9); defense from 26.5% to 39.7%.
* **Season trend (unexpected).** The defensive rate rose from 26.5% in March to about 35–36% from July on. The offensive rate stayed near 18–21%.
* **Plausible non-strategic explanations.**
  * Catchers see every pitch from the best vantage point and receive with the zone in view. Hitters must also decide whether to swing.
  * Catchers are repeat decision-makers across the whole game.
  * Pitcher/catcher communication is possible within the battery.
  * Hitters face a self-assessment bias about their own at-bat.
  * Challenges of correct calls are similar in number on each side (defense 2,164, offense 2,223). The defense's higher overall success rate reflects its many more challenges of calls that really were wrong, not fewer wasted challenges.

  Teams may allocate the shared resource differently by side, but these data cannot show that the difference is a strategy.

## 6. Decision frontier (`article4_decision_frontier.csv`, fig07)

* **Evidence and consequence are nearly independent in the opportunity set.** The Spearman correlation between boundary distance and value is 0.02 on offense and −0.01 on defense. That makes distance a clean evidence axis.
* **Challenge probability reflects both, additively.**
  * With linear distance and log value on both sides: distance OR 1.79 per inch (1.55–2.07), log value OR 2.01 (1.84–2.21).
  * The distance × value interaction is null: OR 0.98 (0.92–1.05).
  * Offense with the held-out recognition logit: recognition OR 2.09 (1.76–2.49), log value OR 1.32 (1.15–1.52), interaction 1.00 (0.92–1.09).

  The held-out recognition measure shares situation inputs with value (Spearman 0.35), so the distance-based surface is the primary evidence here.
* **Surface shape.** For offense, the rate runs from about 8% (smallest miss, lowest value) to 47% (largest miss, highest value). For defense it runs from 14–19% to 66%. The value effect is concentrated in the top value quintile (terminal counts). Within the lower three value quintiles, the rate barely moves with value.
* **Inventory.** Inventory shifts the surface down, most visibly on defense, without an obvious change of shape. The interaction with value is null (Analysis 2).
* **Is a decision-theoretic model worth pursuing?** Behavior responds to evidence, consequence and remaining inventory in the directions such a model predicts, and the calibration is good. Yet a large share of high-evidence, high-value opportunities still go unchallenged: 53% in the top distance and value cell on offense, 34% on defense. Hindsight also shows preserved challenges are usually spent on much lower-value calls. A model of the expected future value of a preserved challenge has a clear empirical target. This is not evidence of suboptimal behavior, which requires that model.

## 7. Competing attention (secondary; `article4_competing_attention_analysis.csv`)

| indicator | side | flagged n | rate flagged | rate unflagged | exact-strata difference | adjusted OR (95% CI) |
|---|---|---|---|---|---|---|
| stolen-base attempt | defense | 165 | 8.5% | 32.2% | −26.6 pts (153 matched) | 0.14 (0.08–0.26) |
| catcher throw evidence | defense | 79 | 7.6% | 32.0% | −29.5 pts | 0.10 (0.04–0.24) |
| runner out on pitch | defense | 37 | 5.4% | 31.9% | −26.0 pts | 0.07 (0.01–0.39) |
| any secondary action | defense | 203 | 9.9% | 32.2% | −26.2 pts | 0.16 (0.10–0.27) |
| stolen-base attempt | offense | 51 | 13.7% | 19.6% | −4.0 pts | 0.72 (0.32–1.59) |
| secondary play reviewed | both | 16 | 12.5% | 25.3% | too few to model | — |

The exact strata match on side, count, outs, bases, 1-inch distance bin and inventory. The adjusted OR comes from a model with value, distance spline, inventory, inning and terminal.

* **Defense.** When a runner action is recorded on the pitch, the defense challenges about one-quarter as often as on otherwise comparable pitches. The association is unusually large, consistent across three analysis methods, and plausible mechanically: the catcher is throwing or fielding at the moment a challenge must be requested.
* **Offense.** No association is detected (wide CI).
* **Measurement limits.**
  * Successful steals leave no throw record.
  * Ball four erases forced-runner plays. 174 eligible rows are flagged, including the Braves case.
  * No source observes attention directly.
  * Flagged events are only 1% of opportunities.

  Misclassified unflagged events would more likely dilute than create the gap.
* **Alternative explanations.** A catcher coming out of the crouch to throw may see the pitch less well. Pitch selection on steal attempts (e.g., fastballs up) may differ in ways the distance control does not capture.
* **Status.** A striking, hypothesis-generating secondary finding. Too small and incompletely measured to carry the article alone.

## 8. Braves case study (`article4_braves_case_exploratory.json`)

Pitch `824887:3:7`, Mets at Braves, 2026-08-10, top of the 1st. Validated facts:
* one out, Bichette on first, 3-2 to Benge;
* the pitch was 2.74 inches inside the top of the ABS zone;
* called ball four;
* no official challenge recorded;
* Baty's grand slam came three batters later;
* the final was 8-5.

Value to Atlanta of correcting the call, from the decision point, under the primary pooled-count table:

| corrected state | primary (pooled) | Sprint 5 smoothing |
|---|---|---|
| recorded/no runner action: strikeout, runner on first, 2 outs | **0.69** | 0.71 |
| Bichette safe at second | **0.61** | 0.62 |
| Bichette out, inning over | **0.92** | 0.94 |

The values change by about 0.02 runs from the earlier ~0.71 / 0.62 / 0.94. The sources do not record the steal attempt, the catcher's throw, any call at second, or Elder's hat-tap request. These gaps are not filled by inference.

The Mets then scored four more runs in the inning, against a decision-point value of 0.61–0.92 runs. The difference is the point: **the realized outcome is not the decision-point value.** The missed correction did not "cost four runs"; it moved expected runs by roughly two-thirds to nine-tenths of a run.

## 9. Sensitivity and robustness (`article4_sensitivity.csv`)

Sixteen headline metrics were recomputed under seven alternatives:
* the Sprint 5 smoothing RE;
* ambiguous rows included at their bound midpoint;
* rows flagged `cf_unrecorded_runner_action_possible` excluded;
* offense only;
* defense only;
* values below 0.05 excluded (threshold fixed a priori);
* the 82 rows negative under Sprint 5 smoothing excluded.

Status counts:
* **No metric is MATERIALLY_CHANGED under any variant.**
* 93 are UNCHANGED (same sign, within 10%).
* 7 are UNCHANGED_NULL_IN_BOTH: the interaction ORs, whose CI includes 1 in both.
* 17 are DIRECTIONALLY_UNCHANGED_MAGNITUDE_DIFFERS. These are almost all the expected side splits, such as a stronger defense inventory effect and a weaker offense one. The rest are hindsight shares that move by 1–1.5 points, such as the Sprint 5 table giving 7.6% vs 8.7% for later-more-valuable after an early ≥0.50 pass.

The 82 negative-value rows under the old method are all low-value count changes (for example 1-0, 2-0 and 3-0 with runners in sparse base states). Excluding them changes nothing. The Sprint 5 smoothing table gives total value 3,002 vs 3,098 runs, a top-10% share of 31.4% vs 29.8%, a value OR of 1.48 vs 1.42, and an inventory OR of 0.66 in both.

## 10. Unexpected findings (hypothesis-generating)

1. **Almost half of all challenges were of correct calls.** 4,387 of 9,485 (46%) challenged calls the geometry says were correct, and 4,386 challenges were confirmed. Inventory is lost to failed challenges of correct calls far more than it is spent recovering value. Failed-challenge risk is therefore central to what a challenge is worth. Article 4 so far values only the upside.
2. **Scarcity is a downshift, not a threshold shift.** Value does not attenuate the inventory association.
3. **Unused inventory is the norm.** 73.6% of team-games end with an unused challenge, and passing a meaningful opportunity barely changes that.
4. **The defense challenge rate climbed through the season**, from 26.5% in March to ~36% by September; offense stayed flat. This could be learning, catcher adaptation, or team policy change. Unverified.
5. **Terminal-count concentration.** 3-2 is 3% of opportunities and 11% of value, yet high-value opportunities (≥0.50) are challenged only about half the time on both sides.
6. **Inning effects beyond inventory.** Challenge odds rise with inning at fixed inventory and value: 4-6 OR 1.36, 7-9 OR 1.85, extras OR 2.50. Late-and-close adds OR 1.23. This is consistent with context-dependent urgency, and cannot be told apart from leverage awareness that is not captured by run expectancy.

## Null findings

* No inventory × value interaction (Analysis 2).
* No evidence of team-specific early-game conservation (Analysis 4).
* No offensive competing-attention association (Analysis 7).
* No evidence/value interaction on the decision surface (Analysis 6).
* Passing meaningful opportunities is not associated with ending games with more unused inventory than the base rate (Analysis 3).

## Open questions

1. How much of the inventory-1 association is selection from an earlier failed challenge? A within-player or within-team design using the timing of the failure could help.
2. What is the expected future value of a preserved challenge by inning, inventory and side? This is a decision model with failure risk; it is out of scope here.
3. Does failure risk (the 46% of challenges on correct calls) explain low challenge rates on small-distance but high-value pitches?
4. Is the defensive season trend real learning? This needs replication on a later snapshot.
5. Can broadcast or tracking data recover the unobserved competing-attention events (like the Braves play)?

## Limitations

* The data are observational. Unmeasured private information (what the player saw, communication, fatigue) may drive every association.
* Correction values depend on a season-level RE table and deterministic counterfactual rules. Ambiguous rows are excluded.
* Inventory states are few (1 and 2) and endogenous.
* Hindsight analyses cannot evaluate decision quality.
* Team effects are modest, and team identity is confounded with the players on the roster.
* Competing-attention events are rare and undercounted.
* The Value Capture Ratio omits failed-challenge cost and mixes skill, strategy and opportunity.
