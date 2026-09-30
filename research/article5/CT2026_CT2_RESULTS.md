# CT-2026 Gate CT2 Result

**Build status: STOPPED**  
**Gate status: FAIL — reference state policy did not converge**  
**Numerical CT-2026 values publishable: NO**

## What ran

The first CT-2026 prototype implemented the frozen non-clairvoyant fitted policy
iteration in `CT2026_SPEC.md`. It used:

- 334,948 future-stream opportunities across 4,390 team-games;
- the G5 constrained correction value;
- fixed `p=0.60`;
- one and two challenge units;
- the 2026 extra-inning restoration rule; and
- 508 supported inventory-cost states selected by the frozen support hierarchy.

All rows found adequate support: 324,313 used the exact state, 9,701 dropped
score bucket, and 934 additionally dropped team role. No legal or future-stream
row remained unsupported.

## Failure

The state-policy fixed point entered a deterministic cycle. At iteration 13,
the policy hash repeated the policy first seen at iteration 11. The maximum
schedule change in the alternating policies was 0.003650 runs. Neither inventory
policy stabilized:

| Iteration | Challenges with one unit | Challenges with two units |
| ---: | ---: | ---: |
| 9 | 41,905 | 66,965 |
| 10 | 41,919 | 66,929 |
| 11 | 41,905 | 66,960 |
| 12 | 41,919 | 66,925 |
| 13 | repeated iteration-11 policy | repeated iteration-11 policy |

This is not a floating-point tolerance failure. A bounded exploratory check
with 0.50 relaxation still failed to stabilize after 200 iterations, with the
maximum update alternating near 0.001568 runs. A 0.25 run was stopped early
after showing the same non-stable pattern. These exploratory checks are not
accepted CT results and are recorded only to reject silent damping as a fix.

## Interpretation

The failure occurs at the discontinuous boundary where a state-level future
inventory price changes a small set of actions, which then changes the price
used on the next iteration. There is no accepted pure fixed point under the
frozen approximation.

Selecting one side of the cycle, averaging the two policies, increasing the
tolerance, or tuning a relaxation factor would create an undisclosed analytical
choice. The specification correctly required the build to stop instead.

## Consequence

- CT1 input reconciliation passed.
- CT4 support passed.
- CT2 failed.
- CT3 and CT5 through CT10 were not run.
- No threshold table, sensitivity range, uncertainty interval, article example,
  or publication claim was accepted.
- The G8 prohibition on an empirical playbook remains unchanged.

## Proposed correction

Amendment 004 replaces the unstable self-consistent future policy with a fixed,
pre-existing reference convention:

```text
future challenge use occurs when fixed p * correction value >= 0.05 runs
```

The `0.05` expected-run policy was named in the original charter,
preregistration, G7 comparisons, and Article 4. It gives CT-2026 a stable
standard price of future inventory without seeing the realized future or
choosing a rule after inspecting threshold values. It is a publication
convention analogous to a fixed benchmark, not an optimal-player claim.

No corrected CT-2026 values may be computed until Amendment 004 is reviewed and
merged.

## Reproduction and artifact hashes

Command:

```text
.venv-article5/bin/python research/article5/exploratory/failed_ct2026_policy_iteration.py --root . --output <empty-output-directory>
```

The failed build exited with status 2 and produced:

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `7bd010833b0e8fa74eaad55dfd29f36862f7b4e31930cd77a869cc322596e01f` |
| `ct2026_policy_iterations.csv` | `f1f21ce0bc31fb92a4ba181c68a784088d0642f982c63441994e44f45607744e` |
| `validation.json` | `7a5901114cffd544f91c6e666a7bc67891565c0bff9b921b0a081ef42658aaf7` |
| `manifest.json` | `8d2c7ded9b185451b05fceda366098cd40612ee5e7a30508dfbe75dc98083098` |

A second isolated run produced the same four hashes byte-for-byte. This confirms
that the CT2 cycle is deterministic; it does not count as CT9 because the
corrected CT-2026 build did not proceed past CT2.

## Resources

Resource class R0. The build and bounded diagnostic used only the locked local
snapshot and local computation. No new data, live API, GitHub Actions, Vercel,
Supabase, Odds API, hosted service, or Claude exchange was used.
