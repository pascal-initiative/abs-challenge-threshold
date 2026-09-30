# ABS Research Sprint — Article 2: What Makes a Batter Challenge?

## Context

We are continuing the Pascal Institute research project examining MLB's 2026 Automated Ball-Strike (ABS) Challenge System.

Article 1 established the methodological foundation for the research.

We reconstructed ABS ball/strike decisions from publicly available pitch-level data and validated the reconstruction against official ABS challenge decisions. The reconstructed decision agreed with 9,482 of 9,485 official decisions.

Using that reconstruction, we identified 10,755 estimated incorrect called strikes where the batter had a legal challenge available.

Only 2,112 of those opportunities were challenged, producing an observed challenge rate of 19.64%.

Article 1 therefore established an important distinction:

An incorrect umpire call does not automatically produce a challenge.

Article 2 will investigate what determines whether a batter challenges an incorrect called strike.

This sprint is a RESEARCH sprint.

Do not write the final article.

The objective is to produce reproducible evidence, statistical analysis, diagnostics, tables, figures, and a research report that can later be used to determine the claims supported by Article 2.

---

# Primary Research Question

Given that:

1. the umpire called a strike,
2. the reconstructed ABS decision indicates that the pitch was a ball, and
3. the batter had a legal challenge available,

what factors are associated with whether the batter actually challenged the call?

The primary outcome variable is:

`challenged`

where:

* `1` = batter challenged the call
* `0` = batter did not challenge the call

The primary analysis population should be the 10,755 legal incorrect-called-strike opportunities identified by the existing research pipeline.

Do not silently redefine this population.

If the reproduced population differs from 10,755, stop and investigate the discrepancy before proceeding.

---

# Research Philosophy

This project is intended to measure decision behavior rather than simply describe outcomes.

Do not assume that a challenge was a good decision merely because it succeeded.

Do not assume that failure to challenge was necessarily a bad decision.

Do not use hindsight outcome information to construct predictors that would not have been available to the batter when the decision occurred.

Distinguish:

* descriptive evidence,
* predictive evidence,
* statistical association,
* causal claims.

Do not make causal claims unless the analysis genuinely supports them.

Use held-out validation where predictive models are evaluated.

Prefer interpretable models and transparent statistics over unnecessary model complexity.

---

# Research Question 1 — Miss Geometry

Determine how the magnitude and direction of the missed call relate to challenge probability.

At minimum investigate:

* absolute miss distance from the ABS boundary,
* horizontal miss distance,
* vertical miss distance,
* side of plate,
* above/below zone,
* inside/outside,
* batter handedness,
* interaction between batter handedness and horizontal location where appropriate.

Determine whether challenge probability increases monotonically with miss distance.

Do not assume linearity.

Evaluate useful transformations or bins and produce an interpretable challenge-probability curve.

Example conceptual output:

| Miss Distance | Opportunities | Challenges | Challenge Rate |
| ------------- | ------------: | ---------: | -------------: |
| 0–0.5 in      |           ... |        ... |            ... |
| 0.5–1.0 in    |           ... |        ... |            ... |
| 1–2 in        |           ... |        ... |            ... |
| 2–3 in        |           ... |        ... |            ... |
| 3+ in         |           ... |        ... |            ... |

Use statistically and analytically defensible bins rather than blindly adopting these example boundaries.

Determine whether equivalent miss distances produce different challenge behavior depending on where the pitch missed the zone.

---

# Research Question 2 — Count

Determine how ball-strike count affects challenge probability.

Analyze every relevant pre-pitch count.

Pay particular attention to called strike three.

Compare situations such as:

* 0-0,
* 0-1,
* 0-2,
* 1-0,
* 1-1,
* 1-2,
* 2-0,
* 2-1,
* 2-2,
* 3-0,
* 3-1,
* 3-2.

Report:

* opportunities,
* challenges,
* raw challenge rate,
* geometry-adjusted challenge effect where supported.

Determine whether count remains informative after controlling for miss geometry.

---

# Research Question 3 — Game Situation

Determine whether game context contributes information beyond pitch geometry.

Investigate, where reliable data exists:

* inning,
* top/bottom inning,
* score differential,
* runners on base,
* outs,
* leverage index or an appropriate pre-pitch leverage measure,
* late-and-close situations,
* potential inning-ending situations,
* potential plate-appearance-ending situations,
* potential game-ending situations.

Do not use post-pitch or post-challenge information to calculate pre-decision leverage.

Determine whether game context materially improves held-out prediction of challenge behavior beyond geometry alone.

---

# Research Question 4 — Challenge Inventory

