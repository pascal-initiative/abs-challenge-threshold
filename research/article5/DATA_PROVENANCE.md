# ABS-05 Data Provenance

## Locked scope

- Dates: 2026-03-25 through 2026-09-09.
- Physical pitches: 645,793.
- Games: 2,195.
- Official challenges: 9,485.
- Source snapshot: the accepted Articles 1–4 content-addressed MLB feed and
  Statcast reconstruction already stored locally.
- New live acquisition: none for the preregistered analysis.

## Accepted dependencies

| Dependency | Status | Required verification |
| --- | --- | --- |
| `data/full_season/raw/objects/` | Immutable cached input | Receipt and object hashes reconcile. |
| `data/full_season/processed/pitches.csv` | Accepted upstream table | Hash matches the accepted manifest. |
| `data/full_season/processed/challenges.csv` | Accepted challenge table | Hash and 9,485 count reconcile. |
| `research/article4/feeds.py` | Reusable | State replay tests pass. |
| `research/article4/counterfactual.py` | Reusable | Rule tests and spot checks pass. |
| `research/article4/output/` | Conditional input | Manifest hashes match; incorrect-only rows are not the policy denominator. |
| `research/article4/decision_value/` | Benchmark only | No result is inherited as an Article 5 conclusion. |

## Immutability contract

The build hashes every accepted input before and after execution and fails on a
change. Raw objects are never modified. Article 5 outputs go only under
`research/article5/output/`, which is ignored and fully regenerated.

## Backup

The 2026-09-25 Google Drive milestone contains a source snapshot and a complete
data-cache snapshot split into eight chunks, with SHA-256 files and restore
instructions. Drive metadata readback confirmed all binary file sizes. The
backup contains no Git history and therefore complements the local Git baseline.
