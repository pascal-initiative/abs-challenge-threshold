"""Classification only callable after successful validation."""

def classify(pitch, gate_passed):
    if not gate_passed:
        raise RuntimeError('Classification prohibited: validation gate did not pass')
    p = dict(pitch)
    p['survival_class'] = 'UNKNOWN'
    p['survival_detail'] = None
    original, derived = p['original_call'], p['derived_abs_call']
    if not p['is_called_pitch']:
        p['survival_detail'] = 'NOT_CALLED_PITCH'
    elif p['source_conflict'] or original is None or derived is None:
        p['survival_detail'] = 'INSUFFICIENT_OR_CONFLICTING_SOURCE_DATA'
    elif original == derived:
        # Even a gate-accepted disagreement must not masquerade as an ordinary correct call.
        if p['challenged'] and p['official_abs_call'] != derived:
            p['survival_detail'] = 'OFFICIAL_DERIVED_DISAGREEMENT'
        else:
            p['survival_class'] = 'CORRECT_CALL'
    elif p['challenge_outcome'] == 'OVERTURNED' and p['official_abs_call'] == derived:
        p['survival_class'] = 'CORRECTED'
    elif p['challenged'] and p['challenge_outcome'] not in ('CONFIRMED',):
        p['survival_detail'] = 'UNKNOWN_CHALLENGE_OUTCOME'
    elif p['challenge_available'] is True:
        p['survival_class'] = 'SURVIVED_RECOGNITION'
        p['survival_detail'] = 'CHALLENGED_BUT_CONFIRMED' if p['challenged'] else 'NOT_CHALLENGED'
    elif p['affected_team_challenges_remaining'] == 0 and p['challenge_unavailable_reason'] == 'EXHAUSTED':
        p['survival_class'] = 'SURVIVED_RESOURCE'
    else:
        p['survival_detail'] = p['challenge_unavailable_reason'] or 'UNKNOWN_AVAILABILITY'
    return p
