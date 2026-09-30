# Sprint 3: 2026 Season-to-Date Offensive Recognition

## 1. Dataset

The accepted snapshot covers **2026-03-25 through 2026-09-09** and is correctly described as 2026 season-to-date. It contains **2,195** completed regular-season games, **645,793** physical pitches, **336,095** called pitches, and **9,485** official ABS challenges. All challenges matched; fixed Sprint 1 geometry agreed on **9,482/9,485 (99.968%)**, above the 99% gate. The modeled universe contains **11,704** incorrect called strikes and **10,755** legal offensive opportunities.

The official ABS dashboard was complete through September 9 at execution. September 10 schedule/feed bytes are archived but excluded because its daily challenge total was not available. The pilot overlap has no changed keys, geometry, calls, inventory, classifications, or recognition opportunities. Twenty-two non-opportunity pitches changed Statcast taxonomy from curveball to sweeper; the overlap audit records this nonmaterial revision.

## 2. Baseline recognition

Batters recognized and challenged **2,112** eligible errors and did not challenge **8,643**, a rate of **19.64%**. The Sprint 2 pilot rate was **19.83%** (96/484), a descriptive difference of -0.20 percentage points. The samples overlap, so this is not treated as an independent test of change.

## 3. Geometry

Boundary distance retained a positive association with recognition (log-odds coefficient **0.460 per inch**, p=1.06e-65). Model A achieved temporal ROC AUC **0.634**, PR AUC **0.302**, and log loss **0.480**. The confirmatory distance finding replicates; direction-specific results remain descriptive.

## 4. Pitch characteristics

Adding pitch family, velocity, movement, spin, extension, release position, and handedness changed temporal log loss by **+0.0029** and ROC AUC by **-0.0021**. Performance did not improve, so the Sprint 2 pitch-block null replicates. Pitch-family and shape tables remain exploratory.

## 5. Situation

Adding count, outs, runners, inning, score differential, and challenge inventory improved temporal log loss by **-0.0409** and ROC AUC by **+0.1046**. Model C reached ROC AUC **0.737** and PR AUC **0.429**. The Sprint 2 situation finding replicates.

## 6. Batter effects

The batter block improved temporal log loss by **-0.0130** and Brier score by **-0.0045**, with enough supported batters to pass the preregistered gate. `batter_adjusted_recognition.csv` reports shrinkage-adjusted estimates and uncertainty. Ranking eligibility requires 30+ opportunities. These are observational associations, not direct measurements of perception or intent.

## 7. Catcher effects

The catcher block changed temporal log loss by **+0.0058** and failed the held-out gate. The Sprint 2 null replicates. No catcher ranking is published, and the result does not measure traditional framing or deception.

## 8. Pitcher effects

Pitcher identity changed temporal log loss by **+0.0107** and failed the gate. No pitcher ranking is published, and no residual mechanism is inferred.

## 9. Umpire effects

Umpire identity changed temporal log loss by **+0.0088** and failed the gate. No visibility ranking is published. This question remains distinct from umpire accuracy.

## 10. Timing

Raw recognition was **16.39%** in innings 1–3, **18.57%** in innings 4–6, and **24.38%** in innings 7+. Model C adjusts inning alongside the other situation features. These patterns do not establish optimality or learning.

## 11. Challenge inventory

Recognition was **19.77%** with two challenges remaining and **19.32%** with one. Zero-challenge pitches are excluded from recognition modeling and retained separately.

## 12. Resource-constrained errors

There were **789** incorrect called strikes after offensive challenge exhaustion. The separate table also covers incorrect called balls after defensive exhaustion by inning, count, outs, base state, score, and affected team. It does not evaluate earlier challenge quality.

## 13. Sprint 2 replication

- **Boundary distance:** REPLICATES (beta=0.4603; p=1.061e-65).
- **Pitch block:** REPLICATES (dLogLoss=0.002861; dAUC=-0.002126).
- **Situation block:** REPLICATES (dLogLoss=-0.04092; dAUC=0.1046).
- **Batter effect:** SUPPORTED (supported).
- **Pitcher effect:** NOT_SUPPORTED (not supported).
- **Catcher effect:** NOT_SUPPORTED (not supported).
- **Umpire effect:** NOT_SUPPORTED (not supported).

## 14. Limitations

This is an observational, season-to-date study. Statcast locations and classifications contain measurement error and can be revised. Identity support remains unequal despite shrinkage; repeated player and game observations create dependence not fully represented by simple coefficient summaries. Unmeasured communication, prior pitches, health, and context may confound associations. Regularization and temporal-boundary sensitivities are reported, but no finite sensitivity set rules out specification dependence. A challenge is an observed action, not direct evidence of what a batter saw or intended.

## 15. Conclusions

### Supported findings

- Larger boundary misses are recognized more often.
- Situation adds substantial temporal held-out information.
- Batter identity adds held-out information and has support for adjusted research rankings.

### Inconclusive findings

- Specific pitch-family, movement, timing, and team mechanisms remain exploratory.
- Adjusted batter differences do not identify perception or intent causally.

### Null findings

- The pitch block does not improve on geometry.
- Pitcher, catcher, and umpire identity do not add validated held-out value.

### Future questions and decision gates

- **A_batter_recognition_skill: PROCEED.**
- **B_catcher_recognition_suppression: DO_NOT_PROCEED.**
- **C_pitcher_pitch_perception: DO_NOT_PROCEED.**
- **D_umpire_error_visibility: DO_NOT_PROCEED.**
- **E_challenge_resource_management: PROCEED.**
- **F_defensive_recognition: PROCEED.**
