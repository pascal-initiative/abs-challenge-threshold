# Article 5 Data

These tables support Pricing an ABS Challenge. The `ct-s1` folders follow the Challenge Threshold Standard 1 build in order, from the prepared inputs through the temporal-stability test, the matched contrasts, the sampling intervals, the reproducibility check, and the claim review. The CT-2026 folder preserves the predecessor model, which failed its validation gate and is kept so the record is complete. The per-state threshold tables are held back for size and are included in the full data set.

| Folder | Contents | Produced by | Source path |
| --- | --- | --- | --- |
| [ct-s1/temporal-stability](ct-s1/temporal-stability/) | Development versus confirmation comparison and compact threshold grid | `python research/article5/build_ct_s1_temporal.py` | `data/ct_s1/temporal` |
| [ct-s1/prepared-inputs](ct-s1/prepared-inputs/) | Support schedules and validation for the prepared inputs | `python research/article5/build_ct_s1_prepared.py` | `data/ct_s1/cts3` |
| [ct-s1/contrasts](ct-s1/contrasts/) | Validation of the matched count, inning, and inventory contrasts | `python research/article5/build_ct_s1_contrasts.py` | `data/ct_s1/cts7` |
| [ct-s1/sampling-intervals](ct-s1/sampling-intervals/) | Bootstrap support costs and completeness audit | `python research/article5/build_ct_s1_uncertainty.py` | `data/ct_s1/cts9` |
| [ct-s1/reproducibility](ct-s1/reproducibility/) | Two-build byte comparison and protected-input hashes | `python research/article5/build_ct_s1_reproducibility.py` | `data/ct_s1/cts10` |
| [ct-s1/claim-review](ct-s1/claim-review/) | Audit of each public claim against its source artifact | `python research/article5/build_ct_s1_claim_review.py` | `data/ct_s1/cts11` |
| [ct-s1/confirmation-reports](ct-s1/confirmation-reports/) | Validation and descriptive reports for the confirmation window | `python research/article5/run_ct_s1_reconstruction.py` | `data/ct_s1/reconstructed/processed` |
| [ct-s1/preflight](ct-s1/preflight/) | Raw-source checks run before the confirmation build | `python research/article5/validate_ct_s1_raw.py` | `data/ct_s1/preflight` |
| [ct-2026-predecessor](ct-2026-predecessor/) | The failed predecessor model, preserved for the record | `python research/article5/build_ct2026.py` | `research/article5/output/ct2026` |
| [g9-benchmarks](g9-benchmarks/) | Effect-size and policy benchmarks from the G9 gate | `python research/article5/build_effect_size.py` | `research/article5/output/g9` |
| [input-audit](input-audit/) | Hash audit of every accepted Article 5 input | `python research/article5/audit_inputs.py` | `research/article5/output` |

The following files are not stored here, either because they record individual pitches or opportunities or because they exceed 5 MB. Each one is in the named archive of the [full data set](../../../data/README.md#the-full-data-set) at the source path shown.

| Source path | Size | Reason | Archive |
| --- | ---: | --- | --- |
| `data/ct_s1/cts3/confirmation_prepared.csv` | 13.8 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/cts3/development_prepared.csv` | 132.5 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/cts7/contrast_audit.csv` | 7.6 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/cts7/contrast_cells.csv` | 147.2 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/cts7/contrast_pairs.csv` | 6.2 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/cts9/reference_sampling_intervals.csv` | 18.3 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/reconstructed/processed/challenges.csv` | 568 KB | Row-level records | ct-s1 |
| `data/ct_s1/reconstructed/processed/pitches.csv` | 62.2 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/temporal/development_candidate_states.csv` | 9.0 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/temporal/exclusions.csv` | 20.2 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/temporal/matched_all_variants.csv` | 57.4 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/temporal/matched_reference.csv` | 6.2 MB | Over 5 MB | ct-s1 |
| `data/ct_s1/temporal/reference_disclosure.csv` | 20.6 MB | Over 5 MB | ct-s1 |
| `research/article5/output/ct2026/ct2026_sensitivity.csv` | 49.2 MB | Over 5 MB | analysis |
| `research/article5/output/ct2026/ct2026_table.csv` | 18.4 MB | Over 5 MB | analysis |
| `research/article5/output/g9/team_game_values.csv` | 11.4 MB | Over 5 MB | analysis |
