# ABS-05 Correction-Value Estimator Specification

## Freeze status

This implementation specification is frozen before the constrained estimator is
run against Article 5 results. It implements the estimator family declared in
`PREREGISTRATION.md`; it does not change the estimand, population, or gates.

## Inputs

- Accepted Article 4 RE288 table: 12 counts x 3 out states x 8 base states.
- Article 4 partial-pooling estimate `re_smoothed`, which shrinks each raw cell
  mean toward its base-out mean with a 40-pitch prior.
- Effective projection weight: `n_pitches + 40`, matching the data and prior
  mass used by the upstream partial-pooling estimate.
- Accepted Article 4 counterfactual states for every incorrect call. The
  Article 5 build must not rewrite those states or the protected Article 4
  outputs.

## Primary constraint

For each of the 24 outs/base-state strata, estimate the 12 count values by the
weighted least-squares projection nearest to `re_smoothed`, subject to:

- an additional ball cannot reduce batting-team run expectancy;
- an additional strike cannot increase batting-team run expectancy; and
- run expectancy is nonnegative.

The projection uses all adjacent count comparisons. It is a deterministic
convex quadratic program solved independently within each outs/base stratum.
Solver failure, a residual ordering violation greater than `1e-9`, a missing
state, or a nonfinite value fails Gate G5.

## Correction values

The value of a state is runs scored on the pitch plus constrained run expectancy
for the remaining count/outs/bases. An ended half-inning or walk-off has no
remaining run-expectancy term. Correction value is oriented to the team entitled
to challenge, using the Article 4 offense/defense convention.

The 40 eligible ambiguous runner-placement rows have no point estimate. Their
alternative states are revalued under the constrained table and retained as
lower and upper bounds. The five additional ambiguous but ineligible rows remain
in the all-incorrect-call audit but not the eligible result population.

## Prespecified sensitivities

Compare the primary constrained values with the accepted Article 4:

- partially pooled unconstrained RE288 values;
- pooled-count values; and
- leave-one-month-out values.

Report mean and maximum absolute differences, correlations on finite
non-ambiguous rows, sign disagreements, and distribution summaries. These are
diagnostics, not an optimization criterion.

## Replay and spot checks

The build must verify that every accepted Article 4 spot check still passes its
automated replay check, that every non-ambiguous reconstructed state has lookup
coverage, and that mechanically correctable non-ambiguous calls never have a
negative correction value beyond numerical tolerance.

## Gate decision

Gate G5 passes only when:

1. all 288 constrained states exist and satisfy the ordering constraints;
2. every non-ambiguous eligible row has finite observed and corrected values;
3. no non-ambiguous eligible correction value is below `-1e-9`;
4. all 40 eligible ambiguous rows retain finite ordered bounds; and
5. all accepted Article 4 automated spot checks remain passing.

Sensitivity disagreement is reported but has no arbitrary pass cutoff at G5.
It is evaluated later by the preregistered stability gate.
