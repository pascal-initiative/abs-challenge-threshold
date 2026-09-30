# Challenge Threshold Standard 1 Methodology

## Purpose and interpretation

This companion explains the data, definitions, validation, uncertainty, and
interpretive limits behind **Challenge Threshold Standard 1** (**CT-S1**),
version **ct-s1.0**.

CT-S1 is a modeled break-even confidence on a 0-to-1 scale. Lower values mean
less confidence is required for break-even under the named reference; higher
values mean more is required. It does not estimate a player's belief,
perception, skill, intent, or access to private team information.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Decision equation

Let:

- `V` be the immediate expected-run gain if an incorrect call is corrected;
- `C` be the modeled future expected-run value of the challenge unit that a
  failed challenge would consume; and
- `deltaW` be a continuation-value difference outside the inventory effect.

The general break-even expression is:

```text
p* = C / (V + deltaW + C)
```

CT-S1 uses a fixed subsequent path, so `deltaW = 0` by construction and the
published reference becomes:

```text
CT-S1 = C / (V + C)
```

The named convention freezes an expected-runs objective for the challenging
team, a constrained partially pooled count-aware run-expectancy estimator, a
fixed future-opportunity probability `p = 0.60`, future use when
`p × correction value >= 0.05` expected runs, and the specified extra-inning
restoration rule.

Here `p` is the fixed input used to value future opportunities; `p*` is the
current break-even threshold.

These inputs standardize the reference. They are not an optimal policy and do
not estimate the success probability held by a player.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Data periods and denominator

The development period runs from March 25 through September 9, 2026. The
untouched confirmation period runs from September 11 through September 27,
2026. September 10 belongs to neither period because pre-existing bytes
prevented an untouched-holdout claim for that date.

The confirmation reconstruction produced 24,880 legal state/inventory rows;
each row is a distinct game-state and inventory combination. Of those, 22,584
resolved to a hierarchy level supported in both development and confirmation,
for 90.7717% common support. The unsupported remainder is retained in the
exclusion audit and receives no public threshold.

Source terms and acquisition risk are documented separately from scientific
validity. Public availability is not presented as proof of public-domain
status.

<!-- claim: CTS11-C02 -->

## Decision-time state and leakage boundary

The public state key contains the original call, side, count, outs, base state,
inning, half-inning, score bucket, team role, and challenge inventory.

Outcome, correctness, challenge result, realized runs, exact future sequence,
and other post-decision fields are excluded from reference action selection and
the public state key. A future-row action canary and a deliberately blacklisted
field test enforce the timing boundary. The retrospective fixed-path valuation
holds the observed post-decision opportunity sequence constant when valuing
future inventory; that sequence is not treated as information available to the
player and cannot select the current action.

This section describes the design controls. It makes no additional public
numerical claim beyond the approved registry.

## Correction value and future inventory value

`V` compares the count-aware expected-run state created by the original call
with the state that would follow a correction. It is evaluated at decision time
and does not use runs that happened later as the value of the earlier choice.

`C` is the modeled difference between retaining the current challenge inventory
and losing one unit after a failed challenge under the named future-use rule.
A successful challenge retains the unit. CT-S1 does not treat success as
consuming inventory.

The fixed-path construction holds the observed post-decision opportunity
sequence constant, which sets `deltaW` to zero. This retrospective restriction
is part of the metric identity and must remain visible whenever the simplified
equation is published.

<!-- claim: CTS11-C01 -->

## Common-support hierarchy

The hierarchy begins with the exact state and moves through predefined coarser
support levels. Outs and inventory remain in every level. Each period uses its
frozen minimum row and game requirements, and a comparison uses the first level
supported in both periods.

The public support statement is 22,584 of 24,880 confirmation state/inventory
rows, or 90.7717%. Unsupported states are not imputed, backfilled, or treated as
validated.

<!-- claim: CTS11-C02 -->

## Temporal validation

The validation weights each supported state/inventory row equally; it does not
weight by pitch frequency or observed challenge frequency. Ties use average
ranks.

Across all 22,584 finite matched supported rows:

- median absolute drift was `0.007628`, or 0.76 percentage points;
- 90th-percentile absolute drift was `0.026143`, or 2.61 percentage points; and
- Spearman rank correlation was `0.995354`.

The numerical acceptance limits are not part of the current public-claim
registry and are therefore not reproduced here. The frozen
publication-readiness gates passed; those gates are workflow conventions, not
scientific constants.

The result supports temporal transport of one frozen named convention. It does
not validate subjective confidence, causal decision quality, or consensus
among the chosen conventions.

<!-- claim: CTS11-C03 -->

## CT Model Spread

CT Model Spread is the minimum-to-maximum threshold range across eight chosen
conventions, including the named reference. The seven alternatives are frozen
one-factor-at-a-time sensitivities: each changes one declared component while
holding the other reference choices fixed.

| Convention | Future `p` | Future-use cutoff | Correction-value estimator | Extra-inning restoration |
| --- | ---: | ---: | --- | --- |
| `reference_fixed_0.60` | `0.60` | `0.05` runs | Constrained partially pooled count-aware RE | On |
| `fixed_0.50` | `0.50` | `0.05` runs | Reference | On |
| `fixed_0.70` | `0.70` | `0.05` runs | Reference | On |
| `cutoff_0.00` | `0.60` | `0.00` runs | Reference | On |
| `cutoff_0.10` | `0.60` | `0.10` runs | Reference | On |
| `re_pooled_count` | `0.60` | `0.05` runs | Accepted Article 4 pooled-count RE | On |
| `re_raw` | `0.60` | `0.05` runs | Accepted Article 4 raw RE288 | On |
| `no_extra_inning_restoration` | `0.60` | `0.05` runs | Reference | Off |

