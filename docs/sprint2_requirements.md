# Pascal ABS Research

## Sprint 2 — Offensive Recognition Analysis

**Project:** Pascal Initiative / Pascal Institute
**Research Area:** MLB Automated Ball-Strike Challenge System
**Sprint:** 2
**Primary Question:** What makes an incorrect called strike more or less likely to be challenged by the batter?
**Input:** Validated Sprint 1 pilot dataset, August 24–30, 2026
**Status:** Requirements

---

# 1. Purpose

Sprint 1 established a validated pitch-level research dataset and achieved 100% agreement with all 447 official ABS challenge outcomes in the pilot period.

Sprint 1 identified:

* 509 incorrect called strikes;
* 96 corrected offensive calls;
* 388 incorrect called strikes that survived while a challenge remained available;
* 15 incorrect called strikes that survived because challenges were exhausted; and
* 10 offensive incorrect-call cases classified as unknown because of position-player-pitching restrictions.

Sprint 2 should investigate the largest remaining population:

> **Incorrect called strikes where the batter had a legal challenge available.**

The research question is:

> **What observable characteristics distinguish an incorrect called strike that a batter challenges from one the batter accepts?**

This sprint is exploratory and inferential. It is not yet intended to produce definitive player rankings or causal claims.

---

# 2. Sprint Objective

Build and evaluate an offensive recognition model using the validated Sprint 1 pilot dataset.

The primary analytical population is:

```text
original_call = STRIKE
derived_abs_call = BALL
challenge_available = TRUE
legal challenge opportunity = TRUE
```

Exclude:

```text
SURVIVED_RESOURCE
UNKNOWN
POSITION_PLAYER_PITCHING
```

The binary outcome should be:

```text
recognized = 1
```

when the incorrect called strike was challenged by the batter.

```text
recognized = 0
```

when the incorrect called strike was not challenged despite a legal challenge being available.

Do not define recognition based on whether the challenge succeeded. The underlying call is already known to be incorrect.

---

# 3. Research Questions

Sprint 2 should answer these questions in order.

## 3.1 Geometry

How strongly does recognition depend on how far the pitch missed the ABS zone?

Investigate:

* absolute distance from ABS boundary;
* horizontal versus vertical miss;
* zone edge;
* above;
* below;
* inside;
* outside;
* corner proximity.

Primary question:

> Are larger umpire errors more likely to be recognized?

---

## 3.2 Pitch Characteristics

After controlling for geometry, do pitch characteristics affect recognition?

Investigate:

```text
pitch_type
release_speed
pfx_x
pfx_z
release_spin_rate
spin_axis
extension
release_pos_x
release_pos_z
pitch_hand
bat_side
```

Primary question:

> Do two equally incorrect pitches have different recognition probabilities because of pitch shape or velocity?

---

## 3.3 Situation

After controlling for geometry and pitch characteristics, does game context affect recognition?

Investigate:

```text
balls
strikes
outs
base_state
inning
score_diff
affected_team_challenges_remaining
```

Where feasible, derive simple categorical representations such as:

```text
two_strike_count
called_strike_three
early_middle_late
bases_empty
runners_on
```

Do not yet build run expectancy, WPA, or leverage models unless those values already exist as validated source fields.

The primary question is:

> Do batters appear more willing to challenge when the immediate consequences of the call are greater?

---

## 3.4 Human Effects

After controlling for pitch and situation, investigate whether identity improves explanatory power.

Test:

```text
batter_id
pitcher_id
catcher_id
umpire_id
```

Do not rank individuals from this one-week sample.

The purpose is to determine whether there is evidence that individual effects may exist and therefore justify full-season study.

---

# 4. Analytical Population Audit

Before fitting any model, create a population audit.

Report:

```text
incorrect_called_strikes
challenge_available
recognized
not_recognized
excluded_resource
excluded_unknown
excluded_other
```

The expected pilot values should reconcile with Sprint 1.

Any difference from the Sprint 1 report must be explained before analysis proceeds.

Do not silently redefine the population.

---

# 5. Outcome Definition

Create:

```text
recognized
```

Allowed values:

