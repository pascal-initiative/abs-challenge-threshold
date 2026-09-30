# ABS-05 Amendment 004 — CT-2026 Fixed Future-Use Convention

## Timing

Date: 2026-09-25

This amendment was written after CT2 failed and before any accepted CT-2026
reference value was computed. The failure trace and bounded relaxation
diagnostic were known. No threshold table, article example, or model-sensitivity
distribution from a corrected build had been viewed.

## Failure being corrected

The Amendment 003 fitted state-policy iteration did not converge. It entered a
deterministic policy cycle at iteration 13. The frozen specification prohibits
damping, cycle averaging, tolerance inflation, or manual selection without a
reviewed amendment.

Relaxation is rejected as the correction. An exploratory 0.50 relaxation did
not stabilize after 200 iterations, and a relaxation coefficient would add a
numerical convention unrelated to the baseball meaning of Challenge Threshold.

## Corrected reference convention

CT-2026 will price future inventory under a fixed use policy:

```text
p_future = 0.60
challenge a future opportunity when p_future * V >= 0.05 expected runs
```

Ties challenge, matching the pre-existing “at least 0.05” policy definition.
Success retains inventory; failure consumes one; the extra-inning rule is
unchanged.

The 0.05 expected-run cutoff is not selected from CT2 results. It appears in the
original research charter, preregistered policy comparisons, G7, and Article 4.
Fixed 0.60 was frozen as the neutral G8 reference before stability results.

The reference future policy is a standardization convention used to price `C`.
It is not a claim that players possess 60% confidence, that teams should follow
the 0.05 rule, or that the policy is optimal.

## Distributional construction

Evaluate the fixed policy over every complete historical team-game sequence.
The policy at an opportunity may use only fixed 0.60 and that opportunity's
correction value. It cannot use later opportunities, exact future marginal cost,
or a row-specific probability model.

Aggregate evaluated marginal continuation values into the frozen CT-2026
decision-state schedule. Compute the reference threshold from the aggregated
inventory price and correction value. Do not average row-level thresholds.

G7 exact-sequence dynamic values remain a privileged-information upper
diagnostic. The fixed policy must not exceed them on the same team-game sequence.

## Sensitivities

The core range remains one-factor-at-a-time and adds the other preregistered
expected-value cutoffs:

- future `p` equal to 0.50 and 0.70 while retaining the 0.05 cutoff;
- expected-value cutoff 0.00 and 0.10 at fixed 0.60;
- approved correction-value estimators;
- extra-inning restoration off; and
- the existing bounded ambiguous cases.

Public-tracking, selected-transport, Article 4 league-behavior, and G7
exact-sequence quantities remain separately labeled diagnostics and do not set
the core range endpoints.

## Validation changes

CT2 now requires:

- exact agreement with brute-force enumeration on synthetic fixed-policy cases;
- deterministic actions from `p * V >= 0.05`;
- G7 inventory mechanics;
- no future fields in action selection; and
- value no greater than the exact-sequence dynamic upper diagnostic.

Convergence and cycle tests remain in the failed implementation record but are
not conditions for the corrected fixed policy, which has no fitted action loop.

## Unchanged restrictions

This amendment does not identify player confidence, validate the rejected win
model, estimate nonzero `deltaW`, model opponent response, judge observed
decisions, or authorize a playbook.

## Resources

Resource class remains R0. No new data or external service is authorized.

