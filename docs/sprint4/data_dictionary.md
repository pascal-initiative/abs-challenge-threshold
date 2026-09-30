# Sprint 4 data dictionary

All probabilities and rates are on [0,1]; effects and uncertainty bounds are recognition-probability differences from the accepted opportunity baseline. `expected_recognized` is the sum of opportunity probabilities. `adjusted_effect` is the average probability change after adding the posterior batter log-odds effect. `recognized_above_expected` is a count residual and is not the adjusted estimate.

`support_classification` is one of `ALL_OBSERVED_BATTERS`, `PUBLICATION_ELIGIBLE`, or `RANKING_ELIGIBLE`. Low-support batters remain in the complete table. `rank_interpretation` and `interval_overlaps_previous` prevent unsupported adjacent-rank claims. Temporal predictions include the actual prior-opportunity count and applied historical effect. Boundary rows use the inclusive rule `abs_distance_inches <= threshold` for exclusion. JSON files mirror their same-named CSV tables.
