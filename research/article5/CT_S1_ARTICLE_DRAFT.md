# Pricing an ABS Challenge

*Challenge Threshold Standard 1 puts the value of correcting a call and the
future value of preserving a challenge on the same scale—without pretending to
know what a player saw.*

Imagine the bottom of the fifth inning. The home team trails by at least two
runs. Nobody is on base, nobody is out, and the offense still has two challenge
units. The umpire calls a strike.

At a 1-1 count, the call moves the plate appearance to 1-2. At a 1-2 count, the
same call ends it. The hitter must decide almost immediately whether to ask the
Automated Ball-Strike system to review the pitch. If the challenge succeeds,
the call is corrected and the team keeps its challenge unit. If it fails, the
call stands and one unit disappears.

The player does not know the answer when the decision must be made. He has a
view of the pitch and the catcher's movement, but not the ABS ruling. The
decision places the possible value of correcting the call against the possible
value of saving a challenge for later.

That tradeoff is the subject of the fifth article in our ABS series. This time,
the question is narrower and more formal:

> Under a declared value model, how confident would a challenger need to be for
> a challenge to break even?

We call the answer **Challenge Threshold**. The public reference developed here
is **Challenge Threshold Standard 1**, or **CT-S1**, version **ct-s1.0**. It is
a common evaluator for a game situation, not a prediction of what a player
believed and not a command to challenge.

<!-- claims: CTS11-C01 CTS11-C05; constraint: CTS11-C08 -->

## The two prices in every challenge

Every challenge puts two quantities in competition.

The first is the immediate value of a correction. We call that `V`: the change
in expected runs if an incorrect call is fixed. The second is `C`: the modeled
future expected-run value of the challenge unit that would be lost after a
failed challenge.

Under the CT-S1 fixed-path reference, the break-even threshold is:

```text
Challenge Threshold = C / (V + C)
```

If the decision-time probability of success equals that value, the modeled
expected value of challenging and preserving the unit is the same. A lower
threshold means the named model requires less confidence to break even. A
higher threshold means it requires more.

The full decision equation can also contain a continuation term, `deltaW`, for
differences outside the inventory effect. CT-S1 fixes that term at zero by
holding the observed post-decision opportunity path constant. This is a
retrospective valuation convention, not information available to a player. The
reference uses an expected-runs objective, a count-aware run-expectancy
estimator, a fixed future-opportunity probability `p = 0.60`, future use when
`p × correction value >= 0.05` expected runs, and an extra-inning restoration
rule. Here `p` is the fixed future-opportunity input; `p*` is the current
break-even threshold.

Those are standardization choices. They give the reference a stable identity,
but they do not make it the only defensible way to price a challenge. CT-S1
tells us how sure a challenger would need to be **under this named model**. It
does not tell us how sure the challenger actually was.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## A stable reference can still be assumption-sensitive

A useful standard should not change dramatically simply because it is applied
to a later group of games. We therefore built CT-S1 on a development period
from March 25 through September 9, 2026, froze the procedure, and evaluated it
on an untouched confirmation period from September 11 through September 27.
September 10 belongs to neither period.

The confirmation period produced 24,880 legal state/inventory rows, where each
row is a distinct game-state and inventory combination. Of those, 22,584 had
support in both periods under the frozen hierarchy, or 90.7717%. Unsupported
states were not filled in or described as validated.

Across those 22,584 finite matched rows, weighted equally rather than by how
often a pitch or challenge occurred, the median absolute change in CT-S1 was
0.007628, or 0.76 percentage points. The 90th-percentile change was 0.026143,
or 2.61 percentage points. The rank correlation between development and
confirmation was 0.995354.

The frozen publication-readiness gate classified those values as temporal
stability for the named reference. That is not the same thing as agreement
about how Challenge Threshold should be modeled.

Within the same 22,584-row support population, completeness was assessed
separately by period. In both periods, 22,428 state/inventory rows had a
complete eight-convention grid. CT Model Spread—the distance between the lowest
and highest threshold produced by those chosen conventions—was wider than 0.10
for 21,942 development rows and 21,929 confirmation rows. That is about 98% of
the complete-spread denominator in each period.

These findings belong together. The first says one frozen convention traveled
well through time. The second says the chosen conventions often assigned
materially different values to the same supported state. Temporal drift and
model disagreement answer different questions, and the favorable result does
not cancel the difficult one.

The eight-convention grid makes that disagreement auditable. Each alternative
changes one declared component of the reference while holding the others
fixed:

| Convention | What changes |
| --- | --- |
| `reference_fixed_0.60` | Reference: future `p=0.60`, a `0.05`-run future-use cutoff, constrained partially pooled count-aware run expectancy, and extra-inning restoration |
| `fixed_0.50` | Future `p` changes to `0.50` |
| `fixed_0.70` | Future `p` changes to `0.70` |
| `cutoff_0.00` | Future-use cutoff changes to `0.00` runs |
| `cutoff_0.10` | Future-use cutoff changes to `0.10` runs |
| `re_pooled_count` | Correction value changes to the accepted Article 4 pooled-count estimator |
| `re_raw` | Correction value changes to the accepted Article 4 raw RE288 estimator |
| `no_extra_inning_restoration` | Extra-inning restoration is turned off |

The future `p` values are standardization inputs used to price future
inventory; they are not estimates of a player's belief. `public_tracking` and
`selected_transport` remain diagnostics outside the eight-convention spread
grid. The chosen set is finite and does not claim to contain every defensible
model.

