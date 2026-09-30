# ABS-05 Gate G5 Result

**Status: PASS**

This is a human-reviewable checkpoint, not an article finding or a challenge
playbook. The complete row-level outputs remain generated and ignored.

## Result

The jointly constrained, partially pooled RE288 estimator produced 288 finite
states and satisfied all 552 within-count and terminal-transition constraints.
The projection removed 40 upstream count-ordering violations. Sixty-eight states
changed; mean and maximum absolute changes were 0.008445 and 0.184338 runs. The
largest change was 1.262 estimated cell standard errors, so no projection was
large relative to its sampling uncertainty.

Among 20,164 eligible incorrect calls, all 20,124 non-ambiguous rows had finite,
nonnegative correction values. Median, mean, and maximum values were 0.101169,
0.149446, and 1.917099 runs. These figures are modeled quantities for the
incorrect-call population, not policy results for all legal decisions.

Ambiguity reconciled as 40 = 38 runner-placement rows with finite ordered bounds
+ 2 catcher-interference rows retained as
`AMBIGUOUS_STRUCTURALLY_UNVALUED`. No counterfactual was invented for those two
rows.

All 85 accepted Article 4 automated spot checks remained passing. All 21,533
exact no-runner-action corrected states matched their canonical ball/strike
successors. The three projection-weight sensitivities (prior mass 20, 80, and
uniform weights) also produced no negative exact eligible correction values.

## Failed first run and controlled correction

The first implementation projected the 12 counts separately within each
outs/base stratum. It removed the within-stratum violations but left four exact
values at -0.011925 runs because ball four crosses base states. It also exposed
two ambiguous catcher-interference rows without any reconstructed alternative.
Gate G5 failed and downstream modeling stopped.

The single permitted Claude correction review identified the need for a global
288-state projection and separate reporting of structurally unvalued rows. The
orchestrator independently verified that diagnosis, recorded
`AMENDMENT_001_G5.md`, implemented the correction, and reran the gate. No further
Claude exchange occurred.

## Determinism and artifact hashes

Two clean builds in separate temporary output directories were byte-identical:

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `80e525cb05940bc6be7c07f585a527620fde172c75fcf5c06231a369edc0be98` |
| `incorrect_call_correction_values.csv` | `183e89b438df273ac9bfed4df91fd5a95562842b0751df7497ab68ca1a9ca7d5` |
| `manifest.json` | `8e30bd36dcd5b540242d6670cb45f63fe82d3928d683e02a6f2e56811a5946e7` |
| `re288_constrained.csv` | `e0c47af2ef4ec643fb7fcf6ce237eaf7017c57f453ed410eb4377cc5ccfcc49f` |
| `validation.json` | `35680529669814a20306c9f9e0f0e17d269c19d330eb692558c3be570c1d053d` |

## Verification commands

```text
.venv-article5/bin/python -m unittest \
  tests/test_article5_input_audit.py \
  tests/test_article5_correction_value.py \
  tests/test_article4_counterfactual.py -v

.venv-article5/bin/python \
  research/article5/build_correction_values.py --output <clean-output>
```

Twenty focused and inherited regression tests passed. No live data, paid API,
GitHub Actions, Vercel, Supabase, or Odds API resources were used.

## Consequence

Gate G5 permits threshold computation to proceed, but does not validate a
decision-time probability model, option-value engine, policy comparison, or
playbook. Those remain blocked by later gates.
