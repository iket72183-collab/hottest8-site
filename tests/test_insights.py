import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_insights import build_insights, fresh_ig, same_identity, ordered, read_snapshots, stamp


def c(id='1',handle='fixture',x=20000,ig=10000,**kw):
    return dict(name='Synthetic '+id,x_id=id,x_handle=handle,x_followers=x,ig_handle='fixture_ig',ig_followers=ig,ig_status='verified',ig_as_of='2026-10-20',**kw)

def s(day,rows):return {'date':day,'fetched_at':day+'T12:00:00+00:00','creators':rows}

def pool(rows):return {'rules':{'min_snapshots':2,'min_followers':10000,'max_combined_followers':1000000},'creators':rows}

class InsightsTests(unittest.TestCase):
    def run_case(self,a=None,b=None,days=('2026-10-20','2026-10-21')):
        a=a or c();b=b or c(x=20100);tracked=[s(days[-1],[c('top','top',x=2000000)])]
        return build_insights(tracked,[s(days[0],[a]),s(days[-1],[b])],pool([b]))
    def test_real_history_recomputes_all_growth(self):
        root=Path(__file__).resolve().parents[1];e=read_snapshots(root,'emerging');d=build_insights(read_snapshots(root),e,json.loads((root/'rising_pool.json').read_text()))
        window=d['rising8']['window'];by_time={r['fetched_at']:r for r in e}
        before={r['x_id']:r for r in by_time[window['from']]['creators'] if r.get('x_id')};after={r['x_id']:r for r in by_time[window['to']]['creators'] if r.get('x_id')}
        for row in d['rising8']['all']:
            self.assertEqual(row['x_growth'],after[row['x_id']]['x_followers']-before[row['x_id']]['x_followers'])
            self.assertAlmostEqual(row['growth_pct'],100*row['growth']/row['start'])
        self.assertAlmostEqual(window['hours'],(stamp(window['to'])-stamp(window['from'])).total_seconds()/3600,delta=.0051)
    def test_short_window_not_week(self):self.assertEqual(self.run_case()['rising8']['status'],'partial_window')
    def test_exact_week(self):self.assertEqual(self.run_case(days=('2026-10-14','2026-10-21'))['rising8']['status'],'published')
    def test_sparse_history_not_week(self):self.assertEqual(self.run_case(days=('2026-10-01','2026-10-21'))['rising8']['status'],'observed_window')
    def test_no_history(self):
        d=build_insights([s('2026-10-20',[c()])],[],pool([]));self.assertEqual(d['rising8']['items'],[])
    def test_renamed_account_same_id(self):
        self.assertEqual(len(self.run_case(c(handle='oldname'),c(handle='newname',x=20100))['rising8']['items']),1)
    def test_reused_handle_different_id(self):
        self.assertEqual(self.run_case(c(),c('2',x=20100))['rising8']['items'],[])
    def test_mixed_identity_evidence_not_joined(self):
        a=c();a.pop('x_id');self.assertEqual(self.run_case(a,c(x=20100))['rising8']['items'],[])
    def test_legacy_name_change_not_joined(self):
        a=c();b=c(x=20100);a.pop('x_id');b.pop('x_id');b['name']='Different person';self.assertFalse(same_identity(a,b))
    def test_missing_x(self):self.assertEqual(self.run_case(c(x=None),c(x=20100))['rising8']['items'],[])
    def test_missing_instagram_cannot_prove_cap(self):
        b=c(x=20100,ig=None);b['ig_status']='pending';self.assertEqual(self.run_case(c(),b)['rising8']['items'],[])
    def test_cap_and_floor(self):
        self.assertEqual(self.run_case(c(),c(x=1000001))['rising8']['items'],[])
        self.assertEqual(self.run_case(c(x=9999),c(x=10001))['rising8']['items'],[])
    def test_exact_cap_allowed(self):self.assertEqual(len(self.run_case(c(x=989900),c(x=990000))['rising8']['items']),1)
    def test_new_instagram_coverage_is_not_growth(self):
        a=c(ig=None);a['ig_status']='pending';b=c(x=20100,ig=300000);b['ig_as_of']='2026-10-21';row=self.run_case(a,b)['rising8']['items'][0];self.assertFalse(row['ig_included']);self.assertEqual(row['growth'],100)
    def test_carried_forward_not_growth(self):
        b=c(x=20100,ig=99999,ig_carried_forward=True);b['ig_as_of']='2026-10-21';self.assertFalse(self.run_case(c(),b)['rising8']['items'][0]['ig_included'])
    def test_ig_identity_change(self):
        b=c(x=20100);b['ig_as_of']='2026-10-21';b['ig_handle']='other';self.assertFalse(fresh_ig(c(),b))
    def test_ig_timestamp_offsets_compare_actual_time(self):
        a=c();b=c(x=20100);a['ig_checked_at']='2026-10-20T23:00:00-05:00';b['ig_checked_at']='2026-10-21T01:00:00Z';self.assertFalse(fresh_ig(a,b))
    def test_x_carried_forward_not_growth(self):
        self.assertEqual(self.run_case(c(),c(x=20100,x_carried_forward=True))['rising8']['items'],[])
    def test_x_repeated_observation_not_growth(self):
        a=c(x_checked_at='2026-10-20T12:00:00Z');b=c(x=20100,x_checked_at='2026-10-20T12:00:00Z');self.assertEqual(self.run_case(a,b)['rising8']['items'],[])
    def test_verified_recheck(self):
        b=c(x=20100,ig=10100);b['ig_as_of']='2026-10-21';row=self.run_case(c(),b)['rising8']['items'][0];self.assertTrue(row['ig_included']);self.assertEqual(row['growth'],200);self.assertEqual(row['start'],30000)
    def test_negative_and_zero_retained_but_not_published(self):
        for x in (19000,20000):
            d=self.run_case(c(),c(x=x));self.assertEqual(d['rising8']['items'],[]);self.assertEqual(len(d['rising8']['all']),1)
    def test_duplicate_observation_rejected(self):
        with self.assertRaises(ValueError):ordered([s('2026-10-20',[c()]),s('2026-10-20',[c()])])
    def test_bad_counts_rejected(self):
        for x in (-1,True,'20000',0.5):
            with self.assertRaises(ValueError):self.run_case(c(),c(x=x))
    def test_milestone_boundaries(self):
        for a,b,expected in [(999999,1000000,1),(1000000,999999,1),(1000001,1000000,0),(1000000,1000001,0)]:
            d=build_insights([s('2026-10-20',[c(x=a)]),s('2026-10-21',[c(x=b)])],[],pool([]));self.assertEqual(len(d['milestones']['crossed']),expected)
    def test_top8_excluded_from_emerging(self):
        a=c();b=c(x=20100);d=build_insights([s('2026-10-21',[b])],[s('2026-10-20',[a]),s('2026-10-21',[b])],pool([b]));self.assertEqual(d['rising8']['items'],[])
    def test_ties_deterministic(self):
        a=[c('1','b'),c('2','a')];b=[c('1','b',x=20100),c('2','a',x=20100)]
        d=build_insights([s('2026-10-21',[c('top','top',x=2000000)])],[s('2026-10-20',a),s('2026-10-21',b)],pool(b));self.assertEqual([r['rank'] for r in d['rising8']['items']],[1,1]);self.assertEqual(d['rising8']['items'][0]['x_handle'],'a')

if __name__=='__main__':unittest.main()
