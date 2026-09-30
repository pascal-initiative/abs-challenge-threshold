# ABS-05 Claim Ledger

CTS11 completed the successor claim review after the analytical package
reproduced byte-for-byte. Restricted CT-S1 numerical drafting is now permitted
only through `CT_S1_PUBLIC_CLAIMS.json`; this does not upgrade a failed or
unidentified scientific claim.

| Claim ID | Proposed statement | Type | Denominator | Artifact / field | Uncertainty | Required gate | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Mathematical threshold definition | Assumed/model definition | Not applicable | Preregistration equations; G7 empirical-sequence engine | `deltaW=0` by construction in G7 | G0, G7 | Computationally validated only for the restricted empirical-sequence formulation |
| C02 | Typical threshold level | Modeled | All legal called pitches in stated state | G5 value component; G7 `threshold_summary.csv`; G8 `scenario_stability.csv`; G8 objective follow-up | Probability benchmarks/assumptions; win-probability model rejected; fixed subsequent game path | G1–G8 | G8 failed; no typical empirical threshold approved. Model-free or explicitly assumption-labeled reference thresholds remain permitted under the preregistration. |
| C03 | Count changes the threshold | Modeled | Declared state comparison | G8 `scenario_stability.csv` | Thirteen audit-band crossings across sensitivities | G5–G8 | Direction may be described only within named assumptions; situational guidance prohibited |
| C04 | Inning/inventory changes option value | Modeled | Declared state comparison | G7 `game_values.csv`; `threshold_summary.csv`; G8 objective follow-up | Probability scenario; rejected cross-phase win model; fixed-path sensitivity | G7–G8 | Engine supports run-scale modeled sensitivity only; player guidance prohibited |
| C05 | Dynamic policy improves on simple rules | Modeled | 4,390 team-games / 2,195 game clusters | G9 `effect_size.csv`; `shuffle_diagnostic.json` | Exact future-sequence knowledge; shuffled-label advantage; player probability unidentified; rejected win scale; fixed game path | G9 | Numerical upper benchmark passed (+0.909617, 95% CI 0.894625–0.924834); deployable policy improvement not demonstrated |
| C06 | Observed MLB behavior resembles the framework | Measured plus modeled comparison | Explicit observed opportunity population | G6 benchmark artifacts | Rolling-origin calibration; selection limitation | G3, G6–G8 | Restricted: descriptive benchmark comparison only |
| C07 | Practical Pascal ABS Challenge Playbook | Policy translation | Validated scenario domain only | G8 validation and objective follow-up | Stability failed; win model rejected; coupled response unmodeled | All gates | Prohibited by G8 |
| C08 | CT-2026 reference evaluator | Assumption-labeled modeled reference | Supported legal called-pitch state grid | `CT2026_SPEC.md`; `CT2026_FIXED_POLICY_RESULTS.md`; local CT build artifacts | Fixed 0.60 and future EV-at-least-0.05 conventions; state-conditioned fixed-path option value; material model sensitivity; `deltaW=0` | CT1-CT10 | CT6 failed: 97.0523% of candidate rows exceeded the 0.10 core-range materiality threshold versus the 25% limit. Numerical publication values and evaluator claims remain prohibited. |
| C09 | Challenge Threshold Standard 1 (`CT-S1`) | Versioned modeled reference | 22,584 matched supported state/inventory rows in development and untouched 2026-09-11 through 2026-09-27 confirmation window; 24,880 confirmation candidates; 22,428 complete-spread rows per period; 20,197 mechanically generated contrasts; 45,168 period/state sampling intervals | `CT_S1_PUBLIC_CLAIMS.json`; `CT_S1_CTS4_CTS8_RESULTS.md`; `CT_S1_CTS7_RESULTS.md`; `CT_S1_CTS9_RESULTS.md`; `CT_S1_CTS10_RESULTS.md`; `CT_S1_CTS11_RESULTS.md`; local temporal, contrast, uncertainty, reproducibility, and claim-audit artifacts | Named reference convention; explicit eight-convention model spread; temporal drift; conditional 2,000-replicate per-state game-clustered sampling intervals; no paired interval for the contrast difference; `deltaW=0`; player belief unidentified; 156 supported incomplete-spread rows per period suppressed or labeled | CTS0-CTS11 | CTS11 passed. Restricted numerical drafting of the reference evaluator and the one eligible ordinary contrast is authorized. A playbook, optimal-policy claim, universal count rule, player grade, and `CT-2026` relabeling remain prohibited. |

## Prohibited interpretations

- “Players made mistakes” from outcomes alone.
- “Unused challenges were wasted.”
- “A failed challenge was a bad decision.”
- “The model knows what the player saw.”
- Causal or psychological explanations for inventory associations.
- A defense evidence model unless it separately passes G6.
