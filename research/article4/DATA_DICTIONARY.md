# Article 4 data dictionary

Generated from `fields.py`; build.py refuses to write undocumented columns.

Timing: DECISION_TIME = known before the pitch (pre-pitch state or strictly earlier pitches); POST_PITCH = produced by or after the pitch; HINDSIGHT = uses later events in the game and must not be used as a decision-time predictor; STATIC = season-level table.

## article4_opportunities

One row per ELIGIBLE incorrect call (OFFENSE = Articles 1-3 population; DEFENSE = extension). article4_all_incorrect_calls.csv has the same columns for every incorrect call, including ineligible ones.

| field | timing | source | definition |
|---|---|---|---|
| `article4_opportunity_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Article 4 row key: 'A4:' + pitch_key. |
| `pitch_key` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Articles 1-3 pitch key game_pk:at_bat_index:play_event_index; the join key to every prior ABS artifact. |
| `game_pk` | IDENTIFIER | processed pitches.csv (Articles 1-3) | MLB game identifier. |
| `game_date` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Official game date (YYYY-MM-DD). |
| `at_bat_index` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Feed plate-appearance index within the game (plate-appearance identifier = game_pk:at_bat_index). |
| `play_event_index` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Feed event index within the plate appearance. |
| `play_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Statcast/feed pitch playId (UUID). |
| `physical_pitch_ordinal` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Physical pitch ordinal within the plate appearance (automatic penalties excluded), Articles 1-3. |
| `opportunity_side` | IDENTIFIER | derived in build.py | OFFENSE = original STRIKE whose derived ABS call is BALL (the Articles 1-3 'incorrect called strike'); DEFENSE = original BALL whose derived ABS call is STRIKE (extension; not part of the Articles 1-3 population). |
| `eligibility_status` | DECISION_TIME | derived in build.py | ELIGIBLE (legal challenge available: inventory > 0, pitcher not a position player, known availability), INELIGIBLE_EXHAUSTED, INELIGIBLE_POSITION_PLAYER_PITCHING, UNKNOWN_AVAILABILITY. The OFFENSE ELIGIBLE set equals the Articles 1-3 population exactly. |
| `batting_team_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Batting team ID. |
| `batting_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Batting team name. |
| `fielding_team_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Fielding team ID. |
| `fielding_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Fielding team name. |
| `entitled_team_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Team entitled to challenge the call: batting team for OFFENSE (incorrect strike), fielding team for DEFENSE (incorrect ball). |
| `entitled_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Name of entitled_team_id. |
| `home_team_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Home team ID. |
| `home_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Home team name. |
| `away_team_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Away team ID. |
| `away_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Away team name. |
| `batter_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Batter MLBAM ID. |
| `batter_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Batter name. |
| `pitcher_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Pitcher MLBAM ID. |
| `pitcher_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Pitcher name. |
| `catcher_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Catcher MLBAM ID (Statcast fielder_2). |
| `catcher_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Catcher name. |
| `umpire_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Home-plate umpire ID. |
| `umpire_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Home-plate umpire name. |
| `venue` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Venue name. |
| `inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Inning. |
| `half_inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | top/bottom. |
| `inning_group` | DECISION_TIME | derived in build.py | Articles 1-3 inning group: EARLY 1-3, MIDDLE 4-6, LATE 7+. |
| `inning_bucket` | DECISION_TIME | derived in build.py | Article 4 inning bucket: 1-3, 4-6, 7-9, 10+ (extra innings separated because inventory rules change). |
| `batting_team_score` | DECISION_TIME | derived in build.py | Batting-team runs before the pitch. |
| `fielding_team_score` | DECISION_TIME | derived in build.py | Fielding-team runs before the pitch. |
| `batting_score_diff` | DECISION_TIME | derived in build.py | batting_team_score - fielding_team_score. |
| `entitled_team_score_diff` | DECISION_TIME | derived in build.py | Score differential from the entitled team's perspective. |
| `outs` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Outs before the pitch. |
| `on_1b` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Runner MLBAM ID on first before the pitch (blank = empty). |
| `on_2b` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Runner ID on second before the pitch. |
| `on_3b` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Runner ID on third before the pitch. |
| `base_state` | DECISION_TIME | derived in build.py | Pre-pitch occupancy string 1B2B3B, e.g. 101 = first and third. |
| `balls` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Balls before the pitch. |
| `strikes` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Strikes before the pitch. |
| `count` | DECISION_TIME | derived in build.py | Pre-pitch count 'balls-strikes'. |
| `late_close` | DECISION_TIME | derived in build.py | Context flag reused from Article 2: inning >= 7 and /batting_score_diff/ <= 2. Not a leverage index. |
| `strike_three_or_ball_four_at_stake` | DECISION_TIME | derived in build.py | True if either call ends the plate appearance (2 strikes or 3 balls before the pitch). |
| `RE_pre_pitch` | DECISION_TIME | derived in build.py | RE288 value of the pre-pitch state (primary table). |
| `challenge_inventory` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Entitled team's challenges remaining before the pitch (Articles 1-3 sequential reconstruction; affected_team_challenges_remaining). |
| `inventory_recomputed` | DECISION_TIME | derived in build.py | Entitled team's inventory independently recomputed in build.py from challenges.csv: start 2, lose one per CONFIRMED challenge, grant one at the start of an extra inning if none remain. |
| `final_challenge_indicator` | DECISION_TIME | derived in build.py | challenge_inventory == 1: a failed challenge here would exhaust the team. |
| `opponent_inventory` | DECISION_TIME | derived in build.py | The other team's recomputed inventory before the pitch. |
| `offense_challenges_remaining` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Batting team inventory before the pitch (Articles 1-3). |
| `defense_challenges_remaining` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Fielding team inventory before the pitch (Articles 1-3). |
| `prior_team_challenges` | DECISION_TIME | derived in build.py | Entitled team's challenges earlier in the game (strictly earlier pitches). |
| `prior_team_challenges_overturned` | DECISION_TIME | derived in build.py | Of prior_team_challenges, number overturned (successful). |
| `prior_team_challenges_confirmed` | DECISION_TIME | derived in build.py | Of prior_team_challenges, number confirmed (unsuccessful). |
| `prior_team_offense_challenges` | DECISION_TIME | derived in build.py | Prior challenges by the entitled team's batters. |
| `prior_team_defense_challenges` | DECISION_TIME | derived in build.py | Prior challenges by the entitled team's pitchers/catchers. |
| `prior_team_eligible_incorrect_calls` | DECISION_TIME | derived in build.py | Earlier eligible incorrect calls against the entitled team in this game (either side). Uses derived geometry; a pre-pitch fact, not necessarily known to players. |
| `prior_team_eligible_unchallenged` | DECISION_TIME | derived in build.py | Of prior_team_eligible_incorrect_calls, number not challenged. |
| `prior_opponent_challenges` | DECISION_TIME | derived in build.py | Opponent's challenges earlier in the game. |
| `extra_inning_grants_before` | DECISION_TIME | derived in build.py | Extra-inning challenge grants received by the entitled team before this pitch. |
| `pitch_type` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Statcast pitch type code. |
| `pitch_name` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Statcast pitch name. |
| `pitch_family` | DECISION_TIME | derived in build.py | Articles 1-3 pitch family mapping. |
| `release_speed` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Release speed (mph). |
| `plate_x` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Horizontal plate location (ft, catcher view). |
| `plate_z` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Vertical plate location (ft). |
| `abs_zone_top` | DECISION_TIME | processed pitches.csv (Articles 1-3) | ABS zone top (ft) used by the Articles 1-3 geometry. |
| `abs_zone_bot` | DECISION_TIME | processed pitches.csv (Articles 1-3) | ABS zone bottom (ft). |
| `signed_boundary_distance_inches` | DECISION_TIME | derived in build.py | Signed distance from ball edge to the ABS zone (inches); positive outside, negative inside. |
| `abs_distance_inches` | DECISION_TIME | derived in build.py | Absolute boundary distance in inches (Articles 1-3 abs_distance_inches for OFFENSE; distance inside the zone for DEFENSE). |
| `miss_axis` | DECISION_TIME | derived in build.py | OFFENSE: Articles 1-3 miss axis (VERTICAL/HORIZONTAL/CORNER). DEFENSE: INSIDE_ZONE (the pitch is a strike; see miss_side). |
| `miss_side` | DECISION_TIME | derived in build.py | OFFENSE: Articles 1-3 miss side (ABOVE/BELOW/INSIDE/OUTSIDE/corner). DEFENSE: NEAREST_TOP/NEAREST_BOTTOM/NEAREST_INSIDE/NEAREST_OUTSIDE, the zone edge closest to the pitch. |
| `horizontal_distance_inches` | DECISION_TIME | derived in build.py | OFFENSE only: horizontal distance outside the plate (Articles 1-3). |
| `vertical_distance_inches` | DECISION_TIME | derived in build.py | OFFENSE only: vertical distance outside the zone (Articles 1-3). |
| `corner_proximity_inches` | DECISION_TIME | derived in build.py | OFFENSE only: corner distance (Articles 1-3). |
| `bat_side` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Batter side. |
| `pitch_hand` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Pitcher hand. |
| `original_call` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Umpire's original call (Articles 1-3). |
| `derived_abs_call` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Fixed a-priori ABS geometry call, abs_2026_circle_rectangle_r1.45in_v1 (Articles 1-3). |
| `official_abs_call` | POST_PITCH | processed pitches.csv (Articles 1-3) | Official ABS result when challenged. |
| `displayed_call` | POST_PITCH | processed pitches.csv (Articles 1-3) | Call displayed in the feed (post-challenge). |
| `survival_class` | POST_PITCH | processed pitches.csv (Articles 1-3) | Articles 1-3 survival class. |
| `survival_detail` | POST_PITCH | processed pitches.csv (Articles 1-3) | Articles 1-3 survival detail. |
| `challenged` | POST_PITCH | derived in build.py | True if the entitled team challenged this pitch. |
| `recognized_article1_3` | POST_PITCH | derived in build.py | Articles 1-3 outcome (1 = batter challenged); OFFENSE eligible rows only; equals challenged. |
| `challenge_outcome` | POST_PITCH | processed pitches.csv (Articles 1-3) | OVERTURNED / CONFIRMED when challenged; blank otherwise. |
| `expected_recognition_prob_article3` | DECISION_TIME | Sprint 4 / Article 3 artifact | Articles 1-3 contextual expected recognition probability (Sprint 4 Model C refit without batter identity, full-season in-sample fit). OFFENSE eligible rows only. Model parameters use the whole season. |
| `expected_recognition_prob_temporal` | DECISION_TIME | Sprint 3 / Article 1-2 artifact | Sprint 3 expanding-window Model C (C_SITUATION) held-out probability, trained only on earlier months; blank for March (no prior month). OFFENSE only. |
| `expected_recognition_temporal_fold` | DECISION_TIME | Sprint 3 / Article 1-2 artifact | Test month of expected_recognition_prob_temporal. |
| `opportunity_difficulty_bucket` | DECISION_TIME | derived in build.py | Quintile of expected_recognition_prob_article3 across the 10,755 OFFENSE opportunities (Q1 = lowest expected recognition, hardest). New Article 4 field; Sprint 4's batter-level difficulty label is unchanged. |
| `feed_call_code` | POST_PITCH | immutable MLB game feed | Feed call code for the pitch (B, *B, C, ...), post-challenge. |
| `feed_call` | POST_PITCH | immutable MLB game feed | Feed call mapped to BALL/STRIKE (post-challenge). |
| `feed_description` | POST_PITCH | immutable MLB game feed | Feed pitch description. |
| `feed_call_matches_expected` | POST_PITCH | derived in build.py | Feed call equals the original call (unchallenged/confirmed) or the official ABS call (challenged). |
| `feed_pa_result_event` | POST_PITCH | immutable MLB game feed | Plate-appearance result event (end of PA; may be after this pitch). |
| `feed_pa_result_description` | POST_PITCH | immutable MLB game feed | Plate-appearance result text (end of PA). |
| `feed_pitch_review_type` | POST_PITCH | immutable MLB game feed | reviewDetails.reviewType on the pitch (MJ = ABS challenge). |
| `feed_pitch_review_overturned` | POST_PITCH | immutable MLB game feed | reviewDetails.isOverturned on the pitch. |
| `observed_state_is_reconstructed` | POST_PITCH | derived in build.py | True for OVERTURNED challenges: the feed shows the corrected outcome, so the 'observed' (incorrect-call-stood) state is the reconstructed one and the corrected state is the one the feed recorded. |
| `obs_balls` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: balls at the next decision point (0 if the PA ended). Blank when the state is AMBIGUOUS. |
| `obs_strikes` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: strikes at the next decision point. Blank when the state is AMBIGUOUS. |
| `obs_outs` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: outs after the pitch (3 = half-inning over). Blank when the state is AMBIGUOUS. |
| `obs_base_state` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: base occupancy after the pitch. Blank when the state is AMBIGUOUS. |
| `obs_runs` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: runs scored by the batting team on the pitch. Blank when the state is AMBIGUOUS. |
| `obs_pa_status` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: CONTINUES / WALK / STRIKEOUT. Blank when the state is AMBIGUOUS. |
| `obs_inning_ended` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: half-inning ended on the pitch. Blank when the state is AMBIGUOUS. |
| `obs_walkoff` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: state ends the game (bottom 9+ and batting team takes the lead); future RE set to 0. Blank when the state is AMBIGUOUS. |
| `obs_state_valid` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: state passes baseball validity checks. Blank when the state is AMBIGUOUS. |
| `cor_balls` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: balls at the next decision point (0 if the PA ended). Blank when the state is AMBIGUOUS. |
| `cor_strikes` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: strikes at the next decision point. Blank when the state is AMBIGUOUS. |
| `cor_outs` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: outs after the pitch (3 = half-inning over). Blank when the state is AMBIGUOUS. |
| `cor_base_state` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: base occupancy after the pitch. Blank when the state is AMBIGUOUS. |
| `cor_runs` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: runs scored by the batting team on the pitch. Blank when the state is AMBIGUOUS. |
| `cor_pa_status` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: CONTINUES / WALK / STRIKEOUT. Blank when the state is AMBIGUOUS. |
| `cor_inning_ended` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: half-inning ended on the pitch. Blank when the state is AMBIGUOUS. |
| `cor_walkoff` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: state ends the game (bottom 9+ and batting team takes the lead); future RE set to 0. Blank when the state is AMBIGUOUS. |
| `cor_state_valid` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: state passes baseball validity checks. Blank when the state is AMBIGUOUS. |
| `cf_rule` | POST_PITCH | derived in build.py | Counterfactual rule applied: R1_NO_RUNNER_ACTION, R2_RUNNER_OUTCOME_STANDS, R3_TERMINAL_CALL_RUNNER_ACTION, R4_UNCAUGHT_THIRD_STRIKE, R5_UNSUPPORTED_MOVEMENT (see METHODOLOGY.md). |
| `cf_confidence` | POST_PITCH | derived in build.py | EXACT (mechanical), RULE_BASED (documented ABS guidance applied), AMBIGUOUS (no primary state; bounds only). |
| `cf_ambiguity_reason` | POST_PITCH | derived in build.py | Why the counterfactual is ambiguous. |
| `actual_state_consistency` | POST_PITCH | derived in build.py | CONSISTENT if the feed movements reconcile with the pre-pitch state and the recorded call; otherwise the discrepancy class. |
| `alternative_states` | POST_PITCH | derived in build.py | JSON of enumerated alternative states for AMBIGUOUS rows. |
| `pa_outcome_changes` | POST_PITCH | derived in build.py | Observed and corrected plate-appearance status differ (e.g., walk vs strikeout). |
| `next_pitch_state_check` | POST_PITCH | derived in build.py | Independent check: reconstructed actual post-pitch state vs the Statcast pre-pitch state of the next pitch in the game (MATCH, MATCH_HALF_ENDED, INTERVENING_STATE_CHANGING_EVENT, MISMATCH, ...). |
| `RE_observed` | POST_PITCH | derived in build.py | Runs on the pitch + RE288(observed post-pitch state). Batting-team expected runs from the decision point to the end of the half-inning if the incorrect call stands. |
| `RE_corrected` | POST_PITCH | derived in build.py | Runs on the pitch + RE288(corrected post-pitch state). |
| `RE_delta_batting` | POST_PITCH | derived in build.py | RE_observed - RE_corrected (batting-team perspective). Positive = the uncorrected call favored the batting team (typical for DEFENSE rows); negative for OFFENSE rows. |
| `RE_delta_fielding` | POST_PITCH | derived in build.py | -RE_delta_batting (fielding-team perspective). |
| `RE_observed_alternatives` | POST_PITCH | derived in build.py | JSON of RE_observed under each enumerated alternative (AMBIGUOUS rows). |
| `RE_corrected_alternatives` | POST_PITCH | derived in build.py | JSON of RE_corrected under each enumerated alternative (AMBIGUOUS rows). |
| `correction_value_runs` | POST_PITCH | derived in build.py | Expected-run value of correcting the call to the ENTITLED team: -RE_delta_batting for OFFENSE, +RE_delta_batting for DEFENSE. Blank if AMBIGUOUS. Never uses subsequent realized runs. |
| `correction_value_runs_lower` | POST_PITCH | derived in build.py | Minimum correction value across enumerated alternatives (= correction_value_runs when not ambiguous). |
| `correction_value_runs_upper` | POST_PITCH | derived in build.py | Maximum correction value across enumerated alternatives. |
| `challenge_value_runs` | POST_PITCH | derived in build.py | Challenged rows: correction_value_runs if OVERTURNED, 0 if CONFIRMED (inventory cost not included). Blank if not challenged. |
| `missed_challenge_value_runs` | POST_PITCH | derived in build.py | Unchallenged ELIGIBLE rows: correction_value_runs (value potentially recoverable). Blank otherwise. |
| `unavailable_correction_value_runs` | POST_PITCH | derived in build.py | Ineligible rows (exhausted, position player): correction value that no challenge could recover. |
| `RE_observed_lomo` | POST_PITCH | derived in build.py | RE_observed using an RE288 table fit without the game's month (leave-one-month-out sensitivity). |
| `RE_corrected_lomo` | POST_PITCH | derived in build.py | RE_corrected, leave-one-month-out table. |
| `RE_delta_batting_lomo` | POST_PITCH | derived in build.py | RE_delta_batting, leave-one-month-out. |
| `RE_delta_fielding_lomo` | POST_PITCH | derived in build.py | RE_delta_fielding, leave-one-month-out. |
| `correction_value_runs_lomo` | POST_PITCH | derived in build.py | correction_value_runs, leave-one-month-out. |
| `RE_observed_pooled` | POST_PITCH | derived in build.py | RE_observed using the pooled-count sensitivity table (re_count_pooled). |
| `RE_corrected_pooled` | POST_PITCH | derived in build.py | RE_corrected, pooled-count table. |
| `RE_delta_batting_pooled` | POST_PITCH | derived in build.py | RE_delta_batting, pooled-count table. |
| `RE_delta_fielding_pooled` | POST_PITCH | derived in build.py | RE_delta_fielding, pooled-count table. |
| `correction_value_runs_pooled` | POST_PITCH | derived in build.py | correction_value_runs, pooled-count sensitivity table. |
| `re_ordering_violation` | POST_PITCH | derived in build.py | Non-ambiguous row whose primary correction value is negative. Runner events are held equal between the two states, so the correct call cannot lower the entitled team's true run expectancy; the primary RE288 table (Sprint 5 smoothing toward the base-out mean) orders the two states against baseball logic in a sparse cell. Retained and flagged, not corrected; see correction_value_runs_pooled. |
| `cf_unrecorded_runner_action_possible` | POST_PITCH | derived in build.py | The recorded outcome is a walk with a forced runner and no linked runner action. A play on a forced runner (e.g., a steal attempt and tag) is nullified by the walk award and absent from every source, so the R1 counterfactual is exact only with respect to the record (see the Braves case study). |
| `ca_stolen_base_attempt` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked stolen_base_*/caught_stealing_* action, or a runner movement whose event is Stolen Base/Caught Stealing, or a non-batter out on a Strikeout Double Play. |
| `ca_stolen_base` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked stolen-base action or Stolen Base movement. |
| `ca_caught_stealing` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked caught-stealing action or movement. |
| `ca_catcher_throw_recorded` | POST_PITCH | derived in build.py from immutable MLB game feed | A catcher (position C) assist, throwing/fielding error, or touch credit on a runner movement. Successful steals carry no throw credit, so False does not mean no throw. |
| `ca_catcher_pickoff_throw` | POST_PITCH | derived in build.py from immutable MLB game feed | The next event is a pickoff with fromCatcher=true. |
| `ca_catcher_throw_any_evidence` | POST_PITCH | derived in build.py from immutable MLB game feed | ca_catcher_throw_recorded OR ca_catcher_pickoff_throw. |
| `ca_wild_pitch` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked wild_pitch action or Wild Pitch movement. |
| `ca_passed_ball` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked passed_ball action or Passed Ball movement. |
| `ca_pickoff_action` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked pickoff_* action (e.g., catcher pickoff out/error). |
| `ca_defensive_indifference` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked defensive_indiff action. |
| `ca_runner_advance` | POST_PITCH | derived in build.py from immutable MLB game feed | A non-batter runner advanced on the pitch other than by a walk force. |
| `ca_runner_out` | POST_PITCH | derived in build.py from immutable MLB game feed | A non-batter runner was put out on the pitch. |
| `ca_error_on_play` | POST_PITCH | derived in build.py from immutable MLB game feed | An error action, Error movement, or error credit on the pitch. |
| `ca_secondary_play_reviewed` | POST_PITCH | derived in build.py from immutable MLB game feed | A linked baserunning action carries replay reviewDetails. |
| `ca_other_secondary_action` | POST_PITCH | derived in build.py from immutable MLB game feed | A linked action type outside the classified set. |
| `ca_other_secondary_types` | POST_PITCH | derived in build.py from immutable MLB game feed | JSON of those types. |
| `ca_any_secondary_action` | POST_PITCH | derived in build.py from immutable MLB game feed | Any linked action, or any non-batter movement that is not a walk force. |
| `attached_event_types` | POST_PITCH | immutable MLB game feed | JSON list of feed events linked to this pitch: baserunning actions whose actionPlayId equals the pitch playId, plus an immediately following pickoff event with fromCatcher=true. |
| `attached_event_descriptions` | POST_PITCH | immutable MLB game feed | JSON list of the linked events' descriptions. |
| `attached_event_is_baserunning` | POST_PITCH | immutable MLB game feed | JSON list of the linked events' isBaseRunningPlay flags. |
| `attached_movements` | POST_PITCH | immutable MLB game feed | JSON list of runner movements whose playIndex is the pitch or a linked event (runner, start, end, isOut, event, movementReason). |
| `attached_credits` | POST_PITCH | immutable MLB game feed | JSON list of fielding credits (credit:position) on non-batter runner movements for the pitch and linked events. |
| `catcher_pickoff_throw_after_pitch` | POST_PITCH | immutable MLB game feed | The next feed event after the pitch is a pickoff with fromCatcher=true. |
| `secondary_review_json` | POST_PITCH | immutable MLB game feed | reviewDetails on any linked baserunning action (replay review of a secondary play). |
| `next_event_type` | POST_PITCH | immutable MLB game feed | Type of the next feed event in the plate appearance (raw). |
| `next_event_from_catcher` | POST_PITCH | immutable MLB game feed | fromCatcher flag of the next event (pickoffs only). |
| `unlinked_baserunning_before_next_pitch` | POST_PITCH | immutable MLB game feed | Baserunning actions before the next pitch that are NOT linked to this pitch (e.g., pitcher pickoffs, balks); audit field. |
| `state_changing_events_before_next_pitch` | POST_PITCH | immutable MLB game feed | JSON list of non-pitch events between this pitch and the next pitch that changed count, bases, or outs (automatic balls/strikes, intentional walks, balks, pickoffs, catcher interference), plus plate appearances without a pitch; audit field. |
| `feed_pitch_start_time` | POST_PITCH | immutable MLB game feed | Feed pitch event startTime (UTC). |
| `feed_pitch_end_time` | POST_PITCH | immutable MLB game feed | Feed pitch event endTime (UTC). |
| `source_game_feed` | IDENTIFIER | processed pitches.csv (Articles 1-3) | SHA-256 of the immutable feed object used for this game. |
| `source_savant` | IDENTIFIER | processed pitches.csv (Articles 1-3) | SHA-256 of the Statcast object that supplied the pitch row. |

