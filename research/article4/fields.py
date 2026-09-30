"""Field registry for every Article 4 output column.

build.py refuses to write a column that is not documented here, and
DATA_DICTIONARY.md is generated from this registry.  Keys are (table, field);
table "*" applies to every table that contains the field.
"""
from __future__ import annotations

from pathlib import Path

D: dict = {}


def doc(field, text, table="*", timing="", source=""):
    D[(table, field)] = {"text": text, "timing": timing, "source": source}


PRE, POST, HIND, CONST, ID = "DECISION_TIME", "POST_PITCH", "HINDSIGHT", "STATIC", "IDENTIFIER"
PT, FEED, DER, S3, S4, CH = ("processed pitches.csv (Articles 1-3)", "immutable MLB game feed", "derived in build.py",
                             "Sprint 3 / Article 1-2 artifact", "Sprint 4 / Article 3 artifact", "processed challenges.csv")

# ---- identity
for f, t in [("article4_opportunity_id", "Article 4 row key: 'A4:' + pitch_key."),
             ("pitch_key", "Articles 1-3 pitch key game_pk:at_bat_index:play_event_index; the join key to every prior ABS artifact."),
             ("game_pk", "MLB game identifier."), ("game_date", "Official game date (YYYY-MM-DD)."),
             ("at_bat_index", "Feed plate-appearance index within the game (plate-appearance identifier = game_pk:at_bat_index)."),
             ("play_event_index", "Feed event index within the plate appearance."),
             ("play_id", "Statcast/feed pitch playId (UUID)."),
             ("physical_pitch_ordinal", "Physical pitch ordinal within the plate appearance (automatic penalties excluded), Articles 1-3."),
             ("home_team_id", "Home team ID."), ("home_team", "Home team name."), ("away_team_id", "Away team ID."), ("away_team", "Away team name."),
             ("batting_team_id", "Batting team ID."), ("batting_team", "Batting team name."),
             ("fielding_team_id", "Fielding team ID."), ("fielding_team", "Fielding team name."),
             ("entitled_team_id", "Team entitled to challenge the call: batting team for OFFENSE (incorrect strike), fielding team for DEFENSE (incorrect ball)."),
             ("entitled_team", "Name of entitled_team_id."),
             ("batter_id", "Batter MLBAM ID."), ("batter_name", "Batter name."), ("pitcher_id", "Pitcher MLBAM ID."),
             ("pitcher_name", "Pitcher name."), ("catcher_id", "Catcher MLBAM ID (Statcast fielder_2)."), ("catcher_name", "Catcher name."),
             ("umpire_id", "Home-plate umpire ID."), ("umpire_name", "Home-plate umpire name."), ("venue", "Venue name."),
             ("source_game_feed", "SHA-256 of the immutable feed object used for this game."),
             ("source_savant", "SHA-256 of the Statcast object that supplied the pitch row.")]:
    doc(f, t, timing=ID, source=PT)
doc("opportunity_side", "OFFENSE = original STRIKE whose derived ABS call is BALL (the Articles 1-3 'incorrect called strike'); DEFENSE = original BALL whose derived ABS call is STRIKE (extension; not part of the Articles 1-3 population).", timing=ID, source=DER)
doc("eligibility_status", "ELIGIBLE (legal challenge available: inventory > 0, pitcher not a position player, known availability), INELIGIBLE_EXHAUSTED, INELIGIBLE_POSITION_PLAYER_PITCHING, UNKNOWN_AVAILABILITY. The OFFENSE ELIGIBLE set equals the Articles 1-3 population exactly.", timing=PRE, source=DER)

# ---- pre-pitch game state
for f, t in [("inning", "Inning."), ("half_inning", "top/bottom."), ("outs", "Outs before the pitch."),
             ("balls", "Balls before the pitch."), ("strikes", "Strikes before the pitch."),
             ("on_1b", "Runner MLBAM ID on first before the pitch (blank = empty)."), ("on_2b", "Runner ID on second before the pitch."),
             ("on_3b", "Runner ID on third before the pitch.")]:
    doc(f, t, timing=PRE, source=PT)
