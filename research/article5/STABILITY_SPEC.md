# ABS-05 Gate G8 Stability Specification

## Freeze status

This specification is frozen before G8 results are inspected. G6 did not
identify subjective player confidence and G7 held subsequent game paths fixed.
Accordingly, every action below is an **assumption-conditional audit action**,
not a recommendation to a player and not an estimate of an optimal MLB policy.

## Reference audit

The reference is the G7 empirical-sequence dynamic policy with:

- the G5 constrained, partially pooled RE288 correction value;
- fixed success probability `p=0.60` at every opportunity;
- the observed complete team-game opportunity sequence;
- one or two challenge units evaluated separately;
- the documented zero-to-one extra-inning grant; and
- `deltaW=0` because the observed post-decision sequence is held fixed.

Fixed 0.60 is a neutral sensitivity anchor within the prespecified 0.50, 0.60,
and 0.70 scenarios. It is not labeled player confidence. Changing the anchor
must not be used to rescue a failed stability result.

## Primary flip population and rule

Rank the 312,228 observed legal decisions by reference constrained correction
value, using a deterministic `>=` cutoff at the empirical 90th percentile. If
ties cause the population to exceed exactly 10%, report the actual denominator.
This top-value population is fixed once and reused for every sensitivity.

For each sensitivity and inventory level, compare its dynamic CHALLENGE/HOLD
action with the reference action on the same pitch keys. The flip rate is:

`number of different actions / fixed top-value population`.

The preregistered G8 action-stability condition passes only if every plausible
primary sensitivity has a flip rate no greater than 10% for both inventory
levels. Unsupported mappings are not silently removed. A missing mandatory
sensitivity makes G8 incomplete and prohibits a playbook.

## One-factor-at-a-time sensitivities

Run each change against the reference while holding other inputs fixed:

1. **Correction-value estimator**
   - Article 4 partially pooled unconstrained `re_smoothed`;
   - Article 4 pooled-count `re_count_pooled`;
   - Article 4 raw RE288 `raw_mean`; and
   - month-specific leave-one-month-out partially pooled RE288.
2. **Probability/information assumption**
   - fixed 0.50 and fixed 0.70;
   - G6 public-tracking full-fit benchmark; and
   - G6 challenger-selected full-fit transport assumption.
3. **Extra-inning treatment**
   - no extra-inning challenge restoration.
4. **Objective scale**
   - a separately specified and validated decision-time win-probability value.
     If no such estimator is available, mark this mandatory sensitivity
     unavailable rather than substituting realized wins or an unvalidated
     runs-to-wins constant.
5. **Opponent response/policy**
   - league-typical and optimized-opponent variants. Under G7's independent,
     fixed empirical team sequences these cannot be identified; mark them
     unavailable unless a coupled transition model is validated.

Ambiguous runner-placement bounds apply only to the 40 observed incorrect-call
rows and do not define counterfactual values for the full legal decision
population. Report their bounded action stability separately; do not impute
their states into the primary denominator.

Do not run a joint factorial grid. Joint adverse combinations are authorized
only if a one-factor result could change the gate decision and the combination
has a defensible interpretation.

## Distribution and scenario audits

Compare the early and late halves of the locked season by date for correction
value, threshold, and reference action rate. This is a distribution-shift
diagnostic, not a same-row flip rate.

Predeclare neutral threshold audit bands based on the prespecified fixed
probability scenarios:

- `LOW_REQUIRED_CONFIDENCE`: threshold `<= 0.50`;
- `INTERMEDIATE_REQUIRED_CONFIDENCE`: threshold `> 0.50` and `<= 0.70`;
- `HIGH_REQUIRED_CONFIDENCE`: threshold `> 0.70`.

These are validation bands, not final article categories. For each inventory,
report band changes for these scenario families:

- ordinary: 0-0 count, zero outs, bases empty, innings 1-3;
- full count: 3-2;
- two outs with a runner in scoring position;
- late and close: innings 7-9 with absolute entitled-team score difference at
  most one; and
- extra innings.

Use median row-level thresholds and report row support. Any band crossing must
be disclosed. Sparse or absent families remain missing and cannot be filled by
hand-selected examples.

## Required outputs

- one row per sensitivity and inventory with the fixed denominator, action
  counts, flips, and flip rate;
- row-level reference and sensitivity actions for the fixed top-value
  population;
- threshold-band scenario table with support and crossings;
- early/late distribution diagnostics;
- bounded ambiguous-case audit;
- machine-readable validation result and manifest; and
- two byte-identical clean builds.

## Interpretation and stopping rule

G8 can pass computationally while remaining scientifically incomplete. A
Pascal ABS Challenge Playbook remains prohibited if any plausible sensitivity
exceeds the 10% flip limit, a mandatory sensitivity is unavailable, a scenario
crossing is undisclosed, or the upstream G6/G7 restrictions remain unresolved.
No G8 result may be described as evidence that observed players made correct or
incorrect decisions.

## Resource ceiling

Resource class is R0. Reuse only the locked local snapshot and cached derived
inputs. No live API, paid source, hosted database, GitHub Actions, Vercel,
Supabase, Odds API, or additional Claude exchange is authorized.
