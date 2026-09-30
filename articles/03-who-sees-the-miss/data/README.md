# Article 3 Data

These tables support Who Sees the Miss? The batter-recognition folder holds the Sprint 4 model, which adjusts each hitter's recognition rate for how difficult his opportunities were and then tests whether that history predicts later behavior. The publication-validation folder holds the data behind each figure, the claims matrix, and the leaderboard rules applied before publication.

| Folder | Contents | Produced by | Source path |
| --- | --- | --- | --- |
| [publication-validation](publication-validation/) | Frozen article numbers, sensitivity checks, and validation audits | `python3 -m src.article3_publication_validation` | `artifacts/publication_validation/article3` |
| [batter-recognition](batter-recognition/) | Sprint 4 batter model, stability tests, and figure data | `python3 -m src.sprint4` | `artifacts/sprint4` |
| [batter-recognition/tables](batter-recognition/tables/) | Sprint 4 batter summaries and leaderboards | `python3 -m src.sprint4` | `data/analysis/sprint4` |

The following files are not stored here, either because they record individual pitches or opportunities or because they exceed 5 MB. Each one is in the named archive of the [full data set](../../../data/README.md#the-full-data-set) at the source path shown.

| Source path | Size | Reason | Archive |
| --- | ---: | --- | --- |
| `data/analysis/sprint4/batter_recognition_opportunities.csv` | 1.0 MB | Row-level records | analysis |
| `data/analysis/sprint4/batter_recognition_temporal.csv` | 2.4 MB | Row-level records | analysis |
| `data/analysis/sprint4/temporal_holdout_predictions.csv` | 251 KB | Row-level records | analysis |