for f, t in [("inning_group", "Articles 1-3 inning group: EARLY 1-3, MIDDLE 4-6, LATE 7+."),
             ("inning_bucket", "Article 4 inning bucket: 1-3, 4-6, 7-9, 10+ (extra innings separated because inventory rules change)."),
             ("batting_team_score", "Batting-team runs before the pitch."), ("fielding_team_score", "Fielding-team runs before the pitch."),
             ("batting_score_diff", "batting_team_score - fielding_team_score."),
             ("entitled_team_score_diff", "Score differential from the entitled team's perspective."),
             ("base_state", "Pre-pitch occupancy string 1B2B3B, e.g. 101 = first and third."),
             ("count", "Pre-pitch count 'balls-strikes'."),
             ("late_close", "Context flag reused from Article 2: inning >= 7 and |batting_score_diff| <= 2. Not a leverage index."),
             ("strike_three_or_ball_four_at_stake", "True if either call ends the plate appearance (2 strikes or 3 balls before the pitch)."),
             ("RE_pre_pitch", "RE288 value of the pre-pitch state (primary table)."),
             ("challenge_inventory", "Entitled team's challenges remaining before the pitch (Articles 1-3 sequential reconstruction; affected_team_challenges_remaining)."),
             ("inventory_recomputed", "Entitled team's inventory independently recomputed in build.py from challenges.csv: start 2, lose one per CONFIRMED challenge, grant one at the start of an extra inning if none remain."),
             ("final_challenge_indicator", "challenge_inventory == 1: a failed challenge here would exhaust the team."),
             ("opponent_inventory", "The other team's recomputed inventory before the pitch."),
             ("offense_challenges_remaining", "Batting team inventory before the pitch (Articles 1-3)."),
             ("defense_challenges_remaining", "Fielding team inventory before the pitch (Articles 1-3)."),
             ("prior_team_challenges", "Entitled team's challenges earlier in the game (strictly earlier pitches)."),
             ("prior_team_challenges_overturned", "Of prior_team_challenges, number overturned (successful)."),
             ("prior_team_challenges_confirmed", "Of prior_team_challenges, number confirmed (unsuccessful)."),
             ("prior_team_offense_challenges", "Prior challenges by the entitled team's batters."),
             ("prior_team_defense_challenges", "Prior challenges by the entitled team's pitchers/catchers."),
             ("prior_team_eligible_incorrect_calls", "Earlier eligible incorrect calls against the entitled team in this game (either side). Uses derived geometry; a pre-pitch fact, not necessarily known to players."),
             ("prior_team_eligible_unchallenged", "Of prior_team_eligible_incorrect_calls, number not challenged."),
             ("prior_opponent_challenges", "Opponent's challenges earlier in the game."),
             ("extra_inning_grants_before", "Extra-inning challenge grants received by the entitled team before this pitch.")]:
    doc(f, t, timing=PRE, source=DER if f not in ("challenge_inventory", "offense_challenges_remaining", "defense_challenges_remaining") else PT)

# ---- pitch / ABS
for f, t in [("pitch_type", "Statcast pitch type code."), ("pitch_name", "Statcast pitch name."), ("release_speed", "Release speed (mph)."),
             ("plate_x", "Horizontal plate location (ft, catcher view)."), ("plate_z", "Vertical plate location (ft)."),
             ("abs_zone_top", "ABS zone top (ft) used by the Articles 1-3 geometry."), ("abs_zone_bot", "ABS zone bottom (ft)."),
             ("bat_side", "Batter side."), ("pitch_hand", "Pitcher hand."),
             ("original_call", "Umpire's original call (Articles 1-3)."), ("derived_abs_call", "Fixed a-priori ABS geometry call, abs_2026_circle_rectangle_r1.45in_v1 (Articles 1-3)."),
             ("official_abs_call", "Official ABS result when challenged."), ("displayed_call", "Call displayed in the feed (post-challenge)."),
             ("survival_class", "Articles 1-3 survival class."), ("survival_detail", "Articles 1-3 survival detail."),
             ("challenge_outcome", "OVERTURNED / CONFIRMED when challenged; blank otherwise.")]:
    doc(f, t, timing=PRE if f not in ("official_abs_call", "displayed_call", "challenge_outcome", "survival_class", "survival_detail") else POST, source=PT)
for f, t in [("pitch_family", "Articles 1-3 pitch family mapping."),
             ("signed_boundary_distance_inches", "Signed distance from ball edge to the ABS zone (inches); positive outside, negative inside."),
             ("abs_distance_inches", "Absolute boundary distance in inches (Articles 1-3 abs_distance_inches for OFFENSE; distance inside the zone for DEFENSE)."),
             ("miss_axis", "OFFENSE: Articles 1-3 miss axis (VERTICAL/HORIZONTAL/CORNER). DEFENSE: INSIDE_ZONE (the pitch is a strike; see miss_side)."),
             ("miss_side", "OFFENSE: Articles 1-3 miss side (ABOVE/BELOW/INSIDE/OUTSIDE/corner). DEFENSE: NEAREST_TOP/NEAREST_BOTTOM/NEAREST_INSIDE/NEAREST_OUTSIDE, the zone edge closest to the pitch."),
             ("horizontal_distance_inches", "OFFENSE only: horizontal distance outside the plate (Articles 1-3)."),
             ("vertical_distance_inches", "OFFENSE only: vertical distance outside the zone (Articles 1-3)."),
             ("corner_proximity_inches", "OFFENSE only: corner distance (Articles 1-3)."),
             ("challenged", "True if the entitled team challenged this pitch."),
             ("recognized_article1_3", "Articles 1-3 outcome (1 = batter challenged); OFFENSE eligible rows only; equals challenged."),
             ("expected_recognition_prob_article3", "Articles 1-3 contextual expected recognition probability (Sprint 4 Model C refit without batter identity, full-season in-sample fit). OFFENSE eligible rows only. Model parameters use the whole season."),
             ("expected_recognition_prob_temporal", "Sprint 3 expanding-window Model C (C_SITUATION) held-out probability, trained only on earlier months; blank for March (no prior month). OFFENSE only."),
             ("expected_recognition_temporal_fold", "Test month of expected_recognition_prob_temporal."),
             ("opportunity_difficulty_bucket", "Quintile of expected_recognition_prob_article3 across the 10,755 OFFENSE opportunities (Q1 = lowest expected recognition, hardest). New Article 4 field; Sprint 4's batter-level difficulty label is unchanged.")]:
    doc(f, t, timing=PRE if f not in ("challenged", "recognized_article1_3") else POST, source=DER if "article3" not in f and "temporal" not in f else (S4 if "article3" in f else S3))

