# ABS-05 CT-S1 Companion Methodology Outline

## Purpose

The companion methodology should let a technically literate reader reproduce
the named CT-S1 reference, understand the validation gates, and distinguish
measured population facts from modeled thresholds and fixed conventions. It is
not a second persuasive article and not a repository dump.

## Metric identity and interpretation

- Public name: **Challenge Threshold Standard 1**.
- Research identity: **CT-S1**.
- Metric version: **ct-s1.0**.
- Unit: required confidence on a 0-to-1 scale, usually displayed as a
  percentage.
- Orientation: lower means less confidence is required for break-even under the
  named model.
- Formal interpretation: the confidence a challenger would need under the
  named value model for the challenge to break even.
- Explicit non-interpretation: the metric does not estimate a player's belief,
  perception, skill, or intent.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Decision equation and named reference

Define:

- `V`: immediate expected-run gain if an incorrect call is corrected;
- `C`: modeled future expected-run value of the challenge unit; and
- `deltaW`: continuation difference outside the inventory effect.

The general break-even expression is:

```text
p* = C / (V + deltaW + C)
```

CT-S1 uses the fixed-path restriction `deltaW = 0`, so the published reference
is:

```text
CT-S1 = C / (V + C)
```

Freeze the reference conventions in a boxed specification:

- expected-runs objective for the challenging team;
- constrained partially pooled count-aware run expectancy;
- future probability convention `p = 0.60`;
- future-use rule `p × correction value >= 0.05` expected runs; and
- reviewed extra-inning restoration rule.

Explain that these are standardization choices. They are not an optimal policy
and do not estimate the probability held by a player.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Data periods and candidate denominator

- Development: March 25 through September 9, 2026.
- Confirmation: September 11 through September 27, 2026.
- September 10 belongs to neither period because pre-existing bytes prevented
  an untouched-holdout claim for that date.

Define the 24,880 confirmation denominator as all legal state/inventory rows
created by the frozen reconstruction. Define the 22,584 numerator as rows
resolving to a hierarchy level supported in both periods. Report
90.7717% common support and preserve the unsupported remainder in the exclusion
audit rather than imputing it.

Document the owner-directed source-terms risk acceptance separately from the
scientific validity of derived results. Do not claim that public availability
establishes public-domain status.

<!-- claims: CTS11-C02 -->

## Decision-time state and leakage boundary

List the public state key: original call, side, count, outs, base state, inning,
half-inning, score bucket, team role, and inventory. Explain why outcome,
correctness, challenge result, realized runs, and exact future sequence are
excluded from reference action selection and public state keys.

Describe the future-row action canary and the deliberately blacklisted-field
test. Later opportunities may affect retrospective continuation value but may
not change the fixed current action.

This section is qualitative; it introduces no additional public result beyond
the approved claim boundary.

## Common-support hierarchy

Describe the hierarchy from exact state through coarser inning/half/outs
levels. Outs and inventory are never dropped. Each period uses its frozen
minimum row and game requirements. A comparison uses the first level supported
in both periods.

Reiterate that the supported share is 22,584 of 24,880, or 90.7717%, and that
unsupported states receive no public threshold.

<!-- claims: CTS11-C02 -->

## Temporal validation of the named convention

Explain that states are unweighted and ties use average ranks. Report the
controlling joint results across all 22,584 supported matched rows:

- median absolute drift `0.007628`, or 0.76 percentage points;
- 90th-percentile absolute drift `0.026143`, or 2.61 percentage points; and
- Spearman rank correlation `0.995354`.

Do not state the numerical acceptance limits unless a later registry extension
authorizes them. The companion may explain qualitatively that the frozen
publication-readiness gates passed and that they are not scientific constants.

Interpretation boundary: these results validate temporal transport of the one
frozen reference convention. They do not validate subjective confidence,
causal decision quality, or agreement among alternative conventions.

<!-- claims: CTS11-C03 -->

## CT Model Spread

Explain that CT Model Spread is the minimum-to-maximum threshold range across
eight chosen conventions. Name and define the complete grid:

- `reference_fixed_0.60`: future `p=0.60`, `0.05`-run future-use cutoff,
  constrained partially pooled count-aware run expectancy, and extra-inning
  restoration;
- `fixed_0.50` and `fixed_0.70`: change only future `p`;
- `cutoff_0.00` and `cutoff_0.10`: change only the future-use cutoff;
- `re_pooled_count` and `re_raw`: change only the correction-value estimator to
  the accepted Article 4 pooled-count and raw RE288 estimators; and
