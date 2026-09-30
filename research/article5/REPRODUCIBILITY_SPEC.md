# ABS-05 Gate G10 Reproducibility Specification

## Freeze status

This specification is frozen before the final paired build is run. G10 tests
whether the accepted Article 5 analytical package reproduces; it cannot reverse
the G8 stability failure, identify player confidence, validate the rejected
win-probability model, or authorize a playbook.

## Clean-build scope

Run the following generators twice, in order, using the same locked local
snapshot and the repository's Article 5 virtual environment:

1. `build_correction_values.py` (G5);
2. `validate_probability.py` (G6);
3. `build_dynamic_engine.py` (G7);
4. `build_stability.py` (G8), with a separate empty cache for each run;
5. `build_win_probability_sensitivity.py` (bounded G8 follow-up); and
6. `build_effect_size.py` (G9).

Each run begins with an empty run directory. Every generator receives an
explicit output directory beneath that run. G8's two caches are isolated from
one another so the second build does not inherit derived state from the first.
No generator may write to its default repository output directory.

G0 through G4 are not regenerated because `audit_inputs.py` writes to a fixed
repository path. Instead, G10 must verify the accepted `input_audit.json` and
`INPUT_AUDIT.md` hashes, confirm the input audit passed, confirm the frozen
preregistration hash, and confirm protected source inputs remain unchanged
before and after both runs.

## Byte comparison

The two run directories must contain identical relative file sets. Compare
every generated file byte-for-byte, including all CSV, JSON, Markdown, and
manifest files. No currently generated Article 5 artifact contains authorized
timestamp metadata, so G10 permits no exclusions.

Record for every file its relative path, size, run-A SHA-256, run-B SHA-256,
and equality status. G10 passes only when:

- all six generators exit successfully in both runs;
- each generator reports its accepted computational status, including the
  preserved scientific failures and restrictions;
- the relative file sets match exactly;
- every paired file is byte-identical;
- the accepted G0–G4 audit and preregistration hashes reconcile;
- protected source inputs are unchanged; and
- the focused Article 5 test suite passes.

Scientific gate failures are expected outputs, not build failures. In
particular, G8 must remain failed for stability, the G8 win-probability model
must remain rejected, and G9 must remain a nondeployable upper benchmark even
if their artifacts reproduce perfectly.

## Required G10 outputs

- `comparison.csv` with one row per paired generated file;
- captured command/status records for both runs;
- `validation.json` with every G10 condition;
- a human-readable `VALIDATION.md`;
- a deterministic manifest for the G10 summary artifacts; and
- a result memo updating the Article 5 status and claim ledger.

The paired generated run directories remain ignored local artifacts. Commit
the generator, tests, specification, and concise result memo; do not commit the
large regenerated outputs.

## Resource ceiling

Resource class is R0. Use local cached inputs and local computation only. No
live acquisition, paid source, GitHub Actions, Vercel, Supabase, Odds API,
hosted database, production system, or additional Claude exchange is
authorized.
