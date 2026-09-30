# Article 4 exploratory analysis

Exploratory analysis of the validated Article 4 dataset (`../output`). It is not an article, and it contains no optimal policy, win-probability model or AnalytIQ integration.

- [EXPLORATORY_ANALYSIS.md](EXPLORATORY_ANALYSIS.md): methodology, findings, uncertainty, competing explanations, nulls, open questions.
- [output/VALIDATION_ANALYSIS.md](output/VALIDATION_ANALYSIS.md): input hashes, reconciliation, leakage audit, models, sensitivity status, reproducibility (generated).
- `output/article4_exploratory_summary.json`: machine-readable statistics and model estimates.
- `output/*.csv`: value distribution, inventory, HINDSIGHT conservation, team, offense/defense, decision frontier, competing attention, sensitivity.
- `output/figures/`: fig01-fig09.

## Reproduce

From the repository root, with the pinned environment (Python 3.9.6, pandas 2.3.3, numpy 1.26.4, statsmodels 0.14.6, scipy 1.13.1, matplotlib 3.9.4):

```sh
/private/tmp/pascal-sprint4-venv/bin/python research/article4/exploratory/analyze.py
/private/tmp/pascal-sprint4-venv/bin/python -m unittest discover -s tests
```

The run takes about 30 seconds and is offline. It stops if the Article 4 inputs no longer match their manifest, if population counts change, or if any protected Articles 1-3 or Article 4 file changes. The primary value is `correction_value_runs_pooled`; the Sprint 5 smoothing RE is a sensitivity. Hindsight outputs are labelled HINDSIGHT and never enter models.
