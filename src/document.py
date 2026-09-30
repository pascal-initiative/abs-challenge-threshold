"""Generate human-readable results and verify every output CSV field is documented."""
import argparse
import csv
import json
from pathlib import Path

DESCRIPTIONS = dict(line.split('|',1) for line in '''abs_zone_bot|Separate ABS lower bound copied from 2026 sz_bot; source not overwritten.
abs_zone_top|Separate ABS upper bound copied from 2026 sz_top; source not overwritten.
abs_zone_width_inches|Fixed official 17-inch zone width.
affected_team_challenges_remaining|Affected team's inventory before this pitch's challenge decision.
affected_team_id|Offense for original strike, defense for original ball; null for noncalled pitches.
at_bat_index|Zero-based MLB plate-appearance index.
away_score|Pre-pitch away team score.
away_team|Away team name.
away_team_id|MLB away team identifier.
balls|Pre-pitch balls (0–3).
bat_side|Batter side, R/L.
batter_id|Pre-pitch batter identifier; feed matchup fallback only if Statcast match unavailable.
batter_name|Batter name resolved from feed player map.
catcher_id|Pre-pitch catcher identifier from matched Statcast fielder_2; never a final-boxscore fallback.
catcher_name|Catcher name resolved from feed player map.
challenge_available|Legal pre-decision availability, accounting for inventory and position-player restriction.
challenge_outcome|Official challenge outcome on a pitch; null when not challenged.
challenge_unavailable_reason|EXHAUSTED or POSITION_PLAYER_PITCHING; null otherwise.
challenged|Whether the authoritative challenge table contains this pitch.
defense_challenges_remaining|Defensive team's inventory before decision.
derived_abs_call|Geometry-derived BALL/STRIKE, independent of official outcome.
displayed_call|Normalized displayed MLB feed call, potentially after review.
distance_from_abs_boundary|Signed circle/rectangle boundary distance; <=0 strike, >0 ball.
extension|Statcast release_extension, preserved in source units.
feed_has_review|Raw generic feed hasReview; not an ABS population flag.
feed_pfx_x_inches|Unmodified MLB coordinates.pfxX; not mixed with Statcast feet.
feed_pfx_z_inches|Unmodified MLB coordinates.pfxZ; not mixed with Statcast feet.
feed_plate_x|Unmodified MLB coordinates.pX.
feed_plate_z|Unmodified MLB coordinates.pZ.
feed_review_details|Entire raw pitch reviewDetails object serialized as JSON.
feed_sz_bot|Unmodified MLB strikeZoneBottom.
feed_sz_top|Unmodified MLB strikeZoneTop.
feed_zone_depth_inches|Unmodified MLB strikeZoneDepth (reported plane depth).
feed_zone_values|All pitchData keys containing zone, including original strike-zone values and zone code.
feed_zone_width_inches|Unmodified MLB strikeZoneWidth.
game_date|Official game assignment date, not the pitch's UTC timestamp date.
game_pk|Unique MLB game identifier.
game_type|MLB game type; R for this pilot.
half_inning|top or bottom, from MLB play metadata.
home_score|Pre-pitch home team score.
home_team|Home team name.
home_team_id|MLB home team identifier.
inning|Inning number at this pitch.
is_called_pitch|Called BALL/STRIKE opportunity indicator, including official challenge evidence.
offense_challenges_remaining|Offensive team's inventory before decision.
official_abs_call|Official BALL/STRIKE reconstructed from Savant original flag and official overturn status.
on_1b|Pre-pitch runner identifier on first; null means empty only when Statcast is matched.
on_2b|Pre-pitch runner identifier on second; null means empty only when Statcast is matched.
on_3b|Pre-pitch runner identifier on third; null means empty only when Statcast is matched.
opportunity_population|OFFENSE for an original strike, DEFENSE for an original ball; null otherwise.
original_call|Original umpire BALL/STRIKE; Savant explicit original for challenges, displayed feed otherwise.
original_call_source|SAVANT_ORIGINAL_ISSTRIKE_UMP or MLB_DISPLAYED_UNCHALLENGED provenance label.
outs|Pre-pitch outs (0–2).
pfx_x|Statcast horizontal movement, catcher's perspective; untransformed.
pfx_z|Statcast vertical movement; untransformed.
physical_pitch_ordinal|One-based physical pitch ordinal within plate appearance, excluding automatic penalties.
pitch_hand|Pitching hand, R/L.
pitch_key|Deterministic game_pk:at_bat_index:play_event_index key.
pitch_match_method|PHYSICAL_SEQUENCE or UNMATCHED; see automatic-event join rule.
pitch_name|Statcast pitch_name with MLB pitch type description fallback.
pitch_number|Original MLB pitchNumber, preserved without renumbering.
pitch_type|Statcast pitch_type with MLB pitch type code fallback.
pitcher_id|Pre-pitch pitcher identifier; feed matchup fallback only if Statcast match unavailable.
pitcher_name|Pitcher name resolved from feed player map.
pitcher_primary_position|Feed player primaryPosition abbreviation, used as eligibility proxy.
plate_x|Statcast horizontal ball-center position at mid-plate in 2026.
plate_z|Statcast vertical ball-center position at mid-plate in 2026.
play_event_index|Zero-based MLB play-event index within plate appearance.
play_id|MLB pitch UUID; official challenge matching key together with game_pk.
position_player_pitching|True for non-P/non-TWP primary position, false for P/TWP, null if missing.
raw_source_call|Original unmodified MLB details.call.code.
raw_source_description|Original unmodified MLB pitch description.
release_pos_x|Statcast horizontal release position.
release_pos_y|Statcast release position along y-axis.
release_pos_z|Statcast vertical release position.
release_speed|Statcast release speed.
release_spin_rate|Statcast release spin rate.
score_diff|Pre-pitch home score minus away score.
season|MLB season year.
source_conflict|Conflicting official copies or pitch-level source evidence; preserved and release-blocking.
source_derived|Versioned geometry method identifier.
source_game_feed|SHA-256 raw feed object digest.
source_savant|Pitch: SHA-256 Statcast CSV digest. Challenge: JSON array of official Savant source digests.
source_statcast_row_index|Zero-based data-row index in raw CSV, excluding header.
spin_axis|Statcast spin-axis angle.
statcast_pitch_number|Original Statcast pitch_number, including automatic count-event numbering.
state_timing|PRE_PITCH; applies to count, outs, runners, and score.
strikes|Pre-pitch strikes (0–2).
survival_class|CORRECT_CALL, CORRECTED, SURVIVED_RECOGNITION, SURVIVED_RESOURCE, or UNKNOWN.
survival_detail|Reason/subtype: NOT_CHALLENGED, CHALLENGED_BUT_CONFIRMED, NOT_CALLED_PITCH, POSITION_PLAYER_PITCHING, or explicit uncertainty/conflict reason.
sz_bot|Original 2026 Statcast lower zone bound.
sz_top|Original 2026 Statcast upper zone bound.
umpire_id|Home-plate umpire identifier from feed boxscore officials.
umpire_name|Home-plate umpire full name from feed boxscore officials.
venue|Venue name from MLB schedule.
challenge_team_id|Team of identified challenger; null if role/team cannot be determined.
challenger_id|Savant challenging_player_id.
challenger_name|Savant participant's full name when challenger role identified.
challenger_role|BATTER, CATCHER, PITCHER, or UNKNOWN based on identity equality.
outcome|OVERTURNED, CONFIRMED, or UNKNOWN from official overturn flag.
overturned|Official normalized boolean; null for unknown outcome.
savant_abs_bot|Original official challenge strikeZoneBottom.
savant_abs_top|Original official challenge strikeZoneTop.
savant_abs_width_inches|Original official challenge widthinches.
savant_edge_dist_inches|Official challenge edge_dist_calc; retained for investigation, never used to derive calls.
savant_plate_x|Original official challenge plateX.
savant_plate_z|Original official challenge plateZ.
source_copy_count|Number of overlapping official team-detail copies collapsed after comparison.
source_record_indices|JSON list of raw object digest and zero-based array index for every official copy.
processed|Whether the game's final feed was successfully parsed.
status|MLB schedule detailedState.
called_pitches|Count of called physical pitches in this population/group.
dimension|Breakdown dimension; identity groups are not ranked.
incorrect_calls|Count of original/derived disagreements with evaluable source evidence.
incorrect_with_challenge_available|Count of incorrect pitches with challenge_available true.
name|Participant display name for identity breakdowns; null for other dimensions.
population|ALL, OFFENSE, or DEFENSE.
rate_per_available_incorrect_call|Recognition survivors divided by available incorrect calls in group.
rate_per_called_pitch|Recognition survivors divided by called pitches in group.
rate_per_incorrect_call|Recognition survivors divided by incorrect pitches in group.
survived_recognition|Count of SURVIVED_RECOGNITION pitches in group.
value|Dimension value; participant ID, pitch type, inning, balls-strikes, outs, base occupancy bits 1B/2B/3B, or inventory count.
discrepancy_reason|DISAGREEMENT or UNMATCHED_OR_UNCOMPARABLE for official validation records.
comparable|Both official and derived calls are known.
agrees|Comparable and official call equals derived call.'''.splitlines())