```text
1 = batter challenged the incorrect called strike
0 = batter did not challenge the incorrect called strike
```

Also preserve:

```text
survival_class
challenge_outcome
```

but do not use challenge outcome to define recognition.

A batter who challenged an objectively incorrect call recognized the error regardless of any downstream source anomaly.

---

# 6. Feature Engineering

Create a dedicated analytical feature table.

Do not overwrite Sprint 1 processed data.

Suggested output:

```text
data/analysis/offensive_recognition_features.csv
```

Include raw fields and separately named derived fields.

## 6.1 Geometry Features

At minimum:

```text
distance_from_abs_boundary
abs_distance
miss_axis
miss_side
horizontal_distance
vertical_distance
```

Use explicit definitions.

Examples:

```text
miss_axis = HORIZONTAL | VERTICAL | CORNER
miss_side = ABOVE | BELOW | INSIDE | OUTSIDE
```

If corner classification requires assumptions, document them.

Preserve batter handedness when defining inside/outside.

---

## 6.2 Pitch Features

Include:

```text
pitch_type
release_speed
release_spin_rate
spin_axis
pfx_x
pfx_z
extension
release_pos_x
release_pos_z
pitch_hand
bat_side
```

Do not normalize or transform source fields in place.

Any standardized versions should have separate names.

---

## 6.3 Situation Features

Include:

```text
inning
balls
strikes
outs
on_1b
on_2b
on_3b
score_diff
affected_team_challenges_remaining
```

Derived:

```text
base_state
two_strike_count
strike_three_call
inning_group
score_state
```

Suggested inning grouping:

```text
EARLY = 1–3
MIDDLE = 4–6
LATE = 7+
```

Also preserve raw inning.

---

# 7. Descriptive Analysis

Before modeling, produce descriptive recognition rates.

At minimum by:

```text
distance_from_abs_boundary bins
miss_side
pitch_type
velocity bins
movement bins
count
inning
inning_group
outs
base_state
challenges_remaining
```

For every group report:

```text
opportunities
recognized
not_recognized
recognition_rate
```

Do not display rates for very small groups without sample-size warnings.

Do not create player leaderboards.

---

# 8. Distance Baseline

The first model should use only pitch geometry.

Suggested conceptual model:

```text
recognized ~ distance_from_abs_boundary
```

Then expand to:

```text
recognized ~ distance_from_abs_boundary
           + miss_side
           + horizontal_distance
           + vertical_distance
```

The purpose is to establish:

> How much recognition can be explained simply by how obviously wrong the call was?

Report:

* coefficient direction;
* uncertainty;
* model fit;
* discrimination;
* calibration where practical.

Do not treat p-values alone as evidence of importance.

---

# 9. Incremental Models

Build models incrementally.

## Model A — Geometry

```text
geometry
```

## Model B — Geometry + Pitch

```text
geometry
+ pitch_type
+ velocity
+ movement
+ release characteristics
```

## Model C — Geometry + Pitch + Situation

```text
geometry
+ pitch characteristics
+ count
+ outs
+ runners
+ inning
+ score
+ challenges remaining
```

## Model D — Exploratory Identity Effects

Add identity terms only after Models A–C.

Possible approaches:

```text
regularized categorical effects
fixed effects where support is adequate
mixed effects if technically justified
```

Do not force a hierarchical model merely because one was mentioned in future research.

The sample is small.

Prefer the simplest defensible method.

---

# 10. Model Evaluation

For each model report:

```text
sample size
number of recognized cases
number of non-recognized cases
AIC/BIC where applicable
log loss
ROC AUC
PR AUC
Brier score
calibration summary
```

Where possible, use cross-validation rather than reporting only in-sample fit.

Because the pilot sample is limited, use a validation strategy appropriate to approximately 484 opportunities.

Document the choice.

Do not optimize aggressively on this pilot.

The goal is understanding, not leaderboard performance.

---

# 11. Incremental Explanatory Value

The most important Sprint 2 output is not the final AUC.

For each model transition report the incremental contribution:

```text
Geometry -> +Pitch
+Pitch -> +Situation
+Situation -> +Identity
```

