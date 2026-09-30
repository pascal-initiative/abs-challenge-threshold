# PV-1 Methodology

PV-1 consumes the accepted 2026-03-25 through 2026-09-09 Sprint 1–5 snapshot without changing it. Phase 1 verifies the 9,485 official challenges, 9,482 agreements, three disagreements, and the 11,704 → 10,755 → 2,112 recognition population. SHA-256 hashes in the run manifest prove the accepted files were unchanged.

The reconstructed ABS classifier is the accepted `abs_2026_circle_rectangle_r1.45in_v1` method. Signed distance is in feet; absolute distances are converted to inches. Validation bins were preregistered as [0,.05), [.05,.10), [.10,.25), [.25,.50), [.50,1), and [1,+∞). Sensitivity excludes every pitch with `abs_distance_inches <= threshold`, so exact-threshold observations belong to the uncertainty band. Thresholds were 0, .05, .10, .25, and .50 inches.

At each threshold, the recognition population and a univariate logistic association with absolute distance were recomputed. Accepted A geometry, B geometry-plus-pitch, and C geometry-plus-pitch-plus-situation models were rerun using expanding monthly holdouts, fixed L2 C=1 logistic regression, and the accepted features. Metrics are pooled ROC AUC, PR AUC, log loss, and Brier score. No alternate model search was conducted.

Representative pitches were selected deterministically after inference and are illustrations only. The novelty review was completed through 2026-09-10 against official, academic, independent, newsletter, tool, and open-source work. Novelty classifications are conservative and require Pascal research-lead acceptance.