## article4_team_game_sequences

Chronological challenge-relevant events per team-game.

| field | timing | source | definition |
|---|---|---|---|
| `team_game_id` | DECISION_TIME | derived in build.py | game_pk:entitled_team_id. |
| `game_pk` | IDENTIFIER | processed pitches.csv (Articles 1-3) | MLB game identifier. |
| `game_date` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Official game date (YYYY-MM-DD). |
| `entitled_team_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Team entitled to challenge the call: batting team for OFFENSE (incorrect strike), fielding team for DEFENSE (incorrect ball). |
| `entitled_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Name of entitled_team_id. |
| `sequence_number` | DECISION_TIME | derived in build.py | 1-based chronological position within the team-game. |
| `sequence_length` | DECISION_TIME | derived in build.py | Rows in the team-game sequence. |
| `pitch_key` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Articles 1-3 pitch key game_pk:at_bat_index:play_event_index; the join key to every prior ABS artifact. |
| `at_bat_index` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Feed plate-appearance index within the game (plate-appearance identifier = game_pk:at_bat_index). |
| `play_event_index` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Feed event index within the plate appearance. |
| `inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Inning. |
| `half_inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | top/bottom. |
| `opportunity_side` | IDENTIFIER | derived in build.py | OFFENSE = original STRIKE whose derived ABS call is BALL (the Articles 1-3 'incorrect called strike'); DEFENSE = original BALL whose derived ABS call is STRIKE (extension; not part of the Articles 1-3 population). |
| `sequence_event_class` | DECISION_TIME | derived in build.py | ELIGIBLE_INCORRECT_CALL, INELIGIBLE_INCORRECT_CALL_EXHAUSTED, INELIGIBLE_INCORRECT_CALL_POSITION_PLAYER_PITCHING, CHALLENGE_OF_GEOMETRY_CORRECT_CALL (a challenge on a call the geometry says was correct; it consumes inventory), CHALLENGE_CALL_GEOMETRY_UNAVAILABLE. |
| `eligibility_status` | DECISION_TIME | derived in build.py | ELIGIBLE (legal challenge available: inventory > 0, pitcher not a position player, known availability), INELIGIBLE_EXHAUSTED, INELIGIBLE_POSITION_PLAYER_PITCHING, UNKNOWN_AVAILABILITY. The OFFENSE ELIGIBLE set equals the Articles 1-3 population exactly. |
| `exercised` | DECISION_TIME | derived in build.py | The team challenged this pitch. |
| `challenge_outcome` | POST_PITCH | processed pitches.csv (Articles 1-3) | OVERTURNED / CONFIRMED when challenged; blank otherwise. |
| `challenge_inventory` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Entitled team's challenges remaining before the pitch (Articles 1-3 sequential reconstruction; affected_team_challenges_remaining). |
| `inventory_after` | DECISION_TIME | derived in build.py | Inventory after this event (minus one after a CONFIRMED challenge). |
| `inventory_recomputed` | DECISION_TIME | derived in build.py | Entitled team's inventory independently recomputed in build.py from challenges.csv: start 2, lose one per CONFIRMED challenge, grant one at the start of an extra inning if none remain. |
| `count` | DECISION_TIME | derived in build.py | Pre-pitch count 'balls-strikes'. |
| `outs` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Outs before the pitch. |
| `base_state` | DECISION_TIME | derived in build.py | Pre-pitch occupancy string 1B2B3B, e.g. 101 = first and third. |
| `entitled_team_score_diff` | DECISION_TIME | derived in build.py | Score differential from the entitled team's perspective. |
| `abs_distance_inches` | DECISION_TIME | derived in build.py | Absolute boundary distance in inches (Articles 1-3 abs_distance_inches for OFFENSE; distance inside the zone for DEFENSE). |
| `expected_recognition_prob_article3` | DECISION_TIME | Sprint 4 / Article 3 artifact | Articles 1-3 contextual expected recognition probability (Sprint 4 Model C refit without batter identity, full-season in-sample fit). OFFENSE eligible rows only. Model parameters use the whole season. |
| `correction_value_runs` | POST_PITCH | derived in build.py | Expected-run value of correcting the call to the ENTITLED team: -RE_delta_batting for OFFENSE, +RE_delta_batting for DEFENSE. Blank if AMBIGUOUS. Never uses subsequent realized runs. |
| `correction_value_runs_lower` | POST_PITCH | derived in build.py | Minimum correction value across enumerated alternatives (= correction_value_runs when not ambiguous). |
| `correction_value_runs_upper` | POST_PITCH | derived in build.py | Maximum correction value across enumerated alternatives. |
| `cf_confidence` | POST_PITCH | derived in build.py | EXACT (mechanical), RULE_BASED (documented ABS guidance applied), AMBIGUOUS (no primary state; bounds only). |
| `ca_any_secondary_action` | POST_PITCH | derived in build.py from immutable MLB game feed | Any linked action, or any non-batter movement that is not a walk force. |
| `realized_value_runs` | POST_PITCH | derived in build.py | Value realized by the challenge: correction value if OVERTURNED, 0 if CONFIRMED; blank if not exercised. |
| `hindsight_later_eligible_opportunities` | HINDSIGHT | derived in build.py | Later ELIGIBLE incorrect calls in the same team-game. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_eligible_ambiguous` | HINDSIGHT | derived in build.py | Of those, AMBIGUOUS-valued. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_eligible_value_sum` | HINDSIGHT | derived in build.py | Sum of later eligible correction values (non-ambiguous). HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_eligible_value_max` | HINDSIGHT | derived in build.py | Maximum later eligible correction value (non-ambiguous). HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_challenges_used` | HINDSIGHT | derived in build.py | Later challenges by the team. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_realized_value_sum` | HINDSIGHT | derived in build.py | Sum of later realized challenge values. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_higher_value_opportunity` | HINDSIGHT | derived in build.py | ELIGIBLE rows: a later eligible opportunity had a higher correction value. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_higher_value_exercised` | HINDSIGHT | derived in build.py | ELIGIBLE rows: a later higher-value opportunity was challenged. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_exhausted_incorrect_calls` | HINDSIGHT | derived in build.py | Later incorrect calls against the team while exhausted. HINDSIGHT: uses future events; never a decision-time predictor. |
| `hindsight_later_exhausted_value_sum` | HINDSIGHT | derived in build.py | Sum of their correction values. HINDSIGHT: uses future events; never a decision-time predictor. |