If reliable challenge-availability information exists, investigate:

* challenges remaining,
* whether the team had one remaining challenge,
* whether challenge inventory changes challenge behavior,
* interactions between challenge inventory and leverage,
* interactions between challenge inventory and inning.

This analysis must respect the actual 2026 ABS challenge rules represented by the existing project.

Do not infer challenge availability using simplified assumptions if the existing pipeline already reconstructs it more accurately.

Document exactly how challenge inventory is determined.

---

# Research Question 5 — Batter Effects

Investigate whether individual batters exhibit challenge behavior that differs meaningfully from what would be expected given the opportunities they encountered.

Raw challenge rate is NOT sufficient for this analysis.

A batter who receives obvious misses should not automatically be considered better at recognizing missed calls than a batter receiving difficult borderline opportunities.

Construct an expected challenge probability for each opportunity using the validated non-batter predictors.

At minimum the baseline should consider:

* miss geometry,
* count,
* game context where validated,
* challenge inventory where validated.

Then aggregate expected probabilities by batter.

For each eligible batter calculate:

* opportunities,
* actual challenges,
* expected challenges,
* actual challenge rate,
* expected challenge rate,
* challenges above/below expected,
* appropriate uncertainty measure.

Conceptually:

`Challenges Above Expected = Actual Challenges - Sum(Expected Challenge Probability)`

Do not create rankings from extremely small samples.

Establish and document a defensible minimum-opportunity threshold.

Also consider shrinkage/hierarchical estimation if appropriate.

Produce candidate lists for:

* most above expected,
* most below expected,
* highest opportunity-adjusted challenge behavior,
* lowest opportunity-adjusted challenge behavior.

Do not label these players "best" or "worst challengers" unless the evidence supports that interpretation.

---

# Recognition vs. Accuracy

Maintain a conceptual distinction between:

## Recognition

Does the batter challenge an incorrect call when presented with an opportunity?

and

## Challenge Accuracy

When the batter chooses to challenge a call, how often is the batter correct?

Article 2 primarily concerns recognition behavior.

Do not collapse recognition and challenge accuracy into a single metric during this sprint.

However, determine whether the available data supports measuring both separately in a future sprint.

Document what would be required to eventually construct a broader player-level ABS decision-quality metric.

---

# Pitch Characteristics — Negative-Control / Incremental Analysis

Previous exploratory work suggested that pitch characteristics such as velocity, movement, spin, extension, and release characteristics may not provide meaningful held-out predictive improvement once pitch geometry is known.

Verify this finding rigorously.

Candidate variables may include:

* velocity,
* horizontal movement,
* vertical movement,
* spin rate,
* extension,
* release position,
* pitch type,
* other available pre-decision pitch characteristics.

Build an appropriate baseline model using geometry and validated situational variables.

Then evaluate whether adding pitch-characteristic variables materially improves held-out prediction.

Report the actual incremental performance.

A null result is a valid and potentially important research finding.

Do not search repeatedly through specifications until a statistically interesting result appears.

---

# Model Progression

Build models incrementally so we can determine what each information layer contributes.

At minimum compare:

## Model A — Geometry

Pitch miss geometry only.

## Model B — Geometry + Count

Add pre-pitch count.

## Model C — Geometry + Situation

Add validated game-context variables.

## Model D — Geometry + Challenge Inventory

Add challenge availability/inventory where reliable.

## Model E — Pitch Characteristics

Add pitch characteristics to the strongest preceding baseline.

## Batter Analysis

Evaluate batter-level residual/above-expected behavior separately rather than simply allowing batter identity to dominate the primary predictive model.

Report held-out performance for each stage.

Use appropriate metrics such as:

* log loss,
* Brier score,
* ROC AUC where useful,
* calibration,
* calibration plots,
* out-of-sample likelihood improvement.

Because challenge behavior is imbalanced, do not rely on classification accuracy as the primary metric.

---

# Temporal Validation

Prefer temporal train/test separation over random row-level splitting.

The objective is to determine whether relationships discovered earlier in the season generalize to later decisions.

Document:

* training period,
* validation period,
* test period if used,
* number of observations in each.

Avoid leakage across the temporal boundary.

If multiple observations from the same batter appear in training and testing, document this and explain its implications.

---

# Required Descriptive Analysis

Before modeling, produce a descriptive profile of the 10,755 opportunities.

Include at minimum:

* total opportunities,
* total challenges,
* challenge rate,
* distribution of miss distance,
* count distribution,
* inning distribution,
* leverage distribution where available,
* batter opportunity distribution,
* challenge inventory distribution where available.