# ---- feed / post-pitch
for f, t in [("feed_call_code", "Feed call code for the pitch (B, *B, C, ...), post-challenge."),
             ("feed_call", "Feed call mapped to BALL/STRIKE (post-challenge)."),
             ("feed_description", "Feed pitch description."),
             ("feed_pa_result_event", "Plate-appearance result event (end of PA; may be after this pitch)."),
             ("feed_pa_result_description", "Plate-appearance result text (end of PA)."),
             ("feed_pitch_review_type", "reviewDetails.reviewType on the pitch (MJ = ABS challenge)."),
             ("feed_pitch_review_overturned", "reviewDetails.isOverturned on the pitch."),
             ("feed_pitch_start_time", "Feed pitch event startTime (UTC)."), ("feed_pitch_end_time", "Feed pitch event endTime (UTC)."),
             ("attached_event_types", "JSON list of feed events linked to this pitch: baserunning actions whose actionPlayId equals the pitch playId, plus an immediately following pickoff event with fromCatcher=true."),
             ("attached_event_descriptions", "JSON list of the linked events' descriptions."),
             ("attached_event_is_baserunning", "JSON list of the linked events' isBaseRunningPlay flags."),
             ("attached_movements", "JSON list of runner movements whose playIndex is the pitch or a linked event (runner, start, end, isOut, event, movementReason)."),
             ("attached_credits", "JSON list of fielding credits (credit:position) on non-batter runner movements for the pitch and linked events."),
             ("catcher_pickoff_throw_after_pitch", "The next feed event after the pitch is a pickoff with fromCatcher=true."),
             ("secondary_review_json", "reviewDetails on any linked baserunning action (replay review of a secondary play)."),
             ("next_event_type", "Type of the next feed event in the plate appearance (raw)."),
             ("next_event_from_catcher", "fromCatcher flag of the next event (pickoffs only)."),
             ("state_changing_events_before_next_pitch", "JSON list of non-pitch events between this pitch and the next pitch that changed count, bases, or outs (automatic balls/strikes, intentional walks, balks, pickoffs, catcher interference), plus plate appearances without a pitch; audit field."),
             ("unlinked_baserunning_before_next_pitch", "Baserunning actions before the next pitch that are NOT linked to this pitch (e.g., pitcher pickoffs, balks); audit field.")]:
    doc(f, t, timing=POST, source=FEED)
doc("feed_call_matches_expected", "Feed call equals the original call (unchallenged/confirmed) or the official ABS call (challenged).", timing=POST, source=DER)
doc("observed_state_is_reconstructed", "True for OVERTURNED challenges: the feed shows the corrected outcome, so the 'observed' (incorrect-call-stood) state is the reconstructed one and the corrected state is the one the feed recorded.", timing=POST, source=DER)
for prefix, label in (("obs", "OBSERVED state = state produced if the incorrect original call stands"),
                      ("cor", "CORRECTED state = state produced if ABS corrects the call")):
    for f, t in [("balls", "balls at the next decision point (0 if the PA ended)"), ("strikes", "strikes at the next decision point"),
                 ("outs", "outs after the pitch (3 = half-inning over)"), ("base_state", "base occupancy after the pitch"),
                 ("runs", "runs scored by the batting team on the pitch"), ("pa_status", "CONTINUES / WALK / STRIKEOUT"),
                 ("inning_ended", "half-inning ended on the pitch"), ("walkoff", "state ends the game (bottom 9+ and batting team takes the lead); future RE set to 0"),
                 ("state_valid", "state passes baseball validity checks")]:
        doc(f"{prefix}_{f}", f"{label}: {t}. Blank when the state is AMBIGUOUS.", timing=POST, source=DER)
for f, t in [("cf_rule", "Counterfactual rule applied: R1_NO_RUNNER_ACTION, R2_RUNNER_OUTCOME_STANDS, R3_TERMINAL_CALL_RUNNER_ACTION, R4_UNCAUGHT_THIRD_STRIKE, R5_UNSUPPORTED_MOVEMENT (see METHODOLOGY.md)."),
             ("cf_confidence", "EXACT (mechanical), RULE_BASED (documented ABS guidance applied), AMBIGUOUS (no primary state; bounds only)."),
             ("cf_ambiguity_reason", "Why the counterfactual is ambiguous."),
             ("actual_state_consistency", "CONSISTENT if the feed movements reconcile with the pre-pitch state and the recorded call; otherwise the discrepancy class."),
             ("alternative_states", "JSON of enumerated alternative states for AMBIGUOUS rows."),
             ("pa_outcome_changes", "Observed and corrected plate-appearance status differ (e.g., walk vs strikeout)."),
             ("next_pitch_state_check", "Independent check: reconstructed actual post-pitch state vs the Statcast pre-pitch state of the next pitch in the game (MATCH, MATCH_HALF_ENDED, INTERVENING_STATE_CHANGING_EVENT, MISMATCH, ...).")]:
    doc(f, t, timing=POST, source=DER)
