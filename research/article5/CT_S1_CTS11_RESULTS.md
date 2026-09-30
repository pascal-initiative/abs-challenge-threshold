# CT-S1 CTS11 Claim-Review Results

## Decision

**CTS11 PASS — RESTRICTED NUMERICAL DRAFTING IS AUTHORIZED.**

All eight registered claims resolved against accepted, content-addressed
artifacts: seven are approved with mandatory context and one prohibits policy
translation. The gate authorizes a versioned CT-S1 reference-evaluator article
and companion methodology. It does not authorize a playbook, optimal-policy
claim, player grade, universal count rule, or use of the failed `CT-2026` name.

## Executable claim audit

`CT_S1_PUBLIC_CLAIMS.json` records the statement, claim type, denominator,
artifact hash, exact field or filtered row, required context, and prohibited
extension for each candidate public claim. `build_ct_s1_claim_review.py` fails
closed when an artifact hash, JSON value, CSV count, or selected CSV value no
longer matches.

| Registry result | Count |
| --- | ---: |
| Approved with restrictions | 7 |
| Prohibited policy translations | 1 |
| Failed mappings | 0 |
| Total | 8 |

The negative test changes the confirmation candidate denominator from 24,880
to 24,881 and confirms that the gate fails and numerical drafting is disabled.

## Controlling publication boundary

The article may publish:

- the CT-S1 fixed-path reference definition and named conventions;
- 90.7717% common support across 24,880 confirmation candidates;
- the frozen convention's temporal drift and rank stability across 22,584
  supported matched rows;
- the fact that model spread exceeded 0.10 in about 98% of complete supported
  rows in each period;
- the one-of-three surviving ordinary representative count contrast, including
  its complete state and its roughly 7.2--7.3-percentage-point reference
  difference; and
- separate per-state conditional sampling intervals, model-spread ranges, and
  computational-reproducibility evidence.

The 22,584-versus-22,428 denominator distinction is mandatory. There are 156
supported rows per period without a complete eight-convention spread. They must
be suppressed from point-value tables or explicitly labeled incomplete.

Temporal stability applies to the named convention only. It is not scientific
consensus among implementations, and it does not overcome the material model
spread. CT Model Spread is a range over eight chosen conventions, not a
distribution and not an interval with a coverage probability.

## Bounded independent review

One Claude Opus 5.5 response reviewed the exact packet in
`CT_S1_CTS11_REVIEW_PACKET.md`. It returned **PASS WITH CORRECTIONS** and no
blocking defect. Accepted corrections define the support denominator, disclose
the 156 incomplete-spread rows per period, change the contrast difference to
7.2--7.3 percentage points, limit alternative-model robustness to direction,
state that no paired interval exists for the difference, and separate score
state from win leverage. The complete disposition is in
`CT_S1_CLAUDE_REVIEW.md`.

No second Claude exchange occurred. The advisory review did not replace or
alter the executable acceptance test.

## Integrity and tests

| Artifact | SHA-256 |
| --- | --- |
| Validation | `adebe710d6162dfcc1f6364714d93a5ca1897404987a79b2fae6f4fcd43581bf` |
| Claim audit | `c7c3f745044cfa61bb94bc8e4f29fec55d655f730abfdab33e4f58b1ee40450c` |
| Manifest | `7893fc3b16263533e8d4a5957ff096499f527ce69cc38fa9946a004af28da963` |
| Public-claim registry | `73eb1195f88941a309243fa3c43e90426c7a7137480f85641102df3f82e60993` |

All three focused CTS11 tests passed. The complete focused Article 5 suite
passed with **102 tests** and nine existing numerical runtime warnings in the
correction-value projection tests.

## Resource accounting

CTS11 used local cached artifacts and local CPU plus one bounded Claude Opus
5.5 advisory response. Test execution used an ephemeral `uv` environment and
downloaded Python test dependencies into the local uv cache after the system
Python lacked the accepted scientific stack. It made zero MLB/data-source,
GitHub Actions, Vercel, Supabase, Odds API, hosted-database, publication, or
site-deployment calls.

## Next gate

Research validation is complete for the restricted CT-S1 claim set. The next
step is a numerical findings outline and companion-methodology outline governed
by `CT_S1_DRAFTING_DECISION.md`. Polished prose, figures, site work, and
publication remain later reviewed steps.
