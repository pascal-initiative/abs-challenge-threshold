# Sprint 5: Challenge Resource Management and Decision Quality

## Decision universe

The locked 2026-03-25 through 2026-09-09 snapshot contains 312,228 legal ABS decision opportunities: 96,538 offensive called strikes and 215,690 defensive called balls. It includes correct and incorrect calls. Players challenged 9,485 times (3.04%); the model recommends a challenge on 10,908 opportunities (3.49%).

## What a challenge is worth

The mean immediate ex-ante value is 0.0386% win probability, while the mean marginal value of preserving the current challenge is 1.4304%. The decision rule retains a successful challenge and removes one after failure. Required confidence is the failure-cost break-even value, not the observed outcome.

Count changes value because a reversed strike three prevents an out and a reversed ball four prevents a walk; bases-loaded ball-four transitions also include the forced run. The largest state changes appear in `count_analysis.csv`. Leverage remains distinct from run expectancy and win probability.

## Ex-ante decision quality

Actual actions agree with a value-maximizing action, including near-indifferent choices, on 96.26% of opportunities. Among actual challenges, 5,594 are supported ex ante. There are 7,773 modeled valuable holds and 3,891 modeled poor challenges. A successful challenge can still be a poor decision, and a failed challenge can still be defensible.

The actual challenge rate with one remaining is 2.86%, versus 3.11% with two. Early decision correctness is 96.35%; ninth-inning correctness is 96.36%. These comparisons are conditional descriptions, not causal claims about intent or coaching.

## Hindsight realized consequences

There are 1,238 final-challenge exhaustion events and 6,590 subsequent challenge-type calls before any reset. 366 later calls were incorrect, across 252 exhaustion sequences, with 6.428 cumulative win-probability units (642.8 percentage points) and 89.768 run value unavailable for correction. These values are **HINDSIGHT_DESCRIPTIVE** and never change the earlier stored ex-ante category.

The counterfactual preservation simulation applies the same policy to later opportunities. It recommends later use in 160 exhaustion sequences and no use in 1,078.

## Validation and benchmarks

The validation gate is **PROCEED**. Component results are in `policy_component_validation.csv`; chronological folds always train before their test month. The primary model is compared with immediate-value-only, a fixed lost-cost rule, a fixed 60% confidence rule, and a declining-threshold proxy. MLB's public model uses location, inventory, runners, and count/out state, while public independent work also uses backward induction; Pascal's comparison keeps those ideas as benchmarks rather than model inputs.

Sensitivity agreement across all opportunities ranges from 99.18% to 100.00%; overlap within the actionable challenge set ranges from 76.42% to 100.00%. The ±15% overturn-probability variant reverses the net actual-versus-recommended challenge-rate comparison, so the over-challenge versus under-challenge headline is **INCONCLUSIVE**.

## Decision gates

- **A. Decision Framework — PROCEED.** All component gates pass and minimum actionable-set sensitivity overlap is 76.42%.
- **B. Resource Management — YES.** Mean marginal future resource value is 1.4304% WP.
- **C. Timing — NOT_SUPPORTED.** Early versus ninth-inning decision correctness differs by +0.02%.
- **D. Inventory — INCONCLUSIVE.** Challenge rates are 3.11% with two and 2.86% with one, but modeled efficiency with one remaining is -83.71%; rate alone cannot establish appropriate selectivity.
- **E. Exhaustion — YES.** 252 of 1,238 exhaustion sequences contain a later incorrect call.
- **F. Best Challenger — DEFER.** Sprint 5 establishes a decision component but does not pass the separate support, uncertainty, temporal ranking, and stability gates for a combined leaderboard.

## Limitations

Challenge behavior is observational, and actual challenges are selected using private information unavailable here. Inverse-propensity weighting addresses selection on recorded variables only. Hawk-Eye/Statcast geometry, run-expectancy lookup, win-probability estimates, and the representative-opportunity Bellman recursion all carry model error. The recursion summarizes future opportunities rather than replaying known future pitches. Batter, catcher, pitcher, and dugout communication are omitted from the normative probability. Repeated players and teams create dependence. The snapshot is season-to-date, counterfactuals are uncertain, extra-inning inventory resets are respected in observed inventory but simplified in future-value approximation, and modeled optimality is conditional on these assumptions.

## Conclusions

**SUPPORTED:** the framework separates outcome from decision quality, models count-aware state changes, and finds measurable option value in preserving inventory.

- **Are players generally using challenges efficiently? NO under the validated conditional model.** Primary decision efficiency is -0.73%; it ranges from -24.22% to 22.19% across specified sensitivities, always far below the modeled optimum.
- **Are players more prone to over-challenge or under-challenge? INCONCLUSIVE.** The net volume comparison reverses under the lower overturn-probability calibration.
- **Does behavior become more efficient late? NOT_SUPPORTED.** Early and ninth-inning decision correctness differ by only +0.02%, and timing efficiency is not monotone.
- **Are players appropriately conservative with the final challenge? INCONCLUSIVE.** Volume falls with one remaining, while selection efficiency is negative under the primary model.
- **Is exhaustion costly in practice? YES descriptively.** 252 exhaustion sequences contain a later incorrect call, totaling 6.428 WP units and 89.768 runs.
- **Does preservation have measurable future value? YES.** Mean marginal preservation value is 1.4304% WP, and the policy would later use a preserved challenge in 160 sequences.

**SENSITIVE:** the number of marginal challenge recommendations changes with probability and future-value assumptions; see the sensitivity artifact.

**INCONCLUSIVE:** whether players generally over-challenge or under-challenge, causal claims about why players differ, and whether the one-challenge adjustment is appropriate. Actual-versus-recommended volume reverses under a plausible probability-calibration sensitivity.

**NULL:** no player or team decision-quality leaderboard is published (`ranking_status = NOT_SUPPORTED`).
