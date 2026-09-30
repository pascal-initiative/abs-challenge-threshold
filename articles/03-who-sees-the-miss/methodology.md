# Hitter Recognition Methodology

Full methods and validation appendix for “Who Sees the Miss?” The analytical snapshot is frozen through September 9, 2026.

**Research status:** Accepted Sprint 4 artifacts. Article 3 uses the immutable results without refitting models or redefining recognition.

## Scope and outcome

The study uses the frozen Article 1 and Article 2 research population from March 25 through September 9, 2026: 10,755 incorrect called strikes where the hitter had a legal challenge opportunity. Hitters challenged 2,112 and did not challenge 8,643. There were 602 observed hitters.

**Recognition** equals one when the hitter challenged the eligible incorrect called strike and zero when he did not. Challenge outcome, success, overturn, and any post-decision information do not define recognition.

## Accepted opportunity model

The baseline is the accepted Sprint 3 situation model. It estimates how recognizable an opportunity was using the previously approved geometry and situational features, without hitter identity. The feature contract was not changed for the batter analysis.

## Point-in-time hitter history

The batter-information model adds only prior recognition behavior available before the opportunity being predicted. It does not use a full-season retrospective rate, future opportunities, future challenges, held-out outcomes, or end-of-season aggregates. A hitter required at least 20 prior opportunities before his historical effect could enter the primary future prediction.

## Temporal evaluation

Development data ended June 30. July was used for validation. Models were then fit through July 31 and evaluated once on the final August 1 through September 9 holdout of 2,830 opportunities.

| Metric | Opportunity model | Hitter-history model | Difference |
| --- | --- | --- | --- |
| Log loss | 0.43033 | 0.41757 | −0.01276 |
| Brier score | 0.13598 | 0.13142 | −0.00456 |
| ROC AUC | 0.75399 | 0.77286 | +0.01887 |

The improvement is modest but consistent across the three primary measures. The conclusion is predictive: prior hitter behavior contains information about future recognition beyond the measured characteristics of the opportunity.

## Adjusted recognition, shrinkage, and support

Expected recognized opportunities equal the sum of the baseline model probabilities for the opportunities each hitter faced. Individual adjusted estimates use a normal random-effect empirical-Bayes model. Partial pooling pulls small-sample estimates toward the population mean more strongly than well-supported estimates.

| Support class | Rule | Observed hitters |
| --- | --- | --- |
| All observed | At least one accepted opportunity | 602 |
| Publication eligible | At least 20 opportunities | 243 |
| Ranking eligible | At least 30 opportunities | 123 |

Leaderboard order is based on the accepted shrinkage-adjusted effect. Adjacent point estimates are not interpreted as meaningfully different when their uncertainty intervals overlap.

## Ordered-half stability

The season was divided into temporally ordered halves. Among 168 hitters with at least 10 opportunities in each half, the Spearman rank correlation between adjusted estimates was 0.474, with a 95 percent bootstrap interval from 0.333 to 0.592. Pearson correlation was 0.561, with an interval from 0.417 to 0.669. This is evidence of moderate within-season repeatability, not a permanent trait.

## Sensitivity and adversarial checks

The future predictive improvement survived every accepted boundary exclusion from 0.05 through 0.50 inches. Adjusted-rank correlations with the primary specification remained at least 0.941. Support-threshold, temporal-partition, accepted-control, negative-control, and influence checks did not eliminate the finding.

The signal was clearest among moderate misses, defined using the existing geometry groups as more than 0.5 inches and no more than 2 inches beyond the boundary. In that group, adding hitter history improved holdout log loss by 0.01189, Brier score by 0.00428, and ROC AUC by 0.01951. It added essentially no predictive value among obvious misses beyond 2 inches, but only seven hitters had sufficient subgroup support there. The subgroup result does not identify a mechanism.

## Interpretive limits

This is an observational, single-season study. Challenge action is not a direct measurement of perception or intent. A hitter may perceive an error and decline to act because of confidence, inventory, coaching, communication, or another unobserved consideration. Identity effects may also proxy omitted context.

The study does not establish that recognition is innate, caused by eyesight or plate discipline, or persistent across seasons. It supports individual differences in observed recognition behavior, modest future predictive value from hitter history, and moderate within-season repeatability.

**Publication wording:** Prefer “recognition behavior” or “batter-specific recognition tendency.” Use “skill” only with immediate qualification.

## Reproducibility record

The accepted Sprint 4 population, model specification, point-in-time history construction, support rules, figure data, claims matrix, and hashes were frozen before Article 3 publication validation. The article assets do not rerun or modify those research artifacts.

[Return to “Who Sees the Miss?”](../) · [Read the Article 2 methodology](../02-the-challenge-threshold/methodology.md)
