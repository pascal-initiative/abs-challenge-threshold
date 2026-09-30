# Article 1 Data

These tables support One in Five. The pilot-week folders come from August 24 through August 30, when we built the pipeline and confirmed that the reconstructed zone matched all 447 official challenges. The season folders come from the March 25 through September 9 snapshot used in the article. The publication-validation folder holds the frozen numbers quoted in the article, the data behind each figure, and the sensitivity checks run before publication.

| Folder | Contents | Produced by | Source path |
| --- | --- | --- | --- |
| [publication-validation](publication-validation/) | Frozen article numbers, sensitivity checks, and validation audits | `python3 -m src.publication_validation` | `artifacts/publication_validation` |
| [publication-validation/figure-data](publication-validation/figure-data/) | The data behind each article figure | `python3 -m src.publication_validation` | `artifacts/publication_validation/article1_figure_data` |
| [pilot-week-reports](pilot-week-reports/) | Pilot validation, data-quality, and descriptive reports | `python3 -m src.pipeline` | `data/processed` |
| [season-reports](season-reports/) | Season validation, data-quality, and descriptive reports | `python3 -m src.pipeline --raw-dir data/full_season/raw --output data/full_season --start 2026-03-25 --end 2026-09-09` | `data/full_season/processed` |
| [pilot-offensive-recognition](pilot-offensive-recognition/) | Sprint 2 recognition figures and models for the pilot week | `python3 -m src.offensive_recognition` | `artifacts/sprint2` |
| [pilot-offensive-recognition/tables](pilot-offensive-recognition/tables/) | Sprint 2 descriptive tables and model metrics | `python3 -m src.offensive_recognition` | `data/analysis` |
| [season-offensive-recognition](season-offensive-recognition/) | Sprint 3 recognition figures, models, and validation for the season | `python3 -m src.sprint3 --start 2026-03-25 --end 2026-09-09` | `artifacts/sprint3` |
| [season-offensive-recognition/tables](season-offensive-recognition/tables/) | Sprint 3 descriptive, monthly, and batter-adjusted tables | `python3 -m src.sprint3 --start 2026-03-25 --end 2026-09-09` | `data/analysis/sprint3` |

The following files are not stored here, either because they record individual pitches or opportunities or because they exceed 5 MB. Each one is in the named archive of the [full data set](../../../data/README.md#the-full-data-set) at the source path shown.

| Source path | Size | Reason | Archive |
| --- | ---: | --- | --- |
| `artifacts/sprint3/temporal_predictions.csv` | 5.2 MB | Over 5 MB | analysis |
| `data/analysis/offensive_recognition_features.csv` | 223 KB | Row-level records | analysis |
| `data/analysis/offensive_recognition_predictions.csv` | 497 KB | Row-level records | analysis |
| `data/analysis/sprint3/offensive_recognition_features.csv` | 5.0 MB | Over 5 MB | analysis |
| `data/analysis/sprint3/offensive_recognition_predictions.csv` | 5.2 MB | Over 5 MB | analysis |
| `data/full_season/processed/challenges.csv` | 5.0 MB | Over 5 MB | season-tables |
| `data/full_season/processed/pitches.csv` | 596.7 MB | Over 5 MB | season-tables |
| `data/processed/challenges.csv` | 242 KB | Row-level records | season-tables |
| `data/processed/pitches.csv` | 25.5 MB | Over 5 MB | season-tables |
