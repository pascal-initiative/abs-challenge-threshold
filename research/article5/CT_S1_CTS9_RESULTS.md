# CT-S1 CTS9 Sampling-Uncertainty Results

## Decision

**CTS9 PASS — READY FOR CTS10.**

All 45,168 supported period/state rows received complete deterministic
game-clustered sampling intervals with the frozen 2,000 replicates. All 4,592
unsupported rows remained suppressed. No partial interval was published, and
sampling fields remain separate from CT Model Spread.

This gate quantifies conditional finite-game sampling uncertainty for the
named reference implementation. It does not include uncertainty in the fixed
probability convention, correction-value estimator, state hierarchy,
future-use policy, or alternative implementations. It does not authorize
article claims, numerical drafting, or a playbook.

## Frozen bootstrap

The build used:

- whole games as the resampling cluster;
- seed `20260926`;
- 2,000 replicates;
- 2.5th and 97.5th percentiles with deterministic linear interpolation;
- 2,195 development games and 229 confirmation games; and
- the unchanged named reference implementation.

Each sampled game retained all of its eligible opportunities. State-level
continuation costs were recomputed from the sampled game multiplicities and
then transformed through `C / (V + C)`. The recomputed point costs reconciled
to the accepted reference costs within `5.40e-13` runs.

## Interval results

| Measure | Development | Confirmation | Combined |
| --- | ---: | ---: | ---: |
| Complete supported rows | 22,584 | 22,584 | 45,168 |
| Median interval width | 0.015266 | 0.040713 | 0.024967 |
| 90th-percentile width | 0.031203 | 0.087405 | 0.069674 |
| 95th-percentile width | 0.041271 | 0.111990 | — |
| Maximum width | 0.427219 | 0.611503 | 0.611503 |

Every accepted reference point fell within its sampling interval. The shorter
confirmation period is appropriately less precise than the full development
period. The widest intervals occur in relatively sparse late-game states and
must not be represented as having typical precision.

## CTS7 surviving example

The surviving ordinary CTS7 count contrast now has the following separate
sampling and model-disclosure fields:

| Period and count | Reference CT | 95% sampling interval | CT Model Spread |
| --- | ---: | ---: | ---: |
| Development, 1–1 | 0.668030 | 0.661667–0.674921 | 0.586870–0.755310 |
| Development, 1–2 | 0.595135 | 0.588236–0.602639 | 0.509246–0.692766 |
| Confirmation, 1–1 | 0.672804 | 0.648558–0.696556 | 0.587087–0.756986 |
| Confirmation, 1–2 | 0.600331 | 0.574113–0.626422 | 0.509469–0.694697 |

These are per-state intervals, not a paired interval for the difference. The
model ranges are substantially wider than the sampling intervals and must not
be merged into or described as statistical confidence intervals.

## Frozen-code conformance correction

The first CTS9 merge used a vectorized multinomial implementation that is
distribution-equivalent to resampling games with replacement and passed the
written assurance conditions. The CTS10 provenance review then found that
`ct_s1_assurance.clustered_reference_intervals` had itself been frozen on
September 26 before confirmation acquisition. The controlling CTS9 build was
therefore regenerated through that exact primitive rather than treating two
valid implementations as interchangeable.

CTS9 still passes with all 45,168 supported rows complete. Monte Carlo
endpoints changed slightly because the two seeded algorithms consume random
numbers differently. The values and hashes in this report supersede the first
CTS9 merge. This correction occurred before CTS10 and before article drafting.

## Validation conditions

All CTS9 conditions passed:

- prior accepted output hashes reconciled;
- protected inputs were unchanged;
- the frozen seed, replicate count, and game cluster were used;
- reference point costs reconciled;
- all published intervals contained exactly 2,000 finite replicates;
- all supported rows received a complete interval;
- no partial or reversed interval was emitted; and
- `sampling_` and `model_spread_` fields remained separate.

## Integrity and tests

| Artifact | SHA-256 |
| --- | --- |
| Validation | `2614d57c05b554569e98c42295365290af225b2a7f2982b7df14acc0fd9497ff` |
| Manifest | `2a49cb1e6f5208a3e989589cd788178f6eaa18cc3bc0a44912cc9e55724f5fda` |
| Reference sampling intervals | `7e696d9562e762bb3b2c997576ec03731a00c3db89ee153f979cb586fa4d6f3c` |
| Completeness audit | `89219b61b954b8a5c5f32079ae61af2624e822c104eb143c01336cb6e0c237ef` |
| Bootstrap support costs | `aacb7f6780d1b7f37bed4615a2b456b0567d0255f6ff99b474b6b54ac6d0a815` |

The focused Article 5 suite passes with the added cluster-bootstrap canary.
CTS10 will rerun the complete accepted build twice and provide the controlling
byte-reproducibility evidence.

## Resource accounting and next gate

The build used local cached inputs and local CPU. It made zero network-data,
GitHub Actions, Vercel, Supabase, Odds API, hosted-database, publication, or
Claude calls.

CTS10 is next: two complete isolated builds, protected-input verification,
zero-exclusion file-tree comparison, runtime-metadata audit, and focused tests.