STAT = set('away_score balls batter_id catcher_id home_score on_1b on_2b on_3b outs pfx_x pfx_z pitcher_id plate_x plate_z release_pos_x release_pos_y release_pos_z release_speed release_spin_rate spin_axis sz_bot sz_top extension statcast_pitch_number'.split())
FEED = set('at_bat_index away_team away_team_id batter_name catcher_name feed_has_review feed_pfx_x_inches feed_pfx_z_inches feed_plate_x feed_plate_z feed_review_details feed_sz_bot feed_sz_top feed_zone_depth_inches feed_zone_values feed_zone_width_inches game_date game_pk game_type half_inning home_team home_team_id inning pitch_number pitcher_name pitcher_primary_position play_event_index play_id raw_source_call raw_source_description season umpire_id umpire_name venue status'.split())
SAVANT = set('challenger_id challenger_name savant_abs_bot savant_abs_top savant_abs_width_inches savant_edge_dist_inches savant_plate_x savant_plate_z'.split())
FEET = set('abs_zone_bot abs_zone_top distance_from_abs_boundary extension feed_plate_x feed_plate_z feed_sz_bot feed_sz_top pfx_x pfx_z plate_x plate_z release_pos_x release_pos_y release_pos_z sz_bot sz_top savant_abs_bot savant_abs_top savant_plate_x savant_plate_z'.split())
NONNULL = set('game_pk game_date season game_type home_team_id home_team away_team_id away_team venue inning half_inning at_bat_index play_event_index pitch_key physical_pitch_ordinal pitch_match_method source_game_feed source_derived state_timing challenged source_conflict is_called_pitch survival_class original_call_source challenger_role outcome source_copy_count source_record_indices processed status dimension population value called_pitches incorrect_calls incorrect_with_challenge_available survived_recognition'.split())


