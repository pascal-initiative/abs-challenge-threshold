"""Descriptive counts only; identity groups sorted by ID, never by performance."""
from collections import Counter, defaultdict
import statistics
from .common import write_csv, write_json


def ratio(numerator, denominator):
    return numerator/denominator if denominator else None


def summary(pitches):
    called = [p for p in pitches if p['is_called_pitch']]
    evaluable = [p for p in called if p['original_call'] is not None and p['derived_abs_call'] is not None and not p['source_conflict']]
    incorrect = [p for p in evaluable if p['original_call'] != p['derived_abs_call']]
    counts = Counter(p['survival_class'] for p in called)
    survived = counts['SURVIVED_RECOGNITION'] + counts['SURVIVED_RESOURCE']
    return dict(games_processed=len({p['game_pk'] for p in pitches}), total_pitches=len(pitches), called_pitches=len(called),
                called_strikes=sum(p['original_call']=='STRIKE' for p in called),called_balls=sum(p['original_call']=='BALL' for p in called),
                evaluable_called_pitches=len(evaluable), incorrect_calls=len(incorrect),
                incorrect_called_strikes=sum(p['original_call']=='STRIKE' for p in incorrect),
                incorrect_called_balls=sum(p['original_call']=='BALL' for p in incorrect),
                incorrect_calls_corrected=counts['CORRECTED'], incorrect_calls_surviving_with_challenge_available=counts['SURVIVED_RECOGNITION'],
                incorrect_calls_surviving_because_challenge_unavailable=counts['SURVIVED_RESOURCE'],
                unknown_classifications=counts['UNKNOWN'],
                incorrect_calls_with_unknown_classification=sum(p['survival_class']=='UNKNOWN' for p in incorrect),
                incorrect_call_rate=ratio(len(incorrect),len(evaluable)),correction_rate=ratio(counts['CORRECTED'],len(incorrect)),
                survival_rate=ratio(survived,len(incorrect)),recognition_survival_rate=ratio(counts['SURVIVED_RECOGNITION'],len(incorrect)),
                resource_constrained_survival_rate=ratio(counts['SURVIVED_RESOURCE'],len(incorrect)))


def describe(pitches, folder):
    populations = {'ALL':pitches, 'OFFENSE':[p for p in pitches if p['opportunity_population']=='OFFENSE'],
                   'DEFENSE':[p for p in pitches if p['opportunity_population']=='DEFENSE']}
    report = {population:summary(rows) for population,rows in populations.items()}
    write_json(folder/'descriptive_report.json', report)
    breakdowns, distributions = [], {}
    dimensions = ['pitch_type','inning','count','outs','base_state','challenges_remaining','batter','pitcher','catcher','umpire']
    for population, rows in populations.items():
        groups = defaultdict(list)
        for p in rows:
            if not p['is_called_pitch']:
                continue
            values = dict(pitch_type=p['pitch_type'],inning=p['inning'], count=f'{p["balls"]}-{p["strikes"]}',
                          outs=p['outs'],base_state=''.join('1' if p[f'on_{i}b'] else '0' for i in (1,2,3)) if p['source_savant'] else None,
                          challenges_remaining=p['affected_team_challenges_remaining'],
                          **{x:p[x+'_id'] for x in ('batter','pitcher','catcher','umpire')})
            for dim in dimensions:
                groups[(dim, str(values[dim]) if values[dim] is not None else 'UNKNOWN')].append(p)
        for (dimension,value), group in sorted(groups.items()):
            survived = sum(p['survival_class']=='SURVIVED_RECOGNITION' for p in group)
            incorrect = [p for p in group if p['original_call'] and p['derived_abs_call'] and p['original_call'] != p['derived_abs_call'] and not p['source_conflict']]
            available = sum(p['challenge_available'] is True for p in incorrect)
            breakdowns.append(dict(population=population,dimension=dimension,value=value,
                                   name=group[0].get(dimension+'_name'),called_pitches=len(group),incorrect_calls=len(incorrect),
                                   incorrect_with_challenge_available=available,survived_recognition=survived,
                                   rate_per_called_pitch=ratio(survived,len(group)),rate_per_incorrect_call=ratio(survived,len(incorrect)),
                                   rate_per_available_incorrect_call=ratio(survived,available)))
        survivors = [p for p in rows if p['survival_class']=='SURVIVED_RECOGNITION']
        distributions[population] = {}
        for field in ('release_speed','pfx_x','pfx_z','plate_x','plate_z','distance_from_abs_boundary'):
            values=sorted(p[field] for p in survivors if p[field] is not None)
            def quantile(q):
                if not values:
                    return None
                index=(len(values)-1)*q
                lower=int(index)
                return values[lower]+(values[min(lower+1,len(values)-1)]-values[lower])*(index-lower)
            distributions[population][field]=dict(n=len(values),missing=len(survivors)-len(values),
                minimum=min(values) if values else None, maximum=max(values) if values else None,
                mean=statistics.mean(values) if values else None,standard_deviation=statistics.stdev(values) if len(values)>1 else None,
                p25=quantile(.25),median=quantile(.5),p75=quantile(.75))
    write_csv(folder/'recognition_breakdowns.csv', breakdowns)
    write_json(folder/'recognition_distributions.json', distributions)
