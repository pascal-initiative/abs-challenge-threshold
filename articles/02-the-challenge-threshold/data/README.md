# Article 2 Data

These tables come from the Article 2 analysis of the 10,755 incorrect called strikes on which a hitter could legally challenge. They relate distance from the zone, count, location, and game situation to whether the hitter challenged. `REPORT.md` summarizes the analysis, `FIGURES.md` describes each figure, and every table is provided as both CSV and Markdown.

| Folder | Contents | Produced by | Source path |
| --- | --- | --- | --- |
| [challenge-behavior](challenge-behavior/) | Report, figures, and tables for Article 2 | `python research/article2/analyze.py --source-root . --output research/article2/output` | `research/article2/output` |

The following files are not stored here, either because they record individual pitches or opportunities or because they exceed 5 MB. Each one is in the named archive of the [full data set](../../../data/README.md#the-full-data-set) at the source path shown.

| Source path | Size | Reason | Archive |
| --- | ---: | --- | --- |
| `research/article2/output/tables/rolling_predictions.csv` | 1.4 MB | Row-level records | analysis |
| `research/article2/output/tables/rolling_predictions.md` | 1.5 MB | Row-level records | analysis |
| `research/article2/output/tables/test_predictions.csv` | 259 KB | Row-level records | analysis |
| `research/article2/output/tables/test_predictions.md` | 245 KB | Row-level records | analysis |
