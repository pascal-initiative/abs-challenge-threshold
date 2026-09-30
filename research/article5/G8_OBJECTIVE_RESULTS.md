# ABS-05 G8 Objective-Scale Follow-up Result

**Computational status: PASS**
**Win-probability sensitivity: FAIL VALIDATION**
**Opponent policy accounting: PASS WITHIN SEPARABLE G7 MODEL ONLY**
**Original G8 stability gate: FAILED, UNCHANGED**
**Playbook status: PROHIBITED**

This post-failure follow-up was authorized by Amendment 002 to investigate two
missing G8 sensitivities. It did not change the reference, denominator, flip
limit, or original result.

## Win-probability model

All 2,195 games had a unique final winner. The model used 645,793 pre-pitch
states, gave every game equal total fitting weight, and used only inning/half
phase plus home score advantage adjusted by G5 constrained run expectancy.
Monthly rolling-origin predictions always trained on strictly earlier dates.

| Evaluation | Rows | Brier | Baseline Brier | AUC | ECE | Calibration intercept | Calibration slope |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall | 623,257 | 0.159645 | 0.249914 | 0.8450 | 0.0175 | -0.0969 | 0.9692 |
| Late and close | 65,625 | 0.201415 | 0.250494 | 0.7585 | 0.0434 | -0.2119 | 0.9220 |

The predictive and aggregate calibration conditions passed. Counterfactual
coherence did not.

Across 334,948 future-stream calls, 5,310 corrections (1.585%) received a
negative value for the team entitled to challenge, exceeding the frozen 0.1%
limit. The fixed G8 top-value population contained 591 negative values, where
the requirement was zero. All 5,310 wrong-sign cases crossed from one
inning/half phase to another; no within-phase correction had the wrong sign.

The failure is methodological rather than a call-orientation bug. Separately
estimated phase intercepts can fit observed win frequency while contradicting a
hypothetical inning-ending transition. The model is therefore rejected for
decision valuation.

For diagnostic purposes only, substituting its values changed 7,772 of 31,443
top-value actions (24.72%) with one unit and 7,017 (22.32%) with two. Both exceed
the original 10% stability limit, but they are not treated as accepted
sensitivity estimates because the model failed first.

## Opponent-policy accounting

Under G7, team opportunity streams are independent and a correction does not
rewrite the observed path. The opponent's value is therefore the same additive
term under focal CHALLENGE and HOLD and cancels from their difference.

Ten thousand deterministic comparisons found zero action changes for both
league-typical and optimized opponent values; maximum numerical difference was
`8.88e-16`. This validates accounting only within the separable G7 construction.
It does not model opponent response or strategic interaction and does not
resolve `deltaW=0`.

## Consequence

G8 is now complete as a failed gate rather than incomplete for lack of an
attempted objective sensitivity. A valid win-probability decision model would
require counterfactually coherent transitions across half-innings and likely a
coupled game-state simulation. Building that would be a new research phase, not
a correction to this gate.

Model-free exposition may continue. Situational recommendations, an optimal MLB
policy claim, and the Pascal ABS Challenge Playbook remain prohibited.

## Determinism and artifact hashes

Two clean builds were byte-identical.

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `a1bb1f052af9f14fbe5294fe44c8113a6baaa0f63c5864000cf017a088085c57` |
| `calibration.csv` | `ef348775e04d578286eef7293727dc898f9785ac07623f4f3b04a55e24af5a55` |
| `manifest.json` | `e3020e272f22797f4f6031988e309807202392481be88692f8b207533b177f3a` |
| `opponent_invariance.json` | `af09c3b9c0713397f3500e576adcd34abb182c4f2f214ba832b11ee6485a77ed` |
| `rolling_predictions.csv` | `22912cb431d807399f735c40567cf27119a09617c53d463a31457faa066058a7` |
| `top_value_wp_actions.csv` | `a669335d1e3ecfe834f65671ef44c03580bea13781d266011ae4576ad018d1c3` |
| `validation.json` | `bed0009e9d95aacee0bcdf9d21c057b258ae4911eb0bbcb0418a7bb02a84e463` |
| `wp_correction_values.csv` | `71259979f0dd0e5c6b7673c67a7eed8fd30cafffeb6e49db643ddfca16986724` |

## Resources

The build used only the locked local snapshot and local computation. It used no
live data, paid API, GitHub Actions, Vercel, Supabase, Odds API, or additional
Claude review. No acceptance condition was skipped.
