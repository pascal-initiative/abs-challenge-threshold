# Article 2 ABS research sprint

Review [the research report](output/REPORT.md), [figures](output/FIGURES.md), and generated CSV/Markdown [tables](output/tables). This is research, not an article draft.

## Reproduce

From the ABS research repository (`.`):

```sh
python3.9 -m venv /private/tmp/abs-article2-venv
/private/tmp/abs-article2-venv/bin/python -m pip install -r research/article2/requirements.txt
PYTHONDONTWRITEBYTECODE=1 /private/tmp/abs-article2-venv/bin/python research/article2/analyze.py \
  --source-root "$PWD" \
  --output "$PWD/research/article2/output"
/private/tmp/abs-article2-venv/bin/python research/article2/verify.py \
  --source-root "$PWD" \
  --output "$PWD/research/article2/output"
```

The existing execution environment is `/private/tmp/pascal-sprint2-venv/bin/python`; it contains the pinned packages. It can replace `/private/tmp/abs-article2-venv/bin/python` above without installing anything. Installing a fresh environment needs network access; analysis itself is offline. Python 3.9.6 was used. Newer Python versions may require different compatible package pins and are not the exact reproduction environment.

Required local inputs: `data/full_season/processed/pitches.csv`, `challenges.csv`, `validation_report.json`, their manifest, existing source modules, and frozen `artifacts/publication_validation`. These large source CSVs/raw archives may be ignored by Git. The analysis calls the existing population builder, asserts 10,755 opportunities and 2,112 challenges, and fails on mismatch. It never runs acquisition or the original pipeline's output-writing entrypoints.

To compare two runs, use `--output /private/tmp/abs-article2-repeat`, then:

```sh
/private/tmp/abs-article2-venv/bin/python research/article2/verify.py \
  --source-root "$PWD" \
  --output "$PWD/research/article2/output" \
  --compare /private/tmp/abs-article2-repeat
```

The verifier checks source hashes, population totals, all 12 counts, split chronology, held-out metrics independently recomputed from predictions, rolling prediction coverage, batter aggregation, candidate support and feature leakage. Repeat comparisons require byte-identical CSV/Markdown and PNG files; PDFs can differ in metadata timestamps and are excluded from byte comparison.

## Analysis decisions

- March–June training; July model selection; August–September 9 final test.
- Fixed A geometry, B +count, C +context, D +inventory. Simplest A–D within .001 validation log loss of best. E adds one fixed pitch block to that baseline.
- L2 logistic C=1; cubic distance spline with five training-quantile knots; no tuning search. All numeric imputation and transformations fit only on training data.
- One thousand paired bootstrap samples by game and batter; conditional on fitted models. No causal claims.
- Batter expected counts use expanding monthly earlier-date fits, April–September. March's 391 rows lack prior-date predictions. July-based specification selection makes earlier rolling residuals retrospective diagnostics.
- Minimum 50 predicted opportunities for candidate lists; sensitivity 30/50/75/100. No best/worst ranking. Conditional, simultaneous and within-player game-bootstrap uncertainty are supplied; none fully covers baseline estimation or persistent within-player dependence.
- Borderline exclusion thresholds fixed at 0/.05/.10/.25/.50 inches. Linear distance and development-selected high-volume batter/team exclusions are sensitivity checks; no population redefinition.

## Outputs

- `output/REPORT.md`: research report and six requested findings categories.
- `output/FIGURES.md`, `output/figures`: seven PNG (300 dpi) and vector PDF figures, with captions.
- `output/tables`: all descriptive, inferential, prediction, residual, sensitivity and plotting data, each CSV paired with Markdown.
- `output/manifest.json`: source hashes, exact features and versions, random seed, exclusions, selection and missingness.
- `verification.json`: verification results from the supplied verifier.

Do not hand-edit generated outputs. Edit code and rerun. The frozen Article 1 reconstruction is unchanged. A future article requires human review of these findings first.
