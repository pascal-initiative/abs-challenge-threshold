import copy
import json
import tempfile
import unittest
from pathlib import Path
from src.fetch_abs import normalize
from src.parse_pitches import displayed_call, parse_pitches
from src.geometry import derive, HALF_WIDTH_FEET, BALL_RADIUS_FEET
from src.reconstruct_inventory import reconstruct
from src.classify_calls import classify
from src.validate import validate
from src.describe import summary, ratio
from src.common import read_sources

FIXTURES=Path(__file__).parent/'fixtures'


def pitch(i=0, original='STRIKE', inning=1, half='top', **kwargs):
    return dict(game_pk=1,pitch_key=f'1:{i}:0',at_bat_index=i,play_event_index=0,home_team_id=1,away_team_id=2,
                inning=inning,half_inning=half,original_call=original,position_player_pitching=False,**kwargs)


def challenge(p, outcome='CONFIRMED', team=2, **kwargs):
    return dict(pitch_key=p['pitch_key'],challenge_team_id=team,outcome=outcome,source_conflict=False,**kwargs)


class ParsingTests(unittest.TestCase):
    def test_called_ball(self):
        self.assertEqual(displayed_call({'details':{'call':{'code':'B'}}}),'BALL')

    def test_called_strike(self):
        self.assertEqual(displayed_call({'details':{'call':{'code':'C'}}}),'STRIKE')

    def test_noncalled_pitch_types(self):
        for code in ['S','F','D','X','E','H','T','W']:
            with self.subTest(code=code):
                self.assertIsNone(displayed_call({'details':{'call':{'code':code}}}))

    def test_dirt_ball_is_called(self):
        self.assertEqual(displayed_call({'details':{'call':{'code':'*B'}}}),'BALL')

    def test_official_challenge_cases(self):
        fixtures=json.loads((FIXTURES/'official_challenges.json').read_text())
        self.assertEqual({tuple(x['category']) for x in fixtures},
                         {(role,outcome) for role in ('BATTER','CATCHER','PITCHER') for outcome in ('OVERTURNED','CONFIRMED')})
        for fixture in fixtures:
            with self.subTest(category=fixture['category']):
                c=normalize(fixture['challenge'])
                self.assertEqual([c['challenger_role'],c['outcome']],fixture['category'])
                self.assertEqual(displayed_call(fixture['event']),c['official_abs_call'])
                if c['overturned']:
                    self.assertNotEqual(c['original_call'],displayed_call(fixture['event']))
                else:
                    self.assertEqual(c['original_call'],displayed_call(fixture['event']))

    def test_unknown_challenger_outcome(self):
        r=json.loads((FIXTURES/'official_challenges.json').read_text())[0]['challenge']
        r.update(challenging_player_id=None,is_challengeABS_overturned=None)
        c=normalize(r)
        self.assertEqual(c['challenger_role'],'UNKNOWN')
        self.assertEqual(c['outcome'],'UNKNOWN')
        self.assertIsNone(c['official_abs_call'])
        self.assertIsNone(c['challenge_team_id'])

    def parse_timer(self, mutate=None):
        fixture=json.loads((FIXTURES/'timer_penalty_pa.json').read_text())
        if mutate:
            mutate(fixture)
        sources=[({'kind':'feed','sha256':'feed'},fixture['feed']),({'kind':'statcast','sha256':'csv'},fixture['statcast'])]
        return parse_pitches(sources,{fixture['game']['gamePk']:fixture['game']},[])

    def test_timer_violation_sequence_does_not_shift_pitches(self):
        pitches,issues,_=self.parse_timer()
        self.assertEqual(len(pitches),5)
        self.assertEqual([p['pitch_number'] for p in pitches],[1,2,3,4,5])
        self.assertEqual([p['statcast_pitch_number'] for p in pitches],[1,2,4,5,6])
        self.assertEqual([p['raw_source_call'] for p in pitches],['B','B','C','C','X'])
        self.assertEqual([p['balls'] for p in pitches],[0,1,3,3,3])
        self.assertEqual([p['strikes'] for p in pitches],[0,0,0,1,2])
        self.assertTrue(all(p['catcher_id'] for p in pitches))
        self.assertFalse(any(p['source_conflict'] for p in pitches))
        self.assertEqual(sum(i['kind']=='automatic_nonpitch_record' for i in issues),1)

    def test_incomplete_sequence_stays_unknown(self):
        pitches,issues,_=self.parse_timer(lambda f:f['statcast'].remove(next(r for r in f['statcast'] if r['description']=='hit_into_play')))
        self.assertEqual(len(pitches),5)
        self.assertTrue(all(p['source_savant'] is None for p in pitches))
        self.assertTrue(any(i['kind']=='physical_pitch_sequence_mismatch' for i in issues))

    def test_semantic_discrepancy_preserved(self):
        def mutate(f):
            for row in f['statcast']:
                if row['pitch_number']=='1':row['description']='swinging_strike'
        pitches,issues,_=self.parse_timer(mutate)
        self.assertTrue(pitches[0]['source_conflict'])
        self.assertTrue(any(i['kind']=='pitch_sequence_semantic_conflict' for i in issues))