for f, t in [("RE_observed", "Runs on the pitch + RE288(observed post-pitch state). Batting-team expected runs from the decision point to the end of the half-inning if the incorrect call stands."),
             ("RE_corrected", "Runs on the pitch + RE288(corrected post-pitch state)."),
             ("RE_delta_batting", "RE_observed - RE_corrected (batting-team perspective). Positive = the uncorrected call favored the batting team (typical for DEFENSE rows); negative for OFFENSE rows."),
             ("RE_delta_fielding", "-RE_delta_batting (fielding-team perspective)."),
             ("RE_observed_alternatives", "JSON of RE_observed under each enumerated alternative (AMBIGUOUS rows)."),
             ("RE_corrected_alternatives", "JSON of RE_corrected under each enumerated alternative (AMBIGUOUS rows)."),
             ("correction_value_runs", "Expected-run value of correcting the call to the ENTITLED team: -RE_delta_batting for OFFENSE, +RE_delta_batting for DEFENSE. Blank if AMBIGUOUS. Never uses subsequent realized runs."),
             ("correction_value_runs_lower", "Minimum correction value across enumerated alternatives (= correction_value_runs when not ambiguous)."),
             ("correction_value_runs_upper", "Maximum correction value across enumerated alternatives."),
             ("challenge_value_runs", "Challenged rows: correction_value_runs if OVERTURNED, 0 if CONFIRMED (inventory cost not included). Blank if not challenged."),
             ("missed_challenge_value_runs", "Unchallenged ELIGIBLE rows: correction_value_runs (value potentially recoverable). Blank otherwise."),
             ("unavailable_correction_value_runs", "Ineligible rows (exhausted, position player): correction value that no challenge could recover."),
             ("RE_observed_lomo", "RE_observed using an RE288 table fit without the game's month (leave-one-month-out sensitivity)."),
             ("RE_corrected_lomo", "RE_corrected, leave-one-month-out table."), ("RE_delta_batting_lomo", "RE_delta_batting, leave-one-month-out."),
             ("RE_delta_fielding_lomo", "RE_delta_fielding, leave-one-month-out."), ("correction_value_runs_lomo", "correction_value_runs, leave-one-month-out."),
             ("RE_observed_pooled", "RE_observed using the pooled-count sensitivity table (re_count_pooled)."),
             ("RE_corrected_pooled", "RE_corrected, pooled-count table."), ("RE_delta_batting_pooled", "RE_delta_batting, pooled-count table."),
             ("RE_delta_fielding_pooled", "RE_delta_fielding, pooled-count table."), ("correction_value_runs_pooled", "correction_value_runs, pooled-count sensitivity table."),
             ("re_ordering_violation", "Non-ambiguous row whose primary correction value is negative. Runner events are held equal between the two states, so the correct call cannot lower the entitled team's true run expectancy; the primary RE288 table (Sprint 5 smoothing toward the base-out mean) orders the two states against baseball logic in a sparse cell. Retained and flagged, not corrected; see correction_value_runs_pooled."),
             ("cf_unrecorded_runner_action_possible", "The recorded outcome is a walk with a forced runner and no linked runner action. A play on a forced runner (e.g., a steal attempt and tag) is nullified by the walk award and absent from every source, so the R1 counterfactual is exact only with respect to the record (see the Braves case study).")]:
    doc(f, t, timing=POST, source=DER)
for f, t in [("ca_stolen_base_attempt", "Linked stolen_base_*/caught_stealing_* action, or a runner movement whose event is Stolen Base/Caught Stealing, or a non-batter out on a Strikeout Double Play."),
             ("ca_stolen_base", "Linked stolen-base action or Stolen Base movement."), ("ca_caught_stealing", "Linked caught-stealing action or movement."),
             ("ca_catcher_throw_recorded", "A catcher (position C) assist, throwing/fielding error, or touch credit on a runner movement. Successful steals carry no throw credit, so False does not mean no throw."),
             ("ca_catcher_pickoff_throw", "The next event is a pickoff with fromCatcher=true."),
             ("ca_catcher_throw_any_evidence", "ca_catcher_throw_recorded OR ca_catcher_pickoff_throw."),
             ("ca_wild_pitch", "Linked wild_pitch action or Wild Pitch movement."), ("ca_passed_ball", "Linked passed_ball action or Passed Ball movement."),
             ("ca_pickoff_action", "Linked pickoff_* action (e.g., catcher pickoff out/error)."), ("ca_defensive_indifference", "Linked defensive_indiff action."),
             ("ca_runner_advance", "A non-batter runner advanced on the pitch other than by a walk force."),
             ("ca_runner_out", "A non-batter runner was put out on the pitch."), ("ca_error_on_play", "An error action, Error movement, or error credit on the pitch."),
             ("ca_secondary_play_reviewed", "A linked baserunning action carries replay reviewDetails."),
             ("ca_other_secondary_action", "A linked action type outside the classified set."), ("ca_other_secondary_types", "JSON of those types."),
             ("ca_any_secondary_action", "Any linked action, or any non-batter movement that is not a walk force.")]:
    doc(f, t, timing=POST, source=DER + " from " + FEED)

