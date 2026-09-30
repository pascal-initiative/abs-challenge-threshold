# Data dictionary

CSV files use UTF-8 and LF records; blank scalar cells represent null. Booleans are `True`/`False`; nested lists/objects are JSON strings. Every numeric field retains its documented source unit. Nullable indicates schema permission, not observed missingness. Runner null semantics depend on a successful Statcast match. All state and inventory fields refer to pre-pitch/pre-decision state.

## pitches.csv

| Field | Description | Source | Unit | Source/derived | Nullable |
|---|---|---|---|---|---|
| abs_zone_bot | Separate ABS lower bound copied from 2026 sz_bot; source not overwritten. | Pascal transformation; see methodology | feet | derived | yes |
| abs_zone_top | Separate ABS upper bound copied from 2026 sz_top; source not overwritten. | Pascal transformation; see methodology | feet | derived | yes |
| abs_zone_width_inches | Fixed official 17-inch zone width. | Pascal transformation; see methodology | inches | derived | yes |
| affected_team_challenges_remaining | Affected team's inventory before this pitch's challenge decision. | Pascal transformation; see methodology | count | derived | yes |
| affected_team_id | Offense for original strike, defense for original ball; null for noncalled pitches. | Pascal transformation; see methodology | identifier | derived | yes |
| at_bat_index | Zero-based MLB plate-appearance index. | MLB schedule/feed | zero-based index | source | no |
| away_score | Pre-pitch away team score. | Savant Statcast CSV | count | source | yes |
| away_team | Away team name. | MLB schedule/feed | text/code | source | no |
| away_team_id | MLB away team identifier. | MLB schedule/feed | identifier | source | no |
| balls | Pre-pitch balls (0–3). | Savant Statcast CSV | count | source | yes |
| bat_side | Batter side, R/L. | Statcast, MLB fallback | text/code | source | yes |
| batter_id | Pre-pitch batter identifier; feed matchup fallback only if Statcast match unavailable. | Savant Statcast CSV | identifier | source | yes |
| batter_name | Batter name resolved from feed player map. | MLB schedule/feed | text/code | source | yes |
| catcher_id | Pre-pitch catcher identifier from matched Statcast fielder_2; never a final-boxscore fallback. | Savant Statcast CSV | identifier | source | yes |
| catcher_name | Catcher name resolved from feed player map. | MLB schedule/feed | text/code | source | yes |
| challenge_available | Legal pre-decision availability, accounting for inventory and position-player restriction. | Pascal transformation; see methodology | boolean | derived | yes |
| challenge_outcome | Official challenge outcome on a pitch; null when not challenged. | Savant official flags / MLB; see method | text/code | derived normalization | yes |
| challenge_unavailable_reason | EXHAUSTED or POSITION_PLAYER_PITCHING; null otherwise. | Pascal transformation; see methodology | text/code | derived | yes |
| challenged | Whether the authoritative challenge table contains this pitch. | Pascal transformation; see methodology | boolean | derived | no |
| defense_challenges_remaining | Defensive team's inventory before decision. | Pascal transformation; see methodology | count | derived | yes |
| derived_abs_call | Geometry-derived BALL/STRIKE, independent of official outcome. | Pascal transformation; see methodology | text/code | derived | yes |
| displayed_call | Normalized displayed MLB feed call, potentially after review. | Pascal transformation; see methodology | text/code | derived | yes |
| distance_from_abs_boundary | Signed circle/rectangle boundary distance; <=0 strike, >0 ball. | Pascal transformation; see methodology | feet | derived | yes |
| extension | Statcast release_extension, preserved in source units. | Savant Statcast CSV | feet | source | yes |
| feed_has_review | Raw generic feed hasReview; not an ABS population flag. | MLB schedule/feed | boolean | source | yes |
| feed_pfx_x_inches | Unmodified MLB coordinates.pfxX; not mixed with Statcast feet. | MLB schedule/feed | inches | source | yes |
| feed_pfx_z_inches | Unmodified MLB coordinates.pfxZ; not mixed with Statcast feet. | MLB schedule/feed | inches | source | yes |
| feed_plate_x | Unmodified MLB coordinates.pX. | MLB schedule/feed | feet | source | yes |
| feed_plate_z | Unmodified MLB coordinates.pZ. | MLB schedule/feed | feet | source | yes |
| feed_review_details | Entire raw pitch reviewDetails object serialized as JSON. | MLB schedule/feed | JSON; nested units documented | source | yes |
| feed_sz_bot | Unmodified MLB strikeZoneBottom. | MLB schedule/feed | feet | source | yes |
| feed_sz_top | Unmodified MLB strikeZoneTop. | MLB schedule/feed | feet | source | yes |
| feed_zone_depth_inches | Unmodified MLB strikeZoneDepth (reported plane depth). | MLB schedule/feed | inches | source | yes |
| feed_zone_values | All pitchData keys containing zone, including original strike-zone values and zone code. | MLB schedule/feed | JSON; nested units documented | source | yes |
| feed_zone_width_inches | Unmodified MLB strikeZoneWidth. | MLB schedule/feed | inches | source | yes |
| game_date | Official game assignment date, not the pitch's UTC timestamp date. | MLB schedule/feed | ISO date | source | no |
| game_pk | Unique MLB game identifier. | MLB schedule/feed | identifier | source | no |
| game_type | MLB game type; R for this pilot. | MLB schedule/feed | text/code | source | no |
| half_inning | top or bottom, from MLB play metadata. | MLB schedule/feed | text/code | source | no |
| home_score | Pre-pitch home team score. | Savant Statcast CSV | count | source | yes |
| home_team | Home team name. | MLB schedule/feed | text/code | source | no |
| home_team_id | MLB home team identifier. | MLB schedule/feed | identifier | source | no |
| inning | Inning number at this pitch. | MLB schedule/feed | count | source | no |
| is_called_pitch | Called BALL/STRIKE opportunity indicator, including official challenge evidence. | Pascal transformation; see methodology | boolean | derived | no |
| offense_challenges_remaining | Offensive team's inventory before decision. | Pascal transformation; see methodology | count | derived | yes |
| official_abs_call | Official BALL/STRIKE reconstructed from Savant original flag and official overturn status. | Savant official flags / MLB; see method | text/code | derived normalization | yes |
| on_1b | Pre-pitch runner identifier on first; null means empty only when Statcast is matched. | Savant Statcast CSV | text/code | source | yes |
| on_2b | Pre-pitch runner identifier on second; null means empty only when Statcast is matched. | Savant Statcast CSV | text/code | source | yes |
| on_3b | Pre-pitch runner identifier on third; null means empty only when Statcast is matched. | Savant Statcast CSV | text/code | source | yes |
| opportunity_population | OFFENSE for an original strike, DEFENSE for an original ball; null otherwise. | Pascal transformation; see methodology | text/code | derived | yes |
| original_call | Original umpire BALL/STRIKE; Savant explicit original for challenges, displayed feed otherwise. | Savant official flags / MLB; see method | text/code | derived normalization | yes |
| original_call_source | SAVANT_ORIGINAL_ISSTRIKE_UMP or MLB_DISPLAYED_UNCHALLENGED provenance label. | Pascal transformation; see methodology | text/code | derived | no |
| outs | Pre-pitch outs (0–2). | Savant Statcast CSV | count | source | yes |
| pfx_x | Statcast horizontal movement, catcher's perspective; untransformed. | Savant Statcast CSV | feet | source | yes |
| pfx_z | Statcast vertical movement; untransformed. | Savant Statcast CSV | feet | source | yes |
| physical_pitch_ordinal | One-based physical pitch ordinal within plate appearance, excluding automatic penalties. | Pascal transformation; see methodology | one-based source ordinal | derived | no |
| pitch_hand | Pitching hand, R/L. | Statcast, MLB fallback | text/code | source | yes |
| pitch_key | Deterministic game_pk:at_bat_index:play_event_index key. | Pascal transformation; see methodology | identifier | derived | no |
| pitch_match_method | PHYSICAL_SEQUENCE or UNMATCHED; see automatic-event join rule. | Pascal transformation; see methodology | text/code | derived | no |
| pitch_name | Statcast pitch_name with MLB pitch type description fallback. | Statcast, MLB fallback | text/code | source | yes |
| pitch_number | Original MLB pitchNumber, preserved without renumbering. | MLB schedule/feed | one-based source ordinal | source | yes |
| pitch_type | Statcast pitch_type with MLB pitch type code fallback. | Statcast, MLB fallback | text/code | source | yes |
| pitcher_id | Pre-pitch pitcher identifier; feed matchup fallback only if Statcast match unavailable. | Savant Statcast CSV | identifier | source | yes |
| pitcher_name | Pitcher name resolved from feed player map. | MLB schedule/feed | text/code | source | yes |
| pitcher_primary_position | Feed player primaryPosition abbreviation, used as eligibility proxy. | MLB schedule/feed | text/code | source | yes |
| plate_x | Statcast horizontal ball-center position at mid-plate in 2026. | Savant Statcast CSV | feet | source | yes |
| plate_z | Statcast vertical ball-center position at mid-plate in 2026. | Savant Statcast CSV | feet | source | yes |
| play_event_index | Zero-based MLB play-event index within plate appearance. | MLB schedule/feed | zero-based index | source | no |
| play_id | MLB pitch UUID; official challenge matching key together with game_pk. | MLB schedule/feed | identifier | source | yes |
| position_player_pitching | True for non-P/non-TWP primary position, false for P/TWP, null if missing. | Pascal transformation; see methodology | boolean | derived | yes |
| raw_source_call | Original unmodified MLB details.call.code. | MLB schedule/feed | text/code | source | yes |
| raw_source_description | Original unmodified MLB pitch description. | MLB schedule/feed | text/code | source | yes |
| release_pos_x | Statcast horizontal release position. | Savant Statcast CSV | feet | source | yes |
| release_pos_y | Statcast release position along y-axis. | Savant Statcast CSV | feet | source | yes |
| release_pos_z | Statcast vertical release position. | Savant Statcast CSV | feet | source | yes |
| release_speed | Statcast release speed. | Savant Statcast CSV | mph | source | yes |
| release_spin_rate | Statcast release spin rate. | Savant Statcast CSV | rpm | source | yes |
| score_diff | Pre-pitch home score minus away score. | Pascal transformation; see methodology | count | derived | yes |
| season | MLB season year. | MLB schedule/feed | year | source | no |
| source_conflict | Conflicting official copies or pitch-level source evidence; preserved and release-blocking. | Pascal transformation; see methodology | boolean | derived | no |
| source_derived | Versioned geometry method identifier. | Pascal transformation; see methodology | text/code | derived | no |
| source_game_feed | SHA-256 raw feed object digest. | Pascal transformation; see methodology | text/code | derived | no |
| source_savant | Pitch: SHA-256 Statcast CSV digest. Challenge: JSON array of official Savant source digests. | Pascal transformation; see methodology | JSON; nested units documented | derived | yes |
| source_statcast_row_index | Zero-based data-row index in raw CSV, excluding header. | Pascal transformation; see methodology | zero-based index | derived | yes |
| spin_axis | Statcast spin-axis angle. | Savant Statcast CSV | degrees | source | yes |
| statcast_pitch_number | Original Statcast pitch_number, including automatic count-event numbering. | Savant Statcast CSV | one-based source ordinal | source | yes |
| state_timing | PRE_PITCH; applies to count, outs, runners, and score. | Pascal transformation; see methodology | text/code | derived | no |
| strikes | Pre-pitch strikes (0–2). | Pascal transformation; see methodology | count | derived | yes |
| survival_class | CORRECT_CALL, CORRECTED, SURVIVED_RECOGNITION, SURVIVED_RESOURCE, or UNKNOWN. | Pascal transformation; see methodology | text/code | derived | no |
| survival_detail | Reason/subtype: NOT_CHALLENGED, CHALLENGED_BUT_CONFIRMED, NOT_CALLED_PITCH, POSITION_PLAYER_PITCHING, or explicit uncertainty/conflict reason. | Pascal transformation; see methodology | text/code | derived | yes |
| sz_bot | Original 2026 Statcast lower zone bound. | Savant Statcast CSV | feet | source | yes |
| sz_top | Original 2026 Statcast upper zone bound. | Savant Statcast CSV | feet | source | yes |
| umpire_id | Home-plate umpire identifier from feed boxscore officials. | MLB schedule/feed | identifier | source | yes |
| umpire_name | Home-plate umpire full name from feed boxscore officials. | MLB schedule/feed | text/code | source | yes |
| venue | Venue name from MLB schedule. | MLB schedule/feed | text/code | source | no |

