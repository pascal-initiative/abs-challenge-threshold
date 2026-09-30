# Challenge-Value Methodology

Data, definitions, model design and interpretive limits for “What Is a Challenge Worth?” The analytical snapshot covers 2,195 completed MLB regular-season games from March 25 through September 9, 2026.

**Analytical window:** March 25–September 9, 2026. The August 10 Mets–Braves game examined in the article falls inside this frozen season-to-date snapshot.

## Data and eligibility

An **incorrect call** is a called pitch that Pascal’s reconstruction of the ABS zone from public Statcast tracking classifies differently from the umpire’s call. An unchallenged pitch never receives an official ABS ruling, so its classification is an estimate from the reconstruction rather than an official decision.

The snapshot contains 21,831 reconstructed incorrect called pitches. Article 4 uses the 20,164 opportunities where the team still had a challenge available and a position player was not pitching. The remaining calls occurred after the team had exhausted its challenges or while a position player was pitching.

| Population | Count | Role in the analysis |
| --- | --- | --- |
| All reconstructed incorrect calls | 21,831 | Incorrect called pitches before challenge-eligibility restrictions |
| Eligible incorrect calls | 20,164 | Team had a challenge available and no position player was pitching |
| Eligible incorrect strikes | 10,755 | Offensive challenge opportunities |
| Eligible incorrect balls | 9,409 | Defensive challenge opportunities |
| Value-analysis population | 20,124 | Eligible calls with an unambiguous corrected game state |
| Adjusted inventory model | 19,899 | Eligible opportunities in regulation innings |
| Official challenges | 9,485 | Training population for challenge-success probability |

The population counts serve different analyses and are not sequential funnel stages. Forty eligible incorrect calls are excluded from the value statistics because runner action on the pitch makes the corrected game state ambiguous. Those calls are flagged rather than assigned a guessed counterfactual state.

## Correction value and run expectancy

The run-expectancy table uses 583,019 pitches from innings one through eight of the frozen snapshot. It estimates the runs a batting team is expected to score through the end of the inning from each combination of count, outs and occupied bases. Runs are counted from actual scoring plays, not from runs batted in.

For each eligible incorrect call, the analysis compares two game states: the state created by the umpire’s call and the state that would have existed if the call had been corrected. The difference in run expectancy is the correction value. No runs from later pitches are used to value the earlier decision.

Runner movement on the pitch can make the corrected state uncertain. When the data do not determine where the runners and outs would have ended after a corrected call, the opportunity is marked ambiguous and excluded from aggregate value statistics rather than resolved by assumption. This leaves 20,124 calls in the value-analysis population.

| Summary | Estimate |
| --- | --- |
| Average correction value | About 0.15 expected runs |
| Median correction value | About 0.11 expected runs |
| Total correctable value | Approximately 3,098 runs |
| Value recovered by successful challenges | Approximately 980 runs |
| Value attached to unchallenged incorrect calls | Approximately 2,118 runs |

The unchallenged total is not an estimate of runs teams could have recovered with perfect strategy. It is calculated after the fact from calls already classified as wrong, while players had to decide without knowing the ABS result.

## Probability of success and decision value

The probability that a challenge succeeds is estimated from all 9,485 official challenges. Predictors are the pitch’s distance from the reconstructed zone edge, without using which side of the edge it fell on; the nearest zone edge; and whether the count had two strikes or three balls.

Each opportunity receives an out-of-month estimate: its probability comes from a model trained without any games from that opportunity’s month. This prevents the same month from supplying both the training outcomes and the fitted probability applied to the call.

The success model predicts weakly, with an area under the receiver operating characteristic curve of 0.59. The low discrimination is an important limitation. Players may see pitch information, receive signals or use contextual knowledge that these public-data predictors do not capture.

**Decision value** is correction value weighted by the estimated probability that the challenge succeeds. It does not subtract the future value of the challenge or any other cost. About 46 percent of official challenges failed. Probability weighting lowers the median from about 0.11 runs of correction value to about 0.06 runs of decision value; the corresponding averages are about 0.15 and 0.08 runs.

## Challenge option value

The option value is the expected number of runs a team can still recover while holding one challenge, assuming league-typical challenge use. For every game, the estimate is built from other months’ games and never from the game receiving the estimate.

