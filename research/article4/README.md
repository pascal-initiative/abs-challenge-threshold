# Article 4 ABS research dataset — what is a challenge worth?

This directory is research data, not an article draft. Start with [METHODOLOGY.md](METHODOLOGY.md), the generated [validation report](output/VALIDATION_REPORT.md) and the generated [data dictionary](DATA_DICTIONARY.md).

## Reproduce

From the ABS research repository root (`.`), with the pinned Sprint 4/5 environment (Python 3.9.6, pandas 2.3.3, numpy 1.26.4, scikit-learn 1.6.1; `requirements-sprint5-lock.txt`):

```sh
# Case-study only (network): archive the Braves schedule and post-snapshot Braves feeds.
/private/tmp/pascal-sprint4-venv/bin/python research/article4/fetch_case_study.py
# Offline build of every artifact plus validation (about 1 minute; the feed replay is cached in /private/tmp/abs-article4-cache).
/private/tmp/pascal-sprint4-venv/bin/python research/article4/build.py
# Counterfactual rule unit tests.
/private/tmp/pascal-sprint4-venv/bin/python -m unittest tests/test_article4_counterfactual.py -v
```

The build reproduces the Articles 1-3 population through the unchanged `src.sprint3.build_population` and stops unless it reproduces 10,755 opportunities and 2,112 challenges. It also stops if any of the 352 protected Article 1-3 inputs change, and if any output column is undocumented. Do not hand-edit outputs; the notes in `manual_review_notes.json` are the only hand-written input.

## Files

| File | Contents |
|---|---|
| `build.py` | Pipeline: population, feed replay, RE288, counterfactual valuation, inventory history, tables, validation |
| `feeds.py` | Feed replay and source-linked event attachment |
| `counterfactual.py` | Pure counterfactual rule engine (R1-R5) |
| `fields.py` | Field registry, which generates `DATA_DICTIONARY.md` |
| `fetch_case_study.py` | Post-snapshot Braves feed archive (case study only) |
| `manual_review_notes.json` | Analyst notes from manual spot checks |
| `output/article4_opportunities.csv` | 1. One row per eligible incorrect call (OFFENSE = Articles 1-3; DEFENSE = extension) |
| `output/article4_all_incorrect_calls.csv` | The same columns for every incorrect call, including ineligible ones |
| `output/article4_team_game_sequences.csv` | 2. Chronological challenge-opportunity histories per team-game |
| `output/article4_team_summary.csv` | 3. Team and league behavior by side, inning bucket and inventory |
| `output/article4_high_value_missed.csv` | 4. Top 250 unchallenged eligible opportunities by value |
| `output/article4_competing_attention.csv` | 5. Opportunities with source-linked secondary actions |
| `output/article4_braves_case_study*.csv`, `article4_braves_case_summary.json`, `article4_braves_game_scores.csv` | 6. Braves case study |
| `DATA_DICTIONARY.md` | 7. Every field with timing and source |
| `METHODOLOGY.md` | 8. Methodology, rules, limitations |
| `output/VALIDATION_REPORT.md`, `validation_report.json`, `article4_spot_checks.csv` | 9. Validation, reconciliation and spot checks |
| `output/article4_re288_table.csv`, `article4_re24_table.csv` | Run-expectancy tables with sample sizes |
| `output/manifest.json` | Code, input and output hashes, row counts and versions |

The stop boundary is dataset construction. There is no inferential modeling, win probability, conclusions about optimal strategy, or AnalytIQ integration.
