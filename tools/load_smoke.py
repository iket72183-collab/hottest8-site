#!/usr/bin/env python3
"""Bounded local-only smoke check, NOT a production capacity measurement.
Plan: 4 workers, 80 synthetic JSON requests + 8 malformed/write requests;
2-second request timeout; 20-second wall budget; stop after 3 failures or p95 > 1s.
No emails, provider calls, authentication attempts or production URLs.
"""
import concurrent.futures
import json
import statistics
import time
import urllib.error
import urllib.request
BASE='http://127.0.0.1:8768'

def request(path,method='GET',body=None):
    started=time.monotonic()
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE+path,data=body,method=method),timeout=2) as response:
            response.read(65536);code=response.status
    except urllib.error.HTTPError as exc:code=exc.code
    except Exception:code=0
    return {'status':code,'ms':round((time.monotonic()-started)*1000,2)}

if __name__=='__main__':
    with urllib.request.urlopen(BASE+'/__test__/state',timeout=2) as response:state=json.load(response)
    if state.get('scenario')!='synthetic':raise SystemExit('Refusing: select the synthetic local fixture first')
    started=time.monotonic();results=[];stopped=False
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for _ in range(20):
            batch=list(executor.map(lambda _:request('/data.json'),range(4)));results.extend(batch)
            values=sorted(r['ms'] for r in results)
            if sum(r['status']!=200 for r in results)>=3 or values[int(.95*(len(values)-1))]>1000 or time.monotonic()-started>20:
                stopped=True;break
    abuse=[]
    if not stopped:
        for path,method,body in [('/../package.json','GET',None),('/%2e%2e/package.json','GET',None),('/.env','GET',None),('/.git/config','GET',None),('/newsletter','POST',b'email=synthetic%40example.invalid'),('/verify','POST',b'{}'),('/__test__/scenario','POST',b'bad-json'),('/__test__/scenario','POST',b'x'*101)]:
            abuse.append({'path':path,'method':method,**request(path,method,body)})
    durations=sorted(r['ms'] for r in results)
    report={'scope':BASE+' synthetic fixture only','concurrency':4,'max_requests':88,'requests_completed':len(results)+len(abuse),'stop_conditions':'3 failures, observed p95 > 1000 ms, 20 s wall budget; request timeout 2 s','stopped_early':stopped,'successes':sum(r['status']==200 for r in results),'p50_ms':statistics.median(durations),'p95_ms':durations[int(.95*(len(durations)-1))],'max_ms':max(durations),'elapsed_seconds':round(time.monotonic()-started,3),'abuse_probes':abuse,'limitation':'Local static-server smoke test only. Does not measure Render capacity or provider signup rate limits.'}
    print(json.dumps(report,indent=2))
    if stopped or any(r['status']!=200 for r in results) or [r['status'] for r in abuse]!=[404,404,404,404,405,405,400,413]:raise SystemExit(1)
