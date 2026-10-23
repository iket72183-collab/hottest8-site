#!/usr/bin/env python3
"""Loopback-only static preview. Test scenarios never use live email or platform services."""
import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import time

SCENARIOS={'normal','empty','malformed','outage','slow','long-names','insights-malformed','newsletter-success','newsletter-outage','newsletter-retry','synthetic'}
SYNTHETIC={'site_name':'Hottest8 test fixture','as_of':'2026-10-23','creators':[{'name':'Fixture Creator '+str(i),'x_handle':'fixture_'+str(i),'x_followers':90000-i*100,'ig_handle':'fixture_'+str(i),'ig_followers':50000+i*100,'ig_status':'verified','x_checked_at':'2026-10-23T12:00:00Z','ig_as_of':'2026-10-22'} for i in range(1,13)]}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def respond(self,code,body=b'',content_type='text/plain; charset=utf-8'):
        self.send_response(code);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.end_headers()
        if self.command!='HEAD':
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
    def do_POST(self):
        if self.path!='/__test__/scenario' or not self.server.scenarios:return self.respond(405,b'No signup or write endpoint')
        n=int(self.headers.get('Content-Length','0'))
        if n>100:return self.respond(413,b'Bound exceeded')
        try:
            scenario=json.loads(self.rfile.read(n))['scenario']
            if scenario not in SCENARIOS:raise ValueError()
        except (ValueError,KeyError):return self.respond(400,b'Invalid fixture')
        self.server.scenario=scenario;self.server.mock_requests=0;self.respond(200,b'Fixture selected')
    def do_HEAD(self):self.do_GET()
    def do_GET(self):
        raw=unquote(urlsplit(self.path).path)
        if raw=='/__test__/state' and self.server.scenarios:return self.respond(200,json.dumps({'scenario':self.server.scenario,'mock_requests':self.server.mock_requests}).encode(),'application/json')
        if raw=='/__mock__/analytics.js':return self.respond(200,b'window.fixtureEvents=[];window.goatcounter={count:function(e){window.fixtureEvents.push(e)}};','text/javascript')
        if raw=='/__mock__/a10ae064-cd08-11f1-b060-c974730c96d2.js':
            self.server.mock_requests+=1
            if self.server.scenario=='newsletter-outage' or (self.server.scenario=='newsletter-retry' and self.server.mock_requests==1):return self.respond(503,b'Fixture provider outage')
            script=b'''const f=document.createElement('form'); f.innerHTML='<label>Fixture email<input type="email" required name="email"></label><button>Test subscription</button>';f.addEventListener('submit',e=>{e.preventDefault();f.setAttribute('data-submitted','local-only');});document.getElementById('newsletter-form').append(f);'''
            return self.respond(200,script,'text/javascript')
        path=(self.server.root/raw.lstrip('/')).resolve()
        if self.server.root not in path.parents and path!=self.server.root:return self.respond(404,b'Not found')
        if any(part.startswith('.') for part in Path(raw).parts):return self.respond(404,b'Not found')
        if path.is_dir():path=path/'index.html'
        if not path.is_file():return self.respond(404,(self.server.root/'404.html').read_bytes(),'text/html; charset=utf-8')
        scenario=self.server.scenario
        if path.name in ['data.json','insights.json']:
            if scenario=='slow':time.sleep(7)
            if scenario in ['outage','slow']:return self.respond(503,b'Fixture outage')
        if path.name=='data.json':
            if scenario=='malformed':return self.respond(200,b'{broken','application/json')
            if scenario in ['empty','long-names','synthetic']:
                d=json.loads(json.dumps(SYNTHETIC))
                if scenario=='empty':d['creators']=[]
                if scenario=='long-names':
                    d['creators'][0]['name']='<img src=x onerror=alert(1)> A very long synthetic creator name that must wrap safely without executing any markup'
                    d['creators'][0]['avatar']='javascript:alert(1)'
                return self.respond(200,json.dumps(d).encode(),'application/json')
        if path.name=='insights.json' and scenario=='insights-malformed':return self.respond(200,b'{"rising8":{"items":[{"growth_pct":"bad"}]}}','application/json')
        body=path.read_bytes()
        if path.name=='data.js' and scenario=='outage':body=b'window.TC_DATA=null; window.H8_AVATARS={};'
        # Test-only substitutions permit exercising the real embed state machine with local scripts.
        if path.name=='site.js' and scenario.startswith('newsletter-'):
            text=body.decode().replace("['hottest8.com','www.hottest8.com'].includes(location.hostname)",'true').replace('https://gc.zgo.at/count.js','/__mock__/analytics.js').replace('https://eomail5.com/form/','/__mock__/');body=text.encode()
        self.respond(200,body,mimetypes.guess_type(path.name)[0] or 'application/octet-stream')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8768);parser.add_argument('--test-scenarios',action='store_true');parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]/'dist');args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.root=args.root.resolve();server.scenarios=args.test_scenarios;server.scenario='normal';server.mock_requests=0;server.daemon_threads=True
    print(f'Hottest8 local preview: http://127.0.0.1:{args.port} (test scenarios: {args.test_scenarios}; no live email)',flush=True);server.serve_forever()
