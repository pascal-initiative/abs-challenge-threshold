"""Normalize official Savant team-detail challenges, retaining all duplicate evidence."""
from collections import defaultdict


def call(flag):
    return 'STRIKE' if flag == 1 else 'BALL' if flag == 0 else None


def normalize(record):
    original = call(record.get('original_isStrike_ump'))
    overturned = record.get('is_challengeABS_overturned')
    outcome = 'OVERTURNED' if overturned == 1 else 'CONFIRMED' if overturned == 0 else 'UNKNOWN'
    official = (('BALL' if original == 'STRIKE' else 'STRIKE') if overturned == 1 else original) if original and outcome != 'UNKNOWN' else None
    player = record.get('challenging_player_id')
    role, name, team = 'UNKNOWN', None, None
    for candidate, field, name_field, team_field in [
        ('BATTER', 'player_at_bat', 'batter_name_flipped', 'bat_team_id'),
        ('CATCHER', 'fielder_2', 'catcher_name_flipped', 'fld_team_id'),
        ('PITCHER', 'pitcher', 'pitcher_name_flipped', 'fld_team_id')]:
        if player is not None and player == record.get(field):
            role, name, team = candidate, record.get(name_field), record.get(team_field)
            break
    return dict(game_pk=record['game_pk'], game_date=record['game_date'][:10], play_id=record['play_id'],
                challenger_id=player, challenger_name=name, challenger_role=role, challenge_team_id=team,
                original_call=original, official_abs_call=official, overturned=None if outcome == 'UNKNOWN' else bool(overturned),
                outcome=outcome, savant_plate_x=record.get('plateX'), savant_plate_z=record.get('plateZ'),
                savant_abs_top=record.get('strikeZoneTop'), savant_abs_bot=record.get('strikeZoneBottom'),
                savant_abs_width_inches=record.get('widthinches'), savant_edge_dist_inches=record.get('edge_dist_calc'))


def parse_challenges(sources, game_ids, start, end):
    grouped = defaultdict(list)
    issues = []
    for receipt, body in sources:
        if receipt['kind'] != 'abs' or body is None:
            continue
        if not isinstance(body.get('data'), list):
            raise ValueError('Invalid Savant team-detail response')
        for index, record in enumerate(body['data']):
            if start <= record['game_date'][:10] <= end:
                if record['game_pk'] not in game_ids:
                    issues.append(dict(kind='challenge_outside_manifest', record=record))
                    continue
                grouped[(record['game_pk'], record['play_id'])].append((normalize(record), receipt['sha256'], index))
    challenges = []
    for key, candidates in sorted(grouped.items()):
        first = candidates[0][0]
        conflicts = [v for v, _, _ in candidates if v != first]
        first = dict(first, pitch_key=None, source_savant=sorted({s for _, s, _ in candidates}),
                     source_record_indices=[{'sha256': s, 'index': i} for _, s, i in candidates],
                     source_copy_count=len(candidates), source_conflict=bool(conflicts))
        if conflicts:
            issues.append(dict(kind='conflicting_official_challenge_copies', key=key, candidates=candidates))
        challenges.append(first)
    return challenges, issues