## challenges.csv

| Field | Description | Source | Unit | Source/derived | Nullable |
|---|---|---|---|---|---|
| challenge_team_id | Team of identified challenger; null if role/team cannot be determined. | Savant official flags / MLB; see method | identifier | derived normalization | yes |
| challenger_id | Savant challenging_player_id. | Savant official challenge detail | identifier | source | yes |
| challenger_name | Savant participant's full name when challenger role identified. | Savant official challenge detail | text/code | source | yes |
| challenger_role | BATTER, CATCHER, PITCHER, or UNKNOWN based on identity equality. | Savant official flags / MLB; see method | text/code | derived normalization | no |
| game_date | Official game assignment date, not the pitch's UTC timestamp date. | MLB schedule/feed | ISO date | source | no |
| game_pk | Unique MLB game identifier. | MLB schedule/feed | identifier | source | no |
| official_abs_call | Official BALL/STRIKE reconstructed from Savant original flag and official overturn status. | Savant official flags / MLB; see method | text/code | derived normalization | yes |
| original_call | Original umpire BALL/STRIKE; Savant explicit original for challenges, displayed feed otherwise. | Savant official flags / MLB; see method | text/code | derived normalization | yes |
| outcome | OVERTURNED, CONFIRMED, or UNKNOWN from official overturn flag. | Savant official flags / MLB; see method | text/code | derived normalization | no |
| overturned | Official normalized boolean; null for unknown outcome. | Savant official flags / MLB; see method | boolean | derived normalization | yes |
| pitch_key | Deterministic game_pk:at_bat_index:play_event_index key. | Pascal transformation; see methodology | identifier | derived | no |
| play_id | MLB pitch UUID; official challenge matching key together with game_pk. | MLB schedule/feed | identifier | source | yes |
| savant_abs_bot | Original official challenge strikeZoneBottom. | Savant official challenge detail | feet | source | yes |
| savant_abs_top | Original official challenge strikeZoneTop. | Savant official challenge detail | feet | source | yes |
| savant_abs_width_inches | Original official challenge widthinches. | Savant official challenge detail | inches | source | yes |
| savant_edge_dist_inches | Official challenge edge_dist_calc; retained for investigation, never used to derive calls. | Savant official challenge detail | inches | source | yes |
| savant_plate_x | Original official challenge plateX. | Savant official challenge detail | feet | source | yes |
| savant_plate_z | Original official challenge plateZ. | Savant official challenge detail | feet | source | yes |
| source_conflict | Conflicting official copies or pitch-level source evidence; preserved and release-blocking. | Pascal transformation; see methodology | boolean | derived | no |
| source_copy_count | Number of overlapping official team-detail copies collapsed after comparison. | Pascal transformation; see methodology | count | derived | no |
| source_record_indices | JSON list of raw object digest and zero-based array index for every official copy. | Pascal transformation; see methodology | JSON; nested units documented | derived | no |
| source_savant | Pitch: SHA-256 Statcast CSV digest. Challenge: JSON array of official Savant source digests. | Pascal transformation; see methodology | JSON; nested units documented | derived | yes |