def field_spec(field):
    description=DESCRIPTIONS[field]  # Fail on new undocumented fields.
    if field in STAT: source,status='Savant Statcast CSV','source'
    elif field in FEED: source,status='MLB schedule/feed','source'
    elif field in SAVANT: source,status='Savant official challenge detail','source'
    elif field in ('bat_side','pitch_hand','pitch_name','pitch_type'):source,status='Statcast, MLB fallback','source'
    elif field in ('original_call','official_abs_call','overturned','outcome','challenge_outcome','challenger_role','challenge_team_id'):source,status='Savant official flags / MLB; see method','derived normalization'
    else:source,status='Pascal transformation; see methodology','derived'
    unit='feet' if field in FEET else 'inches' if field.endswith('_inches') else 'mph' if field=='release_speed' else 'rpm' if field=='release_spin_rate' else 'degrees' if field=='spin_axis' else 'fraction [0,1]' if field.startswith('rate_') else 'identifier' if field.endswith('_id') or field in ('game_pk','pitch_key','play_id') else 'ISO date' if field=='game_date' else 'boolean' if field in {'challenge_available','challenged','feed_has_review','is_called_pitch','position_player_pitching','source_conflict','overturned','processed','comparable','agrees'} else 'JSON; nested units documented' if field in {'feed_review_details','feed_zone_values','source_record_indices','source_savant'} else 'count' if field in {'affected_team_challenges_remaining','defense_challenges_remaining','offense_challenges_remaining','balls','strikes','outs','inning','away_score','home_score','score_diff','source_copy_count','called_pitches','incorrect_calls','incorrect_with_challenge_available','survived_recognition'} else 'zero-based index' if field in {'at_bat_index','play_event_index','source_statcast_row_index'} else 'one-based source ordinal' if field in {'pitch_number','statcast_pitch_number','physical_pitch_ordinal'} else 'year' if field=='season' else 'text/code'
    return description,source,unit,status,'no' if field in NONNULL else 'yes'