| Inning | Estimated one-challenge option value |
| --- | --- |
| 1 | About 0.08 runs |
| 3 | Approximately 0.06 runs |
| 5 | About 0.05 runs |
| 7 | Approximately 0.03 runs |
| 9 | Less than 0.01 runs |

The values depend on the assumed challenge policy. Under a simple alternative rule that uses a challenge whenever estimated decision value is at least 0.05 runs, the option-value estimates roughly double. The level is therefore strategy-dependent; the consistent pattern is that the value of preserving a challenge declines as the game approaches its final out.

## Challenge inventory model

The adjusted inventory analysis uses 19,899 eligible incorrect-call opportunities from regulation innings. The outcome is whether the team challenged. The logistic regression controls for decision value or net value, evidence that the call was missed, side of the call, inning, score state and a late-and-close indicator. Standard errors are clustered by game.

**Net value** is decision value minus the expected option value lost if the challenge fails: probability of failure multiplied by the option value of the challenge at risk.

| Specification | One challenge versus two | 95% confidence interval |
| --- | --- | --- |
| Net-adjusted model | Odds ratio 0.73 | 0.67–0.80 |
| Decision value and option cost entered separately | Odds ratio 0.80 | 0.68–0.93 |

In the net-adjusted specification, the odds of challenging were 27 percent lower with one challenge remaining; in the separate-cost specification, they were 20 percent lower. The analysis found no interaction between challenge inventory and current opportunity value. After adjustment for inning and the other model factors, the one-challenge gap remained across the value range rather than appearing only on lower-value calls.

Inventory is not randomly assigned. During regulation, a team with one challenge has already lost an earlier challenge. The model cannot fully separate resource scarcity from the behavioral effect of having been wrong. Teams also challenged more often after a successful challenge, so part of the observed gap between one and two challenges reflects more aggressive challenging after success, not only caution after failure.

## Challenges remaining and later opportunities

The analysis identified 126 unchallenged opportunities in the first three innings worth at least half a run if corrected. A more valuable opportunity appeared later in only 8.7 percent of those games. This is a hindsight comparison, not information the team could have known at the earlier decision.

Across all team-games, 74.9 percent ended with at least one challenge remaining. Across challenge units, including extra-inning grants, 51.2 percent remained at the final out. A challenge remaining at the end does not by itself establish an error: the team may never have encountered another call it was confident enough to contest.

## Atlanta case study

The Article 4 opening play is evaluated under three treatments of Bo Bichette’s action at second. If Bichette is safe, the corrected state is worth 0.61 expected runs to Atlanta. The 0.69 estimate is the value as recorded, with no runner action. If Bichette is out, the corrected state is worth 0.92 runs. The recorded-state estimate therefore lies inside the 0.61–0.92 range used in the article and Figure 1.

The estimated probability that an Atlanta challenge would succeed was about 53 percent. Weighting the 0.61–0.92 correction-value range by that probability produces an immediate decision value of approximately 0.32–0.49 runs. Atlanta had both challenges available, and the primary option-value estimate placed the future value risked by losing one at about 0.01 runs.

The later grand slam is excluded from every valuation because it had not happened when Atlanta had to decide. The values describe the information state at the decision, not the outcome that followed.

## Interpretive limits

The analysis depends on a public-data reconstruction of the ABS zone. Unchallenged pitches have no official ABS ruling, and reconstruction error can affect eligibility, correction value and fitted probabilities.

The success model’s AUC of 0.59 shows that its public-data predictors capture only a limited portion of challenge outcomes. Out-of-month estimation reduces within-month reuse, but it does not make the probability model a complete account of what hitters, catchers or teams knew.

The success model is trained only on pitches players chose to challenge, so it estimates how often challenges succeed in similar challenged situations. It is not an uninformed estimate of the probability that an unchallenged call was wrong, which averages about 30 percent across these opportunities.

The option-value estimates depend on assumptions about how future opportunities arrive and how challenges are used. The inventory models are observational and cannot fully separate the effect of resource scarcity from earlier success, earlier failure, team policy or unmeasured confidence.

The results do not establish that every successful challenge was a good decision, that every failed challenge was a poor decision or that every challenge remaining at the final out should have been used.

[Return to “What Is a Challenge Worth?”](../) · [Read the Article 3 methodology](../03-who-sees-the-miss/methodology.md)