# ---- sequences
for f, t in [("team_game_id", "game_pk:entitled_team_id."), ("sequence_number", "1-based chronological position within the team-game."),
             ("sequence_length", "Rows in the team-game sequence."),
             ("sequence_event_class", "ELIGIBLE_INCORRECT_CALL, INELIGIBLE_INCORRECT_CALL_EXHAUSTED, INELIGIBLE_INCORRECT_CALL_POSITION_PLAYER_PITCHING, CHALLENGE_OF_GEOMETRY_CORRECT_CALL (a challenge on a call the geometry says was correct; it consumes inventory), CHALLENGE_CALL_GEOMETRY_UNAVAILABLE."),
             ("exercised", "The team challenged this pitch."),
             ("inventory_after", "Inventory after this event (minus one after a CONFIRMED challenge)."),
             ("realized_value_runs", "Value realized by the challenge: correction value if OVERTURNED, 0 if CONFIRMED; blank if not exercised.")]:
    doc(f, t, table="article4_team_game_sequences", timing=PRE if f != "realized_value_runs" else POST, source=DER)
for f, t in [("hindsight_later_eligible_opportunities", "Later ELIGIBLE incorrect calls in the same team-game."),
             ("hindsight_later_eligible_ambiguous", "Of those, AMBIGUOUS-valued."),
             ("hindsight_later_eligible_value_sum", "Sum of later eligible correction values (non-ambiguous)."),
             ("hindsight_later_eligible_value_max", "Maximum later eligible correction value (non-ambiguous)."),
             ("hindsight_later_challenges_used", "Later challenges by the team."),
             ("hindsight_later_realized_value_sum", "Sum of later realized challenge values."),
             ("hindsight_later_higher_value_opportunity", "ELIGIBLE rows: a later eligible opportunity had a higher correction value."),
             ("hindsight_later_higher_value_exercised", "ELIGIBLE rows: a later higher-value opportunity was challenged."),
             ("hindsight_later_exhausted_incorrect_calls", "Later incorrect calls against the team while exhausted."),
             ("hindsight_later_exhausted_value_sum", "Sum of their correction values.")]:
    doc(f, t + " HINDSIGHT: uses future events; never a decision-time predictor.", table="article4_team_game_sequences", timing=HIND, source=DER)

# ---- team summary
for f, t in [("entitled_team", "Team name, or ALL_TEAMS for league rows."), ("opportunity_side", "OFFENSE / DEFENSE."),
             ("inning_bucket", "1-3/4-6/7-9/10+ or ALL."), ("challenge_inventory", "Inventory before the opportunity (1, 2) or ALL."),
             ("opportunities", "Eligible opportunities."), ("challenged", "Challenged opportunities."), ("challenge_rate", "challenged / opportunities."),
             ("overturned", "Overturned challenges."), ("value_known_opportunities", "Non-ambiguous opportunities."),
             ("ambiguous_value_opportunities", "AMBIGUOUS opportunities (excluded from value sums)."),
             ("mean_correction_value_runs", "Mean correction value, non-ambiguous."), ("total_realized_value_runs", "Sum of challenge_value_runs, non-ambiguous."),
             ("total_missed_value_runs", "Sum of missed_challenge_value_runs, non-ambiguous."), ("mean_missed_value_runs", "Mean missed value among unchallenged, non-ambiguous."),
             ("mean_abs_distance_inches", "Mean boundary distance (inches)."), ("mean_expected_recognition_prob", "Mean Articles 1-3 expected recognition (OFFENSE)."),
             ("sum_expected_recognition_prob", "Expected challenges under the Articles 1-3 contextual model (OFFENSE)."),
             ("final_challenge_opportunities", "Opportunities with inventory == 1."), ("competing_attention_opportunities", "Opportunities with any linked secondary action."),
             ("summary_level", "Grouping keys of the row.")]:
    doc(f, t, table="article4_team_summary", timing="SUMMARY", source=DER)

# ---- high value / spot checks
for f, t in [("high_value_rank", "Rank by ranking_value_runs among unchallenged eligible opportunities."),
             ("ranking_value_runs", "correction_value_runs, or its lower bound for AMBIGUOUS rows."),
             ("value_is_bound", "True if ranking_value_runs is a lower bound (AMBIGUOUS row).")]:
    doc(f, t, table="article4_high_value_missed", timing=POST, source=DER)
for f, t in [("spot_check_reason", "Why the row was selected for review."),
             ("automated_check_pass", "Next-pitch state check passes and the feed call is as expected."),
             ("manual_review_note", "Analyst's note from manual review against source play-by-play (manual_review_notes.json).")]:
    doc(f, t, table="article4_spot_checks", timing="AUDIT", source=DER)

