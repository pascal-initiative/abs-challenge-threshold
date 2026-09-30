# Article 4 Data

These tables support What Is a Challenge Worth? The challenge-value folder holds the run-expectancy tables, team summaries, and the August 10 Braves case study. The decision-value folder holds the challenge-success model and the option value of a saved challenge by inning. The exploratory folder holds the value distribution, inventory, and hindsight analyses, and the resource-management folder holds the Sprint 5 work that preceded the article.

| Folder | Contents | Produced by | Source path |
| --- | --- | --- | --- |
| [challenge-value-dataset](challenge-value-dataset/) | Run-expectancy tables, team summaries, and the Braves case study | `python research/article4/build.py` | `research/article4/output` |
| [decision-value](decision-value/) | Challenge-success model, option value, and spend-or-preserve tables | `python research/article4/decision_value/analyze.py` | `research/article4/decision_value/output` |
| [exploratory](exploratory/) | Value distribution, inventory, hindsight, and team analyses | `python research/article4/exploratory/analyze.py` | `research/article4/exploratory/output` |
| [resource-management](resource-management/) | Sprint 5 challenge-resource models and figures | `python3 -m src.sprint5` | `artifacts/sprint5` |
| [resource-management/tables](resource-management/tables/) | Sprint 5 resource-cost summary | `python3 -m src.sprint5` | `data/analysis/sprint5` |

The following files are not stored here, either because they record individual pitches or opportunities or because they exceed 5 MB. Each one is in the named archive of the [full data set](../../../data/README.md#the-full-data-set) at the source path shown.

| Source path | Size | Reason | Archive |
| --- | ---: | --- | --- |
| `artifacts/sprint5/counterfactual_preservation.csv` | 84 KB | Row-level records | analysis |
| `artifacts/sprint5/exhaustion_sequences.csv` | 381 KB | Row-level records | analysis |
| `artifacts/sprint5/low_value_challenges.csv` | 972 KB | Row-level records | analysis |
| `artifacts/sprint5/unsuccessful_good_decisions.csv` | 136 KB | Row-level records | analysis |
| `artifacts/sprint5/valuable_holds.csv` | 1.8 MB | Row-level records | analysis |
| `data/analysis/sprint5/challenge_decision_states.csv` | 39.7 MB | Over 5 MB | analysis |
| `data/analysis/sprint5/challenge_inventory_history.csv` | 960 KB | Row-level records | analysis |
| `data/analysis/sprint5/challenge_opportunities.csv` | 91.3 MB | Over 5 MB | analysis |
| `data/analysis/sprint5/challenge_value_estimates.csv` | 100.5 MB | Over 5 MB | analysis |
| `data/analysis/sprint5/decision_quality.csv` | 53.5 MB | Over 5 MB | analysis |
| `data/analysis/sprint5/exhaustion_events.csv` | 255 KB | Row-level records | analysis |
| `data/analysis/sprint5/post_exhaustion_opportunities.csv` | 1.3 MB | Row-level records | analysis |
| `research/article4/decision_value/output/article4_immediate_expected_value.csv` | 5.9 MB | Over 5 MB | analysis |
| `research/article4/output/article4_all_incorrect_calls.csv` | 28.2 MB | Over 5 MB | analysis |
| `research/article4/output/article4_opportunities.csv` | 26.1 MB | Over 5 MB | analysis |
| `research/article4/output/article4_team_game_sequences.csv` | 5.9 MB | Over 5 MB | analysis |