class GeometryTests(unittest.TestCase):
    def test_inside_and_outside(self):
        self.assertEqual(derive(0,2.5,3.5,1.5)[0],'STRIKE')
        self.assertEqual(derive(2,2.5,3.5,1.5)[0],'BALL')

    def test_ball_overlap(self):
        self.assertEqual(derive(HALF_WIDTH_FEET+.1,2.5,3.5,1.5)[0],'STRIKE')

    def test_rounded_corner_not_expanded_square(self):
        self.assertEqual(derive(HALF_WIDTH_FEET+.1,3.6,3.5,1.5)[0],'BALL')

    def test_missing_invalid_or_wrong_season(self):
        for args in [(None,2,3,1.5),(0,2,1.5,3),(0,float('nan'),3,1.5),(0,2,3,1.5,2025)]:
            self.assertEqual(derive(*args),(None,None))

    def test_boundary_sign(self):
        self.assertLess(derive(0,2,3,1.5)[1],0)
        self.assertGreater(derive(2,2,3,1.5)[1],0)


class InventoryTests(unittest.TestCase):
    def test_success_retained_and_consecutive_success(self):
        rows=[pitch(i) for i in range(4)]
        reconstruct(rows,[challenge(p,'OVERTURNED') for p in rows[:3]])
        self.assertEqual([r['offense_challenges_remaining'] for r in rows],[2,2,2,2])

    def test_first_and_final_loss(self):
        rows=[pitch(i) for i in range(3)]
        reconstruct(rows,[challenge(p) for p in rows[:2]])
        self.assertEqual([r['offense_challenges_remaining'] for r in rows],[2,1,0])
        self.assertEqual([r['challenge_available'] for r in rows],[True,True,False])

    def test_defensive_challenge(self):
        rows=[pitch(i,original='BALL') for i in range(2)]
        reconstruct(rows,[challenge(rows[0],team=1)])
        self.assertEqual(rows[1]['defense_challenges_remaining'],1)
        self.assertEqual(rows[1]['offense_challenges_remaining'],2)

    def test_inventory_follows_team_when_sides_change(self):
        rows=[pitch(0),pitch(1,original='BALL',half='bottom')]
        reconstruct(rows,[challenge(rows[0])])
        self.assertEqual(rows[1]['affected_team_challenges_remaining'],1)

    def test_extra_inning_replenishment_once_per_full_inning(self):
        rows=[pitch(0),pitch(1),pitch(2,inning=10),pitch(3,original='BALL',inning=10,half='bottom'),pitch(4,inning=11)]
        reconstruct(rows,[challenge(rows[0]),challenge(rows[1]),challenge(rows[2])])
        self.assertEqual([r['affected_team_challenges_remaining'] for r in rows],[2,1,1,0,1])

    def test_extra_inning_no_bonus_when_one_remaining(self):
        rows=[pitch(0),pitch(1,inning=10)]
        reconstruct(rows,[challenge(rows[0])])
        self.assertEqual(rows[1]['offense_challenges_remaining'],1)
        self.assertEqual(rows[1]['defense_challenges_remaining'],2)

    def test_unknown_outcome_propagates(self):
        rows=[pitch(0),pitch(1)]
        reconstruct(rows,[challenge(rows[0],'UNKNOWN')])
        self.assertIsNone(rows[1]['challenge_available'])
        self.assertIsNone(rows[1]['offense_challenges_remaining'])
        self.assertEqual(rows[1]['defense_challenges_remaining'],2)

    def test_incomplete_population_not_assumed_unchallenged(self):
        rows=[pitch()]
        reconstruct(rows,[],complete=False)
        self.assertIsNone(rows[0]['offense_challenges_remaining'])
        self.assertIsNone(rows[0]['challenge_available'])

    def test_position_player_pitching(self):
        p=pitch();p['position_player_pitching']=True
        reconstruct([p],[])
        self.assertFalse(p['challenge_available'])
        self.assertEqual(p['challenge_unavailable_reason'],'POSITION_PLAYER_PITCHING')
        self.assertEqual(p['offense_challenges_remaining'],2)

    def test_challenge_with_exhausted_inventory_flags_issue(self):
        rows=[pitch(i) for i in range(3)]
        issues=reconstruct(rows,[challenge(r) for r in rows])
        self.assertEqual(len(issues),1)