## game_manifest.csv

| Field | Description | Source | Unit | Source/derived | Nullable |
|---|---|---|---|---|---|
| away_team | Away team name. | MLB schedule/feed | text/code | source | no |
| game_date | Official game assignment date, not the pitch's UTC timestamp date. | MLB schedule/feed | ISO date | source | no |
| game_pk | Unique MLB game identifier. | MLB schedule/feed | identifier | source | no |
| home_team | Home team name. | MLB schedule/feed | text/code | source | no |
| processed | Whether the game's final feed was successfully parsed. | Pascal transformation; see methodology | boolean | derived | no |
| status | MLB schedule detailedState. | MLB schedule/feed | text/code | source | no |
| venue | Venue name from MLB schedule. | MLB schedule/feed | text/code | source | no |

## recognition_breakdowns.csv

| Field | Description | Source | Unit | Source/derived | Nullable |
|---|---|---|---|---|---|
| called_pitches | Count of called physical pitches in this population/group. | Pascal transformation; see methodology | count | derived | no |
| dimension | Breakdown dimension; identity groups are not ranked. | Pascal transformation; see methodology | text/code | derived | no |
| incorrect_calls | Count of original/derived disagreements with evaluable source evidence. | Pascal transformation; see methodology | count | derived | no |
| incorrect_with_challenge_available | Count of incorrect pitches with challenge_available true. | Pascal transformation; see methodology | count | derived | no |
| name | Participant display name for identity breakdowns; null for other dimensions. | Pascal transformation; see methodology | text/code | derived | yes |
| population | ALL, OFFENSE, or DEFENSE. | Pascal transformation; see methodology | text/code | derived | no |
| rate_per_available_incorrect_call | Recognition survivors divided by available incorrect calls in group. | Pascal transformation; see methodology | fraction [0,1] | derived | yes |
| rate_per_called_pitch | Recognition survivors divided by called pitches in group. | Pascal transformation; see methodology | fraction [0,1] | derived | yes |
| rate_per_incorrect_call | Recognition survivors divided by incorrect pitches in group. | Pascal transformation; see methodology | fraction [0,1] | derived | yes |
| survived_recognition | Count of SURVIVED_RECOGNITION pitches in group. | Pascal transformation; see methodology | count | derived | no |
| value | Dimension value; participant ID, pitch type, inning, balls-strikes, outs, base occupancy bits 1B/2B/3B, or inventory count. | Pascal transformation; see methodology | text/code | derived | no |