# ---- RE tables
for f, t in [("balls", "Balls."), ("strikes", "Strikes."), ("outs", "Outs."), ("base_state", "Base occupancy 1B2B3B."),
             ("raw_mean", "Mean runs from this pitch to the end of the half-inning (feed-replayed runs)."),
             ("n_pitches", "Pitches observed in the state (innings 1-8, complete half-innings)."), ("sd", "Standard deviation of future runs."),
             ("n_half_innings", "Distinct half-innings contributing."),
             ("count_effect_pooled", "Mean (future runs - base-out mean) for the count and outs, pooled across base states."),
             ("re_count_pooled", "Sensitivity RE: base_out_mean + count_effect_pooled."), ("base_out_mean", "Base-out mean (all counts)."),
             ("base_out_n", "Pitches in the base-out state."), ("re_smoothed", "(raw_mean*n + 40*base_out_mean)/(n + 40); the value used for lookup (Sprint 5 smoothing convention).")]:
    doc(f, t, table="article4_re288_table", timing=CONST, source=DER)
for f, t in [("outs", "Outs."), ("base_state", "Base occupancy."), ("re24", "Mean runs to end of half-inning at the first pitch of a plate appearance."),
             ("n_plate_appearances", "Plate appearances observed.")]:
    doc(f, t, table="article4_re24_table", timing=CONST, source=DER)

# ---- Braves
BR = "article4_braves_case_study"
for f, t in [("game_pk", "Game."), ("source_scope", "SNAPSHOT (accepted research snapshot) or POST_SNAPSHOT_CASE_STUDY_ONLY (archived after 2026-09-09 for this search only)."),
             ("feed_sha256", "Feed object hash."), ("game_date", "Date."), ("away", "Away team."), ("home", "Home team."),
             ("final_away", "Final away runs."), ("final_home", "Final home runs."), ("inning", "Inning."), ("half_inning", "Half."),
             ("pitch_key", "Pitch key."), ("batter", "Batter."), ("pitcher", "Pitcher."), ("pre_count", "Pre-pitch count."),
             ("pre_outs", "Pre-pitch outs."), ("pre_bases", "Pre-pitch occupancy."), ("plate_x", "Feed pX."), ("plate_z", "Feed pZ."),
             ("zone_top", "Feed strikeZoneTop."), ("zone_bottom", "Feed strikeZoneBottom."),
             ("derived_abs_call", "Articles 1-3 geometry applied to feed coordinates."), ("signed_boundary_distance_inches", "Signed distance (inches)."),
             ("pitch_review_type", "Pitch reviewType."), ("pitch_review_overturned", "Pitch review overturned."),
             ("attached_event_types", "Linked events."), ("attached_event_descriptions", "Linked event text."),
             ("pa_result_description", "Plate-appearance result."), ("criteria_matched", "Number of recollection criteria matched."),
             ("criteria_total", "Criteria evaluated.")]:
    doc(f, t, table=BR, timing="AUDIT", source=FEED)
for c in ["braves_fielding", "first_inning", "runner_on_first_pre", "one_out_pre", "count_3_2_pre", "called_ball_four",
          "steal_attempt_on_pitch", "catcher_throw_recorded", "secondary_play_reviewed", "geometry_strike", "near_top_of_zone",
          "not_successfully_challenged", "inning_continued", "later_walk_in_inning", "later_home_run_in_inning",
          "braves_trailed_5_0_after_first", "final_score_5_1_braves_loss"]:
    doc(f"criterion_{c}", f"Recollection criterion '{c.replace('_', ' ')}' matched by the source data (near_top_of_zone: |pZ - zone top| <= 3 inches).", table=BR, timing="AUDIT", source=FEED)
for c, txt in [("rev_game_2026_08_10_vs_mets", "game is 2026-08-10 against the Mets"), ("rev_batter_carson_benge", "batter is Carson Benge"),
               ("rev_bichette_on_first", "Bo Bichette on first (advanced on the walk)"), ("rev_pitcher_elder", "pitcher is Bryce Elder"),
               ("rev_baty_homer_three_batters_later", "Brett Baty homered three batters later"), ("rev_mets_lead_5_0_after_homer", "the home run made it 5-0")]:
    doc(f"criterion_{c}", f"Revised-account criterion (user clarification, 2026-09-23): {txt}.", table=BR, timing="AUDIT", source=FEED)
doc("revised_criteria_matched", "Revised-account criteria matched.", table=BR, timing="AUDIT", source=DER)
doc("revised_criteria_total", "Revised-account criteria evaluated.", table=BR, timing="AUDIT", source=DER)
doc("identification_status", "IDENTIFIED_USER_CONFIRMED_GAME for the pitch matching every revised criterion in the user-identified game; otherwise NOT_THE_CASE.", table=BR, timing="AUDIT", source=DER)
BS = "article4_braves_case_study_sequence"
for f, t in [("game_pk", "Game."), ("at_bat_index", "Plate appearance."), ("event_index", "Event index."), ("batter", "Batter."),
             ("event_type", "Feed event type."), ("call_code", "Call code."), ("description", "Event description."),
             ("balls_after", "Balls after event."), ("strikes_after", "Strikes after event."), ("outs_after", "Outs after event."),
             ("plate_z", "pZ."), ("zone_top", "strikeZoneTop."), ("review", "reviewDetails JSON."),
             ("pa_result", "PA result text (last event of PA)."), ("away_score_after_pa", "Away score after PA."), ("home_score_after_pa", "Home score after PA.")]:
    doc(f, t, table=BS, timing="AUDIT", source=FEED)