class ClassificationTests(unittest.TestCase):
    def base(self,**kwargs):
        p=dict(original_call='STRIKE',derived_abs_call='BALL',is_called_pitch=True,source_conflict=False,
               challenged=False,official_abs_call=None,challenge_outcome=None,challenge_available=True,
               affected_team_challenges_remaining=2,challenge_unavailable_reason=None)
        p.update(kwargs)
        return p

    def test_all_five_classes(self):
        for changes,expected in [({'derived_abs_call':'STRIKE'},'CORRECT_CALL'),
                                 ({'challenged':True,'official_abs_call':'BALL','challenge_outcome':'OVERTURNED'},'CORRECTED'),
                                 ({},'SURVIVED_RECOGNITION'),
                                 ({'challenge_available':False,'affected_team_challenges_remaining':0,'challenge_unavailable_reason':'EXHAUSTED'},'SURVIVED_RESOURCE'),
                                 ({'derived_abs_call':None},'UNKNOWN')]:
            with self.subTest(expected=expected):
                self.assertEqual(classify(self.base(**changes),True)['survival_class'],expected)

    def test_confirmed_disagreement_detail(self):
        p=classify(self.base(challenged=True,official_abs_call='STRIKE',challenge_outcome='CONFIRMED'),True)
        self.assertEqual(p['survival_class'],'SURVIVED_RECOGNITION')
        self.assertEqual(p['survival_detail'],'CHALLENGED_BUT_CONFIRMED')

    def test_position_player_is_not_resource_or_recognition(self):
        p=classify(self.base(challenge_available=False,challenge_unavailable_reason='POSITION_PLAYER_PITCHING'),True)
        self.assertEqual(p['survival_class'],'UNKNOWN')

    def test_fail_closed_gate(self):
        with self.assertRaises(RuntimeError):classify(self.base(),False)

    def test_source_conflict_unknown(self):
        self.assertEqual(classify(self.base(source_conflict=True),True)['survival_class'],'UNKNOWN')

    def test_noncalled_not_in_opportunity_universe(self):
        self.assertEqual(classify(self.base(is_called_pitch=False),True)['survival_detail'],'NOT_CALLED_PITCH')