## article4_team_summary

Descriptive team and league challenge behavior by side, inning bucket and inventory.

| field | timing | source | definition |
|---|---|---|---|
| `entitled_team` | SUMMARY | derived in build.py | Team name, or ALL_TEAMS for league rows. |
| `opportunity_side` | SUMMARY | derived in build.py | OFFENSE / DEFENSE. |
| `inning_bucket` | SUMMARY | derived in build.py | 1-3/4-6/7-9/10+ or ALL. |
| `challenge_inventory` | SUMMARY | derived in build.py | Inventory before the opportunity (1, 2) or ALL. |
| `opportunities` | SUMMARY | derived in build.py | Eligible opportunities. |
| `challenged` | SUMMARY | derived in build.py | Challenged opportunities. |
| `challenge_rate` | SUMMARY | derived in build.py | challenged / opportunities. |
| `overturned` | SUMMARY | derived in build.py | Overturned challenges. |
| `value_known_opportunities` | SUMMARY | derived in build.py | Non-ambiguous opportunities. |
| `ambiguous_value_opportunities` | SUMMARY | derived in build.py | AMBIGUOUS opportunities (excluded from value sums). |
| `mean_correction_value_runs` | SUMMARY | derived in build.py | Mean correction value, non-ambiguous. |
| `total_realized_value_runs` | SUMMARY | derived in build.py | Sum of challenge_value_runs, non-ambiguous. |
| `total_missed_value_runs` | SUMMARY | derived in build.py | Sum of missed_challenge_value_runs, non-ambiguous. |
| `mean_missed_value_runs` | SUMMARY | derived in build.py | Mean missed value among unchallenged, non-ambiguous. |
| `mean_abs_distance_inches` | SUMMARY | derived in build.py | Mean boundary distance (inches). |
| `mean_expected_recognition_prob` | SUMMARY | derived in build.py | Mean Articles 1-3 expected recognition (OFFENSE). |
| `sum_expected_recognition_prob` | SUMMARY | derived in build.py | Expected challenges under the Articles 1-3 contextual model (OFFENSE). |
| `final_challenge_opportunities` | SUMMARY | derived in build.py | Opportunities with inventory == 1. |
| `competing_attention_opportunities` | SUMMARY | derived in build.py | Opportunities with any linked secondary action. |
| `summary_level` | SUMMARY | derived in build.py | Grouping keys of the row. |