BG = "article4_braves_game_scores"
for f, t in [("game_pk", "Game."), ("source_scope", "SNAPSHOT or POST_SNAPSHOT_CASE_STUDY_ONLY."), ("game_date", "Date."),
             ("braves_runs", "Braves final runs."), ("opponent_runs", "Opponent final runs."), ("opponent_first_inning_runs", "Opponent first-inning runs.")]:
    doc(f, t, table=BG, timing="AUDIT", source=FEED)

FIELD_DOCS = D

CA_LIST = ["ca_stolen_base_attempt", "ca_stolen_base", "ca_caught_stealing", "ca_catcher_throw_recorded", "ca_catcher_pickoff_throw",
           "ca_catcher_throw_any_evidence", "ca_wild_pitch", "ca_passed_ball", "ca_pickoff_action", "ca_defensive_indifference",
           "ca_runner_advance", "ca_runner_out", "ca_error_on_play", "ca_secondary_play_reviewed", "ca_other_secondary_action",
           "ca_other_secondary_types", "ca_any_secondary_action"]

OPP_COLUMNS = [
    "article4_opportunity_id", "pitch_key", "game_pk", "game_date", "at_bat_index", "play_event_index", "play_id", "physical_pitch_ordinal",
    "opportunity_side", "eligibility_status", "batting_team_id", "batting_team", "fielding_team_id", "fielding_team",
    "entitled_team_id", "entitled_team", "home_team_id", "home_team", "away_team_id", "away_team",
    "batter_id", "batter_name", "pitcher_id", "pitcher_name", "catcher_id", "catcher_name", "umpire_id", "umpire_name", "venue",
    "inning", "half_inning", "inning_group", "inning_bucket", "batting_team_score", "fielding_team_score", "batting_score_diff",
    "entitled_team_score_diff", "outs", "on_1b", "on_2b", "on_3b", "base_state", "balls", "strikes", "count", "late_close",
    "strike_three_or_ball_four_at_stake", "RE_pre_pitch",
    "challenge_inventory", "inventory_recomputed", "final_challenge_indicator", "opponent_inventory", "offense_challenges_remaining",
    "defense_challenges_remaining", "prior_team_challenges", "prior_team_challenges_overturned", "prior_team_challenges_confirmed",
    "prior_team_offense_challenges", "prior_team_defense_challenges", "prior_team_eligible_incorrect_calls",
    "prior_team_eligible_unchallenged", "prior_opponent_challenges", "extra_inning_grants_before",
    "pitch_type", "pitch_name", "pitch_family", "release_speed", "plate_x", "plate_z", "abs_zone_top", "abs_zone_bot",
    "signed_boundary_distance_inches", "abs_distance_inches", "miss_axis", "miss_side", "horizontal_distance_inches",
    "vertical_distance_inches", "corner_proximity_inches", "bat_side", "pitch_hand", "original_call", "derived_abs_call",
    "official_abs_call", "displayed_call", "survival_class", "survival_detail", "challenged", "recognized_article1_3",
    "challenge_outcome", "expected_recognition_prob_article3", "expected_recognition_prob_temporal",
    "expected_recognition_temporal_fold", "opportunity_difficulty_bucket",
    "feed_call_code", "feed_call", "feed_description", "feed_call_matches_expected", "feed_pa_result_event",
    "feed_pa_result_description", "feed_pitch_review_type", "feed_pitch_review_overturned", "observed_state_is_reconstructed",
    "obs_balls", "obs_strikes", "obs_outs", "obs_base_state", "obs_runs", "obs_pa_status", "obs_inning_ended", "obs_walkoff", "obs_state_valid",
    "cor_balls", "cor_strikes", "cor_outs", "cor_base_state", "cor_runs", "cor_pa_status", "cor_inning_ended", "cor_walkoff", "cor_state_valid",
    "cf_rule", "cf_confidence", "cf_ambiguity_reason", "actual_state_consistency", "alternative_states", "pa_outcome_changes",
    "next_pitch_state_check",
    "RE_observed", "RE_corrected", "RE_delta_batting", "RE_delta_fielding", "RE_observed_alternatives", "RE_corrected_alternatives",
    "correction_value_runs", "correction_value_runs_lower", "correction_value_runs_upper", "challenge_value_runs",
    "missed_challenge_value_runs", "unavailable_correction_value_runs",
    "RE_observed_lomo", "RE_corrected_lomo", "RE_delta_batting_lomo", "RE_delta_fielding_lomo", "correction_value_runs_lomo",
    "RE_observed_pooled", "RE_corrected_pooled", "RE_delta_batting_pooled", "RE_delta_fielding_pooled", "correction_value_runs_pooled",
    "re_ordering_violation", "cf_unrecorded_runner_action_possible",
] + CA_LIST + [
    "attached_event_types", "attached_event_descriptions", "attached_event_is_baserunning", "attached_movements", "attached_credits",
    "catcher_pickoff_throw_after_pitch", "secondary_review_json", "next_event_type", "next_event_from_catcher",
    "unlinked_baserunning_before_next_pitch", "state_changing_events_before_next_pitch", "feed_pitch_start_time", "feed_pitch_end_time", "source_game_feed", "source_savant",
]

