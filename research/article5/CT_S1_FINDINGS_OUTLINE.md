# ABS-05 CT-S1 Numerical Findings Outline

## Editorial status

This is the first numerical outline authorized after CTS11. It is not polished
article prose, a publication figure set, or a challenge playbook. The only
numerical claims permitted here are the restricted claims in
`CT_S1_PUBLIC_CLAIMS.json`.

Working title: **Challenge Threshold: A Named Reference for Pricing an ABS
Challenge**

Formal thesis: Challenge Threshold is the confidence a challenger would need,
under a named value model, for a challenge to break even. It prices the game
situation; it does not estimate what a particular player saw or believed.

Editorial shorthand, after the formal definition is established:

> Challenge Threshold tells you how sure you need to be. It does not tell you
> how sure you are.

## Reader promise

The reader should finish understanding:

- why an ABS challenge has an immediate benefit and a future inventory cost;
- how CT-S1 converts those quantities into a required-confidence percentage;
- why one frozen convention can be stable over time while alternative
  conventions still disagree materially;
- what one representative count comparison reveals—and what it cannot support;
  and
- why CT-S1 is a shared evaluator rather than a verdict on a player.

## Recommended narrative

### The decision arrives before the answer

Open on a generic called pitch, not an observed player's pass or failed
challenge. The challenger must act before knowing the ABS result. Correcting a
wrong call has immediate value; failing consumes future inventory; passing a
wrong call leaves the original state in place.

The opening should frame this as a pricing problem under uncertainty. It must
not imply that the article can reconstruct a player's private evidence.

No numerical claim is needed in the opening.

### Put the decision on one scale

Define `V` as the expected-run gain if an incorrect call is corrected, `C` as
the modeled future expected-run value of the challenge unit, and `deltaW` as a
continuation difference outside the inventory effect. Under CT-S1's fixed-path
reference model, `deltaW` is zero by construction:

```text
Challenge Threshold = C / (V + C)
```

This is the break-even required-confidence percentage. Lower values mean the
named model requires less confidence; higher values mean it requires more. The
reference convention also freezes an expected-runs objective, a count-aware
run-expectancy estimator, `p = 0.60` for future opportunities, future use when
`p × correction value >= 0.05` expected runs, and the reviewed extra-inning
restoration rule. Publish it as **Challenge Threshold Standard 1 (CT-S1),
version ct-s1.0**, so readers can distinguish the named reference from other
defensible conventions.

The paragraph must call those inputs standardization choices. They are not an
estimate of player belief and not an optimal policy.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

### Test the standard on games it had not seen

Explain the temporal design before giving the favorable stability result. The
development period is March 25 through September 9, 2026. The untouched
confirmation period is September 11 through September 27; September 10 is in
neither period.

The confirmation period supplied 24,880 legal state/inventory rows.
Under the frozen common-support hierarchy, 22,584 were supported in both
periods, or 90.7717%. Unsupported states were not filled in or treated as
validated.

Across the 22,584 supported matched state/inventory rows, with every row
weighted equally rather than by pitch or challenge frequency, the unchanged
reference had median absolute drift of 0.007628, or 0.76 percentage points;
90th-percentile drift of 0.026143, or 2.61 percentage points; and Spearman rank
correlation of 0.995354.

The interpretive sentence matters more than the favorable numbers: this shows
that the one named convention was temporally stable on the holdout. It does not
show that alternative conventions agree, that player confidence is identified,
or that CT-S1 is uniquely valid.

Put the dominant caveat beside that favorable result, not several sections
later. Of the same common-support state set, 22,428 state/inventory rows had a
complete eight-convention grid in each period. Model spread was wider than
0.10 for 21,942 development rows and 21,929 confirmation rows—about 98% of the
complete-spread denominator in each period. This is convention disagreement,
not temporal drift, and the two quantities use different denominators.

Name the complete grid when it is introduced: `reference_fixed_0.60`,
`fixed_0.50`, `fixed_0.70`, `cutoff_0.00`, `cutoff_0.10`,
`re_pooled_count`, `re_raw`, and `no_extra_inning_restoration`. Explain that
the seven alternatives change one reference component at a time. Future `p`
is a standardization input rather than player belief; `public_tracking` and
`selected_transport` are diagnostics outside CT Model Spread.

<!-- claims: CTS11-C02 CTS11-C03 CTS11-C04 CTS11-C09 -->

### Make the abstraction concrete with one count comparison

Use the only ordinary representative that met the frozen rule. Keep "one of
three" attached to the example every time it is introduced.

The complete state is an offensive challenge of an original called strike in
the bottom of the fifth, with the home team trailing by at least two, bases
empty, no outs, and two challenge units available. Compare a 1-1 count with a
1-2 count, where another called strike ends the plate appearance.

| Period | CT-S1 at 1-1 | CT-S1 at 1-2 |
| --- | ---: | ---: |
| Development | 0.668030 | 0.595135 |
| Confirmation | 0.672804 | 0.600331 |

Under the named reference, the called-strike-three state required about
7.2--7.3 percentage points less confidence. That is the supported comparison;
the approved claim does not separately identify which modeled component caused
the difference.