## article4_high_value_missed

Top unchallenged eligible opportunities by correction value, with review context.

| field | timing | source | definition |
|---|---|---|---|
| `high_value_rank` | POST_PITCH | derived in build.py | Rank by ranking_value_runs among unchallenged eligible opportunities. |
| `ranking_value_runs` | POST_PITCH | derived in build.py | correction_value_runs, or its lower bound for AMBIGUOUS rows. |
| `value_is_bound` | POST_PITCH | derived in build.py | True if ranking_value_runs is a lower bound (AMBIGUOUS row). |
| `article4_opportunity_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Article 4 row key: 'A4:' + pitch_key. |
| `pitch_key` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Articles 1-3 pitch key game_pk:at_bat_index:play_event_index; the join key to every prior ABS artifact. |
| `game_date` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Official game date (YYYY-MM-DD). |
| `game_pk` | IDENTIFIER | processed pitches.csv (Articles 1-3) | MLB game identifier. |
| `opportunity_side` | IDENTIFIER | derived in build.py | OFFENSE = original STRIKE whose derived ABS call is BALL (the Articles 1-3 'incorrect called strike'); DEFENSE = original BALL whose derived ABS call is STRIKE (extension; not part of the Articles 1-3 population). |
| `entitled_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Name of entitled_team_id. |
| `batting_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Batting team name. |
| `fielding_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Fielding team name. |
| `batter_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Batter name. |
| `pitcher_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Pitcher name. |
| `catcher_name` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Catcher name. |
| `inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Inning. |
| `half_inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | top/bottom. |
| `batting_score_diff` | DECISION_TIME | derived in build.py | batting_team_score - fielding_team_score. |
| `count` | DECISION_TIME | derived in build.py | Pre-pitch count 'balls-strikes'. |
| `outs` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Outs before the pitch. |
| `base_state` | DECISION_TIME | derived in build.py | Pre-pitch occupancy string 1B2B3B, e.g. 101 = first and third. |
| `challenge_inventory` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Entitled team's challenges remaining before the pitch (Articles 1-3 sequential reconstruction; affected_team_challenges_remaining). |
| `final_challenge_indicator` | DECISION_TIME | derived in build.py | challenge_inventory == 1: a failed challenge here would exhaust the team. |
| `abs_distance_inches` | DECISION_TIME | derived in build.py | Absolute boundary distance in inches (Articles 1-3 abs_distance_inches for OFFENSE; distance inside the zone for DEFENSE). |
| `miss_side` | DECISION_TIME | derived in build.py | OFFENSE: Articles 1-3 miss side (ABOVE/BELOW/INSIDE/OUTSIDE/corner). DEFENSE: NEAREST_TOP/NEAREST_BOTTOM/NEAREST_INSIDE/NEAREST_OUTSIDE, the zone edge closest to the pitch. |
| `expected_recognition_prob_article3` | DECISION_TIME | Sprint 4 / Article 3 artifact | Articles 1-3 contextual expected recognition probability (Sprint 4 Model C refit without batter identity, full-season in-sample fit). OFFENSE eligible rows only. Model parameters use the whole season. |
| `obs_balls` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: balls at the next decision point (0 if the PA ended). Blank when the state is AMBIGUOUS. |
| `obs_strikes` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: strikes at the next decision point. Blank when the state is AMBIGUOUS. |
| `obs_outs` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: outs after the pitch (3 = half-inning over). Blank when the state is AMBIGUOUS. |
| `obs_base_state` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: base occupancy after the pitch. Blank when the state is AMBIGUOUS. |
| `obs_runs` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: runs scored by the batting team on the pitch. Blank when the state is AMBIGUOUS. |
| `obs_pa_status` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: CONTINUES / WALK / STRIKEOUT. Blank when the state is AMBIGUOUS. |
| `cor_balls` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: balls at the next decision point (0 if the PA ended). Blank when the state is AMBIGUOUS. |
| `cor_strikes` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: strikes at the next decision point. Blank when the state is AMBIGUOUS. |
| `cor_outs` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: outs after the pitch (3 = half-inning over). Blank when the state is AMBIGUOUS. |
| `cor_base_state` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: base occupancy after the pitch. Blank when the state is AMBIGUOUS. |
| `cor_runs` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: runs scored by the batting team on the pitch. Blank when the state is AMBIGUOUS. |
| `cor_pa_status` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: CONTINUES / WALK / STRIKEOUT. Blank when the state is AMBIGUOUS. |
| `cf_rule` | POST_PITCH | derived in build.py | Counterfactual rule applied: R1_NO_RUNNER_ACTION, R2_RUNNER_OUTCOME_STANDS, R3_TERMINAL_CALL_RUNNER_ACTION, R4_UNCAUGHT_THIRD_STRIKE, R5_UNSUPPORTED_MOVEMENT (see METHODOLOGY.md). |
| `cf_confidence` | POST_PITCH | derived in build.py | EXACT (mechanical), RULE_BASED (documented ABS guidance applied), AMBIGUOUS (no primary state; bounds only). |
| `RE_observed` | POST_PITCH | derived in build.py | Runs on the pitch + RE288(observed post-pitch state). Batting-team expected runs from the decision point to the end of the half-inning if the incorrect call stands. |
| `RE_corrected` | POST_PITCH | derived in build.py | Runs on the pitch + RE288(corrected post-pitch state). |
| `RE_delta_batting` | POST_PITCH | derived in build.py | RE_observed - RE_corrected (batting-team perspective). Positive = the uncorrected call favored the batting team (typical for DEFENSE rows); negative for OFFENSE rows. |
| `correction_value_runs` | POST_PITCH | derived in build.py | Expected-run value of correcting the call to the ENTITLED team: -RE_delta_batting for OFFENSE, +RE_delta_batting for DEFENSE. Blank if AMBIGUOUS. Never uses subsequent realized runs. |
| `correction_value_runs_lower` | POST_PITCH | derived in build.py | Minimum correction value across enumerated alternatives (= correction_value_runs when not ambiguous). |
| `correction_value_runs_upper` | POST_PITCH | derived in build.py | Maximum correction value across enumerated alternatives. |
| `missed_challenge_value_runs` | POST_PITCH | derived in build.py | Unchallenged ELIGIBLE rows: correction_value_runs (value potentially recoverable). Blank otherwise. |
| `correction_value_runs_lomo` | POST_PITCH | derived in build.py | correction_value_runs, leave-one-month-out. |
| `ca_any_secondary_action` | POST_PITCH | derived in build.py from immutable MLB game feed | Any linked action, or any non-batter movement that is not a walk force. |
| `attached_event_descriptions` | POST_PITCH | immutable MLB game feed | JSON list of the linked events' descriptions. |
| `feed_description` | POST_PITCH | immutable MLB game feed | Feed pitch description. |
| `feed_pa_result_description` | POST_PITCH | immutable MLB game feed | Plate-appearance result text (end of PA). |
| `next_pitch_state_check` | POST_PITCH | derived in build.py | Independent check: reconstructed actual post-pitch state vs the Statcast pre-pitch state of the next pitch in the game (MATCH, MATCH_HALF_ENDED, INTERVENING_STATE_CHANGING_EVENT, MISMATCH, ...). |

