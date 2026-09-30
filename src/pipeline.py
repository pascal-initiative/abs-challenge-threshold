"""Offline reconstruction with fail-closed release gate and deterministic artifacts."""
import argparse
from collections import Counter
import hashlib
from pathlib import Path
from .common import read_sources, constant, write_csv, write_json
from .fetch_abs import parse_challenges
from .parse_pitches import parse_pitches
from .reconstruct_inventory import reconstruct
from .validate import validate


def run(root, start='2026-08-24', end='2026-08-30', output=None, raw_dir=None):
    output = output or root / 'data'
    interim, processed = output / 'interim', output / 'processed'
    sources = read_sources(root, raw_dir)
    games = {}
    excluded_games = []
    for receipt, body in sources:
        if receipt['kind'] == 'schedule' and body:
            for day in body['dates']:
                for g in day['games']:
                    if start <= g['officialDate'] <= end:
                        if g['gameType'] == 'R' and g['status']['abstractGameState'] == 'Final':
                            games[g['gamePk']] = g
                        else:
                            excluded_games.append({'game_pk':g['gamePk'], 'reason':'NOT_FINAL_REGULAR_SEASON', 'status':g['status']})
    challenges, issues = parse_challenges(sources, games, start, end)
    pitches, pitch_issues, done = parse_pitches(sources, games, challenges)
    issues.extend(pitch_issues)
    expected = None
    daily = []
    for receipt, body in sources:
        if receipt['kind'] == 'abs_dashboard' and body:
            daily = [r for r in constant(body, 'absSummaryData') if start <= r['game_date'][:10] <= end]
            # The official dashboard publishes rows on game dates, not on the
            # All-Star-break dates with no completed regular-season games.
            game_dates = {g['officialDate'] for g in games.values()}
            if {r['game_date'][:10] for r in daily} == game_dates:
                expected = sum(r['challenges'] for r in daily)
    daily_reconciliation = [dict(game_date=r['game_date'][:10], expected=r['challenges'],
                                 observed=sum(c['game_date'] == r['game_date'][:10] for c in challenges)) for r in daily]
    complete = expected == len(challenges) and bool(challenges) and all(r['expected'] == r['observed'] for r in daily_reconciliation)
    inventory_issues = reconstruct(pitches, challenges, complete=complete)
    issues.extend(inventory_issues)
    blockers = []
    if set(done) != set(games) or not games:
        blockers.append('INCOMPLETE_GAME_COVERAGE')
    if any(body is None for receipt, body in sources):
        blockers.append('FAILED_SOURCE_DOWNLOADS')
    if not complete:
        blockers.append('DAILY_OFFICIAL_CHALLENGE_TOTALS_NOT_RECONCILED')
    called = [p for p in pitches if p['is_called_pitch']]
    if any(p['catcher_id'] is None for p in called):
        blockers.append('MISSING_CALLED_PITCH_CATCHER')
    if any(p['umpire_id'] is None for p in called):
        blockers.append('MISSING_CALLED_PITCH_UMPIRE')
    material_kinds = ('conflicting_official_challenge_copies','feed_savant_outcome_conflict',
                      'displayed_official_call_conflict','impossible_inventory_or_eligibility',
                      'unknown_challenge_team','physical_pitch_sequence_mismatch','statcast_row_not_uniquely_matched')
    material = [i for i in issues if i['kind'] in material_kinds]
    # Description disagreements on swings/fouls cannot affect the called-pitch
    # universe. Called-pitch disagreements remain blocking.
    material.extend(i for i in issues if i['kind'] == 'pitch_sequence_semantic_conflict'
                    and i.get('feed_call') in ('B','*B','C','P','I'))
    # A feed-only MJ flag is nonmaterial only when the complete dedicated ABS
    # population and official daily totals reconcile exactly.
    if not complete:
        material.extend(i for i in issues if i['kind'] == 'feed_abs_missing_savant')
    if material:
        blockers.append('MATERIAL_SOURCE_OR_INVENTORY_DISCREPANCIES')
    validation, discrepancies, comparisons = validate(pitches, challenges, expected, blockers)
    validation['daily_reconciliation'] = daily_reconciliation
    monthly_validation = []
    for month in sorted({c['game_date'][:7] for c in comparisons}):
        rows = [c for c in comparisons if c['game_date'].startswith(month)]
        agreements = sum(bool(c['agrees']) for c in rows)
        monthly_validation.append(dict(month=month, official_challenges=len(rows),
                                       geometry_agreements=agreements,
                                       geometry_disagreements=len(rows)-agreements,
                                       agreement_rate=agreements/len(rows) if rows else None))
    validation['monthly_validation'] = monthly_validation
    validation['geometry_method'] = 'abs_2026_circle_rectangle_r1.45in_v1'
    manifest = [dict(game_pk=pk,game_date=g['officialDate'],away_team=g['teams']['away']['team']['name'],
                     home_team=g['teams']['home']['team']['name'],venue=g['venue']['name'],status=g['status']['detailedState'],
                     processed=pk in done) for pk,g in sorted(games.items())]
    quality = dict(expected_games=len(games), successfully_processed_games=len(done), total_pitches=len(pitches),
                   called_pitches=len(called), called_strikes=sum(p['original_call']=='STRIKE' for p in called),
                   called_balls=sum(p['original_call']=='BALL' for p in called),
                   missing_pitch_locations=sum(p['plate_x'] is None or p['plate_z'] is None for p in pitches),
                   missing_movement_data=sum(p['pfx_x'] is None or p['pfx_z'] is None for p in pitches),
                   missing_catcher_ids=sum(p['catcher_id'] is None for p in pitches),
                   missing_called_pitch_catcher_ids=sum(p['catcher_id'] is None for p in called),
                   missing_umpire_ids=sum(p['umpire_id'] is None for p in pitches),
                   missing_challenge_matches=sum(c['pitch_key'] is None for c in challenges),
                   duplicate_pitch_keys=len(pitches)-len({p['pitch_key'] for p in pitches}),
                   impossible_counts=sum(p['balls'] is not None and not 0<=p['balls']<=3 or p['strikes'] is not None and not 0<=p['strikes']<=2 or p['outs'] is not None and not 0<=p['outs']<=2 for p in pitches),
                   impossible_challenge_inventory=len(inventory_issues),
                   unknown_classifications=None, classification_status='NOT_RUN_VALIDATION_GATE',
                   failed_game_downloads=sorted(set(games)-set(done)),
                   failed_source_downloads=[r for r,b in sources if b is None],
                   source_discrepancies=dict(Counter(i['kind'] for i in issues)),
                   pitch_rows_deleted=0, game_exclusions=excluded_games,
                   source_record_exclusions=[dict(reason='AUTOMATIC_NONPITCH_EVENT',row_count=sum(i['kind']=='automatic_nonpitch_record' for i in issues),
                       percentage_of_population=100*sum(i['kind']=='automatic_nonpitch_record' for i in issues)/(len(pitches)+sum(i['kind']=='automatic_nonpitch_record' for i in issues)))],
                   classification_exclusions=[dict(reason='VALIDATION_GATE_NOT_PASSED',row_count=len(called),percentage_of_population=100 if called else 0)] if not validation['gate_passed'] else [])
    write_csv(processed/'game_manifest.csv', manifest)
    write_csv(interim/'pitches.csv', pitches)
    write_csv(processed/'challenges.csv', challenges)
    write_csv(processed/'validation_discrepancies.csv', discrepancies, fields=None if discrepancies else ['game_pk','pitch_key','discrepancy_reason'])
    write_csv(interim/'official_challenge_comparisons.csv', comparisons)
    write_json(interim/'source_discrepancies.json', issues)
    write_json(processed/'validation_report.json', validation)
    if validation['gate_passed']:
        from .classify_calls import classify
        from .describe import describe
        classified = [classify(p, True) for p in pitches]
        write_csv(processed/'pitches.csv', classified)
        describe(classified, processed)
        quality['unknown_classifications'] = sum(p['survival_class']=='UNKNOWN' for p in classified if p['is_called_pitch'])
        quality['classification_status'] = 'COMPLETED'
    else:
        # Never let a prior passing run masquerade as this run's result.
        for name in ('pitches.csv','descriptive_report.json','recognition_breakdowns.csv','recognition_distributions.json'):
            path = processed/name
            if path.exists():
                archived = interim/'superseded'/hashlib.sha256(path.read_bytes()).hexdigest()
                archived.parent.mkdir(parents=True, exist_ok=True)
                if not archived.exists():
                    archived.write_bytes(path.read_bytes())
                path.unlink()
        write_json(processed/'stop_report.json', dict(status='STOPPED', reasons=validation['stop_reasons'],
            next_investigation='Inspect every official comparison and source discrepancy. Verify measurement precision and authoritative zone inputs. Do not fit geometry parameters to improve agreement. Do not classify unchallenged pitches until the gate passes.'))
    if validation['gate_passed'] and (processed/'stop_report.json').exists():
        (processed/'stop_report.json').unlink()
    write_json(processed/'data_quality_report.json',quality)
    write_json(processed/'run_manifest.json',dict(start=start,end=end, expected_games=len(games),processed_games=len(done),
                                                gate_passed=validation['gate_passed'],source_sha256s=sorted({r['sha256'] for r,b in sources if b is not None})))
    return validation, quality


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--start',default='2026-08-24')
    parser.add_argument('--end',default='2026-08-30')
    parser.add_argument('--raw-dir',type=Path)
    args=parser.parse_args()
    report, quality=run(args.root,args.start,args.end,args.output,args.raw_dir)
    print(__import__('json').dumps({'validation':report,'quality':quality},indent=2))
    raise SystemExit(0 if report['gate_passed'] else 2)