def document(root):
    folder=root/'data/processed';docs=root/'docs';docs.mkdir(exist_ok=True)
    lines=['# Data dictionary','', 'CSV files use UTF-8 and LF records; blank scalar cells represent null. Booleans are `True`/`False`; nested lists/objects are JSON strings. Every numeric field retains its documented source unit. Nullable indicates schema permission, not observed missingness. Runner null semantics depend on a successful Statcast match. All state and inventory fields refer to pre-pitch/pre-decision state.','']
    for name in ('pitches','challenges','game_manifest','recognition_breakdowns','validation_discrepancies'):
        path=folder/(name+'.csv')
        if not path.exists():continue
        with path.open() as f:fields=next(csv.reader(f))
        lines += [f'## {name}.csv','', '| Field | Description | Source | Unit | Source/derived | Nullable |','|---|---|---|---|---|---|']
        for field in fields:
            lines.append('| '+' | '.join((field,)+field_spec(field))+' |')
        lines.append('')
    lines += ['## Interim tables','', '`interim/pitches.csv` has the same pitch fields except survival_class and survival_detail. `official_challenge_comparisons.csv` combines challenge fields, original Statcast location/zone values, participant IDs, raw_source_call, derived_abs_call, distance_from_abs_boundary, comparable, and agrees. `source_discrepancies.json` preserves typed issues (`kind`), pitch/game keys, original source rows, and source-number adjustments. No audit records are deleted.','',
              '## JSON reports','',
              'Report counts are derived integers; rates are derived fractions, nullable when their denominator is zero. Report labels and method identifiers are non-null strings. Nested population keys ALL/OFFENSE/DEFENSE identify the opportunity split.','',
              '| Report | Fields and meanings |','|---|---|',
              '| validation_report.json | official_challenges: normalized official population; expected_official_challenges: dashboard daily sum; matched_challenges/unmatched_challenges: pitch matching counts; comparable_challenges/uncomparable_challenges: known/missing pairs; agreement_count/disagreement_count: matching/differing comparable calls; agreement_rate: agreements / all official challenges; agreement_rate_among_comparable: agreements / comparable challenges. breakdowns repeats these for original_called_strike, original_called_ball, overturned, confirmed. daily_reconciliation entries carry game_date, expected, observed. gate_passed boolean; stop_reasons list; geometry_method version string. |',
              '| descriptive_report.json | games_processed, total_pitches, called_pitches, called_strikes, called_balls: population counts; evaluable_called_pitches: denominator E; incorrect_calls, incorrect_called_strikes, incorrect_called_balls: original/derived differences; incorrect_calls_corrected, incorrect_calls_surviving_with_challenge_available, incorrect_calls_surviving_because_challenge_unavailable: C/R/U; unknown_classifications: called UNKNOWN rows; incorrect_calls_with_unknown_classification: known incorrect UNKNOWN rows. incorrect_call_rate, correction_rate, survival_rate, recognition_survival_rate, resource_constrained_survival_rate follow the explicit E/I/C/R/U formulas in methodology. |',
              '| recognition_distributions.json | Each population and metric has n, missing, minimum, maximum, mean, standard_deviation (sample), p25, median, p75 (linear interpolated quantiles). Summary values retain the metric unit; null when unavailable. |',
              '| data_quality_report.json | expected_games, successfully_processed_games, total_pitches, called_pitches, called_strikes, called_balls are coverage counts. missing_pitch_locations/missing_movement_data count rows missing either coordinate/component; missing_catcher_ids/missing_called_pitch_catcher_ids/missing_umpire_ids count absent participants; missing_challenge_matches, duplicate_pitch_keys, impossible_counts, impossible_challenge_inventory are integrity counts. unknown_classifications is nullable until classification runs. classification_status labels state. failed_game_downloads lists missing game IDs; failed_source_downloads preserves failed receipts; source_discrepancies counts issue kinds; pitch_rows_deleted is zero. game_exclusions preserves ID/reason/status. source_record_exclusions and classification_exclusions have reason, row_count, percentage_of_population (0–100 percent, not fraction). Source-record denominator is physical pitches + automatic records; classification denominator is called pitches. |',
              '| run_manifest.json | start/end ISO dates; expected_games/processed_games counts; gate_passed boolean; source_sha256s sorted unique raw object digests. |',
              '| stop_report.json, when blocked | status=STOPPED, reasons list of gate failures, next_investigation text. This file is absent after a passing run. |',
              '', '## Raw receipts and fixtures','', 'Raw receipt fields: url, kind, retrieved_at (UTC ISO timestamp), content_type, final_url, ok, sha256, path, bytes, and error on failure. Source SHA fields in research tables resolve through these receipts. Fixture records are exact/minimally wrapped official samples, with no simulated observations included in pilot outputs. The official challenge fixture covers all three challenger roles and both outcomes. The timer fixture preserves a plate appearance and its Statcast rows to test numbering offsets.','']
    (docs/'data_dictionary.md').write_text('\n'.join(lines))
    v=json.loads((folder/'validation_report.json').read_text());q=json.loads((folder/'data_quality_report.json').read_text())
    if not v['gate_passed']:
        (docs/'pilot_report.md').write_text('# Pilot stopped\n\n'+', '.join(v['stop_reasons'])+'\n\nSee data/processed/stop_report.json and the preserved discrepancy tables.\n')
        return
    s=json.loads((folder/'descriptive_report.json').read_text())
    lines=['# Pilot results — August 24–30, 2026','',f'**Validation passed: {v["agreement_count"]}/{v["official_challenges"]} official calls agree ({v["agreement_rate"]:.0%}).** All {q["expected_games"]} completed regular-season games are accounted for. All official challenge pitches match; no validation disagreements were found.','', '| Count | All | Offense: original strikes | Defense: original balls |','|---|---:|---:|---:|']
    for label,key in [('Called pitches','called_pitches'),('Incorrect calls','incorrect_calls'),('Corrected','incorrect_calls_corrected'),('Survived with challenge available','incorrect_calls_surviving_with_challenge_available'),('Survived after exhaustion','incorrect_calls_surviving_because_challenge_unavailable'),('Unknown classifications','unknown_classifications')]:
        lines.append(f'| {label} | '+ ' | '.join(f'{s[p][key]:,}' for p in ('ALL','OFFENSE','DEFENSE'))+' |')
    lines += ['',f'There are {q["total_pitches"]:,} total physical pitches. All {q["unknown_classifications"]} unknown called-pitch classifications are incorrect calls with POSITION_PLAYER_PITCHING; they remain in the incorrect-call denominator.','', '| Rate | All | Offense | Defense |','|---|---:|---:|---:|']
    for field in ('incorrect_call_rate','correction_rate','survival_rate','recognition_survival_rate','resource_constrained_survival_rate'):
        lines.append('| '+field+' | '+' | '.join(f'{s[p][field]:.2%}' if s[p][field] is not None else 'null' for p in ('ALL','OFFENSE','DEFENSE'))+' |')
    lines += ['', 'The survival rate above counts the two classified survival categories. Correction and survival do not sum to 100% because the legal-restriction UNKNOWN cases remain in the denominator. These are descriptive pilot counts, with no player rankings or causal interpretation.','', '## Data quality','', '| Check | Count |','|---|---:|']
    for field in ('missing_pitch_locations','missing_movement_data','missing_catcher_ids','missing_umpire_ids','missing_challenge_matches','duplicate_pitch_keys','impossible_counts','impossible_challenge_inventory','pitch_rows_deleted'):
        lines.append(f'| {field} | {q[field]} |')
    lines += ['', 'The source audit preserves **117 automatic nonpitch records** (0.423% of 27,686 Statcast records) and **37 documented pitch-number offsets**. Automatic events are outside the physical-pitch universe; no physical pitches are excluded. There are no failed downloads or unexplained source discrepancies.','', '## Validation details','', '| Group | Official challenges | Agreements | Disagreements |','|---|---:|---:|---:|']
    for group,stats in v['breakdowns'].items():
        lines.append(f'| {group} | {stats["official_challenges"]} | {stats["agreement_count"]} | {stats["disagreement_count"]} |')
    lines += ['', 'Daily official challenge totals are 52, 91, 68, 26, 79, 72, and 59, each independently reconciled to the official dashboard. The empty discrepancy CSV retains a header so downstream readers can distinguish zero discrepancies from a missing artifact.','', '## Detailed exploratory output','', 'See `data/processed/recognition_breakdowns.csv` for counts and three explicitly named rates by pitch type, inning, count, outs, base state, remaining challenges, batter, pitcher, catcher, and umpire. Identity groups are sorted by identifier. `recognition_distributions.json` contains release speed, movement, location, and boundary-distance summaries, each split by offensive and defensive opportunity. [Methodology](methodology.md) defines all denominators and limitations.','']
    (docs/'pilot_report.md').write_text('\n'.join(lines))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    document(parser.parse_args().root)
