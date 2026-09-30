# Sprint 5 data dictionary

All state inputs use PRE_PITCH timing. Empty values are allowed only where the upstream source or event concept is inapplicable.

## `challenge_opportunities.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_date` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_pk` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `physical_pitch_ordinal` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `at_bat_index` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `play_event_index` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inning` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `half_inning` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `balls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `strikes` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `outs` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `base_state` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `on_1b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `on_2b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `on_3b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `home_score` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `away_score` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `score_diff` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `batter_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `batter_name` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `pitcher_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `pitcher_name` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `catcher_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `catcher_name` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `umpire_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `umpire_name` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_side` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `original_call` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `derived_abs_call` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `challenge_available` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `affected_team_challenges_remaining` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `actual_action` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `challenge_outcome` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `plate_x` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `plate_z` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `abs_zone_top` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `abs_zone_bot` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `distance_from_abs_boundary` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `wrong_way_margin_inches` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `pitch_type` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `release_speed` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `pfx_x` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `pfx_z` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `geometry_incorrect` | int64 | boolean | original call differs from derived ABS call | hindsight description only | no |

## `challenge_decision_states.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_date` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_pk` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_side` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_inning` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_half_inning` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_balls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_strikes` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_outs` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_on_1b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_on_2b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_on_3b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_home_score` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_away_score` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_base_state` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_runs_scored` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_plate_appearance_status` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `hold_inning_ended` | bool | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_inning` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_half_inning` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_balls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_strikes` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_outs` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_on_1b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_on_2b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_on_3b` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_home_score` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_away_score` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_base_state` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_runs_scored` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_plate_appearance_status` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `overturn_inning_ended` | bool | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |

## `challenge_value_estimates.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `P_overturn` | float64 | probability | selection-weighted pre-decision model | normative success probability | no |
| `P_overturn_geometry_sensitivity` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `RE_hold_batting` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `RE_overturn_batting` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `delta_RE_raw` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `delta_RE` | float64 | runs | challenger-oriented HOLD/OVERTURN RE difference | immediate run leverage | no |
| `WP_hold` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `WP_overturn` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `delta_WP_raw` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `delta_WP` | float64 | probability | challenger-oriented HOLD/OVERTURN WP difference | immediate win leverage | no |
| `challenge_leverage` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `immediate_expected_value` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `expected_future_opportunities` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `future_value_with_inventory` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `future_value_after_failed_challenge` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `future_challenge_value` | float64 | probability | Bellman V(k)-V(k-1) | failure resource cost | no |
| `EV_hold` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `EV_challenge` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `EV_difference` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `required_confidence` | float64 | probability | resource/(immediate upside+resource) | break-even confidence | no |
| `decision_margin` | float64 | probability | EV actual minus EV alternative | ex-ante decision strength | no |
| `model_version` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `analysis_perspective` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |

## `decision_quality.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_date` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_pk` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_side` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `actual_action` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `challenge_outcome` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | yes |
| `recommended_action` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_correct` | bool | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_quality_category` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `EV_difference` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_margin` | float64 | probability | EV actual minus EV alternative | ex-ante decision strength | no |
| `required_confidence` | float64 | probability | resource/(immediate upside+resource) | break-even confidence | no |
| `P_overturn` | float64 | probability | selection-weighted pre-decision model | normative success probability | no |
| `geometry_incorrect` | int64 | boolean | original call differs from derived ABS call | hindsight description only | no |
| `analysis_perspective` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `model_version` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |

## `challenge_inventory_history.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_date` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_pk` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `physical_pitch_ordinal` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_side` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inning` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `half_inning` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `outs` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `balls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `strikes` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inventory_before` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inventory_after` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `challenge_outcome` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inventory_event` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |

## `exhaustion_events.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_date` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_pk` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `physical_pitch_ordinal` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_side` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inning` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `half_inning` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `balls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `strikes` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `outs` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inventory_before` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inventory_after` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `challenge_outcome` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `immediate_expected_value` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `future_challenge_value` | float64 | probability | Bellman V(k)-V(k-1) | failure resource cost | no |
| `EV_difference` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_margin` | float64 | probability | EV actual minus EV alternative | ex-ante decision strength | no |
| `decision_quality_category` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `recommended_action` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `delta_RE` | float64 | runs | challenger-oriented HOLD/OVERTURN RE difference | immediate run leverage | no |
| `delta_WP` | float64 | probability | challenger-oriented HOLD/OVERTURN WP difference | immediate win leverage | no |
| `analysis_perspective` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |

## `post_exhaustion_opportunities.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `exhaustion_pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `exhaustion_order` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `pitch_key` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_date` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `game_pk` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `physical_pitch_ordinal` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team_id` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_team` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `decision_side` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `inning` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `half_inning` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `balls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `strikes` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `outs` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `base_state` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `original_call` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `derived_abs_call` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `call_correct` | bool | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `geometry_incorrect` | int64 | boolean | original call differs from derived ABS call | hindsight description only | no |
| `P_overturn` | float64 | probability | selection-weighted pre-decision model | normative success probability | no |
| `delta_RE` | float64 | runs | challenger-oriented HOLD/OVERTURN RE difference | immediate run leverage | no |
| `delta_WP` | float64 | probability | challenger-oriented HOLD/OVERTURN WP difference | immediate win leverage | no |
| `recommended_action` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `required_confidence` | float64 | probability | resource/(immediate upside+resource) | break-even confidence | no |
| `realized_run_value_lost` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `realized_wp_value_lost` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `analysis_perspective` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |

## `resource_cost_summary.csv`

| Field | Type | Unit | Source / derivation | Analytical purpose | Nullable |
|---|---|---|---|---|---|
| `dimension` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `group` | object | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `incorrect_calls` | int64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `run_value_lost` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `wp_value_lost` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `mean_wp_loss` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `median_wp_loss` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `p90_wp_loss` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
| `maximum_wp_loss` | float64 | identifier/value | upstream pitch state or documented Sprint 5 transformation | reconstruction, grouping, or audit | no |
