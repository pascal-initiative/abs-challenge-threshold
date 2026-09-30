# ABS Challenge-Decision Methodology

Full methods and validation appendix for “The Challenge Threshold: What Makes a Hitter Ask ABS?” The analytical snapshot is frozen through September 9, 2026.

**Reproduction status:** 72 checks passed. The pinned analysis was rerun from the frozen source files and produced byte-identical tables, reports, and PNG figures.

## Scope and frozen snapshot

The accepted dataset covers 2,195 completed MLB regular-season games from March 25 through September 9, 2026. It contains 645,793 physical pitches. Dates, source hashes, processing versions, and the publication-validation artifacts were frozen before the Article 2 analysis.

| Funnel stage | Count | Definition |
| --- | --- | --- |
| Physical pitches | 645,793 | All tracked physical pitches in the accepted snapshot |
| Called pitches | 336,095 | Non-swing called balls and strikes |
| Called strikes | 103,768 | Umpire’s original call was strike |
| Legal, classifiable opportunities | 96,486 | Hitter could challenge and an official or reconstructed ABS decision was available |
| Reconstructed incorrect-call population | 10,755 | Reconstructed ABS ball, legal hitter challenge |

## Population construction

The descriptive Article 2 universe starts with every pitch whose original umpire call was `STRIKE`. A row is eligible when the batting team had at least one challenge before the pitch, a position player was not pitching, the system was available, and the ABS classification can be established.

Challenge inventory is reconstructed sequentially from the official game feed. Both teams begin with two. An official confirmed challenge decrements inventory; an overturn retains it. At the start of each extra inning, a team at zero receives one. Inventory is recorded before the current pitch is processed.

| Disposition | Count |
| --- | --- |
| Included legal, classifiable opportunities | 96,486 |
| Excluded after challenge exhaustion | 6,913 |
| Excluded during position-player pitching | 317 |
| Excluded unclassifiable opportunities | 52 |
| Total called strikes | 103,768 |

One challenged pitch had an uncertain reconstructed survival classification. It remains in the 96,486 because the observed challenge proves that the opportunity was legal and its official ABS ruling supplies the classification. No unchallenged row with unresolved classification enters the population.

## Reconstructed ABS geometry

Pascal reconstructed the 2026 ABS decision environment from public pitch location and batter-specific strike-zone measurements. The zone is a two-dimensional rectangle positioned at the middle of the plate. A pitch is a strike when any part of the modeled baseball intersects the zone. The reconstruction uses a 1.45-inch ball radius and rounded corner geometry.

Signed boundary distance is retained in feet and converted to inches for publication. Negative values denote a pitch inside the reconstructed zone; positive values denote a pitch outside. Direction is assigned to above, below, batter-inside, batter-outside, or corner using actual batting side. Horizontal and vertical components are center-to-rectangle distances and are not substitutes for the radius-adjusted boundary distance.

**Terminology:** unchallenged pitches never receive an official ABS ruling. Their classifications are estimates from the public-data reconstruction, not official MLB decisions.

## Outcome definitions

The four-outcome descriptive table uses the official ABS ruling for challenged pitches and the reconstructed ruling for unchallenged pitches. This avoids overriding an observed official result while still allowing the unchallenged decision space to be studied.

| Hitter action | ABS classification | Label | Count |
| --- | --- | --- | --- |
| Challenge | Strike | Incorrect challenge | 2,223 |
| Challenge | Ball | Correct recognition | 2,112 |
| Accept | Strike | Correct restraint | 83,508 |
| Accept | Ball | Missed correction | 8,643 |

The primary predictive sprint uses only the 10,755 reconstructed incorrect called strikes that were legal to challenge. Its binary outcome is whether the hitter challenged: 2,112 challenged and 8,643 did not. Challenge success is not used to build that outcome.

## Predictor definitions and decision timing

All model inputs were available by the moment of decision. No official result, later count, later score, eventual winner, future inventory, player identity, or challenge outcome entered the predictors.

| Block | Inputs |
| --- | --- |
| Geometry | Cubic spline of absolute boundary distance; direction; plate side; batter hand; prespecified interactions |
| Count | All 12 pre-pitch ball-strike counts |
| Game context | Inning, half-inning, batting-team score differential, outs, base state, late-and-close and potential-ending indicators |
| Inventory | One versus two challenges remaining, plus prespecified inning and late-close interactions |
| Pitch characteristics | Velocity, horizontal and vertical movement, spin, extension, release position, pitch family, throwing hand |

Late-and-close means inning seven or later with the batting team’s pre-pitch score margin within two runs. Potential plate-appearance ending means two strikes. Potential inning ending adds two outs; potential game ending additionally requires the bottom of the ninth or later with the batting team behind. These are transparent state flags, not a leverage index.

## Model specification and temporal evaluation

The fixed progression uses L2-regularized logistic regression with C=1 and no class reweighting. Absolute distance uses a cubic spline with five training-quantile knots. Numeric imputation, scaling, knots, and categorical encodings are fit only on the training data. Sparse unseen categories map to zero. The random seed is 20260915.