The remaining 156 supported rows per period are included in the temporal-drift
population but lacked a complete convention grid. Those rows cannot appear as
ordinary point estimates; they must be suppressed or marked incomplete.

<!-- claims: CTS11-C02 CTS11-C03 CTS11-C04 CTS11-C09 -->

## One situation, two counts

The opening example is the only one of three prespecified representative
contrasts that survived the frozen qualification rule. The full state is
an offensive challenge of an original called strike in the bottom of the fifth,
with the home team trailing by at least two, bases empty, no outs, and two
challenge units available.

Only the count changes:

| Period | CT-S1 at 1-1 | CT-S1 at 1-2 |
| --- | ---: | ---: |
| Development | 0.668030 | 0.595135 |
| Confirmation | 0.672804 | 0.600331 |

Under the named reference, the called-strike-three state required about
7.2–7.3 percentage points less confidence to break even. All eight chosen
conventions, including the named reference, preserved the direction of that
comparison, but not its magnitude.

That distinction prevents the example from becoming a universal baseball rule.
It does not establish that every two-strike call should have a lower threshold,
and the analysis does not isolate one modeled component as the cause
of the difference. The score bucket is part of the state key, but CT-S1 uses
expected runs; it is not a win-probability leverage measure.

The other two prespecified representatives—an early-versus-late comparison and an
inventory comparison—did not qualify and were not replaced. The frozen rule
required complete finite cells, the same direction in both periods and all
eight chosen conventions, and reference separation of at least 0.05 threshold
points on the 0-to-1 scale in each period. Keeping the failures visible is part
of the result.

<!-- claim: CTS11-C05; constraint: CTS11-C08 -->

## Two kinds of uncertainty

The count comparison also shows why a single threshold should never travel
alone. For each confirmation-period state, we report both a conditional sampling
interval and CT Model Spread.

| Count | CT-S1 reference | 95% conditional sampling interval | CT Model Spread: min–max across eight conventions |
| --- | ---: | ---: | ---: |
| 1-1 | 0.672804 | 0.648558–0.696556 | 0.587087–0.756986 |
| 1-2 | 0.600331 | 0.574113–0.626422 | 0.509469–0.694697 |

The sampling intervals come from 2,000 game-clustered replicates while the
reference definition remains fixed. They describe sampling variation under
that frozen definition. They are per-state intervals; no paired sampling
interval was calculated for the difference between the two counts. The fact
that the displayed intervals do not overlap is not a substitute for a paired
interval or a test of the contrast difference.

CT Model Spread describes something else: implementation disagreement across
eight selected conventions. It is not a confidence interval, not a probability
distribution, and not a guarantee that every reasonable specification lies
inside the range.

In confirmation, the reference contrast is smaller than the width of either
displayed convention range. The comparison between counts survived all eight
chosen conventions in direction, but the precise threshold attached to either
state remains convention-dependent.

<!-- claims: CTS11-C05 CTS11-C06 -->

## What the standard can measure

Challenge Threshold gives baseball a common vocabulary for the price embedded
in an ABS decision. The metric separates the question “How much confidence does
this value model require?” from the question “How convincing was the evidence
available to this player?”

That separation is essential because the second question remains unidentified.
Public tracking cannot reproduce a hitter's or catcher's view, private team
signals, preparation, or split-second confidence. A successful challenge can
follow a weak decision, and a failed challenge can follow a rational one. The
outcome does not reveal the quality of the choice by itself.

CT-S1 also does not produce a challenge playbook. It does not support
action-colored challenge bands, a universal rule for a count, an optimal
strategy, or grades for observed player decisions. Another declared convention
can set a different break-even value.

The model is therefore best understood in the same spirit as other public
baseball evaluators: useful because its definition is explicit, comparable,
and repeatable—not because it eliminates judgment or uncertainty.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## A result that can be rebuilt

The CT-S1 package was run twice in isolated environments. The builds reproduced
25 generated files byte-for-byte with zero differences or exclusions, left 447
protected inputs unchanged, and passed 99 focused validation tests.

Reproducibility does not establish that the chosen convention is uniquely
correct. It establishes that another run of the frozen procedure reproduces the
same evidence, including the unsupported states, failed representatives, and
material model sensitivity.

<!-- claim: CTS11-C07 -->

## The question CT-S1 answers

An ABS challenge is decided before the answer is known. The current call has a
possible correction value; a failed challenge has a possible future cost; and
the person making the decision has evidence that the public data cannot fully
observe.

Challenge Threshold Standard 1 puts the first two pieces on a common scale. For
the one surviving prespecified comparison, the named reference required less
confidence at 1-2 than at 1-1. Across the broader supported state space, the
named reference met the frozen temporal-stability gate. Across chosen
conventions, however, about 98% of complete-spread rows showed material
disagreement.

The resulting metric is deliberately narrower than a verdict. It does not say
whether a player was right to challenge, wrong to wait, or certain enough in
the moment. It provides a measurable, versioned answer to a more disciplined
question: under a declared value model, how much evidence would make the risk
break even?

That is the role CT-S1 can defend. The judgment that surrounds it remains part
of baseball.

<!-- claims: CTS11-C01 CTS11-C03 CTS11-C04 CTS11-C05; constraint: CTS11-C08 -->
