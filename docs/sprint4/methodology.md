# Sprint 4 methodology

Sprint 4 consumes only the hash-verified accepted Sprint 3 feature population. The exact frozen hashes and every declared Sprint 3 output are checked before analysis. The outcome, geometry, feature blocks, exclusions, and temporal ordering are unchanged.

The accepted Model C opportunity specification is fit without batter identity. Batter history is a Normal(0, tau²) log-odds random effect estimated by empirical Bayes from prior-period residual recognition only. Tau uses maximum marginal likelihood with 31-point Gauss-Hermite quadrature; posterior summaries use a fixed 401-point grid. Full-season adjusted estimates are descriptive. Prospective claims use validation and final holdout partitions only.

Primary support thresholds are publication n=20, ranking n=30, and temporal-history n=20. Support sensitivity spans (10, 15, 20, 25, 30, 40, 50). Boundary sensitivity uses the accepted inclusive bands (0.0, 0.05, 0.1, 0.25, 0.5) inches and excludes `abs_distance_inches <= threshold`. Difficulty groups combine existing Sprint 3 distance bins. Bootstrap correlation intervals use seed 20260910 and 2000 replicates.

The leaderboard requires final-holdout delta log loss <= -0.001, delta Brier <= -0.0005, positive AUC change, ordered-half Spearman >= 0.2, minimum rank sensitivity >= 0.85, and at least 20 ranking-supported batters. Adjacent interval overlap is retained. The bottom-ranking gate is separate and more cautious.
