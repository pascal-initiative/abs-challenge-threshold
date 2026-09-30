# CT-S1 Acquisition Readiness and Bounded Resource Plan

## Status

**OWNER-DIRECTED RISK ACCEPTANCE RECORDED — WAITING FOR WINDOW COMPLETION.**

This document is the pre-acquisition receipt required by Amendment 005, updated
by Amendment 006. The owner reviewed the source-terms warning and explicitly
directed the existing public-data process to continue. That direction does not
establish public-domain status or resolve the terms question. Execution remains
date-gated until the holdout is complete and completeness checks can run.

## Scope

| Field | Frozen value |
| --- | --- |
| Research identity | CT-S1 |
| Date window | 2026-09-11 through 2026-09-27 inclusive |
| Game type | MLB regular season only |
| Earliest execution | After September 27 and after every required source reports completeness through September 27 |
| Raw destination | New isolated content-addressed directory; never append to or overwrite the accepted full-season raw cache |
| Processing | Local only |
| Publication | Derived summaries only after CTS2-CTS11; no raw redistribution |

September 10 is excluded because some source bytes were archived previously.
The September 11–27 interval has not been acquired or analyzed in this
repository.

## Intended source classes

The existing reconstruction requires four source classes:

1. MLB regular-season schedule and final game feeds;
2. daily Baseball Savant Statcast CSV data;
3. team-level Baseball Savant ABS extracts for all 30 clubs; and
4. the official ABS dashboard for completeness reconciliation.

Current public URLs identify the contemplated sources. The owner-directed
exception applies only to this bounded CT-S1 window. Official schedule
announcements and documentation pages are planning sources, not confirmation
data.

## Source-terms risk record

Written permission or an applicable license remains preferable. If obtained,
record it with:

- automated collection or a licensed bulk-delivery mechanism;
- the schedule/feed, Statcast, and ABS fields required by the reconstruction;
- local immutable retention and private backup;
- reproducible analysis; and
- publication of derived, non-raw findings on the Pascal Institute site.

The record must identify its effective date, scope, restrictions, attribution,
and expiration. For this run, the owner's explicit direction is the controlling
risk decision; it is not evidence that the data are legally public domain.

## Request budget if the source gate is cleared

The following is a hard ceiling, not a target:

| Class | Unique-request ceiling | Basis |
| --- | ---: | --- |
| Schedule | 1 | One bounded regular-season schedule query |
| Final game feeds | 275 | Maximum 17-day slate plus makeup/doubleheader margin |
| Daily Statcast | 17 | One date-bounded response per day |
| Team ABS extracts | 30 | One per MLB club |
| ABS dashboard | 1 | Completeness reconciliation |
| Source/schema documents | 2 | Only if required by the authorized mechanism |
| **Total unique requests** | **326** | Hard stop before request 327 |

Each URL receives at most two total attempts: the original request and one
retry. Therefore the absolute HTTP-attempt ceiling is **652**. Retries use
bounded backoff. Concurrency is at most two, and the client must honor any
provider-specific rate limit or a stricter licensed limit.

The acquisition aborts rather than expanding scope if the schedule would
require more than 275 final game feeds. Resumption must use verified cached
objects and may not refetch successful URLs.

## Byte and storage budget

Historical local receipts provide the planning basis:

- final game feed: approximately 806 KB average, 1.16 MB observed maximum;
- September daily Statcast response: approximately 1.8–3.2 MB in the accepted
  snapshot;
- 30 team ABS extracts: approximately 32.5 MB combined;
- schedule: approximately 2.9 MB; and
- ABS dashboard: approximately 1.4 MB.

The hard downloaded-response ceiling is **450 MiB**. The process checks the
running receipt total after every completed response and stops before scheduling
new work when the ceiling would be exceeded. Any single response above 10 MiB
is quarantined for review rather than parsed automatically.

Reserve **2 GiB** of free local disk for raw objects, derived staging, manifests,
and temporary backup packaging. The host currently has substantially more than
that reserve, but free space must be rechecked immediately before execution.

## Cache, immutability, and failure behavior

- Write into a new CT-S1 raw directory.
- Store response bodies by SHA-256 and never modify them in place.
- Append one receipt per attempted URL with URL, retrieval time, status,
  content type, final URL, bytes, SHA-256, and error if any.
- Refuse duplicate URLs with conflicting successful hashes until reviewed.
- Require final game status before accepting a feed.
- Keep partial pulls quarantined; they cannot enter analysis.
- Fail closed on schema changes, missing required fields, checksum mismatch,
  nonfinal games, incomplete ABS totals, or request/byte cap exhaustion.
- Do not log cookies, authorization headers, credentials, or signed URLs.

No `.env`, token, browser profile, or credential may enter the raw cache,
manifest, Git, or backup.

## Processing boundary

Acquisition and analysis are separate commands. A successful download does not
authorize parsing into CT-S1 results. Before processing:

1. reconcile request and byte totals;
2. verify every receipt/object hash;
3. confirm source completeness through September 27;
4. compare rules and schemas with the development snapshot;
5. freeze an immutable raw manifest; and
6. obtain the CTS2 go decision.

The accepted 2026-03-25 through 2026-09-09 files remain read-only. September 10
objects remain outside both periods.

## Google Drive backup

After raw-manifest acceptance, create a private CT-S1 data-cache milestone using
the existing backup protocol:

- exclude Git internals, credentials, `.env`, virtual environments, caches,
  operating-system metadata, and generated files not required for recovery;
- produce a deterministic file inventory and SHA-256 manifest;
- package the authorized raw cache and required processed inputs;
- split files into approximately 90 MiB chunks, each below the 512 MiB connector
  limit;
- upload the source snapshot, data chunks, checksums, and restore instructions;
- read back Drive metadata and verify every expected filename and byte size; and
- retain local data after upload.

No source data are uploaded until the source-rights record also permits private
off-machine backup.

## External-service budget

| Service | Authorized calls |
| --- | ---: |
| GitHub Actions | 0 |
| Vercel | 0 |
| Supabase | 0 |
| Odds API | 0 |
| Hosted databases | 0 |
| Claude | 0 |

GitHub is used only for source/document review through the normal pull-request
workflow; generated data and raw objects remain ignored.

## Approval sequence

1. Merge Amendment 006, this readiness record, and the guarded acquisition
   implementation.
2. Wait until the September 11–27 window is complete and required sources report
   completeness.
3. Run the dry plan and verify the frozen caps.
4. Execute once with the explicit `--execute --owner-risk-accepted` switches.
5. Stop at CTS2 before analysis if reconciliation fails.

No confirmation acquisition command may run before steps 1–3 are complete.

After acquisition, `validate_ct_s1_raw.py` performs the mandatory offline
preflight. It verifies the exact source set, content-addressed hashes, receipt
fields, request/attempt/byte caps, final game status, feed identities, Statcast
schema and date scope, 30-team ABS response structure, official daily challenge
coverage, and raw-snapshot immutability. Only a passing preflight may hand the
isolated cache to `src.pipeline`; pipeline output remains quarantined until CTS2
population and rules reconciliation passes.

`run_ct_s1_reconstruction.py` is the only approved reconstruction entry point
for CT-S1. It revalidates the raw snapshot against the saved preflight, requires
an empty isolated output directory, protects the development inputs, invokes
the existing fail-closed pipeline, reconciles game/challenge/date/rule outputs,
and rehashes both raw and development inputs afterward. Only
`PASS_CTS2_READY_FOR_CTS3` releases the reconstructed snapshot to successor
model validation.