Answer:

> Does pitch information explain recognition beyond geometry?

> Does game situation explain recognition beyond the pitch?

> Is there preliminary evidence of batter, pitcher, catcher, or umpire effects after controlling for observable context?

Use effect sizes and predictive improvement, not only statistical significance.

---

# 12. Pitch-Type Analysis

Specifically examine whether pitch type appears related to recognition after controlling for distance from the ABS boundary.

At minimum compare major pitch families where sample size permits:

```text
four-seam fastball
sinker
cutter
slider
sweeper
curveball
changeup
splitter
other
```

Do not make claims for groups with inadequate observations.

For each supported pitch group, report:

```text
opportunities
mean boundary distance
recognition rate
model-adjusted recognition estimate where appropriate
```

This analysis is intended to test the hypothesis that movement or pitch shape affects perception.

---

# 13. Movement Analysis

Investigate whether movement contributes to recognition.

Analyze:

```text
pfx_x
pfx_z
```

Prefer continuous treatment over arbitrary buckets in the main model.

Buckets may be used for descriptive visualization.

Consider interactions only if justified by sample size, such as:

```text
distance × pfx_x
distance × pfx_z
pitch_type × distance
```

Do not create a large interaction search.

Any interaction tested must be motivated and documented.

---

# 14. Catcher Signal

Sprint 2 should investigate whether there is preliminary evidence for a catcher effect, but should **not** attempt to rank catchers.

Compare:

### Baseline model

```text
geometry + pitch + situation + batter/pitcher controls where appropriate
```

against:

### Catcher-added model

```text
baseline + catcher identity
```

Determine whether catcher identity produces meaningful incremental explanatory or predictive value.

Report:

* number of catchers;
* opportunity counts per catcher;
* distribution of sample sizes;
* model improvement;
* uncertainty.

The conclusion should be one of:

```text
no detectable pilot signal
weak pilot signal
meaningful pilot signal requiring full-season validation
insufficient sample
```

Do not call the result causal.

---

# 15. Pitcher Signal

Perform the same staged analysis for pitcher identity.

The question is:

> After controlling for pitch characteristics, does pitcher identity still help explain whether an incorrect call survives?

Possible explanations for any residual effect belong in discussion only.

Do not attribute residual pitcher effects to deception, tunneling, sequencing, or command without additional evidence.

---

# 16. Batter Signal

Evaluate whether batter identity contributes explanatory value after controlling for opportunity difficulty.

This is the beginning of a future recognition-skill metric.

Do not produce a “best batter challenger” leaderboard from the pilot.

Report only whether individual recognition tendencies appear large enough to justify full-season modeling.

---

# 17. Umpire Signal

Evaluate whether umpire identity predicts whether an incorrect call is recognized after controlling for the pitch and situation.

This is different from umpire accuracy.

The question is:

> Are some umpires' errors more or less likely to be recognized?

Do not interpret any pilot umpire coefficient as umpire quality.

---

# 18. Early Versus Late

Perform descriptive and controlled analysis of inning effects.

Compare:

```text
EARLY
MIDDLE
LATE
```

Then test raw inning as appropriate.

The goal is to determine whether recognition behavior appears to change with game progression after controlling for:

* pitch geometry;
* pitch characteristics;
* count;
* outs;
* runners;
* score;
* challenges remaining.

Do not yet conclude that late-game behavior is optimal or suboptimal.

That belongs to future leverage/resource research.

---

# 19. Challenges Remaining

Test whether recognition behavior differs when the batting team has:

```text
2 challenges
1 challenge
```

Exclude zero-challenge opportunities from the recognition population.

The purpose is to determine whether scarcity affects willingness to challenge before exhaustion.

Do not yet build a dynamic optimization model.

---

# 20. Visualizations

Produce research-quality exploratory visualizations.

At minimum:

1. recognition probability versus distance from ABS boundary;
2. recognition rate by miss location;
3. recognition rate by pitch type;
4. recognition versus horizontal/vertical movement;
5. recognition rate by count;
6. recognition rate by inning;
7. recognition rate by challenges remaining.

Where possible, show:

* sample sizes;
* uncertainty intervals;
* raw observations or bin counts.

Do not use misleading truncated axes.

Do not overplot tiny identity groups.

---

# 21. Statistical Restraint

This is a pilot analysis.

Explicitly avoid:

* causal claims;
* definitive player conclusions;
* definitive catcher conclusions;
* definitive pitcher conclusions;
* p-value fishing;
* automated feature selection across dozens of interactions;
* selecting only statistically significant findings;
* tuning the model until an expected baseball story appears.

Record null results.

Record contradictory results.

---

# 22. Multiple Comparisons

Because several related hypotheses are being explored, distinguish:

### Primary hypotheses

1. boundary distance affects recognition;
2. pitch characteristics add information beyond boundary distance;
3. game situation adds information beyond pitch characteristics.

### Secondary exploratory hypotheses

* catcher effect;
* pitcher effect;
* batter effect;
* umpire effect;
* specific pitch types;
* early/late effects.

Treat the identity analyses as exploratory.

Do not present every coefficient as an independent discovery.

---

# 23. Required Outputs

Create:

```text
data/analysis/offensive_recognition_features.csv
data/analysis/offensive_recognition_population_audit.json
data/analysis/offensive_recognition_descriptive.csv
data/analysis/offensive_recognition_model_metrics.csv
data/analysis/offensive_recognition_predictions.csv
```

Create a human-readable report:

```text
docs/sprint2_offensive_recognition_report.md
```

Suggested notebook:

```text
notebooks/03_offensive_recognition.ipynb
```

Any model artifacts should live under:

```text
artifacts/sprint2/
```

Do not alter Sprint 1 accepted outputs.

---

# 24. Sprint 2 Report

The final report should answer, in order:

## 1. Population

How many eligible incorrect called strikes were analyzed?

## 2. Baseline recognition

What percentage were challenged?

## 3. Geometry

How strongly was recognition associated with boundary distance and miss location?

## 4. Pitch characteristics

Did pitch type, velocity, or movement add explanatory value?

## 5. Situation

Did count, inning, outs, runners, score, or challenge inventory add explanatory value?

## 6. Human effects

Was there preliminary evidence of batter, pitcher, catcher, or umpire effects?

## 7. Early versus late

Did recognition behavior change as games progressed after controlling for other factors?

## 8. Limitations

Which conclusions cannot be supported by a one-week pilot?

## 9. Recommendation

Should the research expand to the full 2026 season?

If yes, identify which hypotheses deserve full-season testing.

---

# 25. Acceptance Criteria

Sprint 2 is accepted when:

* the analytical population reconciles exactly to Sprint 1;
* no resource-constrained or legally unavailable pitches enter the recognition population;
* the outcome variable is defined independently of challenge result;
* geometry baseline analysis is complete;
* pitch-characteristic analysis is complete;
* game-situation analysis is complete;
* incremental model comparisons are reported;
* catcher, pitcher, batter, and umpire identity effects are evaluated cautiously;
* early-versus-late behavior is described and controlled for;
* no pilot player rankings are produced;
* null results are preserved;
* model assumptions and limitations are documented;
* all outputs are reproducible;
* Sprint 1 artifacts remain unchanged.

---

# 26. Stop Conditions

Stop and report before interpreting results if:

* Sprint 2 population does not reconcile with Sprint 1;
* outcome labels are ambiguous;
* derived geometry fields cannot be reproduced;
* model results depend materially on unexplained missing values;
* separation or severe overfitting makes a model unreliable;
* identity effects cannot be estimated because observations per group are too sparse;
* data leakage is detected;
* a modeling choice materially changes the headline conclusion without a defensible reason.

Do not force a model through a stop condition.

---

# 27. Guiding Principle

Sprint 2 is not trying to answer:

> Who is the best ABS challenger?

It is trying to answer:

> **What makes an incorrect strike recognizable to the batter?**

The preferred progression is:

```text
geometry
→ pitch characteristics
→ situation
→ human effects
```

Only after the mechanisms are understood should Pascal attempt individual recognition rankings.

The most important result may be that a suspected effect does **not** exist.

Preserve that possibility.