## article4_competing_attention

Eligible opportunities with a source-linked secondary action (columns defined under article4_opportunities).

| field | timing | source | definition |
|---|---|---|---|
| `article4_opportunity_id` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Article 4 row key: 'A4:' + pitch_key. |
| `pitch_key` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Articles 1-3 pitch key game_pk:at_bat_index:play_event_index; the join key to every prior ABS artifact. |
| `game_pk` | IDENTIFIER | processed pitches.csv (Articles 1-3) | MLB game identifier. |
| `game_date` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Official game date (YYYY-MM-DD). |
| `opportunity_side` | IDENTIFIER | derived in build.py | OFFENSE = original STRIKE whose derived ABS call is BALL (the Articles 1-3 'incorrect called strike'); DEFENSE = original BALL whose derived ABS call is STRIKE (extension; not part of the Articles 1-3 population). |
| `entitled_team` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Name of entitled_team_id. |
| `inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Inning. |
| `half_inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | top/bottom. |
| `count` | DECISION_TIME | derived in build.py | Pre-pitch count 'balls-strikes'. |
| `outs` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Outs before the pitch. |
| `base_state` | DECISION_TIME | derived in build.py | Pre-pitch occupancy string 1B2B3B, e.g. 101 = first and third. |
| `challenged` | POST_PITCH | derived in build.py | True if the entitled team challenged this pitch. |
| `challenge_outcome` | POST_PITCH | processed pitches.csv (Articles 1-3) | OVERTURNED / CONFIRMED when challenged; blank otherwise. |
| `challenge_inventory` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Entitled team's challenges remaining before the pitch (Articles 1-3 sequential reconstruction; affected_team_challenges_remaining). |
| `abs_distance_inches` | DECISION_TIME | derived in build.py | Absolute boundary distance in inches (Articles 1-3 abs_distance_inches for OFFENSE; distance inside the zone for DEFENSE). |
| `expected_recognition_prob_article3` | DECISION_TIME | Sprint 4 / Article 3 artifact | Articles 1-3 contextual expected recognition probability (Sprint 4 Model C refit without batter identity, full-season in-sample fit). OFFENSE eligible rows only. Model parameters use the whole season. |
| `correction_value_runs` | POST_PITCH | derived in build.py | Expected-run value of correcting the call to the ENTITLED team: -RE_delta_batting for OFFENSE, +RE_delta_batting for DEFENSE. Blank if AMBIGUOUS. Never uses subsequent realized runs. |
| `cf_rule` | POST_PITCH | derived in build.py | Counterfactual rule applied: R1_NO_RUNNER_ACTION, R2_RUNNER_OUTCOME_STANDS, R3_TERMINAL_CALL_RUNNER_ACTION, R4_UNCAUGHT_THIRD_STRIKE, R5_UNSUPPORTED_MOVEMENT (see METHODOLOGY.md). |
| `cf_confidence` | POST_PITCH | derived in build.py | EXACT (mechanical), RULE_BASED (documented ABS guidance applied), AMBIGUOUS (no primary state; bounds only). |
| `ca_stolen_base_attempt` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked stolen_base_*/caught_stealing_* action, or a runner movement whose event is Stolen Base/Caught Stealing, or a non-batter out on a Strikeout Double Play. |
| `ca_stolen_base` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked stolen-base action or Stolen Base movement. |
| `ca_caught_stealing` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked caught-stealing action or movement. |
| `ca_catcher_throw_recorded` | POST_PITCH | derived in build.py from immutable MLB game feed | A catcher (position C) assist, throwing/fielding error, or touch credit on a runner movement. Successful steals carry no throw credit, so False does not mean no throw. |
| `ca_catcher_pickoff_throw` | POST_PITCH | derived in build.py from immutable MLB game feed | The next event is a pickoff with fromCatcher=true. |
| `ca_catcher_throw_any_evidence` | POST_PITCH | derived in build.py from immutable MLB game feed | ca_catcher_throw_recorded OR ca_catcher_pickoff_throw. |
| `ca_wild_pitch` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked wild_pitch action or Wild Pitch movement. |
| `ca_passed_ball` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked passed_ball action or Passed Ball movement. |
| `ca_pickoff_action` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked pickoff_* action (e.g., catcher pickoff out/error). |
| `ca_defensive_indifference` | POST_PITCH | derived in build.py from immutable MLB game feed | Linked defensive_indiff action. |
| `ca_runner_advance` | POST_PITCH | derived in build.py from immutable MLB game feed | A non-batter runner advanced on the pitch other than by a walk force. |
| `ca_runner_out` | POST_PITCH | derived in build.py from immutable MLB game feed | A non-batter runner was put out on the pitch. |
| `ca_error_on_play` | POST_PITCH | derived in build.py from immutable MLB game feed | An error action, Error movement, or error credit on the pitch. |
| `ca_secondary_play_reviewed` | POST_PITCH | derived in build.py from immutable MLB game feed | A linked baserunning action carries replay reviewDetails. |
| `ca_other_secondary_action` | POST_PITCH | derived in build.py from immutable MLB game feed | A linked action type outside the classified set. |
| `ca_other_secondary_types` | POST_PITCH | derived in build.py from immutable MLB game feed | JSON of those types. |
| `ca_any_secondary_action` | POST_PITCH | derived in build.py from immutable MLB game feed | Any linked action, or any non-batter movement that is not a walk force. |
| `attached_event_types` | POST_PITCH | immutable MLB game feed | JSON list of feed events linked to this pitch: baserunning actions whose actionPlayId equals the pitch playId, plus an immediately following pickoff event with fromCatcher=true. |
| `attached_event_descriptions` | POST_PITCH | immutable MLB game feed | JSON list of the linked events' descriptions. |
| `attached_movements` | POST_PITCH | immutable MLB game feed | JSON list of runner movements whose playIndex is the pitch or a linked event (runner, start, end, isOut, event, movementReason). |
| `attached_credits` | POST_PITCH | immutable MLB game feed | JSON list of fielding credits (credit:position) on non-batter runner movements for the pitch and linked events. |
| `catcher_pickoff_throw_after_pitch` | POST_PITCH | immutable MLB game feed | The next feed event after the pitch is a pickoff with fromCatcher=true. |
| `secondary_review_json` | POST_PITCH | immutable MLB game feed | reviewDetails on any linked baserunning action (replay review of a secondary play). |
| `next_event_type` | POST_PITCH | immutable MLB game feed | Type of the next feed event in the plate appearance (raw). |
| `next_event_from_catcher` | POST_PITCH | immutable MLB game feed | fromCatcher flag of the next event (pickoffs only). |

