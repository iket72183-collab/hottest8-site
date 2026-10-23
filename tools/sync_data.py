#!/usr/bin/env python3
"""Regenerate current data exports from the latest real snapshot, entirely offline.
Run after appending a snapshot, then commit that snapshot and both exports together.
Only reviewed editorial fields survive; observation fields always come from the snapshot.
"""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile
from build_insights import ordered, read_snapshots, count
from build_site import safe_json


def generate(root):
    snapshots=ordered(read_snapshots(root))
    if not snapshots:raise ValueError('No snapshots to sync')
    latest=snapshots[-1];old=json.loads((root/'data.json').read_text())
    by_handle={c['x_handle'].lower():c for c in old['creators']}
    by_id={str(c['x_id']):c for c in old['creators'] if c.get('x_id')}
    avatars=json.loads((root/'approved-avatars.json').read_text())
    creators=[]
    for row in latest['creators']:
        c=dict(row);handle=c['x_handle'].lower()
        if not isinstance(c.get('name'),str) or not c['name'].strip() or len(c['name'])>160:raise ValueError('Invalid name')
        if not re.fullmatch(r'[A-Za-z0-9_]{1,15}',c['x_handle']):raise ValueError('Invalid X handle')
        if c.get('ig_handle') and not re.fullmatch(r'[A-Za-z0-9_.]{1,30}',c['ig_handle']):raise ValueError('Invalid Instagram handle')
        if count(c.get('ig_followers')) and (not c.get('ig_handle') or c.get('ig_status')!='verified'):raise ValueError('Instagram count requires a verified account')
        if count(c.get('x_followers')) and count(c.get('ig_followers')) and not count(c['x_followers']+c['ig_followers']):raise ValueError('Count overflow')
        prior=by_id.get(str(c.get('x_id'))) or by_handle.get(handle)
        if prior:
            if prior.get('x_id') and (not c.get('x_id') or str(prior['x_id'])!=str(c['x_id'])):raise ValueError('Stable X identity conflict: review before syncing')
            same_id=bool(prior.get('x_id') and c.get('x_id') and str(prior['x_id'])==str(c['x_id']))
            if not same_id and prior['name']!=c['name']:raise ValueError('Legacy identity changed: review before syncing')
            if 'retired' not in c and 'retired' in prior:c['retired']=prior['retired']
            # Never transfer an image to an unreviewed handle or changed URL.
            if prior.get('avatar')==avatars.get(handle) and prior.get('avatar'):c['avatar']=prior['avatar']
        if c.get('avatar')!=avatars.get(handle):c.pop('avatar',None)
        c['x_checked_at']=c.get('x_checked_at') or c.get('fetched_at') or latest['fetched_at']
        creators.append(c)
    sources=latest.get('source',{})
    if not isinstance(sources,dict):raise ValueError('Snapshot source metadata must be an object')
    note=' · '.join(filter(None,[sources.get('x'),sources.get('instagram')])) or latest.get('note','See per-platform observation dates.')
    data={'site_name':old.get('site_name','Hottest8'),'as_of':latest['date'],'as_of_note':note,'contact_email':old.get('contact_email','hello@hottest8.com'),'x_source':sources.get('x','See per-account X observation dates.'),'ig_source':sources.get('instagram','See per-account Instagram observation dates.'),'creators':creators}
    return {'data.json':json.dumps(data,indent=2,ensure_ascii=False)+'\n','data.js':'window.TC_DATA='+safe_json(data)+';\nwindow.H8_AVATARS='+safe_json(avatars)+';\n'}


def sync(root,check=False):
    exports=generate(root)
    if check:return all((root/name).read_text()==body for name,body in exports.items())
    # Validate/serialize everything before writing; replace each file atomically.
    staged=[]
    try:
        for name,body in exports.items():
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=root,prefix='.sync-',delete=False) as f:
                f.write(body);staged.append((Path(f.name),root/name))
        for temporary,target in staged:os.replace(temporary,target)
    finally:
        for temporary,_ in staged:temporary.unlink(missing_ok=True)
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true',help='Exit nonzero if exports differ; do not write');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if not sync(root,args.check):raise SystemExit('Exports differ: run python3 tools/sync_data.py and commit snapshot + data.json + data.js together')
    print('Current exports match latest snapshot.' if args.check else 'Synced data.json and data.js. Commit both with the latest snapshot; no services called.')
