# ABS-05 Gate G9 Effect-Size Specification

## Freeze status and inherited restrictions

This specification is frozen before G9 results are inspected. G6 did not
identify player confidence, G7 holds the subsequent game path fixed, and G8
failed stability. G9 cannot reverse those results or authorize situational
guidance.

The G7 exact-sequence dynamic policy observes the complete remaining empirical
opportunity sequence. It is therefore an **upper benchmark**, not a deployable
decision-time policy. G9 reports its numerical effect separately from whether a
practical policy improvement has been demonstrated.

## Primary numerical comparison

Use the G5 constrained correction value, fixed `p=0.60`, documented extra-inning
restoration, and two starting challenge units. Evaluate all 4,390 team-games.

Compare exact-sequence dynamic value with the best simple non-oracle policy
among:

- never challenge;
- fixed confidence cutoffs 0.50, 0.60, and 0.70;
- challenge when `p * V >= 0.05` runs; and
- the pre-existing Article 4 static inning/half/team-role preservation-cost
  policy, using `OV1_league_behavior` with one unit and
  `M2_league_behavior` with two.

The static policy challenges when `p * V > (1-p) * C_static`; ties hold. For
innings after the tenth, use the inning-10 value for the same half and team
role. The Article 4 table predates Article 5 and is not refit to G9 outcomes.

The point estimate is mean team-game value of the dynamic benchmark minus the
largest mean among simple policies. Resample the 2,195 games, keeping both team
rows together, for 10,000 deterministic cluster-bootstrap replicates. Within
each replicate, subtract the largest simple-policy mean so competitor selection
is included in uncertainty.

The preregistered numerical condition passes only if the two-unit point estimate
is at least 0.01 expected runs per team-game and the percentile 95% interval is
strictly above zero. Report the one-unit comparison as secondary.

## Sensitivities

Repeat the comparison for fixed `p=0.50`, fixed `p=0.70`, the G6
public-tracking benchmark, and the challenger-selected transport assumption.
These are named assumptions or benchmarks, not player-confidence estimates.

Report the observed league's realized corrected-call value and the hindsight
oracle upper bound descriptively, but exclude both from the primary simple
comparator set. Observed actions use selected private information and realized
outcomes; the oracle knows correctness and never fails. Neither is comparable
to a fixed-probability policy estimand.

The rejected G8 win-probability model is not reused. The mandatory win-scale
policy comparison remains unavailable, and late/close practical claims remain
prohibited.

## Falsification

Shuffle the G6 public correctness labels with seed `20260925`, refit the frozen
public feature formula, and require AUC between 0.48 and 0.52 on the shuffled
labels. Apply its probabilities to the G9 sequence and report the dynamic-minus-
best-simple result.

If the upper-benchmark advantage remains at least 0.01 with a positive interval
after label shuffling, interpret that as evidence that the gain is driven by
exact future-sequence/value allocation rather than validated probability
information. In that case the numerical condition may pass, but a deployable
policy effect is not demonstrated.

## Gate statuses

Report both:

1. **Numerical benchmark condition:** pass/fail under the fixed 0.60
   exact-sequence benchmark.
2. **Scientific G9 status:** practical improvement demonstrated only if the
   policy is decision-time deployable, the probability mapping is identified,
   the win-probability sensitivity is valid, the full required comparator set is
   available, and the falsification result does not show the same gain without
   label information.

Given inherited G6/G8 restrictions, a numerical pass is expected to remain an
assumption-conditional upper-bound result. It must not be called evidence that
players or teams should follow the policy.

## Required outputs

- team-game value by probability scenario and policy;
- policy summary with one- and two-unit means;
- primary and sensitivity effect estimates with cluster-bootstrap intervals;
- observed-policy and oracle descriptive benchmarks;
- shuffled-label diagnostics and effect estimate;
- validation JSON, human-readable report, and deterministic manifest; and
- two byte-identical clean builds.

## Resource ceiling

Resource class is R0. Use the locked local snapshot and local computation only.
No live data, paid source, hosted database, GitHub Actions, Vercel, Supabase,
Odds API, or additional Claude exchange is authorized.