Check for missing data and report exclusions explicitly.

Never silently drop observations.

---

# Required Figures

Produce publication-quality analytical figures for review.

At minimum attempt:

1. Challenge probability vs. miss distance.
2. Challenge rate by count.
3. Challenge behavior by leverage or game situation.
4. Zone/location visualization showing where missed called strikes are most and least likely to be challenged.
5. Actual vs. expected challenge behavior for qualifying batters.
6. Model calibration for the strongest validated model.
7. Incremental predictive performance by model stage.

Figures should be understandable without reading source code.

Use clear titles, axis labels, sample sizes, and captions.

Do not apply Pascal branding unless an existing project visualization standard already defines it.

---

# Required Tables

Produce machine-readable and human-readable tables for:

1. Overall opportunity statistics.
2. Challenge rate by miss-distance group.
3. Challenge rate by count.
4. Challenge rate by inning/game-state group.
5. Challenge rate by challenge inventory.
6. Model comparison.
7. Batter actual vs. expected challenge behavior.
8. Pitch-characteristic incremental-value analysis.

Include denominators.

Never report percentages without the corresponding sample size somewhere in the output.

---

# Robustness Checks

Perform appropriate robustness checks.

At minimum investigate:

* sensitivity to very small ABS reconstruction margins,
* alternative miss-distance specifications,
* minimum batter sample thresholds,
* temporal stability,
* potential dependence among repeated observations from the same batter,
* whether results are disproportionately driven by a small number of players or teams.

Because Article 1's ABS reconstruction is extremely accurate but not perfect, determine whether excluding extremely borderline reconstructed calls materially changes conclusions.

Do not modify the Article 1 reconstruction methodology merely to improve Article 2 results.

---

# Reproducibility

All analysis must be reproducible from repository code and source data.

Do not manually edit analytical outputs.

Record:

* source datasets,
* dataset versions/dates where available,
* filters,
* exclusions,
* feature definitions,
* model specifications,
* random seeds where applicable,
* package/environment requirements.

Generated artifacts should be reproducible by a documented command.

Do not modify or overwrite Article 1 frozen research artifacts.

Article 2 outputs should live in a clearly separated research/output location.

---

# Required Deliverables

At completion, provide:

## 1. Research Report

A Markdown report summarizing:

* methodology,
* dataset,
* descriptive findings,
* model results,
* robustness results,
* limitations,
* strongest supported conclusions,
* hypotheses that were not supported,
* unresolved questions.

This is NOT the final Pascal Institute article.

## 2. Figures

Publication-ready figures plus source data where practical.

## 3. Tables

CSV or equivalent machine-readable tables plus Markdown summaries.

## 4. Reproduction Instructions

Document the exact command(s) required to reproduce the analysis.

## 5. Research Findings Summary

Finish with a section explicitly divided into:

### Strong Evidence

Findings supported by robust descriptive and/or held-out evidence.

### Suggestive Evidence

Interesting relationships that require additional validation.

### No Evidence Found

Hypotheses tested without meaningful support.

### Cannot Determine From Available Data

Questions the available public data cannot reliably answer.

### Recommended Article 2 Claims

Claims that can responsibly appear in the published article.

### Claims We Should NOT Make

Interpretations that would overstate the evidence.

---

# Scope Restrictions

Do NOT make catcher, pitcher, or umpire effects a major component of this sprint.

They may be retained in the dataset and noted where necessary as possible confounders, but dedicated analysis of those entities belongs in later research.

Do NOT write Article 2.

Do NOT optimize for an exciting result.

Do NOT change Article 1 methodology merely because an alternative produces stronger Article 2 findings.

Do NOT use outcome information unavailable at the moment of the challenge decision as a predictor.

Do NOT equate correlation with causation.

Do NOT rank players using inadequate samples.

Do NOT hide negative findings.

---

# Definition of Done

This sprint is complete when we can answer, with reproducible evidence:

1. How strongly does miss distance affect the probability of a challenge?
2. Does the direction/location of the miss matter beyond distance?
3. Does count affect challenge behavior after accounting for geometry?
4. Does game situation or leverage provide additional information?
5. Does remaining challenge inventory influence behavior?
6. Do individual batters challenge more or less frequently than expected after adjusting for opportunity difficulty?
7. Do pitch characteristics add meaningful predictive information beyond geometry and situation?
8. Which findings generalize to held-out data?
9. Which intuitive hypotheses fail to receive support?
10. What can Article 2 responsibly claim?

When complete, stop and present the findings for human review before beginning article drafting or expanding the research scope.
