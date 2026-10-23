import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from sync_data import sync, generate
from build_site import enrich, build
ROOT=Path(__file__).resolve().parents[1]

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        for name in ['data.json','data.js','approved-avatars.json']:shutil.copyfile(ROOT/name,self.root/name)
        shutil.copytree(ROOT/'snapshots',self.root/'snapshots')
    def tearDown(self):self.temp.cleanup()
    def newest(self):return sorted((self.root/'snapshots').glob('????-??-??.json'))[-1]
    def mutate(self,fn):
        p=self.newest();s=json.loads(p.read_text());fn(s);p.write_text(json.dumps(s))
    def test_idempotent_exports_and_muse_credit(self):
        sync(self.root);before=(self.root/'data.json').read_bytes();sync(self.root);self.assertEqual(before,(self.root/'data.json').read_bytes());self.assertTrue(sync(self.root,True));self.assertIn('Muse research',before.decode());enrich(self.root)
    def test_latest_snapshot_wins_and_guard_requires_sync(self):
        self.mutate(lambda s:s['creators'][0].update(x_followers=123456))
        with self.assertRaises(ValueError):enrich(self.root)
        self.assertFalse(sync(self.root,True));sync(self.root);self.assertEqual(enrich(self.root)['creators'][0]['x_followers'],123456)
    def test_pending_counts_remain_unknown(self):
        sync(self.root);d=enrich(self.root);pending=[c for c in d['creators'] if c['name'] in ['Brandi Love','Ava Addams']];self.assertEqual(len(pending),2);self.assertTrue(all(c['ig_followers'] is None and c['ig_status']=='pending_verification' for c in pending))
    def test_editorial_fields_preserved_but_observation_metadata_replaced(self):
        sync(self.root);d=enrich(self.root);self.assertTrue(d['creators'][0]['retired']);self.assertIn('avatar',d['creators'][0]);self.assertTrue(d['creators'][0]['ig_carried_forward'])
    def test_changed_legacy_identity_fails_without_partial_write(self):
        before=(self.root/'data.json').read_bytes();self.mutate(lambda s:s['creators'][0].update(name='Unrelated synthetic identity'))
        with self.assertRaises(ValueError):sync(self.root)
        self.assertEqual(before,(self.root/'data.json').read_bytes())
    def test_data_js_matches_json(self):
        sync(self.root);d=json.loads((self.root/'data.json').read_text());js=(self.root/'data.js').read_text();self.assertEqual(json.loads(js.split('window.TC_DATA=',1)[1].split(';\n',1)[0]),d)

if __name__=='__main__':unittest.main()
