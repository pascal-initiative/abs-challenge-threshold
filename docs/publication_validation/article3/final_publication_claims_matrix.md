# Article 3 Final Publication Claims Matrix

This matrix governs Article 3 wording. The machine-readable CSV and JSON are authoritative mirrors.

## 1. Historical batter recognition behavior contains information about future recognition beyond measured opportunity characteristics.

- Status: **SUPPORTED**
- Sprint 4 evidence: Final temporal holdout: log loss -0.012760, Brier -0.004563, ROC AUC +0.018869 versus the accepted opportunity model.
- Publication-safe wording: Historical batter recognition behavior contained information about future recognition beyond the measured characteristics of the opportunity.
- Limitations: One season; predictive, not causal; recognition is challenge action; unmeasured context may remain.
- Prohibited wording: Batter identity proves who sees the strike zone best.

## 2. Some batters differed in adjusted recognition behavior.

- Status: **SUPPORTED_WITH_QUALIFICATION**
- Sprint 4 evidence: Empirical-Bayes batter effects remained after accepted opportunity adjustment; 123 batters met ranking support.
- Publication-safe wording: The adjusted estimates show meaningful batter-to-batter differences in observed recognition behavior, with substantial uncertainty around many players.
- Limitations: Effects combine perception, decision, timing, instruction, and other unmeasured influences.
- Prohibited wording: The leaderboard identifies the batters with the best eyes.

## 3. Adjusted recognition showed temporal repeatability within the season.

- Status: **SUPPORTED_WITH_QUALIFICATION**
- Sprint 4 evidence: 168 supported batters; split-half Spearman 0.474 (95% interval 0.333 to 0.592), Pearson 0.561 (0.417 to 0.669).
- Publication-safe wording: Adjusted recognition showed moderate within-season repeatability.
- Limitations: Ordered halves are not separate seasons; repeatability is not permanence or determinism.
- Prohibited wording: Recognition is a stable, permanent trait.

## 4. Raw recognition rate is not equivalent to adjusted recognition.

- Status: **SUPPORTED**
- Sprint 4 evidence: Forty-six ranking-eligible batters moved at least 10 places after opportunity adjustment.
- Publication-safe wording: Raw recognition rate and adjusted recognition answer different questions; opportunity difficulty materially changed some players' standings.
- Limitations: The adjusted model is an estimate, not ground truth.
- Prohibited wording: The adjusted ranks reveal the true ordering.

## 5. The batter-history signal was concentrated in moderate misses rather than obvious misses.

- Status: **SUPPORTED_AS_SENSITIVITY_RESULT**
- Sprint 4 evidence: Moderate misses: log loss -0.011886, Brier -0.004278, ROC AUC +0.019507. Obvious misses: no improvement and only seven supported batters.
- Publication-safe wording: In the prespecified difficulty sensitivity, the predictive gain appeared in moderate misses; the obvious-miss subgroup was too thin to support a strong comparative conclusion.
- Limitations: Subgroup evidence is secondary; obvious-miss support is sparse; no mechanism is identified.
- Prohibited wording: Batters differ only on moderate misses, or moderate misses cause the batter effect.

## 6. An adjusted batter-recognition leaderboard may be published.

- Status: **SUPPORTED_WITH_EDITORIAL_CONTROLS**
- Sprint 4 evidence: Ranking threshold 30 opportunities; empirical-Bayes shrinkage; intervals; boundary rank correlation at least 0.941.
- Publication-safe wording: These are shrinkage-adjusted estimates among batters with at least 30 opportunities; adjacent point ranks are often statistically indistinguishable.
- Limitations: Single-season estimates; most adjacent intervals overlap; rank numbers are display order, not proof of separation.
- Prohibited wording: No. 10 is meaningfully better than No. 11 because the point estimate is higher.

## 7. Recognition is a skill.

- Status: **NOT_SUPPORTED_WITHOUT_QUALIFICATION**
- Sprint 4 evidence: Held-out predictive gain and moderate split-half repeatability support a repeatable component of behavior.
- Publication-safe wording: The results are consistent with a repeatable batter-specific component of recognition behavior.
- Limitations: Observed challenge action is not a direct test of perception or innate ability.
- Prohibited wording: ABS recognition is a proven innate skill.

## 8. Recognition is persistent across seasons.

- Status: **NOT_SUPPORTED**
- Sprint 4 evidence: No multi-season test was conducted.
- Publication-safe wording: Whether the differences persist across seasons remains unknown.
- Limitations: Only within-season ordered halves and one future holdout are available.
- Prohibited wording: The best recognizers will remain the best in future seasons.

## 9. Batter vision, experience, plate discipline, coaching, confidence, cognition, or innate ability causes the effect.

- Status: **NOT_SUPPORTED**
- Sprint 4 evidence: Sprint 4 did not test causal mechanisms.
- Publication-safe wording: The analysis does not identify why batter histories differ.
- Limitations: Identity effects can proxy multiple measured and unmeasured processes.
- Prohibited wording: The effect is caused by superior eyesight, discipline, experience, coaching, confidence, or intelligence.
