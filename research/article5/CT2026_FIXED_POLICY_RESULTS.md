# CT-2026 Fixed-Policy Build Results

## Decision

**CT6 sensitivity failed. Numerical CT-2026 values remain prohibited in
article prose and publication artifacts.**

The corrected fixed-policy engine passed its construction, information-timing,
support, mathematical, uncertainty, and example-selection checks. It did not
pass the preregistered publication-readiness safeguard requiring no more than
25% of candidate states to have a core Challenge Threshold range wider than
0.10. The observed share was **97.0523%**.

This is a scientific stopping point, not a software failure and not evidence
that the Challenge Threshold definition is mathematically invalid. It means a
single CT-2026 table spanning the frozen core assumptions is too
assumption-sensitive to publish as the proposed stable industry evaluator.

## What was built

The accepted engine prices future challenge inventory under the reviewed,
predeclared convention:

```text
p_future = 0.60
challenge a future opportunity when p_future * V >= 0.05 expected runs
```

The action rule uses only fixed probability and the current opportunity's
correction value. It has no convergence loop and cannot inspect later
opportunities when selecting an action. The evaluator then applies that fixed
rule to complete historical team-game paths and aggregates marginal
continuation value into the frozen decision states.

The build covered 312,228 observed legal decisions across 4,390 team-games.
All 64,694 candidate table rows met the support and reference-publication
eligibility conditions. Those rows are nevertheless not approved for public
numerical use because CT6 failed.

## Gate results

| Gate | Result | Finding |
| --- | --- | --- |
| CT1 inputs | Pass | Protected inputs and locked population reconciled. |
| CT2 reference engine | Pass | Fixed policy obeyed inventory mechanics and stayed below the exact-future upper diagnostic for every team-game/inventory comparison. |
| CT3 information timing | Pass | Actions were frozen from `p`, current `V`, and the cutoff; inventory levels used the same action rule. |
| CT4 support | Pass | No future-stream row required suppression after the frozen hierarchy. |
| CT5 mathematics | Pass | Reference thresholds were bounded and used state-level `C` with current-state `V`. |
| CT6 sensitivity | **Fail** | 97.0523% exceeded the 0.10 core-range materiality rule; the limit was 25%. |
| CT7 uncertainty | Pass | All 500 game-clustered bootstrap replicates were finite. |
| CT8 examples | Pass | All five mechanically required example groups were produced. |
| CT9 reproducibility | Pass as failure-record validation | Two isolated builds produced 10 byte-identical files and the same CT6 stop; 48 focused tests passed. This does not override CT6. |
| CT10 claim review | Pass | Output wording preserves the player-confidence and playbook prohibitions. |

## Sensitivity decomposition

The 97.0523% result is the width across all required one-factor-at-a-time core
variants, not the share moved by every individual variant. Relative to the
reference threshold:

| Variant | Share with absolute CT change > 0.10 | Median absolute change | 90th-percentile absolute change |
| --- | ---: | ---: | ---: |
| Future probability 0.50 | 0.0000% | 0.0766 | 0.0858 |
| Future probability 0.70 | 19.9184% | 0.0870 | 0.1041 |
| EV cutoff 0.00 | 0.0000% | 0.0430 | 0.0608 |
| EV cutoff 0.10 | 14.1559% | 0.0654 | 0.1049 |
| Pooled-count correction value | 27.2297% | 0.0512 | 0.1772 |
| Raw RE288 correction value | 2.8627% of defined comparisons | 0.0067 | 0.0474 |
| No extra-inning restoration | 0.7667% | 0.0000 | 0.0058 |

The raw RE288 estimator produced negative correction values for 1,423 future
opportunities and undefined raw-variant thresholds for 1,336 candidate rows.
They were retained as material sensitivity rather than clipped, removed, or
converted into plausible-looking values.

The reference CT distribution itself ranged from approximately 0.0047 to 1.0,
with median 0.5673. These are validation diagnostics only and are not approved
article findings.

## Exact-future diagnostic

The mean fixed-policy value of starting with one challenge unit was 0.278877
expected runs per team-game, compared with 0.872823 for the privileged
exact-future upper diagnostic. With two starting units, the corresponding
means were 0.567449 and 1.477066. The fixed evaluator stayed below the upper
diagnostic as required. The large separation reinforces that the exact-future
quantity must not be presented as a decision-time policy value.

## Reproduction

```bash
PYTHONPYCACHEPREFIX=/tmp/pascal-pycache \
  .venv-article5/bin/python research/article5/build_ct2026.py --root .

PYTHONPYCACHEPREFIX=/tmp/pascal-pycache \
  .venv-article5/bin/python research/article5/verify_ct2026_reproducibility.py --root .
```

The first command intentionally exits nonzero while CT6 fails. Large generated
tables remain ignored local artifacts.

## Consequence and next decision

Do not solve this by relaxing the 0.10 width, removing the 0.50 or 0.70
probability cases, dropping the pooled estimator, or selecting attractive
states after seeing results.

A future reviewed amendment may investigate a narrower, clearly labeled
evaluator domain or replace a single point estimate with an assumption surface.
That work must be specified before new candidate results are inspected. Until
then, public work may explain the Challenge Threshold framework and why the
attempted CT-2026 standardization was not stable enough; it may not publish the
reference table, give situational prescriptions, grade players, or claim a
validated Pascal playbook.
