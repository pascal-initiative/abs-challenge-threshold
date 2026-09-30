# CT-S1 CTS3 Frozen-Implementation Results

## Decision

**CTS3 PASS — READY FOR CTS4--CTS8 VALIDATION.**

The named CT-S1 reference and complete alternative grid executed on the
accepted development and confirmation snapshots using the same reviewed code.
This gate validates implementation identity and prepared inputs. It does not
establish temporal stability, model-spread acceptability, contrast stability,
sampling uncertainty, an article claim, or a playbook.

## Prepared periods

| Measure | Development | Confirmation |
| --- | ---: | ---: |
| Complete called-pitch opportunity stream | 334,948 | 34,842 |
| Legal candidate decisions | 312,228 | 31,825 |
| Opportunities after observed inventory exhaustion | 22,720 | 3,017 |
| Team-games | 4,390 | 458 |
| Reference fixed-policy actions | 234,521 | 24,525 |
| Geometry fallbacks for diagnostic probabilities | 172 | 13 |

Development covers March 25--September 9. Confirmation covers September
11--27. The schemas match exactly and the periods do not overlap.

## Frozen implementation

The reference remains fixed probability 0.60, constrained count-aware
correction value, expected-value cutoff 0.05 runs, expected-runs objective, and
reviewed extra-inning restoration. The future-use action is identical for one
and two units and depends only on the current row's fixed probability and
correction value. Changing a later opportunity changed evaluated continuation
value but not the current action in the required canary.

The complete core grid contains:

- fixed probabilities 0.50, 0.60, and 0.70;
- future-use cutoffs 0.00, 0.05, and 0.10;
- constrained, pooled-count, and raw correction-value estimators; and
- extra-inning restoration on and off.

Public-tracking and selected-transport probabilities remain diagnostics and do
not set CT Model Spread endpoints.

## Implementation audit correction

Before executing CTS3 on confirmation outcomes, the code-to-standard audit
found that the required `0.00` and `0.10` cutoff alternatives were absent from
the successor core tuple and schema even though Amendment 005 already required
them. They were restored before the run and protected by a complete-grid test.
This conformed the implementation to the merged standard; it did not change a
gate after viewing results.

## Validation conditions

All CTS3 conditions passed:

- accepted CTS1/CTS2 hashes reconciled;
- protected inputs were unchanged;
- source schemas matched;
- periods did not overlap;
- the confirmation window was exact;
- all eight core and two diagnostic variants were present;
- reference actions were inventory-invariant;
- the future-row action canary passed;
- reference continuation costs were finite and nonnegative; and
- both period support schedules were generated.

The schedules retain all eligible hierarchy levels: 682 distinct development
level/key groups and 432 confirmation groups for each variant. Harmonization
and candidate-row coverage remain CTS5 tasks and have not been evaluated here.

## Integrity anchors

| Artifact | SHA-256 |
| --- | --- |
| CTS3 validation | `5d4917b1a2a3634624930976773628534a5d92bc60bb7dba9beb76d697c2d8c7` |
| CTS3 manifest | `c0ba5aeece560382a792fd3fe58b3e4b880b6b0699534d1148373e515d689fef` |
| Development prepared rows | `b9da818d49204646903c445f0b3f51965f050ec57717a258b3e1f59b49d123b2` |
| Confirmation prepared rows | `7b8f8d3c68dd21d9d74857265da04e1108f557f81e889518b5ea4786a4e0e67b` |
| Support schedules | `33fe93cc0d228dae07ff8199bd1e396f61e918728c390e4d793fee2025eb8a4c` |
| Team-game values | `91a29110664b30dfbb77c98259b50c2dbc32ac9a59c80296cda3ec8f45e5f929` |

Generated row-level artifacts remain ignored and local.

## Resource accounting

CTS3 used local cached inputs and local CPU. It made zero network, GitHub
Actions, Vercel, Supabase, Odds API, hosted-database, publication, or Claude
calls.

## Next gate

CTS4 must reassert information timing on published keys. CTS5 must construct
the common candidate grid, retain unmatched confirmation rows in its coverage
denominator, and harmonize both periods to the finest common supported level.
Only then may CTS6 temporal drift, CTS7 contrasts, and CTS8 model disclosure be
evaluated.