- `no_extra_inning_restoration`: change only the restoration rule.

State that future `p` is a standardization input, not player belief, and that
`public_tracking` and `selected_transport` remain diagnostics outside the
spread grid. The set is chosen and finite; the range is not a probability
distribution, not a confidence interval, and not a claim to contain every
defensible model.

For the same common-support state set, 22,428 state/inventory rows had a
complete spread in each period; 21,942 development rows and 21,929 confirmation
rows had width above 0.10, about 98% of that complete-spread denominator. The
matched construction yields the same completeness count in each period.
Another 156 supported rows per period lacked a complete spread. They must be
suppressed from point-value tables or explicitly marked incomplete.

Explain why this result can coexist with strong temporal stability: one
convention can transport well while other plausible conventions price the same
state differently.

<!-- claims: CTS11-C04 CTS11-C09 -->

## Representative-contrast selection

Document the mechanically enumerated contrast families. Candidates were
selected using development data; qualification then required complete finite
cells, a common nonzero direction in both periods and all eight core
implementations, and reference separation of at least 0.05 in each period.

Only one of three ordinary representatives qualified. Give its complete state
and the two counts, then report:

| Period | 1-1 | 1-2 |
| --- | ---: | ---: |
| Development | 0.668030 | 0.595135 |
| Confirmation | 0.672804 | 0.600331 |

The alternatives preserved direction only. Preserve the failed early/late and
inventory representatives in the companion material without replacing them.
State that the trailing score bucket is not win-probability leverage under the
fixed-path expected-runs objective.

<!-- claim: CTS11-C05; constraint: CTS11-C08 -->

## Conditional sampling uncertainty

Document whole-game clusters, the frozen seed, 2,000 replicates, and the frozen
percentile construction with deterministic linear interpolation. The reference
definition, correction-value estimator, hierarchy, probability convention,
future-use rule, and alternative grid remain fixed.

For the confirmation example, report:

| Count | Reference | 95% conditional sampling interval | CT Model Spread |
| --- | ---: | ---: | ---: |
| 1-1 | 0.672804 | 0.648558–0.696556 | 0.587087–0.756986 |
| 1-2 | 0.600331 | 0.574113–0.626422 | 0.509469–0.694697 |

These are per-state intervals. No paired sampling interval was calculated for
the 1-2-minus-1-1 difference. Non-overlap of the two per-state intervals is not
a substitute for a paired interval or a test of the contrast difference. The
reference contrast is smaller than the width of either displayed convention
range. Do not infer a coverage probability from CT Model Spread or combine the
two uncertainty objects.

<!-- claims: CTS11-C06 -->

## Reproducibility

Describe the two isolated complete builds, 25 byte-identical generated files,
zero differences or exclusions, 447 unchanged protected inputs, and 99 focused
Article 5 tests in the frozen CTS10 harness.

Separate computational reproducibility from scientific interpretation. The
reproducible package faithfully preserves material convention sensitivity,
unsupported rows, and failed representative contrasts.

<!-- claims: CTS11-C07 -->

## Version policy

State which changes require a new public version: run environment, ABS rules,
challenge allotment or restoration, correction-value estimator, reference
probability, future-use rule, support hierarchy, or alternative grid. Historical
versions remain available; values are not silently overwritten.

Do not reuse a prior metric label for CT-S1 or silently overwrite a historical
version. Any factual description of a predecessor's validation status requires
a separately approved claim.

<!-- claim: CTS11-C01; constraint: CTS11-C08 -->

## Limitations and prohibited interpretations

- Player confidence is unidentified.
- `deltaW` is zero by construction under a fixed subsequent path.
- Score state does not make this a win-probability model.
- The eight-convention spread depends on the alternatives selected.
- Conditional sampling intervals omit model-definition uncertainty.
- Unsupported and incomplete-spread rows cannot appear as ordinary point
  estimates.
- One qualifying ordinary representative does not create a universal count
  rule.
- A failed challenge is not necessarily a bad decision, and an unused unit is
  not necessarily wasted.
- CT-S1 does not support a playbook, action bands, an optimal strategy, or
  grades of observed player decisions.

<!-- claims: CTS11-C04 CTS11-C05 CTS11-C06; constraint: CTS11-C08 -->

## Reproducibility appendix

Provide the repository revision, public-claim registry hash, accepted output
hash manifests, deterministic commands, environment versions, and a compact
gate table for CTS0 through CTS11. Link the exclusion audit and complete-spread
labels without redistributing raw source data.

Every numerical item in the appendix still requires an approved registry claim
or a later reviewed extension to that registry.
