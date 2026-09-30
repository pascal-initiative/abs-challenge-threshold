# ABS-05 Gate G6 Result

**Build status: PASS**  
**Scientific status: RESTRICTED — player probability not identified**

This result is a methodological stop on empirical evidence-to-action guidance,
not a failure of the model-free Challenge Threshold definition.

## What validated

Two fixed benchmark models were evaluated with expanding monthly rolling-origin
folds. Every test prediction used only strictly earlier dates.

| Benchmark | Evaluation rows | AUC | Brier | Calibration slope | Intercept | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact public tracking | 300,775 | 0.9261 | 0.0457 | 1.014 | -0.006 | 0.0009 |
| Challenger-selected | 9,199 | 0.5869 | 0.2426 | 0.783 | 0.009 | 0.0150 |

Both cleared the aggregate calibration alerts. The feature gate rejected the
signed-distance canary, all required group tables were produced, the 312,228
legal-decision and 9,485 challenge populations reconciled, and two clean builds
were byte-identical.

## What did not validate

Neither benchmark identifies the probability in a player's head:

- exact unsigned tracking distance is not directly observed by the player;
- actual challengers select using private information, so their success model
  cannot be transported to unchallenged decisions without an assumption;
- Article 3 predicts recognition conditional on a known wrong offensive call,
  not the probability that a new call is wrong; and
- no defense player-perception model has been validated.

The selection gap is material. Among 9,199 out-of-time challenged pitches,
observed success was 53.74%, while the exact public-tracking model assigned a
mean incorrect-call probability of 24.92%. This is descriptive evidence that
challengers select on omitted/private evidence, not a causal estimate of player
skill.

The challenger-selected benchmark also triggered calibration alerts in several
otherwise supported situational groups: counts 1-0, 2-1, and 3-2, plus innings
1-3 and 7-9. Pitchers, counts 0-2/2-0/3-0/3-1, and extra innings lacked the
preregistered subgroup support. These groups cannot support situational advice.

## Consequence for Article 5

- Empirical statements of the form “when the evidence looks like X, challenge”
  remain prohibited.
- Defense receives model-free thresholds only.
- Model-free threshold surfaces may proceed.
- Dynamic-policy work may use public-tracking, challenger-selected, or assumed
  probabilities only as clearly named sensitivities—not as estimates of what a
  player knew.
- A Pascal ABS Challenge Playbook remains blocked.

## Determinism and artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `7469815bac7824f389195c1920117e0e074fb30f862703f8734efca003e2054e` |
| `calibration.csv` | `468c01f05acb767d9ea8a0579214521bdeae3f7ae2341cff8285494ba3ed17c6` |
| `calibration_curves.csv` | `0c614c55e574a4662062a6a2ef4d1f5ceee59c7ef503057cd7817fdab46bd9d8` |
| `manifest.json` | `efd0232e4ede1e6a5014c373727d22ce09765468e32392a753e15b55c47efa65` |
| `public_rolling_predictions.csv` | `e2b75ec695d0607974188a0d179880fcafd69b6feeddf88a19a22e69807f90f6` |
| `selected_rolling_predictions.csv` | `bc06790b0f106c00009398cefe78d2ebc215639ba977664c25c1a6cdc781c83b` |
| `validation.json` | `907b2e417abf8050676a12a798b54d55ae16a370c5feffe7335dbf03871118d4` |

## Resource use

The build used only the locked local snapshot. It consumed no live data, paid
API, GitHub Actions, Vercel, Supabase, or Odds API resources. No additional
Claude review was used; the Article 5 specialist/correction budget remains
exhausted after G5.
