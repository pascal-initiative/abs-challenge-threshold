"""Sequential inventory before decision; uncertainty propagates forward per team."""
from collections import defaultdict


def reconstruct(pitches, challenges, complete=True):
    lookup = {c['pitch_key']: c for c in challenges if c['pitch_key']}
    grouped = defaultdict(list)
    for p in pitches:
        grouped[p['game_pk']].append(p)
    issues = []
    for pk, rows in sorted(grouped.items()):
        inventory = {rows[0]['home_team_id']: 2 if complete else None, rows[0]['away_team_id']: 2 if complete else None}
        last_inning = 0
        for p in sorted(rows, key=lambda r: (r['at_bat_index'], r['play_event_index'])):
            if p['inning'] > last_inning:
                if p['inning'] > 9:
                    for team, remaining in inventory.items():
                        if remaining == 0:
                            inventory[team] = 1
                last_inning = p['inning']
            offense = p['away_team_id'] if p['half_inning'] == 'top' else p['home_team_id']
            defense = p['home_team_id'] if p['half_inning'] == 'top' else p['away_team_id']
            affected = offense if p['original_call'] == 'STRIKE' else defense if p['original_call'] == 'BALL' else None
            p['offense_challenges_remaining'] = inventory[offense]
            p['defense_challenges_remaining'] = inventory[defense]
            p['affected_team_id'] = affected
            p['affected_team_challenges_remaining'] = inventory.get(affected)
            count = inventory.get(affected)
            position_player = p['position_player_pitching']
            p['challenge_available'] = (False if position_player is True or count == 0 else
                                        True if position_player is False and count is not None and affected else None)
            p['challenge_unavailable_reason'] = ('POSITION_PLAYER_PITCHING' if position_player is True else
                                                   'EXHAUSTED' if count == 0 else None)
            c = lookup.get(p['pitch_key'])
            if c:
                team = c['challenge_team_id']
                if team not in inventory:
                    inventory = {team_id: None for team_id in inventory}
                    issues.append(dict(kind='unknown_challenge_team', pitch_key=p['pitch_key']))
                elif c['source_conflict'] or c['outcome'] == 'UNKNOWN':
                    inventory[team] = None
                elif inventory[team] == 0 or p['position_player_pitching'] is True or team != affected:
                    issues.append(dict(kind='impossible_inventory_or_eligibility', pitch_key=p['pitch_key'], team=team, remaining=inventory[team]))
                    inventory[team] = None
                elif c['outcome'] == 'CONFIRMED' and inventory[team] is not None:
                    inventory[team] -= 1
    return issues
