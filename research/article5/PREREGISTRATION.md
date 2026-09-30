# ABS-05 Preregistration

## Status and amendment rule

This document is frozen before Article 5 implementation. Its SHA-256 must be
recorded in every run manifest. Any change requires a dated amendment stating
whether results had been inspected and which conclusions could be affected.

## Primary estimand

At decision state `s` with `n` challenge units, let `s_c` be the state if the
on-field call stands and `s_k` the state if corrected. Let `R` be expected run
differential for the challenging team and `W_pi(s,n)` the future value of its
inventory under declared policy `pi`.

```text
HOLD      = R(s_c) + W_pi(s_c, n)
CHALLENGE = p * [R(s_k) + W_pi(s_k, n)]
            + (1-p) * [R(s_c) + W_pi(s_c, n-1)]

V      = R(s_k) - R(s_c)
deltaW = W_pi(s_k, n) - W_pi(s_c, n)
C      = W_pi(s_c, n) - W_pi(s_c, n-1)

Delta EV = p * (V + deltaW) - (1-p) * C
p*       = C / (V + deltaW + C)
```

Pass cost is the forgone `p * (V + deltaW)` and is not added separately.
Report the simplified `C/(V+C)` only when `deltaW` is demonstrated negligible.

## Objective scales

- **Primary:** expected run differential for the challenging team.
- **Mandatory sensitivity:** win probability. Do not publish late/close guidance
  based on runs alone where the two objectives materially disagree.

## Population and denominator

The confirmatory decision population is every legal, challengeable called pitch
in the locked 2026-03-25 through 2026-09-09 snapshot, whether subsequently known
to be correct or incorrect. Position-player-pitching and legally unavailable
states are excluded with counts and reasons. Incorrect-only ABS-04 rows may
describe correction-value distributions but may not evaluate a policy.

## Decision-time feature allowlist

Allowed state features are pre-pitch count, outs, bases, inning, half, score,
home/away, both inventories, call as made, and strictly prior history. Role and
identity features require minimum support and rolling-origin construction.
Pitch-type knowledge is role-specific and must be justified.

Exact tracking location is not a player-observed feature. A perception model may
use a declared noisy-location simulation, but its noise parameter is an
assumption and must be varied. Model-free `p*` results do not require this model.

### Hard leakage blacklist

- signed boundary distance or `wrong_way_margin_inches`;
- correctness, ABS result, or challenge outcome;
- raw coordinates plus zone bounds that reconstruct the side of the boundary;
- challenge action as a predictor of success;
- same-game future or realized outcomes;
- same-game umpire accuracy computed after the decision;
- tables or models trained on the evaluation date or later dates;
- outcome-conditioned eligibility flags.

The pipeline must use an allowlist and reject a deliberately leaky canary model.

## Correction-value estimator

Primary: a count-aware estimator constrained so that an additional ball cannot
improve the fielding team's state and an additional strike cannot improve the
batting team's state, with partial pooling for sparse cells. Predeclare the
constraint and shrinkage implementation before fitting.

Sensitivities: ABS-04 pooled-count values, ABS-04 raw RE288 values, and
leave-one-period-out values. The 40 ambiguous runner-placement rows are evaluated
as exclusion, lower bound, and upper bound.

## Probability and perception

The threshold itself is primary and model-free. Mapping evidence to `p` is a
separate secondary layer.

- All-pitch geometry labels estimate a public-information probability only after
  agreement with official challenge results passes the label-fidelity gate.
- Offense may use the Article 3 temporal model only after a feature audit and a
  new rolling-origin calibration test.
- Defense has no accepted perception model. Defense receives model-free
  thresholds unless a separately validated model passes the same gates.
- Challenger-selected success rates describe selected behavior; they do not
  identify private perception or population success without assumptions.
- Oracle correctness is an upper bound and never an achievable policy.

## Future option value

Use distributional backward dynamic programming or an equivalent simulation
over the empirical distribution of future legal called pitches. State includes
inning, half, outs, bases where material, home/away, own inventory, game
truncation, and extra-inning grant eligibility. Report marginal values `C(1)`
and `C(2)` separately; do not assume concavity.

The policy used to define `C` must be the policy being evaluated. Solve the
dynamic threshold to a fixed point. Validate the dynamic program against a
separate full-game simulation. The opponent policy is league-typical in the
primary run and optimized in sensitivity.

## Policy comparisons

- never challenge;
- emulated observed league policy;
- fixed confidence cutoffs 0.50, 0.60, and 0.70;
- established decision value at least 0.05 runs;
- static inning-only thresholds;
- dynamic Challenge Threshold policy;
- oracle upper bound.

Report net runs per team-game with game-clustered intervals and the comparable
win-probability result.

## Staged sensitivities

First vary one factor at a time: RE estimator, ambiguous-case treatment,
perception assumption, probability model, opponent policy, objective scale,
extra-inning treatment, and early/late opportunity distribution. Then run only
jointly adverse combinations that can reverse a result. A full factorial grid
is prohibited unless a first-stage result demonstrates it is necessary.

## Stop/go rules

The required gates are defined in `VALIDATION_PLAN.md`. Failure of probability
identification does not invalidate model-free threshold tables; it does prohibit
evidence-to-action claims and an empirical playbook. Failure of threshold
stability prohibits situational recommendations. Null improvement over a simple
policy must be reported as such.
