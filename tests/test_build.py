import json
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from urllib.parse import urlsplit,unquote
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_site import build, enrich, prerender, safe_json
ROOT=Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=set();self.links=[];self.scripts=[];self.inline_events=[];self.h1=0;self.errors=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids:self.errors.append('Duplicate ID '+a['id'])
            self.ids.add(a['id'])
        if tag=='h1':self.h1+=1
        if tag=='a':self.links.append(a.get('href',''))
        if tag=='script' and a.get('type')!='application/ld+json':self.scripts.append(a.get('src'))
        self.inline_events += [k for k in a if k.startswith('on')]

class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.output=Path(cls.temp.name)/'dist';build(ROOT,cls.output)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_internal_links_and_fragments(self):
        pages={p.name:Document(p.read_text()) for p in self.output.glob('*.html')}
        for name,doc in pages.items():
            self.assertEqual(doc.h1,1,name);self.assertFalse(doc.errors,name)
            for href in doc.links:
                url=urlsplit(href)
                if url.scheme or url.netloc:continue
                target=url.path.lstrip('/') or (name if not url.path else 'index.html')
                path=self.output/target
                self.assertTrue(path.is_file(),f'{name}: {href}')
                if url.fragment:self.assertIn(unquote(url.fragment),pages[target].ids,f'{name}: {href}')
    def test_static_output_excludes_maintenance_and_dependencies(self):
        for forbidden in ['tools','tests','node_modules','package.json','render.yaml','.git','docs']:
            self.assertFalse((self.output/forbidden).exists(),forbidden)
    def test_no_inline_handlers_or_scripts(self):
        for p in self.output.glob('*.html'):
            doc=Document(p.read_text());self.assertFalse(doc.inline_events,p.name);self.assertTrue(all(doc.scripts),p.name)
    def test_prerendered_ranking_matches_json(self):
        text=(self.output/'index.html').read_text();r=json.loads((self.output/'rankings.json').read_text())
        names=re.findall(r'<h3 class="creator-name">(.*?)</h3>',text)
        self.assertEqual(names,[c['name'] for c in r['top8']]);self.assertNotIn('{{',text)
    def test_platform_dates_enriched_from_snapshots(self):
        data=enrich(ROOT)
        self.assertTrue(all(c.get('x_checked_at') for c in data['creators']))
        self.assertTrue(all(c.get('ig_as_of') for c in data['creators'] if c['ig_followers'] is not None))
    def test_backup_json_cannot_close_script(self):
        self.assertNotIn('</script>',safe_json({'name':'</script><script>evil</script>'}))
    def test_prerender_escapes_synthetic_names_and_observation_attributes(self):
        name='<img src=x onerror=alert(1)> "Fixture"'
        creator={'name':name,'x_handle':'fixture_1','ig_handle':'fixture.1','x_followers':2,'ig_followers':3,'ig_status':'verified','x_checked_at':'2026-10-23" onmouseover="x'}
        markup=prerender({'creators':[creator]})
        doc=Document(markup)
        self.assertNotIn('<img',markup)
        self.assertIn('&lt;img',markup)
        self.assertFalse(doc.inline_events)
        self.assertEqual(doc.links,['https://x.com/fixture_1','https://www.instagram.com/fixture.1'])
    def test_no_package_runtime_dependencies(self):
        d=json.loads((ROOT/'package.json').read_text());self.assertFalse(d.get('dependencies'))
    def test_requested_fakecheck_copy_and_signup(self):
        text=(self.output/'verify.html').read_text();self.assertIn('Coming Soon',text);self.assertIn('100+ accounts',text);self.assertIn('our AI algorithm',text);self.assertIn('privately to the creator only',text);self.assertIn('id="newsletter-form"',text)
    def test_all_navs_match_requested_order(self):
        for p in self.output.glob('*.html'):
            nav=re.search(r'<nav aria-label="Main navigation">(.*?)</nav>',p.read_text()).group(1)
            self.assertEqual(re.findall(r'>([^<]+)</a>',nav),['Top 8','Rising 8','Fake Check','Newsletter','About'])
            self.assertIn('href="/about.html"',nav)
    def test_minimal_home_and_complete_about(self):
        home=(self.output/'index.html').read_text().split('<main',1)[1].split('</main>')[0]
        self.assertNotIn('class="hero"',home);self.assertNotIn('class="stats"',home);self.assertNotIn('editorial-rail',home);self.assertNotIn('newsletter-consent',home)
        self.assertIn('Muse research',home);self.assertIn('class="hero"',(self.output/'about.html').read_text())
    def test_no_placeholders_in_any_public_html(self):
        for p in self.output.glob('*.html'):self.assertNotRegex(p.read_text(),r'\{\{[^{}]+\}\}|<!--RANKINGS-->')
    def test_unknown_placeholder_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture=Path(temp)/'source'
            shutil.copytree(ROOT,fixture,ignore=shutil.ignore_patterns('node_modules','dist','.git','docs','__pycache__'))
            with (fixture/'index.html').open('a') as f:f.write('{{UNRECOGNIZED}}')
            with self.assertRaisesRegex(ValueError,'Unresolved template'):build(fixture,Path(temp)/'dist')
            self.assertFalse((Path(temp)/'dist'/'index.html').exists())
    def test_guard_old_artifacts(self):
        extra=self.output/'unexpected.txt';extra.write_text('should fail closed')
        try:
            with self.assertRaises(ValueError):build(ROOT,self.output)
        finally:extra.unlink()

if __name__=='__main__':unittest.main()