## validation_discrepancies.csv

| Field | Description | Source | Unit | Source/derived | Nullable |
|---|---|---|---|---|---|
| game_pk | Unique MLB game identifier. | MLB schedule/feed | identifier | source | no |
| pitch_key | Deterministic game_pk:at_bat_index:play_event_index key. | Pascal transformation; see methodology | identifier | derived | no |
| discrepancy_reason | DISAGREEMENT or UNMATCHED_OR_UNCOMPARABLE for official validation records. | Pascal transformation; see methodology | text/code | derived | yes |

## Interim tables

`interim/pitches.csv` has the same pitch fields except survival_class and survival_detail. `official_challenge_comparisons.csv` combines challenge fields, original Statcast location/zone values, participant IDs, raw_source_call, derived_abs_call, distance_from_abs_boundary, comparable, and agrees. `source_discrepancies.json` preserves typed issues (`kind`), pitch/game keys, original source rows, and source-number adjustments. No audit records are deleted.

## JSON reports

Report counts are derived integers; rates are derived fractions, nullable when their denominator is zero. Report labels and method identifiers are non-null strings. Nested population keys ALL/OFFENSE/DEFENSE identify the opportunity split.

| Report | Fields and meanings |
|---|---|
| validation_report.json | official_challenges: normalized official population; expected_official_challenges: dashboard daily sum; matched_challenges/unmatched_challenges: pitch matching counts; comparable_challenges/uncomparable_challenges: known/missing pairs; agreement_count/disagreement_count: matching/differing comparable calls; agreement_rate: agreements / all official challenges; agreement_rate_among_comparable: agreements / comparable challenges. breakdowns repeats these for original_called_strike, original_called_ball, overturned, confirmed. daily_reconciliation entries carry game_date, expected, observed. gate_passed boolean; stop_reasons list; geometry_method version string. |
| descriptive_report.json | games_processed, total_pitches, called_pitches, called_strikes, called_balls: population counts; evaluable_called_pitches: denominator E; incorrect_calls, incorrect_called_strikes, incorrect_called_balls: original/derived differences; incorrect_calls_corrected, incorrect_calls_surviving_with_challenge_available, incorrect_calls_surviving_because_challenge_unavailable: C/R/U; unknown_classifications: called UNKNOWN rows; incorrect_calls_with_unknown_classification: known incorrect UNKNOWN rows. incorrect_call_rate, correction_rate, survival_rate, recognition_survival_rate, resource_constrained_survival_rate follow the explicit E/I/C/R/U formulas in methodology. |
| recognition_distributions.json | Each population and metric has n, missing, minimum, maximum, mean, standard_deviation (sample), p25, median, p75 (linear interpolated quantiles). Summary values retain the metric unit; null when unavailable. |
| data_quality_report.json | expected_games, successfully_processed_games, total_pitches, called_pitches, called_strikes, called_balls are coverage counts. missing_pitch_locations/missing_movement_data count rows missing either coordinate/component; missing_catcher_ids/missing_called_pitch_catcher_ids/missing_umpire_ids count absent participants; missing_challenge_matches, duplicate_pitch_keys, impossible_counts, impossible_challenge_inventory are integrity counts. unknown_classifications is nullable until classification runs. classification_status labels state. failed_game_downloads lists missing game IDs; failed_source_downloads preserves failed receipts; source_discrepancies counts issue kinds; pitch_rows_deleted is zero. game_exclusions preserves ID/reason/status. source_record_exclusions and classification_exclusions have reason, row_count, percentage_of_population (0–100 percent, not fraction). Source-record denominator is physical pitches + automatic records; classification denominator is called pitches. |
| run_manifest.json | start/end ISO dates; expected_games/processed_games counts; gate_passed boolean; source_sha256s sorted unique raw object digests. |
| stop_report.json, when blocked | status=STOPPED, reasons list of gate failures, next_investigation text. This file is absent after a passing run. |

## Raw receipts and fixtures

Raw receipt fields: url, kind, retrieved_at (UTC ISO timestamp), content_type, final_url, ok, sha256, path, bytes, and error on failure. Source SHA fields in research tables resolve through these receipts. Fixture records are exact/minimally wrapped official samples, with no simulated observations included in pilot outputs. The official challenge fixture covers all three challenger roles and both outcomes. The timer fixture preserves a plate appearance and its Statcast rows to test numbering offsets.