| Model | Information added | Test log loss | Test AUC |
| --- | --- | --- | --- |
| A | Geometry | 0.47702 | 0.66392 |
| B | + Count | 0.43747 | 0.74073 |
| C | + Game context | 0.43263 | 0.75201 |
| D | + Challenge inventory | 0.43137 | 0.75314 |
| E | + Pitch-characteristic block | 0.43181 | 0.75325 |

March through June formed the training set (6,131 opportunities, 1,186 challenges). July was used once for specification selection (1,794, 359). The simplest model within 0.001 log loss of the best was selected; Model D qualified. Models were then refit through July 31 and evaluated on August 1 through September 9 (2,830, 567).

| Increment | Δ test log loss | Game-cluster 95% interval | Assessment |
| --- | --- | --- | --- |
| Count beyond geometry | −0.03955 | −0.05038 to −0.02836 | Strong improvement |
| Context beyond count | −0.00484 | −0.00932 to −0.00032 | Supported smaller improvement |
| Inventory beyond context | −0.00126 | −0.00360 to +0.00130 | Suggestive; interval crosses zero |
| Pitch block beyond selected baseline | +0.00043 | −0.00267 to +0.00366 | No improvement established |

## Uncertainty, sensitivity, and robustness

Paired bootstrap comparisons used 1,000 resamples clustered separately by game and batter. The intervals are conditional on fitted models; they do not include complete retraining uncertainty. Association-model coefficients use batter-cluster robust intervals. Neither approach removes unmeasured confounding.

Boundary sensitivity excluded pitches at or below 0.05, 0.10, 0.25, and 0.50 inches from the reconstructed boundary. The positive per-inch association remained at every threshold. Count improved on geometry in every rolling month. Context improved in five of six months; the exception was April, when training included only 391 March rows. Pitch characteristics worsened the selected baseline in all six rolling months.

Additional checks replaced the distance spline with a linear term and separately removed the ten highest-volume development-period batters and three highest-volume teams. The ordering of the main information blocks remained intact. These are influence checks, not independent replication.

## Published-number audit

Raw counts and rates were independently recalculated from the frozen pitch-level file. Model outputs were reproduced using the pinned Python 3.9 environment. The generated run passed 72 integrity, denominator, chronology, leakage, metric, coverage, candidate-support, and deterministic-output checks.

| Claim | Recalculation | Status |
| --- | --- | --- |
| Overall recognition | 2,112 / 10,755 = 19.637% | Verified |
| Correct-call challenge rate | 2,223 / 85,731 = 2.593% | Verified |
| Incorrect calls, fewer than two strikes | 1,532 / 9,553 = 16.037% | Verified |
| Incorrect calls, two strikes | 580 / 1,202 = 48.253% | Verified |
| Correct calls, fewer than two strikes | 1,346 / 79,198 = 1.700% | Verified |
| Correct calls, two strikes | 877 / 6,533 = 13.424% | Verified |
| Challenge precision, fewer than two strikes | 1,532 / 2,878 = 53.231% | Verified |
| Challenge precision, two strikes | 580 / 1,457 = 39.808% | Verified |
| Incorrect challenges >1 inch inside | 1,245 / 2,223 = 56.005% | Corrected in figure |
| Missed corrections >1 inch outside | 3,239 / 8,643 = 37.475% | Corrected in figure |
| Missed corrections >2 inches outside | 926 / 8,643 = 10.714% | Corrected in figure |

**Figure correction:** the supplied distance-mistakes graphic listed 1,247, 3,240, and 929 for three threshold counts. The source rows yield 1,245, 3,239, and 926. The published asset was corrected; the rounded 37.5% and 10.7% labels were unchanged, while 56.1% became 56.0%.

The half-inch directional panels are model-based publication estimates, not raw cell proportions. They should be read as descriptive comparisons at specified locations, holding modeled covariates constant. The reproducible research sprint independently supports the broader directional claim through held-out geometry ablation and the below-versus-above association; it does not establish a perceptual mechanism.

## Interpretive limits

This is observational research. The models do not observe hitter eyesight, private confidence, teammate signals, coaching, motivation, or who first recognized a questionable call. They do not determine whether a challenge was optimal, whether accepting a call was a mistake, or whether a successful challenge was a good use of the resource.

The test period is held out from this specified run, but the same frozen season appeared in earlier exploratory work. This is temporal validation, not a never-seen external replication. Repeated observations by players and teams, residual source measurement error, and omitted catcher, pitcher, and umpire effects can remain.

No validated pre-pitch leverage index was available in the processed data, so the article makes no leverage-effect claim. The inventory increment is explicitly treated as suggestive because its clustered interval crosses zero. The null pitch-block result means no added predictive value was established for the fixed block; it does not prove pitch physics never affects perception.

## Reproducibility record

The analysis is generated from the accepted processed inputs with pinned package versions. Source SHA-256 hashes are checked before and after execution. The verifier independently recalculates held-out log loss, Brier score, and AUC from row-level predictions; checks all denominators and chronological partitions; rejects outcome, identity, or future-state leakage; reconciles rolling predictions and batter aggregates; and compares generated analytical tables, reports, and PNGs byte for byte.

[Return to “The Challenge Threshold”](../) · [Read the Article 1 methodology](../01-one-in-five/methodology.md)
