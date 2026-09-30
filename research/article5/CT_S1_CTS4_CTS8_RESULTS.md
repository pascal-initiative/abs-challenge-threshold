# CT-S1 CTS4, CTS5, CTS6, and CTS8 Results

## Decision

**CTS4, CTS5, CTS6, and CTS8 PASS — READY FOR CTS7.**

The unchanged named CT-S1 reference transported from the March 25--September
9 development period to the untouched September 11--27 confirmation period
within all three frozen temporal-stability limits. The information-timing,
common-support, and model-disclosure contracts also passed.

This is not approval for an article claim or playbook. CTS7 contrast stability,
CTS9 sampling uncertainty, CTS10 isolated reproducibility, and CTS11 claim
review remain required.

## CTS4: information timing

The public state key uses only original call, side, count, outs, base state,
inning, half-inning, score bucket, team role, and challenge inventory. The
fixed-policy action inputs use only fixed probability, correction value, and
the fixed expected-value cutoff. The CTS3 future-row action canary remained
passed. No outcome, correctness, challenge-result, exact-sequence, or realized
run field entered action selection or the public key.

## CTS5: common support

The confirmation period produced 24,880 candidate state/inventory rows, all of
which remained in the controlling denominator. Of those, 22,584 resolved to a
common supported level, for **90.7717% coverage** against the frozen 90% floor.

| Harmonized result | Rows | Share of confirmation candidates |
| --- | ---: | ---: |
| Exact state support (`L0_EXACT`) | 14,514 | 58.34% |
| Score-dropped support (`L1_NO_SCORE`) | 8,070 | 32.44% |
| No common supported level | 394 | 1.58% |
| No development match | 1,902 | 7.64% |

Development schedules enforced at least 200 rows and 100 games; confirmation
schedules enforced at least 50 rows and 25 games. Neither period borrowed
observations or outcomes from the other.

## CTS6: temporal stability

The controlling joint calculation used all 22,584 finite matched reference
rows without favorable-state weighting.

| Frozen measure | Result | Required | Decision |
| --- | ---: | ---: | --- |
| Median absolute CT drift | 0.007628 | <= 0.05 | Pass |
| 90th-percentile absolute CT drift | 0.026143 | <= 0.10 | Pass |
| Spearman correlation, average ranks | 0.995354 | >= 0.80 | Pass |
| Maximum absolute drift, descriptive only | 0.126742 | No gate | — |

Inventory-specific calculations also passed. Inventory one had median drift
0.008028, 90th-percentile drift 0.027100, and correlation 0.994738. Inventory
two had median drift 0.007182, 90th-percentile drift 0.025182, and correlation
0.995816.

## CTS8: model disclosure

All eight required core implementations and both diagnostic implementations
were present. Diagnostics did not set the CT Model Spread endpoints. Every row
received the required spread label, and material disagreement was not hidden.

The disclosure result is important: among 22,428 supported rows with a
complete core grid in each period, 21,942 development rows and 21,929
confirmation rows had model-spread width above 0.10. Median complete-grid width
was approximately 0.171 in development and 0.170 in confirmation. Only 985
period/state rows qualified for the compact within-0.10 presentation; 43,871
require explicit material-disagreement disclosure, 312 have incomplete spread,
and 4,592 are unsupported.

CTS8 passes because it is a disclosure-safety gate, not a requirement that
alternative conventions agree. This result supports evaluating one named,
temporally stable convention only when the substantial convention sensitivity
is shown alongside it. It does not revive the failed CT-2026 consensus claim.

## Integrity and tests

| Artifact | SHA-256 |
| --- | --- |
| Validation | `94d4e818336aa093bb3c83be843da04ff545011251e2e360f696024772724671` |
| Manifest | `a9d157e5be503bdf4f0c404975db77c926142185e1ee3520ab39851f315fcec5` |
| Matched reference | `ee8f286c29a60eb8f64f4f727017b7c933eb90901a95d0ee2e74cea012665cb0` |
| Disclosure table | `ca2cb7bdd6be75fc26f73c49a343b7a870db061bf775a7cd6c99212996b7554a` |
| Exclusion audit | `176f118ec1ce8d8478c6bf2fb4950ea56ec65d6e985d942b0468c51b06c4bdff` |

All 93 focused Article 5 tests passed. The repository-wide suite recorded 197
passes and four unrelated failures: three legacy determinism tests could not
rewrite generated artifacts under the task sandbox, and the pre-existing
publication-validation manifest disagrees with nine current Sprint 4 files.
No file implicated by those failures is an input to this build.

## Resource accounting and next gate

The build used local cached inputs and local CPU. It made zero network, GitHub
Actions, Vercel, Supabase, Odds API, hosted-database, publication, or Claude
calls.

CTS7 is next. It must mechanically generate the preregistered contrast classes
from this matched table and preserve every failed contrast. Numerical drafting
and the playbook remain prohibited until all remaining gates pass.