## article4_re288_table

Count-aware run-expectancy table.

| field | timing | source | definition |
|---|---|---|---|
| `balls` | STATIC | derived in build.py | Balls. |
| `strikes` | STATIC | derived in build.py | Strikes. |
| `outs` | STATIC | derived in build.py | Outs. |
| `base_state` | STATIC | derived in build.py | Base occupancy 1B2B3B. |
| `raw_mean` | STATIC | derived in build.py | Mean runs from this pitch to the end of the half-inning (feed-replayed runs). |
| `n_pitches` | STATIC | derived in build.py | Pitches observed in the state (innings 1-8, complete half-innings). |
| `sd` | STATIC | derived in build.py | Standard deviation of future runs. |
| `n_half_innings` | STATIC | derived in build.py | Distinct half-innings contributing. |
| `base_out_mean` | STATIC | derived in build.py | Base-out mean (all counts). |
| `base_out_n` | STATIC | derived in build.py | Pitches in the base-out state. |
| `re_smoothed` | STATIC | derived in build.py | (raw_mean*n + 40*base_out_mean)/(n + 40); the value used for lookup (Sprint 5 smoothing convention). |
| `count_effect_pooled` | STATIC | derived in build.py | Mean (future runs - base-out mean) for the count and outs, pooled across base states. |
| `re_count_pooled` | STATIC | derived in build.py | Sensitivity RE: base_out_mean + count_effect_pooled. |