All eight alternatives preserved the direction, not the 7.2--7.3-point
magnitude. The two other ordinary representatives—an early/late comparison and
an inventory comparison—did not qualify and were not replaced. The frozen rule
required complete finite cells, the same direction in both periods and all
eight alternatives, and at least 0.05 reference separation in each period.

The score state is part of the support key. It is not win-probability leverage
under this fixed-path expected-runs objective. This example cannot become a
general rule for all two-strike counts.

<!-- claim: CTS11-C05; constraint: CTS11-C08 -->

### Show two different kinds of uncertainty

For the confirmation-period example, display the reference, its conditional
sampling interval, and CT Model Spread as three distinct visual objects.

| Count | CT-S1 reference | 95% conditional sampling interval | CT Model Spread |
| --- | ---: | ---: | ---: |
| 1-1 | 0.672804 | 0.648558–0.696556 | 0.587087–0.756986 |
| 1-2 | 0.600331 | 0.574113–0.626422 | 0.509469–0.694697 |

The sampling intervals use 2,000 game-clustered replicates while holding the
reference definition fixed. They are per-state intervals; no paired sampling
interval was calculated for the difference. Their non-overlap is not a
substitute for a paired interval or a test of the contrast difference.

CT Model Spread is the range across eight chosen conventions. It is not a
confidence interval, not a probability distribution, and not a guarantee that
all reasonable specifications lie inside it.

For each of these two states, the reference contrast is smaller than the width
of the displayed convention range. That comparison reinforces why the article
must not present the named reference without CT Model Spread.

<!-- claims: CTS11-C06 -->

### Stable over time does not mean assumption-free

This section expands the counterweight introduced alongside temporal
stability. For the same common-support state set, 22,428 state/inventory rows
had a complete eight-convention grid in each period. Of that complete-spread
denominator, 21,942 development rows and 21,929 confirmation rows had model
spread wider than 0.10—about 98% in each period.

The matched construction yields the same completeness count in each period;
another 156 supported rows per period did not have a complete spread. They may
not appear as bare point estimates; a table must suppress them or label them
explicitly as incomplete.

The article should confront the strongest counterargument directly: CT-S1
point values substantially encode a chosen standard, and calling the object a
"Standard" may give it more authority than readers grant its caveats. The
answer is not to hide the disagreement. It is to publish the named reference,
the chosen-convention range, the version, and the interpretation boundary
together.

<!-- claim: CTS11-C04; constraint: CTS11-C08 -->

### A reproducible evaluator, not a command

The methodology may note that two isolated builds reproduced 25 generated
files byte-for-byte with zero differences or exclusions, left 447 protected
inputs unchanged, and passed 99 focused Article 5 tests. Keep this out of the
main narrative unless a short reproducibility box improves reader trust.

Computational reproducibility does not establish that a modeling convention is
uniquely correct. It means another run of the same frozen procedure produces
the same evidence, including the inconvenient model spread and failed
representatives.

<!-- claims: CTS11-C07 -->

### End with the question the metric can answer

Return to the split-second decision. CT-S1 can state the break-even confidence
required under one named value model. A reader may compare decision-time
evidence with that reference while recognizing that another declared
convention can set a different break-even value.

The closing should invite readers to use Challenge Threshold as a common lens,
not as a challenge/preserve instruction. No Pascal ABS Challenge Playbook,
action-colored band, universal count rule, optimal strategy, or grade of an
observed decision is supported.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Figure-data plan

Do not build publication graphics at this stage. Prepare reviewable data specs
only.

### The three prices of a challenge

A conceptual decision diagram defining `V`, `C`, and the fixed-path equation.
It contains no empirical player-confidence estimate.

Source claim: `CTS11-C01`. Policy constraint: `CTS11-C08`.

### One state, two counts

Show the development and confirmation reference values for the surviving
ordinary representative. The label must say "one of three representatives"
and must state that alternatives preserved direction only. A note must identify
the failed early/late and inventory representatives rather than silently
dropping them.

Source claim: `CTS11-C05`.

### One reference, two uncertainty objects

For the same confirmation states, show the per-state sampling intervals and the
eight-convention model spreads with visibly different marks and labels. Do not
draw an interval for the difference.

Source claims: `CTS11-C04`, `CTS11-C06`.

### Stable reference, visible disagreement

A compact summary comparing temporal drift with the share of complete rows
carrying material model disagreement. It must not visually imply that temporal
stability cancels convention sensitivity, and it must label the 22,584-row
temporal denominator separately from the 22,428-row complete-spread
denominator.

Source claims: `CTS11-C03`, `CTS11-C04`.

## Article-level acceptance checklist

- Every numerical sentence cites an approved CTS11 claim in the drafting map.
- The formal definition appears before the editorial shorthand.
- "One of three" travels with the representative example.
- The two failed ordinary representatives remain visible.
- Sampling intervals and model spread use different names and visual encodings.
- The article says that no paired sampling interval was calculated for the
  contrast difference.
- The 156 incomplete-spread rows per period are suppressed or labeled.
- Score state is not described as win leverage.
- No observed player, challenge, failure, pass, or unused unit is graded.
- No playbook, action band, universal count rule, or optimal-policy claim
  appears.
- Publication calls to action are added only during the later site-content
  stage, remain separate from research claims, and receive a fresh CTS11-C08
  policy review.
