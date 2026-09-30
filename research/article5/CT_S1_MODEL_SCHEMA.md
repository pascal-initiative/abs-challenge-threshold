# CT-S1 Frozen Validation Schema

## Status and boundary

This schema freezes the data-agnostic CTS3--CTS8 mechanics before the
September 28, 2026 confirmation acquisition boundary. It does not authorize
acquisition, expose confirmation outcomes, or establish that CT-S1 passes.

The reference remains a named convention: constrained partially pooled
count-aware run expectancy, `p = 0.60`, a fixed future-use action rule of
`p * correction value >= 0.05`, expected-runs objective, and the reviewed
extra-inning restoration rule. It is not a model of a particular player's
belief or skill.

## Prepared row contract

The period adapter must produce one canonically ordered row per eligible
decision opportunity. At minimum it supplies:

- `game_pk`, `team_id`, and zero-based `decision_sequence` within team-game;
- inning, half-inning, outs, team role, and decision-time team score
  difference;
- original call, count, base state, and inventory;
- the frozen reference correction value and each required alternative value;
- the fixed reference probability and every required alternative probability;
- evaluated marginal continuation costs for inventory one and two; and
- explicit source-period and version identifiers.

Ordering is validated rather than silently repaired. Probability fitting,
value fitting, and sequence construction remain outside the pure validation
module and require their own provenance artifacts.

## Information timing

Action selection and public state keys may contain only fields established at
the decision instant. Names denoting future opportunities, next events,
challenge results, overturns, actual correctness, or realized runs are
blacklisted. A failing canary stops CTS4.

Later rows may affect retrospective evaluation of continuation value. They may
not change the action selected at the current row under the fixed policy.

## Support hierarchy and harmonization

The hierarchy is ordered from finest to coarsest:

1. exact inning, half, outs, team role, score bucket;
2. exact inning, half, outs, team role;
3. exact inning, half, outs;
4. inning bucket, half, outs; and
5. inning bucket, outs.

Outs and inventory are never dropped. Development support requires 200 rows
and 100 games. Confirmation support requires 50 rows and 25 games. Schedules
are computed at every eligible level. A matched scenario uses the first level,
in hierarchy order, supported in both periods; neither estimate borrows rows or
outcomes from the other period.

At least 90% of candidate confirmation scenarios must resolve. Unsupported
and nonfinite scenarios remain in the exclusion audit.

## Temporal calculation

For each finite matched scenario and inventory level:

```text
absolute drift = abs(CT_confirmation - CT_development)
```

States are unweighted. Ties use average ranks. The joint CTS6 gate requires a
median absolute drift no greater than 0.05, 90th percentile no greater than
0.10, and Spearman correlation at least 0.80. Inventory-specific results are
reported but do not replace the controlling joint result.

## Required implementation grid

Every public candidate row must contain these core variants:

- `reference_fixed_0.60`;
- `fixed_0.50`;
- `fixed_0.70`;
- `cutoff_0.00`;
- `cutoff_0.10`;
- `re_pooled_count`;
- `re_raw`; and
- `no_extra_inning_restoration`.

`public_tracking` and `selected_transport` remain diagnostics and cannot set
model-spread endpoints. Model-spread low, high, and width use only the complete
core grid. Width above 0.10 is labeled `MATERIAL_MODEL_DISAGREEMENT`. A missing
or undefined core alternative is labeled `INCOMPLETE_MODEL_SPREAD` and cannot
appear as an unlabeled compact point estimate.

Sampling intervals are separate fields and are never combined with model
spread into one interval.

## Contrast audit

Each mechanically generated contrast must contain members A and B for both
periods and every core implementation. It is article-eligible only when:

- all required cells are present and finite;
- `CT_B - CT_A` has the same nonzero sign in both periods and all core
  implementations; and
- the absolute reference separation is at least 0.05 in each period.

No failed contrast may be manually replaced after examining confirmation
outcomes. CTS7 requires at least one eligible contrast classified as
`ordinary`; otherwise numerical article examples stop.

## Machine outputs after confirmation

The eventual adapter must emit the matched-state table, support/exclusion
audit, reference table with model spread and separate sampling fields,
contrast audit, gate-level JSON, human-readable report, reproducibility record,
claim-ledger update, and decision memo. Until those artifacts pass, this file
and its tests describe a candidate procedure—not a validated evaluator.
