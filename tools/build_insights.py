#!/usr/bin/env python3
"""Deterministic, offline insights. Importable for fixtures; no API calls or credentials."""
import argparse
import datetime as dt
import json
from pathlib import Path


def count(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9_007_199_254_740_991


def stamp(value):
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Observation timestamps must include a timezone')
    return result


def identity(row):
    return ('id', str(row['x_id'])) if row.get('x_id') else ('handle', row['x_handle'].lower())


def indexed(snapshot):
    rows = {}
    handles = set()
    for row in snapshot['creators']:
        key = identity(row)
        handle = row['x_handle'].lower()
        if key in rows or handle in handles:
            raise ValueError('Duplicate account identity in snapshot')
        for field in ('x_followers', 'ig_followers'):
            if row.get(field) is not None and not count(row[field]):
                raise ValueError('Invalid follower count')
        rows[key] = row
        handles.add(handle)
    return rows


def same_identity(a, b):
    if a.get('x_id') or b.get('x_id'):
        return bool(a.get('x_id') and b.get('x_id') and str(a['x_id']) == str(b['x_id']))
    # Legacy tracked snapshots have no stable IDs. Do not join changed names/handles.
    return a.get('name') == b.get('name') and a['x_handle'].lower() == b['x_handle'].lower()


def fresh_ig(a, b):
    if not all(count(c.get('ig_followers')) and c.get('ig_status') == 'verified' for c in (a,b)):
        return False
    if not a.get('ig_handle') or a['ig_handle'].lower() != str(b.get('ig_handle','')).lower():
        return False
    if a.get('ig_id') or b.get('ig_id'):
        if not a.get('ig_id') or str(a.get('ig_id')) != str(b.get('ig_id')):
            return False
    old, new = a.get('ig_checked_at') or a.get('ig_as_of'), b.get('ig_checked_at') or b.get('ig_as_of')
    def observed(value):
        return stamp(value+'T00:00:00+00:00' if len(value)==10 else value)
    try:
        return bool(old and new and observed(new)>observed(old) and not b.get('ig_carried_forward'))
    except (ValueError,TypeError):
        return False


def ordered(snapshots):
    snapshots = sorted(snapshots, key=lambda s: stamp(s['fetched_at']))
    times = [stamp(s['fetched_at']) for s in snapshots]
    if len(set(times)) != len(times):
        raise ValueError('Duplicate snapshot time')
    for s in snapshots:
        indexed(s)
    return snapshots


def fresh_x(a, b, start, end):
    """A carried-forward or backwards platform observation is not new history."""
    old = a.get('x_checked_at') or a.get('fetched_at') or start['fetched_at']
    new = b.get('x_checked_at') or b.get('fetched_at') or end['fetched_at']
    try:
        return not b.get('x_carried_forward') and stamp(old) < stamp(new) <= stamp(end['fetched_at'])
    except (ValueError, TypeError):
        return False


def ranked(rows, metric):
    rows = sorted(rows, key=lambda c: (-metric(c), c['x_handle'].lower()))
    previous, rank = None, 0
    result = []
    for i, c in enumerate(rows):
        value = metric(c)
        if value != previous:
            rank = i + 1
        previous = value
        result.append((rank,c))
    return result


def build_insights(snapshots, emerging, pool):
    snapshots, emerging = ordered(snapshots), ordered(emerging)
    if not snapshots:
        raise ValueError('No tracked snapshots')
    latest = snapshots[-1]
    valid = [c for c in latest['creators'] if count(c.get('x_followers')) and count(c.get('ig_followers')) and c.get('ig_status') == 'verified']
    total = lambda c: c['x_followers'] + c['ig_followers']
    top = [c for _,c in ranked(valid,total)[:8]]
    top_handles = {c['x_handle'].lower() for c in top}
    top_ids = {str(c['x_id']) for c in top if c.get('x_id')}
    out = {'generated_from':[s['date'] for s in snapshots], 'latest_snapshot':latest['date']}
    rules=pool['rules']; entries={identity(c):c for c in pool['creators']}
    rising={'status':'not_published','items':[],'all':[],'excluded':[],'pool_size':len(entries),'note':'Two real, dated observations are required. No growth is estimated.'}
    if len(emerging) >= max(2,rules['min_snapshots']):
        end=emerging[-1]; target=stamp(end['fetched_at'])-dt.timedelta(days=7)
        before=[s for s in emerging[:-1] if stamp(s['fetched_at'])<=target]
        start=before[-1] if before else emerging[0]
        hours=(stamp(end['fetched_at'])-stamp(start['fetched_at'])).total_seconds()/3600
        base=indexed(start); rows=[]
        for key,c in indexed(end).items():
            b=base.get(key); p=entries.get(key); reason=None
            if not p: continue
            if not b or not same_identity(b,c): reason='No comparable account identity at both observations'
            elif not all(count(v.get('x_followers')) for v in (b,c)): reason='Missing X observation'
            elif not fresh_x(b,c,start,end): reason='X observation was not independently refreshed'
            elif c['x_handle'].lower() in top_handles or str(c.get('x_id','')) in top_ids: reason='In current Top 8'
            # Eligibility cannot be inferred from an unknown Instagram count.
            cap_ig=c.get('ig_followers') if c.get('ig_status')=='verified' else None
            if cap_ig is None and p.get('ig_status')=='verified' and p.get('ig_as_of') and p['ig_as_of']<=end['date']:
                cap_ig=p.get('ig_followers')
            if not reason and not count(cap_ig): reason='Combined-cap eligibility unknown: Instagram unverified'
            if not reason and c['x_followers']+cap_ig>rules['max_combined_followers']: reason='Over combined follower cap'
            if reason:
                rising['excluded'].append({'name':c['name'],'x_handle':c['x_handle'],'reason':reason});continue
            include_ig=fresh_ig(b,c)
            initial=b['x_followers']+(b['ig_followers'] if include_ig else 0)
            if initial < rules['min_followers'] or initial<=0:
                rising['excluded'].append({'name':c['name'],'x_handle':c['x_handle'],'reason':'Below observation floor'});continue
            dx=c['x_followers']-b['x_followers']; di=c['ig_followers']-b['ig_followers'] if include_ig else None
            growth=dx+(di or 0)
            rows.append({'name':c['name'],'x_handle':c['x_handle'],'x_id':c.get('x_id'),'start':initial,'growth':growth,'growth_pct':100*growth/initial,'x_growth':dx,'ig_growth':di,'ig_included':include_ig,'identity_basis':'stable X ID' if c.get('x_id') else 'unchanged legacy name and handle','x_from':b.get('x_checked_at') or b.get('fetched_at') or start['fetched_at'],'x_to':c.get('x_checked_at') or c.get('fetched_at') or end['fetched_at'],'ig_from':(b.get('ig_checked_at') or b.get('ig_as_of')) if include_ig else None,'ig_to':(c.get('ig_checked_at') or c.get('ig_as_of')) if include_ig else None})
        rows.sort(key=lambda r:(-r['growth']/r['start'],-r['growth'],r['x_handle'].lower()))
        last=None; position=0
        for i,r in enumerate(rows):
            key=(r['growth']/r['start'],r['growth'])
            if key!=last:position=i+1
            last=key;r['rank']=position
        rising.update(status='published' if 165<=hours<=171 else 'partial_window' if hours<165 else 'observed_window',window={'from':start['fetched_at'],'to':end['fetched_at'],'hours':round(hours,2),'label':f'{hours:.1f}-hour observed window'},metric='Percentage growth over the stated observations. X only unless the same Instagram account was independently rechecked at both ends; unknown Instagram growth is not zero.',items=[r for r in rows if r['growth']>0][:8],all=rows)
    out['rising8']=rising
    crossed=[]
    for a,b in zip(snapshots,snapshots[1:]):
        A=indexed(a)
        for key,c in indexed(b).items():
            p=A.get(key)
            if not p or not same_identity(p,c):continue
            for platform,field in [('X','x_followers'),('Instagram','ig_followers')]:
                if not count(p.get(field)) or not count(c.get(field)):continue
                if platform=='Instagram' and not fresh_ig(p,c):continue
                if platform=='X' and not fresh_x(p,c,a,b):continue
                old,new=p[field],c[field]
                if old==new:continue
                # Landing ON a milestone from above is not falling below it.
                low,high=sorted((old,new))
                first=low//1_000_000+1
                for m in range(first,high//1_000_000+1):
                    milestone=m*1_000_000
                    crossed.append({'date':b['date'],'name':c['name'],'platform':platform,'milestone':milestone,'direction':'up' if new>old else 'down','from':old,'to':new})
    next_up=[]
    for c in latest['creators']:
        for platform,field in [('X','x_followers'),('Instagram','ig_followers')]:
            v=c.get(field)
            if not count(v) or (platform=='Instagram' and c.get('ig_status')!='verified'):continue
            milestone=(v//1_000_000+1)*1_000_000
            next_up.append({'name':c['name'],'platform':platform,'next_milestone':milestone,'to_go':milestone-v,'current':v,'as_of':c.get('ig_as_of') if platform=='Instagram' else c.get('fetched_at',latest['fetched_at'])})
    next_up.sort(key=lambda x:(x['to_go'],x['name']))
    out['milestones']={'crossed':crossed,'closest_next':next_up[:5]}
    gaps=[]
    for platform,rows,metric in [('Combined',valid,total),('X',[c for c in latest['creators'] if count(c.get('x_followers'))],lambda c:c['x_followers']),('Instagram',valid,lambda c:c['ig_followers'])]:
        rr=ranked(rows,metric)
        for (ra,a),(rb,b) in zip(rr,rr[1:]):gaps.append({'platform':platform,'ranks':[ra,rb],'leader':a['name'],'chaser':b['name'],'gap':metric(a)-metric(b),'leader_count':metric(a),'chaser_count':metric(b)})
    gaps.sort(key=lambda x:(x['gap'],x['platform'],x['leader']))
    out['closest_battles']={'items':gaps[:5]}
    return out


def read_snapshots(root, sub=''):
    return [json.loads(p.read_text()) for p in sorted((root/'snapshots'/sub).glob('????-??-??.json'))]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args();root=args.root
    result=build_insights(read_snapshots(root),read_snapshots(root,'emerging'),json.loads((root/'rising_pool.json').read_text()))
    (root/'insights.json').write_text(json.dumps(result,indent=2)+'\n')
    rankings=json.loads((root/'rankings.json').read_text())
    for k in ('rising8','milestones','closest_battles'):rankings[k]={a:b for a,b in result[k].items() if a!='all'}
    (root/'rankings.json').write_text(json.dumps(rankings,indent=2)+'\n')
    print(f"Built {len(result['rising8']['items'])} Rising entries from real snapshots; {result['rising8'].get('window',{}).get('label','no window')}")

if __name__=='__main__':main()
