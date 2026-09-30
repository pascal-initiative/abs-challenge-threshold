# CT-S1 Public Convention Registry Extension

## Decision

**APPROVED — THE EIGHT MODEL-SPREAD CONVENTIONS MAY BE NAMED AND DEFINED IN
PUBLIC ARTICLE MATERIALS.**

The owner approved this narrow registry extension on September 28, 2026. It
adds `CTS11-C09` to the CT-S1 public-claim registry without changing the
underlying evaluator, data, results, metric version, or policy boundary.

## Authorized definitions

The public methodology may name the reference and seven one-factor sensitivity
conventions:

1. `reference_fixed_0.60`
2. `fixed_0.50`
3. `fixed_0.70`
4. `cutoff_0.00`
5. `cutoff_0.10`
6. `re_pooled_count`
7. `re_raw`
8. `no_extra_inning_restoration`

The registry defines the component changed by each convention and identifies
the frozen source specification and implementation by SHA-256.

## Guardrails retained

- The seven alternatives are one-factor-at-a-time sensitivity conventions.
- Future `p` is a standardization input for valuing future inventory, not an
  estimate of player confidence.
- `public_tracking` and `selected_transport` remain diagnostics outside CT
  Model Spread.
- The eight-convention grid is finite and is not claimed to contain every
  defensible model.
- CT Model Spread remains implementation disagreement, not a confidence
  interval.
- The extension does not authorize a playbook, optimal-policy claim, player
  grade, action band, or challenge/preserve command.

## Workflow consequence

The outline and draft claim maps are repinned to the extended registry and now
require all eight convention names plus the diagnostic exclusion language.
Publication, figures, calls to action, site integration, and deployment remain
separate later gates.

## Validation

- The content-addressed claim audit passes with eight approved restricted
  claims, one prohibited policy claim, and no failures.
- The outline and draft claim-boundary validators pass with no unexpected
  numerical tokens.
- The complete focused Article 5 suite passes all 110 tests.
- A negative test removes one convention name and confirms that CTS11 fails
  closed.