Future `p` is a standardization input used to value future inventory, not an
estimate of player belief. `public_tracking` and `selected_transport` are
diagnostics outside the eight-convention spread grid and cannot set its
endpoints. The grid is chosen and finite; it does not claim to enumerate every
defensible model.

Within the 22,584-row common-support population, spread completeness was
assessed separately by period. In both periods, 22,428 state/inventory rows had
a complete spread; 21,942 development rows and 21,929 confirmation rows had
width above 0.10, about 98% of that complete-spread denominator. Another 156
supported rows per period remained in the temporal-drift population but lacked
a complete spread. They must be suppressed from point-value tables or
explicitly marked incomplete.

CT Model Spread is a finite sensitivity range. It is not a probability
distribution, not a confidence interval, and not a claim that every defensible
model lies inside it. Strong temporal stability and wide model spread can
coexist because they measure different things: transport of one definition
through time and disagreement across definitions.

<!-- claims: CTS11-C04 CTS11-C09 -->

## Representative contrast

Representative contrast candidates were selected using development data.
Qualification then required complete finite cells, a common nonzero direction
in development and confirmation and across all eight chosen conventions, and
reference separation of at least 0.05 threshold points on the 0-to-1 scale in
both periods.

Only one of three prespecified representative contrasts qualified. It is an
offensive challenge of an original called strike in the bottom of the fifth,
with the home team trailing by at least two, bases empty, no outs, and two
challenge units. The comparison changes the count from 1-1 to 1-2:

| Period | CT-S1 at 1-1 | CT-S1 at 1-2 |
| --- | ---: | ---: |
| Development | 0.668030 | 0.595135 |
| Confirmation | 0.672804 | 0.600331 |

The named reference required about 7.2–7.3 percentage points less confidence
for the called-strike-three state. The eight chosen conventions preserved
direction only, not that magnitude. The failed early/late and inventory
representatives remain part of the disclosure and were not replaced.

The trailing score bucket is a state key, not win-probability leverage under
the fixed-path expected-runs objective. One qualifying contrast cannot be
generalized into a rule for all two-strike counts.

<!-- claim: CTS11-C05; constraint: CTS11-C08 -->

## Conditional sampling uncertainty

Conditional sampling uncertainty uses whole-game clusters, a frozen seed,
2,000 replicates, and a frozen percentile construction with deterministic
linear interpolation. The reference definition, correction-value estimator,
support hierarchy, probability convention, future-use rule, and
chosen-convention grid remain fixed.

For the confirmation-period representative:

| Count | CT-S1 reference | 95% conditional sampling interval | CT Model Spread: min–max across eight conventions |
| --- | ---: | ---: | ---: |
| 1-1 | 0.672804 | 0.648558–0.696556 | 0.587087–0.756986 |
| 1-2 | 0.600331 | 0.574113–0.626422 | 0.509469–0.694697 |

The sampling intervals are per-state intervals conditional on the frozen
reference definition. No paired sampling interval was calculated for the
1-2-minus-1-1 difference. Non-overlap of the per-state intervals is not a
substitute for a paired interval or a test of the contrast difference.

The reference contrast is smaller than the width of either displayed
convention range. CT Model Spread must remain visually and verbally distinct
from the conditional sampling intervals.

<!-- claims: CTS11-C05 CTS11-C06 -->

## Computational reproducibility

Two isolated complete CT-S1 builds reproduced 25 generated files byte-for-byte
with zero differences or exclusions. They left 447 protected inputs unchanged
and passed 99 focused Article 5 tests in the frozen harness.

This establishes computational reproducibility of the declared procedure. It
does not establish that the reference convention is uniquely correct. The
reproducible package also preserves unsupported rows, failed representative
contrasts, and material convention sensitivity.

<!-- claim: CTS11-C07 -->

## Version policy

A change to the run environment, ABS rules, challenge allotment or restoration,
correction-value estimator, reference probability, future-use rule, support
hierarchy, or chosen-convention grid requires a new public version. Historical
versions remain available and values are not silently overwritten.

CT-S1 must not reuse a prior metric label. Any public factual description of a
predecessor's validation status requires its own approved claim.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Interpretive limits

- Player confidence remains unidentified.
- `deltaW` is zero by construction under a fixed subsequent path.
- Score state does not turn CT-S1 into a win-probability model.
- The eight-convention range depends on the conventions selected.
- Conditional sampling intervals omit model-definition uncertainty.
- Unsupported and incomplete-spread rows cannot appear as ordinary point
  estimates.
- One qualifying prespecified representative contrast does not establish a
  universal count rule.
- A failed challenge is not necessarily a bad decision, and an unused unit is
  not necessarily wasted.
- CT-S1 does not support a playbook, action bands, an optimal strategy, or
  grades of observed player decisions.

<!-- claims: CTS11-C04 CTS11-C05 CTS11-C06; constraint: CTS11-C08 -->

## Reproducibility record

The accepted reproducibility and claim-review artifacts record the input and
output hashes, deterministic commands, environment versions, and validated gate
chain. The publication release will pin its final repository revision and link
the exclusion audit and complete-spread labels without redistributing raw
source data.

Every numerical statement remains subject to the approved public-claim
registry or a later reviewed extension.
