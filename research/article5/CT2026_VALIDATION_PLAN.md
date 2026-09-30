# CT-2026 Validation Plan

## Purpose

This plan governs the implementation of `CT2026_SPEC.md`. Passing it authorizes
publication of the CT-2026 reference table and representative evaluator
examples. It does not reverse the ABS-05 G8 failure or authorize a playbook.

## Gates

| Gate | Requirement | Failure consequence |
| --- | --- | --- |
| CT1 Inputs | Locked population, G5 values, G7 mechanics, rules, and source hashes reconcile. | Stop build. |
| CT2 Reference engine | Fixed-0.60, EV-at-least-0.05 policy matches G7 inventory mechanics, synthetic enumeration, and does not exceed the exact-sequence upper diagnostic. | Stop build. |
| CT3 Information timing | Future actions use only fixed 0.60 and current correction value; no exact realized-future cost affects action selection or publication values. | Stop publication. |
| CT4 Support | Mechanical hierarchy is followed; every published row meets row/game minimums and records its backoff. | Suppress failing rows. |
| CT5 Mathematics | All inputs are finite; boundary cases are handled; CT is in `[0,1]`; CT is nonincreasing in `V` for fixed `C` and nondecreasing in `C` for fixed `V`. | Stop build. |
| CT6 Sensitivity | Core range and diagnostic alternatives are complete; material model sensitivity is flagged. | Stop publication. |
| CT7 Uncertainty | Game-clustered intervals reproduce with frozen seed and are kept separate from model ranges. | Publish no sampling intervals. |
| CT8 Examples | Article states are selected by the frozen mechanical rules and trace to table rows. | Stop article examples. |
| CT9 Reproducibility | Two isolated clean builds have identical files and the focused test suite passes. | Stop publication. |
| CT10 Claim review | Every public sentence and figure passes the CT permitted/prohibited-use contract and claim ledger. | Return to draft review. |

## Required tests

### Formula tests

- hand-calculated `V,C` pairs match the implementation;
- `C=0,V>0` returns zero;
- `V=0,C>0` returns one;
- `V=C=0` returns unpublished/undefined;
- percentage formatting rounds correctly at boundary values; and
- reference CT is computed from state-level expected `C` and `V`, never by
  averaging row-level thresholds or exact-sequence costs.

### Information-timing tests

- a row's policy action is invariant when only later opportunities in that
  team-game are changed while fixed probability and current correction value
  are held fixed;
- publication output contains no future opportunity count, later result,
  challenge outcome, correctness label, realized runs, or exact-sequence cost;
- state keys use only declared decision-time fields; and
- a deliberate exact-future canary causes validation failure.

For the snapshot build, add a leave-one-game-out audit on a deterministic sample
of at least 100 games. Record the maximum and median CT change; this is a
stability diagnostic, not a route for inserting game-specific schedules.

### Fixed-policy tests

- action selection reads only fixed `p`, current `V`, the 0.05 cutoff, and
  inventory availability;
- `p * V == 0.05` challenges and values immediately below it hold;
- synthetic sequences match brute-force enumeration;
- the fixed-policy value is no greater than the G7 exact-sequence value for
  every team-game/inventory comparison within numerical tolerance;
- shuffling future row order within a canary copy can change estimated state
  values but cannot give individual actions access to the new exact order; and
- changing a later opportunity cannot change the current fixed-policy action.

### Support tests

- exact cells meeting support do not back off;
- unsupported cells follow the hierarchy in order;
- outs and inventory are never dropped;
- row and distinct-game counts match independent groupings;
- every suppressed row has a reason; and
- every state key maps deterministically to at most one published row.

### Baseball-mechanics tests

- successful challenges retain inventory;
- failures consume one unit;
- extra-inning restoration changes zero to one only;
- game end sets future inventory value to zero;
- offense and defense call transitions are oriented to the entitled team;
- terminal count transitions use the validated G5 correction values; and
- no claim of universal `C(2) <= C(1)` is enforced.

### Sensitivity tests

- every core variant is present or explicitly unavailable with a reason;
- public and selected diagnostic variants never set core range endpoints;
- the material-sensitivity flag equals range width greater than 0.10;
- G8 action-flip and band-crossing results remain unchanged; and
- no variant is removed because it produces an unattractive value.

### Reproducibility tests

- two empty output directories produce identical relative file sets;
- every corresponding file is byte-identical;
- manifests contain no volatile timestamps;
- protected G0-G10 and Article 4 inputs remain unchanged; and
- the existing 40 focused Article 5 tests continue to pass.

## Required outputs

- `ct2026_table.csv` — full supported state table;
- `ct2026_examples.csv` — mechanically selected article states;
- `ct2026_inventory_schedule.csv` — reference and variant `C` schedules;
- `ct2026_sensitivity.csv` — core and diagnostic variant results;
- `ct2026_sampling_intervals.csv` — clustered uncertainty when CT7 passes;
- `VALIDATION.json` and `VALIDATION.md`;
- deterministic `manifest.json`; and
- a concise result memo updating the claim ledger and publication status.

Large generated tables remain ignored local artifacts unless the repository's
artifact policy explicitly permits a compact publication table. Commit the
generator, tests, specification, hashes, and human-reviewable summaries.

## Human review packet

Before article drafting uses numerical CT values, reviewers receive:

1. reference convention and rationale;
2. support/backoff counts and suppressed states;
3. distribution of reference CT by inning, inventory, count, side, and support
   level;
4. core sensitivity widths and flagged-state counts;
5. public/selected diagnostic comparison;
6. sampling uncertainty summary;
7. representative-state selection trace;
8. prohibited-interpretation checklist; and
9. deterministic build record.

## Stopping rules

Stop and report before using CT values in article prose if:

- exact-future information affects reference action selection or a publication
  value;
- the reference engine fails G7 mechanics, fixed-policy enumeration, or the
  exact-sequence upper-bound check;
- more than 10% of candidate publication states fail the minimum support after
  the full hierarchy;
- more than 25% of candidate states carry material model sensitivity;
- ordinary representative states cannot be produced without manual selection;
- a required core sensitivity cannot be computed;
- outputs do not reproduce byte-for-byte; or
- the metric cannot be described without implying knowledge of player belief.

The 10% support and 25% sensitivity limits are publication-readiness safeguards,
not claims that values below those limits are scientifically true. Failure may
lead to a narrower supported domain or a revised, newly reviewed specification;
it may not be cured by silently dropping inconvenient states.

## Resource ceiling

Resource class is R0. The validation uses local cached data and computation
only. It may not invoke GitHub Actions, Vercel, Supabase, Odds API, hosted
databases, production services, live acquisition, or additional Claude review.
