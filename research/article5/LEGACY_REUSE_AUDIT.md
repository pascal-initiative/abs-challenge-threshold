# ABS-05 Legacy Reuse Audit

Legacy Sprint 5 predates the validated Article 4 counterfactual work and is
quarantined. Its outputs are evidence about prior implementation attempts, not
accepted Article 5 results.

| Legacy component | Disposition | Reason / acceptance test |
| --- | --- | --- |
| `wrong_way_margin_inches` overturn model | Reject | Signed direction reveals correctness and violates the information set. |
| Existing win-probability conclusions | Reject as evidence | Different primary objective and inherited leaky probability model. |
| Representative-opportunity Bellman recursion | Reject as primary | It does not integrate the future opportunity distribution; `E[max]` is not `max(E)`. |
| Claims of optimal/suboptimal observed decisions | Reject | Private perception is unobserved and selected challenges do not identify it. |
| 312,228-opportunity enumeration | Quarantine | Reconcile keys and legal-state reasons against Article 4 replay before reuse. |
| Inventory transition helpers | Quarantine | Retention, failure loss, grants, and truncation require direct tests. |
| Unit tests | Candidate reuse | Retain only tests that express current rules and pass against the Article 4 engine. |
| IPW selection model | Normally omit | Correctness exists for all pitches; IPW is relevant only to behavioral emulation. |

## Article 4 assets

Feed replay, counterfactual rules, inventory reconstruction, and content-addressed
inputs are accepted subject to manifest verification. RE values are conditional:
the new primary estimator must fix sparse-cell ordering violations. The 40
ambiguous counterfactuals are carried as exclusion/lower/upper variants.

Article 4 option values remain named policy benchmarks. They cannot be inserted
as `C` for the dynamic policy because resource value is policy-dependent.

## Required reconciliation artifact

Implementation must produce a table with each legacy/new population count,
join difference, rule difference, and disposition. No unexplained difference is
allowed to flow into modeling.

## Observed baseline test defect — 2026-09-25

The pinned Python 3.9.6 environment ran all 95 legacy tests. Ninety-two passed.
Three in-place determinism tests did not pass after Git history was established:
Sprint 3 rewrote `artifacts/sprint3/run_manifest.json` because its manifest embeds
the current `git rev-parse HEAD`, while the accepted snapshot recorded the prior
uncommitted state. Sprint 4 then correctly rejected the changed upstream hash.

Only the Sprint 3 run manifest differed; all other Sprint 3 generated files were
byte-identical. The accepted manifest was restored from the verified pre-test
backup. This is provenance coupling, not evidence that the underlying estimates
changed. Do not rerun legacy Sprint 3 or Sprint 4 in place. Run them in an
isolated copy with an explicit source-revision parameter, then compare outputs
while treating runtime provenance metadata separately from scientific content.
