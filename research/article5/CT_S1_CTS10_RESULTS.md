# CT-S1 CTS10 Reproducibility Results

## Decision

**CTS10 PASS — READY FOR CTS11.**

Two complete successor builds ran from separate empty copy-on-write roots with
separate derived caches. Every one of the 25 generated files was byte-identical
with no comparison exclusions. All prior successor gate statuses reproduced,
all 447 protected inputs remained unchanged, no forbidden runtime metadata was
present, and all 99 focused Article 5 tests passed.

This establishes computational reproducibility. It does not override the
scientific limitations already recorded, approve an article claim, identify
player confidence, or authorize a playbook. CTS11 claim review remains.

## Isolated builds

Each run independently regenerated:

- the CTS3 prepared development and confirmation streams and support schedules;
- CTS4 information timing, CTS5 common support, CTS6 temporal stability, and
  CTS8 model disclosure;
- all CTS7 contrast pairs, cells, audits, and validation; and
- CTS9 frozen-primitive sampling intervals and completeness artifacts.

The roots used identical relative paths so scientific manifests did not encode
run-specific filesystem names. Inputs were created with copy-on-write cloning
where supported, and each run wrote only to its own fresh
`data/ct_s1/isolated` tree and cache.

## Comparison

| Component | Files compared | Byte differences |
| --- | ---: | ---: |
| CTS3 | 6 | 0 |
| CTS4/5/6/8 temporal package | 9 | 0 |
| CTS7 | 5 | 0 |
| CTS9 | 5 | 0 |
| **Total** | **25** | **0** |

The comparison included all CSV, JSON, manifest, validation, prepared-row,
contrast-cell, disclosure, exclusion, and sampling-interval artifacts. There
were no timestamp or other exclusions.

## Reproduced scientific statuses

Both runs independently reproduced:

- CTS3 prepared-implementation pass;
- CTS4 information-timing pass;
- CTS5 90.7717% common-support coverage pass;
- CTS6 temporal-stability pass;
- CTS7 one-surviving-ordinary-contrast pass;
- CTS8 model-disclosure pass with material disagreement preserved; and
- CTS9 complete frozen-bootstrap interval pass.

Reproducibility preserves both favorable and unfavorable evidence. It does not
turn the extensive CT Model Spread into agreement or convert failed contrasts
into article examples.

## Protected inputs and runtime audit

The audit hashed 447 files before run A and after run B, including confirmation
raw objects and receipts, reconstructed and processed inputs, accepted prior
artifacts, Article 4 dependencies, Article 5 source code, preregistration,
amendments, specifications, plans, and hash manifests. Zero files changed.

Eight generated JSON files per run were checked for forbidden wall-clock keys.
No `created_at`, `generated_at`, `run_at`, `runtime_timestamp`, or `timestamp`
field was present.

Two preliminary dependency checks stopped before producing a CTS10 decision:
the minimal isolated-root inventory initially omitted transitive Article 4
modules. The final harness protects and copies the complete Article 4 research
module. Neither preliminary check changed an accepted input, and the reported
CTS10 result comes only from the subsequent complete paired run.

## Integrity and tests

| Artifact | SHA-256 |
| --- | --- |
| Validation | `713593a76613ff8d24a9b34cbb9b5be67394f5cb33789c3131eb2be11d51249c` |
| Manifest | `eac3c5da3599763c19dcf103ba704a6597483e4e920b48f6ddf81b41bd08d8e7` |
| File comparison | `68d5c68c97117616a47c071d48608f60436442e0c867dc91f623165e1e42d776` |
| Command record | `261905bb20d32de2891b725f25f1a3997eddced97b83b3e7ba4799f71904115d` |
| Protected inputs before | `3da7d487164515e226e06ea48b495341f037352d255019ebb371488a854621b4` |
| Protected inputs after | `3da7d487164515e226e06ea48b495341f037352d255019ebb371488a854621b4` |

All 99 focused Article 5 tests passed inside the CTS10 harness.

## Resource accounting and next gate

CTS10 used local cached inputs, local CPU, temporary copy-on-write roots, and
zero GitHub Actions, Vercel, Supabase, Odds API, hosted-database, publication,
network-data, or Claude calls. Temporary isolated roots were deleted after the
comparison; their complete per-file hashes and sizes remain in the comparison
artifact.

CTS11 is next. It must map every proposed public statement and number to the
accepted artifacts, enforce terminology and caveats, decide the permitted
article/playbook scope, and produce the final drafting decision memo.
