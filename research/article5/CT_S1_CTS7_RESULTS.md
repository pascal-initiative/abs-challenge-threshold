# CT-S1 CTS7 Contrast-Stability Results

## Decision

**CTS7 PASS — READY FOR CTS9.**

One of the three mechanically selected ordinary representatives preserved its
direction across the development and confirmation periods and all eight core
implementations, while exceeding the frozen 0.05 reference-separation minimum
in both periods. The two failed ordinary representatives remain in the audit
and were not replaced.

This gate authorizes continued validation. It does not yet authorize article
claims, numerical drafting, or a playbook. CTS9 sampling uncertainty, CTS10
isolated reproducibility, and CTS11 claim review remain.

## Mechanical selection

The generator enumerated every supported pair under the three frozen families:

| Contrast family | Audited | Article-eligible | Share eligible |
| --- | ---: | ---: | ---: |
| Ordinary count vs. terminal count | 5,260 | 3,989 | 75.84% |
| Early inning vs. paired late inning | 3,642 | 1,249 | 34.29% |
| One challenge unit vs. two | 11,292 | 994 | 8.80% |
| Development-selected ordinary representatives | 3 | 1 | 33.33% |
| **Total** | **20,197** | **6,233** | **30.86%** |

`CT_S1_CTS7_SELECTION_RULES.md` records the executable pairing details. The
first three families were exhaustively enumerated. The three ordinary
representatives were selected among bases-empty/no-out pairs using proximity
to the development-period reference median only, with a stable lexicographic
tie-break. Confirmation thresholds and confirmation eligibility did not enter
selection.

The original validation plan froze the families and acceptance test but not
every pairing and tie-break detail. The selection-rules file is therefore an
implementation clarification made before the CTS7 run, not a newly frozen
scientific gate. Exhaustive enumeration and development-only selection reduce,
but do not erase, that procedural limitation.

## Surviving ordinary contrast

The surviving contrast is an offensive challenge of an original called strike
in the bottom of the fifth, home team trailing by at least two runs, bases
empty, no outs, and two challenge units available:

- Member A: 1 ball, 1 strike before the call.
- Member B: 1 ball, 2 strikes before the call, so another called strike is
  terminal.

| Period | Member A CT | Member B CT | B minus A |
| --- | ---: | ---: | ---: |
| Development | 0.668030 | 0.595135 | -0.072895 |
| Confirmation | 0.672804 | 0.600331 | -0.072474 |

Under the named reference convention, the terminal-count state requires about
7.3 percentage points less confidence before challenging. Every core
implementation preserved that negative direction. The smallest alternative
separation was approximately 0.0208 under the pooled-count run-expectancy
sensitivity; the frozen 0.05 minimum applies to the named reference in each
period, while all alternatives must preserve direction.

This is an assumption-labeled modeled comparison. It does not measure what a
player saw or believed, and it does not establish that a particular player
should have challenged.

## Preserved failures

The ordinary early/late and inventory representatives both failed direction
stability across the complete core grid. Their reference separations were also
small: approximately 0.0059 for early/late and 0.0064 development/0.0042
confirmation for inventory.

Across all 20,197 contrasts, failure accounting was:

- 9,597 direction-instability failures;
- 4,190 development reference separations below 0.05;
- 83 confirmation reference separations below 0.05; and
- 94 nonfinite core grids caused by undefined sensitivity thresholds.

## Integrity and tests

| Artifact | SHA-256 |
| --- | --- |
| Validation | `61080a5d13e2185094544a814fba63a206a83d4191317c582892f1b519ed1616` |
| Manifest | `cf2aa1ecb6bbfeb79e35b806ed463b963f2dae5a3785e95e600afffcbfb3a7d2` |
| Contrast pairs | `0d315404752b7f03735d2ca34c67e5bf752caceb0b8c18e2741d77b2ee3c811c` |
| Contrast audit | `fe6d30712a56ab760d70bbddc7a4116ee4ca444c3b88bc3408cae85a3e7bd000` |

All 96 focused Article 5 tests passed. The build protected and reverified the
prior CTS4--CTS8 outputs and the selection rules before and after execution.

## Resource accounting and next gate

The build used local cached inputs and local CPU. It made zero network-data,
GitHub Actions, Vercel, Supabase, Odds API, hosted-database, publication, or
Claude calls.

CTS9 is next. It must add the preregistered game-clustered sampling intervals
to the reference estimates while keeping those intervals separate from CT
Model Spread.
