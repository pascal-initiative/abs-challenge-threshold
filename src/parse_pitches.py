"""One row per physical pitch; align full PA sequences excluding automatic penalties."""
from collections import defaultdict
from .common import number
from .geometry import derive, METHOD

CALLS = {'B': 'BALL', '*B': 'BALL', 'C': 'STRIKE', 'P': 'BALL', 'I': 'BALL'}
STAT_FIELDS = ['release_speed', 'release_spin_rate', 'spin_axis', 'pfx_x', 'pfx_z',
               'release_pos_x', 'release_pos_y', 'release_pos_z', 'plate_x', 'plate_z', 'sz_top', 'sz_bot']
STATE_FIELDS = {'balls': 'balls', 'strikes': 'strikes', 'outs': 'outs_when_up',
                'on_1b': 'on_1b', 'on_2b': 'on_2b', 'on_3b': 'on_3b',
                'home_score': 'home_score', 'away_score': 'away_score'}


def displayed_call(event):
    return CALLS.get(event.get('details', {}).get('call', {}).get('code'))


def parse_pitches(sources, games, challenges):
    statcast = defaultdict(list)
    for receipt, body in sources:
        if receipt['kind'] == 'statcast' and body is not None:
            for index, row in enumerate(body):
                if number(row.get('game_pk')) in games:
                    key = (number(row['game_pk']), number(row['at_bat_number']) - 1, number(row['pitch_number']))
                    statcast[key].append((row, receipt['sha256'], index))
    chal = defaultdict(list)
    for c in challenges:
        chal[(c['game_pk'], c['play_id'])].append(c)
    pitches, issues, processed = [], [], []
    used = set()
    stat_pa = defaultdict(list)
    for key, values in statcast.items():
        if not all(r.get("description") in ("automatic_ball", "automatic_strike") for r, _, _ in values):
            stat_pa[key[:2]].append(key)
    for keys in stat_pa.values():
        keys.sort(key=lambda k: k[2])
    for receipt, feed in sources:
        if receipt['kind'] != 'feed' or feed is None or feed['gamePk'] not in games:
            continue
        pk = feed['gamePk']
        g = games[pk]
        if feed['gameData']['status']['abstractGameState'] != 'Final':
            issues.append(dict(kind='nonfinal_feed', game_pk=pk))
            continue
        processed.append(pk)
        players = feed['gameData']['players']
        officials = [o['official'] for o in feed['liveData']['boxscore'].get('officials', []) if o['officialType'] == 'Home Plate']
        ump = officials[0] if len(officials) == 1 else {}
        for play in feed['liveData']['plays']['allPlays']:
            about, matchup = play['about'], play['matchup']
            physical = [e for e in play['playEvents'] if e.get('isPitch')]
            sc_keys = stat_pa.get((pk, about['atBatIndex']), [])
            aligned = len(physical) == len(sc_keys)
            if not aligned:
                issues.append(dict(kind='physical_pitch_sequence_mismatch',game_pk=pk,at_bat_index=about['atBatIndex'],feed_count=len(physical),statcast_count=len(sc_keys)))
            sequence = 0
            for event in play['playEvents']:
                if not event.get('isPitch'):
                    continue
                ab, pn, ei = about['atBatIndex'], event.get('pitchNumber'), event['index']
                key = sc_keys[sequence] if aligned else (pk, ab, None)
                sequence += 1
                candidates = statcast.get(key, [])
                sc, sc_hash, sc_index = candidates[0] if len(candidates) == 1 else ({}, None, None)
                if len(candidates) != 1:
                    issues.append(dict(kind='statcast_match_count', game_pk=pk, at_bat_index=ab, pitch_number=pn, match_count=len(candidates)))
                else:
                    used.add(key)
                if sc and key[2] != pn:
                    issues.append(dict(kind='documented_pitch_number_offset',game_pk=pk,at_bat_index=ab,feed_pitch_number=pn,statcast_pitch_number=key[2],physical_pitch_ordinal=sequence))
                detail, pd = event.get('details', {}), event.get('pitchData', {})
                coords = pd.get('coordinates', {})
                p = dict(game_pk=pk, game_date=g['officialDate'], season=int(g['season']), game_type=g['gameType'],
                         home_team_id=g['teams']['home']['team']['id'], home_team=g['teams']['home']['team']['name'],
                         away_team_id=g['teams']['away']['team']['id'], away_team=g['teams']['away']['team']['name'],
                         venue=g['venue']['name'], inning=about['inning'], half_inning=about['halfInning'],
                         at_bat_index=ab, pitch_number=pn, play_event_index=ei, play_id=event.get('playId'),
                         statcast_pitch_number=number(sc.get('pitch_number')), physical_pitch_ordinal=sequence,
                         pitch_match_method='PHYSICAL_SEQUENCE' if aligned else 'UNMATCHED',
                         pitch_key=f'{pk}:{ab}:{ei}', source_game_feed=receipt['sha256'], source_savant=sc_hash,
                         source_statcast_row_index=sc_index, state_timing='PRE_PITCH',
                         raw_source_call=detail.get('call', {}).get('code'), raw_source_description=detail.get('description'),
                         displayed_call=displayed_call(event), original_call=displayed_call(event), official_abs_call=None,
                         umpire_id=ump.get('id'), umpire_name=ump.get('fullName'),
                         bat_side=sc.get('stand') or matchup.get('batSide', {}).get('code'),
                         pitch_hand=sc.get('p_throws') or matchup.get('pitchHand', {}).get('code'),
                         pitch_type=sc.get('pitch_type') or detail.get('type', {}).get('code'),
                         pitch_name=sc.get('pitch_name') or detail.get('type', {}).get('description'),
                         feed_plate_x=coords.get('pX'), feed_plate_z=coords.get('pZ'),
                         feed_sz_top=pd.get('strikeZoneTop'), feed_sz_bot=pd.get('strikeZoneBottom'),
                         feed_zone_width_inches=pd.get('strikeZoneWidth'), feed_zone_depth_inches=pd.get('strikeZoneDepth'),
                         feed_pfx_x_inches=coords.get('pfxX'), feed_pfx_z_inches=coords.get('pfxZ'),
                         feed_zone_values={k:v for k,v in pd.items() if 'zone' in k.lower()},
                         feed_has_review=detail.get('hasReview'), feed_review_details=event.get('reviewDetails'),
                         source_derived=METHOD, original_call_source='MLB_DISPLAYED_UNCHALLENGED',
                         challenge_outcome=None, challenged=False, source_conflict=False)
                for participant, sc_field in [('batter', 'batter'), ('pitcher', 'pitcher'), ('catcher', 'fielder_2')]:
                    identity = number(sc.get(sc_field))
                    if identity is None and participant in ('batter', 'pitcher'):
                        identity = matchup[participant]['id']
                    p[participant+'_id'] = identity
                    p[participant+'_name'] = players.get('ID'+str(identity), {}).get('fullName')
                # A two-way player is eligible; a non-pitcher listed position is not assumed eligible.
                profile = players.get('ID'+str(p['pitcher_id']), {})
                position = profile.get('primaryPosition', {}).get('abbreviation')
                p['pitcher_primary_position'] = position
                p['position_player_pitching'] = None if not position else position not in ('P', 'TWP')
                for out, source in STATE_FIELDS.items():
                    p[out] = number(sc.get(source))
                p['score_diff'] = None if p['home_score'] is None or p['away_score'] is None else p['home_score'] - p['away_score']
                for field in STAT_FIELDS:
                    p[field] = number(sc.get(field))
                p['extension'] = number(sc.get('release_extension'))
                p['abs_zone_top'] = p['sz_top']
                p['abs_zone_bot'] = p['sz_bot']
                p['abs_zone_width_inches'] = 17
                matches = chal.get((pk, p['play_id']), [])
                if len(matches) == 1:
                    c = matches[0]
                    c['pitch_key'] = p['pitch_key']
                    p.update(original_call=c['original_call'], official_abs_call=c['official_abs_call'],
                             challenge_outcome=c['outcome'], challenged=True, source_conflict=c['source_conflict'],
                             original_call_source='SAVANT_ORIGINAL_ISSTRIKE_UMP')
                    review = event.get('reviewDetails')
                    if review and review.get('reviewType') == 'MJ' and review.get('isOverturned') != c['overturned']:
                        p['source_conflict'] = True
                        issues.append(dict(kind='feed_savant_outcome_conflict', pitch_key=p['pitch_key'], review=review, challenge=c))
                    if p['displayed_call'] != c['official_abs_call']:
                        p['source_conflict'] = True
                        issues.append(dict(kind='displayed_official_call_conflict', pitch_key=p['pitch_key'], displayed=p['displayed_call'], official=c['official_abs_call']))
                elif event.get('reviewDetails', {}).get('reviewType') == 'MJ':
                    # The dedicated ABS extract and its daily official total are
                    # authoritative.  A feed-only MJ annotation is preserved for
                    # audit but is not promoted to an official ABS challenge.
                    issues.append(dict(kind='feed_abs_missing_savant', pitch_key=p['pitch_key'],
                                       resolution='DEDICATED_ABS_AND_DAILY_TOTAL_EXCLUDE_FEED_ANNOTATION'))
                sc_description = sc.get('description')
                expected_description = {'B': 'ball', '*B': 'blocked_ball', 'C': 'called_strike', 'S': 'swinging_strike', 'F': 'foul'}.get(p['raw_source_call'])
                sc_class = 'in_play' if sc_description == 'hit_into_play' else sc_description
                expected_description = 'in_play' if detail.get('isInPlay') else expected_description
                if expected_description and sc_description and sc_class != expected_description:
                    p['source_conflict'] = True
                    issues.append(dict(kind='pitch_sequence_semantic_conflict',pitch_key=p['pitch_key'],feed_call=p['raw_source_call'],statcast_description=sc_description))
                p['is_called_pitch'] = p['original_call'] in ('BALL', 'STRIKE') or p['displayed_call'] in ('BALL', 'STRIKE') or p['challenged']
                p['derived_abs_call'], p['distance_from_abs_boundary'] = derive(p['plate_x'], p['plate_z'], p['abs_zone_top'], p['abs_zone_bot'], p['season'])
                p['opportunity_population'] = 'OFFENSE' if p['original_call'] == 'STRIKE' else 'DEFENSE' if p['original_call'] == 'BALL' else None
                pitches.append(p)
    for key, records in sorted(statcast.items()):
        if key not in used:
            automatic = all(r.get('description') in ('automatic_ball','automatic_strike') for r, _, _ in records)
            issues.append(dict(kind='automatic_nonpitch_record' if automatic else 'statcast_row_not_uniquely_matched', key=key, rows=[r for r, _, _ in records]))
    return sorted(pitches, key=lambda p: (p['game_pk'], p['at_bat_index'], p['play_event_index'])), issues, sorted(processed)