SEQ_COLUMNS = ["team_game_id", "game_pk", "game_date", "entitled_team_id", "entitled_team", "sequence_number", "sequence_length",
               "pitch_key", "at_bat_index", "play_event_index", "inning", "half_inning", "opportunity_side", "sequence_event_class",
               "eligibility_status", "exercised", "challenge_outcome", "challenge_inventory", "inventory_after", "inventory_recomputed",
               "count", "outs", "base_state", "entitled_team_score_diff", "abs_distance_inches", "expected_recognition_prob_article3",
               "correction_value_runs", "correction_value_runs_lower", "correction_value_runs_upper", "cf_confidence",
               "ca_any_secondary_action", "realized_value_runs",
               "hindsight_later_eligible_opportunities", "hindsight_later_eligible_ambiguous", "hindsight_later_eligible_value_sum",
               "hindsight_later_eligible_value_max", "hindsight_later_challenges_used", "hindsight_later_realized_value_sum",
               "hindsight_later_higher_value_opportunity", "hindsight_later_higher_value_exercised",
               "hindsight_later_exhausted_incorrect_calls", "hindsight_later_exhausted_value_sum"]

HV_COLUMNS = ["high_value_rank", "ranking_value_runs", "value_is_bound", "article4_opportunity_id", "pitch_key", "game_date", "game_pk",
              "opportunity_side", "entitled_team", "batting_team", "fielding_team", "batter_name", "pitcher_name", "catcher_name",
              "inning", "half_inning", "batting_score_diff", "count", "outs", "base_state", "challenge_inventory",
              "final_challenge_indicator", "abs_distance_inches", "miss_side", "expected_recognition_prob_article3",
              "obs_balls", "obs_strikes", "obs_outs", "obs_base_state", "obs_runs", "obs_pa_status",
              "cor_balls", "cor_strikes", "cor_outs", "cor_base_state", "cor_runs", "cor_pa_status",
              "cf_rule", "cf_confidence", "RE_observed", "RE_corrected", "RE_delta_batting", "correction_value_runs",
              "correction_value_runs_lower", "correction_value_runs_upper", "missed_challenge_value_runs", "correction_value_runs_lomo",
              "ca_any_secondary_action", "attached_event_descriptions", "feed_description", "feed_pa_result_description",
              "next_pitch_state_check"]

SPOT_COLUMNS = ["spot_check_reason", "pitch_key", "game_date", "opportunity_side", "inning", "half_inning", "count", "outs", "base_state",
                "challenged", "challenge_outcome", "feed_description", "feed_pa_result_description", "attached_event_descriptions",
                "obs_balls", "obs_strikes", "obs_outs", "obs_base_state", "obs_runs", "obs_pa_status",
                "cor_balls", "cor_strikes", "cor_outs", "cor_base_state", "cor_runs", "cor_pa_status",
                "cf_rule", "cf_confidence", "RE_observed", "RE_corrected", "correction_value_runs", "next_pitch_state_check",
                "feed_call_matches_expected", "automated_check_pass", "manual_review_note"]

DECISION_TIME_FIELDS = [f for (t, f), d in D.items() if d["timing"] == PRE and t == "*"]

TABLES = {
    "article4_opportunities": "One row per ELIGIBLE incorrect call (OFFENSE = Articles 1-3 population; DEFENSE = extension). article4_all_incorrect_calls.csv has the same columns for every incorrect call, including ineligible ones.",
    "article4_team_game_sequences": "Chronological challenge-relevant events per team-game.",
    "article4_team_summary": "Descriptive team and league challenge behavior by side, inning bucket and inventory.",
    "article4_high_value_missed": "Top unchallenged eligible opportunities by correction value, with review context.",
    "article4_competing_attention": "Eligible opportunities with a source-linked secondary action (columns defined under article4_opportunities).",
    "article4_re288_table": "Count-aware run-expectancy table.", "article4_re24_table": "Base-out run-expectancy table (reference).",
    "article4_braves_case_study": "Candidate pitches evaluated against the remembered Braves play.",
    "article4_braves_case_study_sequence": "Full event sequence of the best candidate's half-inning.",
    "article4_braves_game_scores": "Every Braves game searched, with final and first-inning scores.",
    "article4_spot_checks": "Rows selected for automated and manual review (columns defined under article4_opportunities).",
}


def write_dictionary(path: Path, table_columns: dict) -> None:
    lines = ["# Article 4 data dictionary", "", "Generated from `fields.py`; build.py refuses to write undocumented columns.", "",
             "Timing: DECISION_TIME = known before the pitch (pre-pitch state or strictly earlier pitches); POST_PITCH = produced by or after the pitch; HINDSIGHT = uses later events in the game and must not be used as a decision-time predictor; STATIC = season-level table.", ""]
    for table, cols in table_columns.items():
        lines += [f"## {table}", "", TABLES.get(table, ""), "", "| field | timing | source | definition |", "|---|---|---|---|"]
        for c in cols:
            d = D.get((table, c)) or D.get(("*", c))
            lines.append(f"| `{c}` | {d['timing']} | {d['source']} | {d['text'].replace('|', '/')} |")
        lines.append("")
    path.write_text("\n".join(lines) + "\n")
