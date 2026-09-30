"""Conservative gate: full official population, complete comparisons and >=99% agreement."""
from collections import Counter


def validate(pitches, challenges, expected, blockers=()):
    by_key = {p['pitch_key']: p for p in pitches}
    discrepancies = []
    comparisons = []
    for c in challenges:
        p = by_key.get(c['pitch_key'])
        derived = p['derived_abs_call'] if p else None
        official = c['official_abs_call']
        comparable = derived is not None and official is not None
        agrees = comparable and derived == official
        row = dict(c, derived_abs_call=derived, comparable=comparable, agrees=agrees)
        if p:
            row.update({k: p[k] for k in ('plate_x', 'plate_z', 'sz_top', 'sz_bot', 'distance_from_abs_boundary',
                                         'raw_source_call', 'batter_id', 'catcher_id', 'umpire_id')})
        comparisons.append(row)
        if not agrees:
            discrepancies.append(dict(row, discrepancy_reason='DISAGREEMENT' if comparable else 'UNMATCHED_OR_UNCOMPARABLE'))
    def stats(rows):
        agreement = sum(r['agrees'] for r in rows)
        comparable = sum(r['comparable'] for r in rows)
        return dict(official_challenges=len(rows), matched_challenges=sum(r['pitch_key'] is not None for r in rows),
                    unmatched_challenges=sum(r['pitch_key'] is None for r in rows), comparable_challenges=comparable,
                    uncomparable_challenges=len(rows)-comparable, agreement_count=agreement,
                    disagreement_count=comparable-agreement, agreement_rate=agreement/len(rows) if rows else None,
                    agreement_rate_among_comparable=agreement/comparable if comparable else None)
    report = stats(comparisons)
    report['expected_official_challenges'] = expected
    report['breakdowns'] = {name:stats([r for r in comparisons if r[field] == value]) for name,field,value in
                             [('original_called_strike','original_call','STRIKE'),('original_called_ball','original_call','BALL'),
                              ('overturned','outcome','OVERTURNED'),('confirmed','outcome','CONFIRMED')]}
    reasons = list(blockers)
    if not challenges:
        reasons.append('NO_OFFICIAL_CHALLENGES')
    if expected is None or len(challenges) != expected:
        reasons.append('OFFICIAL_POPULATION_NOT_RECONCILED')
    if report['unmatched_challenges'] or report['uncomparable_challenges']:
        reasons.append('INCOMPLETE_OFFICIAL_COMPARISONS')
    if report['agreement_rate'] is None or report['agreement_rate'] < .99:
        reasons.append('GEOMETRY_AGREEMENT_BELOW_99_PERCENT')
    if len(by_key) != len(pitches):
        reasons.append('DUPLICATE_PITCH_KEYS')
    report['stop_reasons'] = sorted(set(reasons))
    report['gate_passed'] = not reasons
    return report, discrepancies, comparisons
