# CT-S1 CTS1/CTS2 Data Acceptance Results

## Decision

**CTS1 PASS — CTS2 PASS — READY FOR CTS3 FROZEN IMPLEMENTATION.**

The September 11--27, 2026 confirmation snapshot passed bounded acquisition,
offline raw preflight, and isolated reconstruction. This decision releases the
reconstructed tables only to the already-frozen CT-S1 implementation. It does
not establish temporal stability, validate a numerical successor, authorize an
article claim, or permit a playbook.

## Accepted population

| Measure | Accepted value |
| --- | ---: |
| Regular-season games | 230 |
| Physical pitches | 67,355 |
| Official ABS challenges | 1,050 |
| Deduplicated team ABS challenges | 1,050 |
| Source URLs in accepted view | 279 |
| Receipt rows, including refresh history | 312 |
| HTTP attempts | 312 |
| Successful / failed receipts | 311 / 1 |
| Retained content-addressed bytes | 309,891,150 |

The sole failed receipt is the preserved header-only September 27 Statcast
refresh. It did not supersede the accepted view. The later 3,928-row response
did supersede the original empty object through the audited receipt chain.

## Source reconciliation

The accepted source view contains:

- one regular-season schedule;
- 230 final game feeds;
- 17 daily Statcast exports;
- 30 team ABS extracts; and
- one official ABS dashboard.

All expected URLs are present and no extras enter the accepted view. Every
historical object referenced by a receipt is retained and content-addressed.
The daily team challenge records reconcile exactly to the official dashboard's
1,050 challenges. Statcast schemas and dates reconcile to the frozen window.

## CTS2 reconstruction checks

All required checks passed:

- pipeline validation status;
- game and challenge counts;
- daily challenge totals;
- pitch and challenge date isolation;
- source hashes against the accepted preflight;
- geometry-method identity;
- emitted validation identity;
- development-input immutability; and
- raw-snapshot immutability.

The accepted development pitches, development challenges, Article 4 RE288
table, preregistration, amendments, CT specifications, and successor validation
plan retained their protected hashes throughout reconstruction.

## Acquisition incidents

Three source-representation or publication-latency events were handled before
reconstruction:

1. MLB listed one postponed game twice in the schedule. The reviewed parser
   retained exactly one completed representation after identity fields agreed.
2. The first September 27 Statcast export contained a header and zero rows. A
   later populated response was accepted through an immutable supersession
   receipt.
3. The dashboard and team ABS extracts initially ended September 26. The
   dashboard-first guarded refresh waited for September 27 and then refreshed
   the 30 frozen team URLs.

The incident records and regression tests are committed. None changed the date
window, population definition, model, support thresholds, or scientific gates.

## Integrity anchors

| Artifact | SHA-256 |
| --- | --- |
| Accepted raw snapshot inventory | `9754fd36aa5f9c91740e5a74bc65952b591c4e03c007670b7ea8d254cca0e684` |
| CTS1 preflight validation | `3d16d2e333a7efc1a41fb65cefa16bea7e95a1c0d3b66406aeb5663ce913fa7f` |
| CTS2 validation | `96e698c709fd1ef8184a7fac3cfe437fc7fb1c5bba8839985578b4489bf0f566` |
| Reconstructed run manifest | `3ac747e630b02fb9495b50815fddbeefae072fea09b32e795fc6aa21154d4f72` |
| Reconstructed pitches | `cab175ac79404e529b266a6c3b7e51b947862ab38565d75929e8da4a81a538cc` |
| Reconstructed challenges | `9e00cba2d7a749940cb2c1e6a4a222a1911aec3524cee2a2f72016b1ca0af077` |

Large raw and reconstructed files remain ignored. These hashes and the local
generated validations are the audit bridge to CTS3.

## Resource accounting

The acquisition remained below the 326-URL, 652-attempt, 450 MiB total, 10 MiB
per-response, and concurrency-one ceilings. Reconstruction used local cached
data and local CPU. GitHub Actions, Vercel, Supabase, Odds API, hosted databases,
publication systems, and Claude were not used.

## Next gate

CTS3 must consume the accepted reconstructed snapshot without tuning against
its outcomes. CTS3--CTS8 remain unpassed until the frozen reference and complete
alternative grid execute on development and confirmation data and produce their
required audits.
