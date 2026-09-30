# Sprint 4 completion report

Sprint 3 snapshot/hash: 58abbfabb9318692e14199dcd6099fe847ae6497ef27e84e22cea45f9b5561d0 (VERIFIED)
Population: 10755 opportunities; 2112 recognized; 8643 not recognized
Batters observed: 602
Publication-eligible batters: 243
Ranking-eligible batters: 123

Baseline log loss: 0.430328
Batter-model log loss: 0.417568
Difference: -0.012760

Baseline Brier: 0.135983
Batter-model Brier: 0.131420
Difference: -0.004563

Baseline ROC AUC: 0.753994
Batter-model ROC AUC: 0.772862
Difference: +0.018869

Split-half supported batters: 168
Split-half Spearman: 0.473988 (95% bootstrap 0.332983, 0.591821)
Other stability results: Pearson 0.560523; directional consistency 0.636905

Primary minimum opportunity threshold: publication 20; ranking 30; prospective history 20
Sensitivity range: 10–50 opportunities
Minimum ranking correlation: 0.941379

Boundary sensitivity result: minimum nonzero-band rank correlation 0.941379; future improvement survived all approved bands

Leaderboard gate: PROCEED
Bottom-ranking gate: SUPPORTED_WITH_CAUTION
Case-study gate: PROCEED
Article 3 gate: READY_FOR_PUBLICATION_VALIDATION

Tests: see test run reported with the delivery
Artifact hashes: artifacts/sprint4/artifact_hashes.sha256 and artifacts/sprint4/run_manifest.json

## Substantive finding (≤150 words)

Historical batter recognition behavior improved future prediction beyond the accepted geometry and situation model in the final temporal holdout. Shrinkage-adjusted effects were moderately repeatable across ordered season halves; rank ordering was robust to support, boundary, and regularization choices. The 50-opportunity split-half check was inconclusive because only six batters had balanced support. Opportunity adjustment materially changed some standings, confirming that raw challenge rate is not a defensible skill ranking. The evidence supports sending an uncertainty-forward leaderboard to publication validation, not publishing it directly. Adjacent ranks often overlap and should not be described as meaningfully distinct. Bottom rankings warrant extra caution. These results establish repeatable individual differences in observed behavior; they do not establish innate skill, eyesight, plate discipline, experience, coaching, confidence, cognitive ability, or another causal mechanism.