## article4_re24_table

Base-out run-expectancy table (reference).

| field | timing | source | definition |
|---|---|---|---|
| `outs` | STATIC | derived in build.py | Outs. |
| `base_state` | STATIC | derived in build.py | Base occupancy. |
| `re24` | STATIC | derived in build.py | Mean runs to end of half-inning at the first pitch of a plate appearance. |
| `n_plate_appearances` | STATIC | derived in build.py | Plate appearances observed. |

## article4_braves_case_study

Candidate pitches evaluated against the remembered Braves play.

| field | timing | source | definition |
|---|---|---|---|
| `game_pk` | AUDIT | immutable MLB game feed | Game. |
| `source_scope` | AUDIT | immutable MLB game feed | SNAPSHOT (accepted research snapshot) or POST_SNAPSHOT_CASE_STUDY_ONLY (archived after 2026-09-09 for this search only). |
| `feed_sha256` | AUDIT | immutable MLB game feed | Feed object hash. |
| `game_date` | AUDIT | immutable MLB game feed | Date. |
| `away` | AUDIT | immutable MLB game feed | Away team. |
| `home` | AUDIT | immutable MLB game feed | Home team. |
| `final_away` | AUDIT | immutable MLB game feed | Final away runs. |
| `final_home` | AUDIT | immutable MLB game feed | Final home runs. |
| `inning` | AUDIT | immutable MLB game feed | Inning. |
| `half_inning` | AUDIT | immutable MLB game feed | Half. |
| `pitch_key` | AUDIT | immutable MLB game feed | Pitch key. |
| `batter` | AUDIT | immutable MLB game feed | Batter. |
| `pitcher` | AUDIT | immutable MLB game feed | Pitcher. |
| `pre_count` | AUDIT | immutable MLB game feed | Pre-pitch count. |
| `pre_outs` | AUDIT | immutable MLB game feed | Pre-pitch outs. |
| `pre_bases` | AUDIT | immutable MLB game feed | Pre-pitch occupancy. |
| `plate_x` | AUDIT | immutable MLB game feed | Feed pX. |
| `plate_z` | AUDIT | immutable MLB game feed | Feed pZ. |
| `zone_top` | AUDIT | immutable MLB game feed | Feed strikeZoneTop. |
| `zone_bottom` | AUDIT | immutable MLB game feed | Feed strikeZoneBottom. |
| `derived_abs_call` | AUDIT | immutable MLB game feed | Articles 1-3 geometry applied to feed coordinates. |
| `signed_boundary_distance_inches` | AUDIT | immutable MLB game feed | Signed distance (inches). |
| `pitch_review_type` | AUDIT | immutable MLB game feed | Pitch reviewType. |
| `pitch_review_overturned` | AUDIT | immutable MLB game feed | Pitch review overturned. |
| `attached_event_types` | AUDIT | immutable MLB game feed | Linked events. |
| `attached_event_descriptions` | AUDIT | immutable MLB game feed | Linked event text. |
| `pa_result_description` | AUDIT | immutable MLB game feed | Plate-appearance result. |
| `criterion_braves_fielding` | AUDIT | immutable MLB game feed | Recollection criterion 'braves fielding' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_first_inning` | AUDIT | immutable MLB game feed | Recollection criterion 'first inning' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_runner_on_first_pre` | AUDIT | immutable MLB game feed | Recollection criterion 'runner on first pre' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_one_out_pre` | AUDIT | immutable MLB game feed | Recollection criterion 'one out pre' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_count_3_2_pre` | AUDIT | immutable MLB game feed | Recollection criterion 'count 3 2 pre' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_called_ball_four` | AUDIT | immutable MLB game feed | Recollection criterion 'called ball four' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_steal_attempt_on_pitch` | AUDIT | immutable MLB game feed | Recollection criterion 'steal attempt on pitch' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_catcher_throw_recorded` | AUDIT | immutable MLB game feed | Recollection criterion 'catcher throw recorded' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_secondary_play_reviewed` | AUDIT | immutable MLB game feed | Recollection criterion 'secondary play reviewed' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_geometry_strike` | AUDIT | immutable MLB game feed | Recollection criterion 'geometry strike' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_near_top_of_zone` | AUDIT | immutable MLB game feed | Recollection criterion 'near top of zone' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_not_successfully_challenged` | AUDIT | immutable MLB game feed | Recollection criterion 'not successfully challenged' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_inning_continued` | AUDIT | immutable MLB game feed | Recollection criterion 'inning continued' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_later_walk_in_inning` | AUDIT | immutable MLB game feed | Recollection criterion 'later walk in inning' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_later_home_run_in_inning` | AUDIT | immutable MLB game feed | Recollection criterion 'later home run in inning' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_braves_trailed_5_0_after_first` | AUDIT | immutable MLB game feed | Recollection criterion 'braves trailed 5 0 after first' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criterion_final_score_5_1_braves_loss` | AUDIT | immutable MLB game feed | Recollection criterion 'final score 5 1 braves loss' matched by the source data (near_top_of_zone: /pZ - zone top/ <= 3 inches). |
| `criteria_matched` | AUDIT | immutable MLB game feed | Number of recollection criteria matched. |
| `criteria_total` | AUDIT | immutable MLB game feed | Criteria evaluated. |
| `criterion_rev_game_2026_08_10_vs_mets` | AUDIT | immutable MLB game feed | Revised-account criterion (user clarification, 2026-09-23): game is 2026-08-10 against the Mets. |
| `criterion_rev_batter_carson_benge` | AUDIT | immutable MLB game feed | Revised-account criterion (user clarification, 2026-09-23): batter is Carson Benge. |
| `criterion_rev_bichette_on_first` | AUDIT | immutable MLB game feed | Revised-account criterion (user clarification, 2026-09-23): Bo Bichette on first (advanced on the walk). |
| `criterion_rev_pitcher_elder` | AUDIT | immutable MLB game feed | Revised-account criterion (user clarification, 2026-09-23): pitcher is Bryce Elder. |
| `criterion_rev_baty_homer_three_batters_later` | AUDIT | immutable MLB game feed | Revised-account criterion (user clarification, 2026-09-23): Brett Baty homered three batters later. |
| `criterion_rev_mets_lead_5_0_after_homer` | AUDIT | immutable MLB game feed | Revised-account criterion (user clarification, 2026-09-23): the home run made it 5-0. |
| `revised_criteria_matched` | AUDIT | derived in build.py | Revised-account criteria matched. |
| `revised_criteria_total` | AUDIT | derived in build.py | Revised-account criteria evaluated. |
| `identification_status` | AUDIT | derived in build.py | IDENTIFIED_USER_CONFIRMED_GAME for the pitch matching every revised criterion in the user-identified game; otherwise NOT_THE_CASE. |

