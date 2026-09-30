# Sprint 2 data dictionary

The feature table preserves the named Sprint 1 fields documented in `data_dictionary.md`. New fields are listed below. Blank cells are null; the population gate rejects missing required model inputs.

| Field | Definition | Unit/type | Status |
|---|---|---|---|
| recognized | One when the eligible incorrect called strike was challenged by the batter; zero otherwise. | binary | derived |
| abs_distance | Absolute Sprint 1 signed boundary distance. | feet | derived |
| abs_distance_inches | `abs_distance * 12`. | inches | derived |
| miss_axis | HORIZONTAL, VERTICAL, or CORNER from center-to-rectangle excess. | category | derived |
| miss_side | Handedness-aware INSIDE/OUTSIDE, ABOVE/BELOW, or combined corner label. | category | derived |
| horizontal_distance | Ball-center horizontal excess beyond the 17-inch rectangle. | feet | derived |
| horizontal_distance_inches | Horizontal distance converted to inches. | inches | derived |
| vertical_distance | Ball-center vertical excess beyond the batter's ABS bounds. | feet | derived |
| vertical_distance_inches | Vertical distance converted to inches. | inches | derived |
| corner_proximity | Euclidean center-to-corner excess when both axes exceed the rectangle; otherwise zero. | feet | derived |
| corner_proximity_inches | Corner proximity converted to inches. | inches | derived |
| pitch_family | Fixed mapping of source pitch code into nine documented families. | category | derived |
| spin_axis_sin / spin_axis_cos | Circular encoding of source spin axis. | scalar | derived |
| count | Pre-pitch balls-strikes. | category | derived |
| base_state | 1B/2B/3B occupancy bits. | category | derived |
| two_strike_count | YES when pre-pitch strikes equals two. | category | derived |
| strike_three_call | YES when this incorrect called strike was made with two strikes. | category | derived |
| inning_group | EARLY (1–3), MIDDLE (4–6), or LATE (7+). | category | derived |
| offense_score_diff | Batting-team runs minus fielding-team runs, derived from the preserved home-minus-away score difference and half inning. | runs | derived |
| score_state | AHEAD/TIED/BEHIND from batting-team `offense_score_diff`. | category | derived |
| date_scope | Fixed pilot range. | text | derived |
| feature_version | Versioned transformation identifier. | text | derived |

Model metrics use fractions on [0,1]. AIC/BIC and parameter count are null where penalization makes classical likelihood criteria inappropriate. Calibration intercept is ideally zero and slope ideally one. Prediction rows contain one averaged repeated out-of-fold probability per pitch/model. The descriptive `display_rate` is text and is suppressed below 20 observations; unsuppressed numerical rates and Wilson intervals remain available for audit.

`artifacts/sprint2/model_coefficients.csv` distinguishes `UNPENALIZED_RAW_SCALE` from `L2_C_1_STANDARDIZED_FULL_SAMPLE`. Classical standard errors, intervals, and exploratory p-values exist only for the former. `secondary_analyses.json` stores pitch-family summaries, identity support, fixed identity-signal labels, and average marginal predictions. `run_manifest.json` stores scope, seed, cross-validation design, all Sprint 1 input hashes, and all Sprint 2 output hashes.