class GateTests(unittest.TestCase):
    def rows(self,n=100):
        pitches=[dict(pitch_key=str(i),derived_abs_call='STRIKE',**{f:None for f in ('plate_x','plate_z','sz_top','sz_bot','distance_from_abs_boundary','raw_source_call','batter_id','catcher_id','umpire_id')}) for i in range(n)]
        challenges=[dict(pitch_key=str(i),official_abs_call='STRIKE',original_call='BALL',outcome='OVERTURNED') for i in range(n)]
        return pitches,challenges

    def test_threshold_99_inclusive_and_discrepancy_retained(self):
        p,c=self.rows();p[0]['derived_abs_call']='BALL'
        report,discrepancies,_=validate(p,c,100)
        self.assertTrue(report['gate_passed'])
        self.assertEqual(len(discrepancies),1)
        p[1]['derived_abs_call']='BALL'
        report,discrepancies,_=validate(p,c,100)
        self.assertFalse(report['gate_passed'])
        self.assertEqual(len(discrepancies),2)

    def test_unmatched_not_removed_from_denominator(self):
        p,c=self.rows();c[0]['pitch_key']=None
        report,_,_=validate(p,c,100)
        self.assertFalse(report['gate_passed'])
        self.assertEqual(report['agreement_rate'],.99)
        self.assertEqual(report['unmatched_challenges'],1)

    def test_missing_derivation_blocks_even_with_99_percent(self):
        p,c=self.rows();p[0]['derived_abs_call']=None
        report,_,_=validate(p,c,100)
        self.assertFalse(report['gate_passed'])
        self.assertEqual(report['uncomparable_challenges'],1)

    def test_expected_total_and_material_discrepancies_block(self):
        p,c=self.rows()
        self.assertFalse(validate(p,c,101)[0]['gate_passed'])
        self.assertFalse(validate(p,c,100,['MATERIAL_DISCREPANCY'])[0]['gate_passed'])

    def test_no_challenges_not_vacuous_success(self):
        self.assertFalse(validate([],[],0)[0]['gate_passed'])

    def test_duplicate_pitch_keys(self):
        p,c=self.rows();p.append(dict(p[0]))
        self.assertFalse(validate(p,c,100)[0]['gate_passed'])


class FullPilotTests(unittest.TestCase):
    def test_offline_determinism_and_population_accounting(self):
        root=Path(__file__).resolve().parents[1]
        if not (root/'data/raw/receipts.jsonl').exists():
            self.skipTest('Acquire pilot raw sources to run integration/determinism test')
        from src.pipeline import run
        with tempfile.TemporaryDirectory() as temp:
            first,second=Path(temp)/'first',Path(temp)/'second'
            report,q=run(root,output=first)
            run(root,output=second)
            files=sorted(p.relative_to(first) for p in first.rglob('*') if p.is_file())
            self.assertEqual(files,sorted(p.relative_to(second) for p in second.rglob('*') if p.is_file()))
            for path in files:
                self.assertEqual((first/path).read_bytes(),(second/path).read_bytes(),str(path))
            self.assertEqual(q['expected_games'],93)
            self.assertEqual(q['total_pitches'],27569)
            self.assertEqual(report['official_challenges'],447)
            self.assertTrue(report['gate_passed'])
            self.assertEqual(q['pitch_rows_deleted'],0)
            stats=json.loads((first/'processed/descriptive_report.json').read_text())
            self.assertEqual(stats['ALL']['incorrect_calls'],stats['OFFENSE']['incorrect_calls']+stats['DEFENSE']['incorrect_calls'])
            s=stats['ALL']
            self.assertEqual(s['incorrect_calls'],s['incorrect_calls_corrected']+s['incorrect_calls_surviving_with_challenge_available']+s['incorrect_calls_surviving_because_challenge_unavailable']+s['incorrect_calls_with_unknown_classification'])


if __name__=='__main__':unittest.main()