## article4_braves_case_study_sequence

Full event sequence of the best candidate's half-inning.

| field | timing | source | definition |
|---|---|---|---|
| `game_pk` | AUDIT | immutable MLB game feed | Game. |
| `at_bat_index` | AUDIT | immutable MLB game feed | Plate appearance. |
| `event_index` | AUDIT | immutable MLB game feed | Event index. |
| `batter` | AUDIT | immutable MLB game feed | Batter. |
| `event_type` | AUDIT | immutable MLB game feed | Feed event type. |
| `call_code` | AUDIT | immutable MLB game feed | Call code. |
| `description` | AUDIT | immutable MLB game feed | Event description. |
| `balls_after` | AUDIT | immutable MLB game feed | Balls after event. |
| `strikes_after` | AUDIT | immutable MLB game feed | Strikes after event. |
| `outs_after` | AUDIT | immutable MLB game feed | Outs after event. |
| `plate_z` | AUDIT | immutable MLB game feed | pZ. |
| `zone_top` | AUDIT | immutable MLB game feed | strikeZoneTop. |
| `review` | AUDIT | immutable MLB game feed | reviewDetails JSON. |
| `pa_result` | AUDIT | immutable MLB game feed | PA result text (last event of PA). |
| `away_score_after_pa` | AUDIT | immutable MLB game feed | Away score after PA. |
| `home_score_after_pa` | AUDIT | immutable MLB game feed | Home score after PA. |

## article4_braves_game_scores

Every Braves game searched, with final and first-inning scores.

| field | timing | source | definition |
|---|---|---|---|
| `game_pk` | AUDIT | immutable MLB game feed | Game. |
| `source_scope` | AUDIT | immutable MLB game feed | SNAPSHOT or POST_SNAPSHOT_CASE_STUDY_ONLY. |
| `game_date` | AUDIT | immutable MLB game feed | Date. |
| `braves_runs` | AUDIT | immutable MLB game feed | Braves final runs. |
| `opponent_runs` | AUDIT | immutable MLB game feed | Opponent final runs. |
| `opponent_first_inning_runs` | AUDIT | immutable MLB game feed | Opponent first-inning runs. |

## article4_spot_checks

Rows selected for automated and manual review (columns defined under article4_opportunities).

| field | timing | source | definition |
|---|---|---|---|
| `spot_check_reason` | AUDIT | derived in build.py | Why the row was selected for review. |
| `pitch_key` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Articles 1-3 pitch key game_pk:at_bat_index:play_event_index; the join key to every prior ABS artifact. |
| `game_date` | IDENTIFIER | processed pitches.csv (Articles 1-3) | Official game date (YYYY-MM-DD). |
| `opportunity_side` | IDENTIFIER | derived in build.py | OFFENSE = original STRIKE whose derived ABS call is BALL (the Articles 1-3 'incorrect called strike'); DEFENSE = original BALL whose derived ABS call is STRIKE (extension; not part of the Articles 1-3 population). |
| `inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Inning. |
| `half_inning` | DECISION_TIME | processed pitches.csv (Articles 1-3) | top/bottom. |
| `count` | DECISION_TIME | derived in build.py | Pre-pitch count 'balls-strikes'. |
| `outs` | DECISION_TIME | processed pitches.csv (Articles 1-3) | Outs before the pitch. |
| `base_state` | DECISION_TIME | derived in build.py | Pre-pitch occupancy string 1B2B3B, e.g. 101 = first and third. |
| `challenged` | POST_PITCH | derived in build.py | True if the entitled team challenged this pitch. |
| `challenge_outcome` | POST_PITCH | processed pitches.csv (Articles 1-3) | OVERTURNED / CONFIRMED when challenged; blank otherwise. |
| `feed_description` | POST_PITCH | immutable MLB game feed | Feed pitch description. |
| `feed_pa_result_description` | POST_PITCH | immutable MLB game feed | Plate-appearance result text (end of PA). |
| `attached_event_descriptions` | POST_PITCH | immutable MLB game feed | JSON list of the linked events' descriptions. |
| `obs_balls` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: balls at the next decision point (0 if the PA ended). Blank when the state is AMBIGUOUS. |
| `obs_strikes` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: strikes at the next decision point. Blank when the state is AMBIGUOUS. |
| `obs_outs` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: outs after the pitch (3 = half-inning over). Blank when the state is AMBIGUOUS. |
| `obs_base_state` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: base occupancy after the pitch. Blank when the state is AMBIGUOUS. |
| `obs_runs` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: runs scored by the batting team on the pitch. Blank when the state is AMBIGUOUS. |
| `obs_pa_status` | POST_PITCH | derived in build.py | OBSERVED state = state produced if the incorrect original call stands: CONTINUES / WALK / STRIKEOUT. Blank when the state is AMBIGUOUS. |
| `cor_balls` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: balls at the next decision point (0 if the PA ended). Blank when the state is AMBIGUOUS. |
| `cor_strikes` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: strikes at the next decision point. Blank when the state is AMBIGUOUS. |
| `cor_outs` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: outs after the pitch (3 = half-inning over). Blank when the state is AMBIGUOUS. |
| `cor_base_state` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: base occupancy after the pitch. Blank when the state is AMBIGUOUS. |
| `cor_runs` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: runs scored by the batting team on the pitch. Blank when the state is AMBIGUOUS. |
| `cor_pa_status` | POST_PITCH | derived in build.py | CORRECTED state = state produced if ABS corrects the call: CONTINUES / WALK / STRIKEOUT. Blank when the state is AMBIGUOUS. |
| `cf_rule` | POST_PITCH | derived in build.py | Counterfactual rule applied: R1_NO_RUNNER_ACTION, R2_RUNNER_OUTCOME_STANDS, R3_TERMINAL_CALL_RUNNER_ACTION, R4_UNCAUGHT_THIRD_STRIKE, R5_UNSUPPORTED_MOVEMENT (see METHODOLOGY.md). |
| `cf_confidence` | POST_PITCH | derived in build.py | EXACT (mechanical), RULE_BASED (documented ABS guidance applied), AMBIGUOUS (no primary state; bounds only). |
| `RE_observed` | POST_PITCH | derived in build.py | Runs on the pitch + RE288(observed post-pitch state). Batting-team expected runs from the decision point to the end of the half-inning if the incorrect call stands. |
| `RE_corrected` | POST_PITCH | derived in build.py | Runs on the pitch + RE288(corrected post-pitch state). |
| `correction_value_runs` | POST_PITCH | derived in build.py | Expected-run value of correcting the call to the ENTITLED team: -RE_delta_batting for OFFENSE, +RE_delta_batting for DEFENSE. Blank if AMBIGUOUS. Never uses subsequent realized runs. |
| `next_pitch_state_check` | POST_PITCH | derived in build.py | Independent check: reconstructed actual post-pitch state vs the Statcast pre-pitch state of the next pitch in the game (MATCH, MATCH_HALF_ENDED, INTERVENING_STATE_CHANGING_EVENT, MISMATCH, ...). |
| `feed_call_matches_expected` | POST_PITCH | derived in build.py | Feed call equals the original call (unchallenged/confirmed) or the official ABS call (challenged). |
| `automated_check_pass` | AUDIT | derived in build.py | Next-pitch state check passes and the feed call is as expected. |
| `manual_review_note` | AUDIT | derived in build.py | Analyst's note from manual review against source play-by-play (manual_review_notes.json). |
