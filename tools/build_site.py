#!/usr/bin/env python3
"""Build a small allowlisted static artifact. No networking, dependencies or account access."""
import argparse
import html
import json
import re
import shutil
from pathlib import Path
from build_insights import build_insights, read_snapshots, ranked, ordered, count

FILES=['index.html','about.html','rising.html','verify.html','404.html','style.css','core.js','site.js','app.js','insights.js','favicon.svg','og-image.png','robots.txt','sitemap.xml','llms.txt']

def safe_json(data):
    return json.dumps(data,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')


def enrich(root):
    source=json.loads((root/'data.json').read_text());latest=ordered(read_snapshots(root))[-1]; rows={c['x_handle'].lower():c for c in latest['creators']}
    if len(rows)!=len(source['creators']):raise ValueError('Data and latest snapshot membership differ; review before publishing')
    for c in source['creators']:
        s=rows.get(c['x_handle'].lower())
        if not s or s['name']!=c['name']:raise ValueError('Identity mismatch between data and snapshot')
        for k in ['x_followers','ig_followers','ig_handle']:
            if c.get(k)!=s.get(k):raise ValueError(f'{k} differs from snapshot: refresh data before build')
        if not re.fullmatch(r'[A-Za-z0-9_]{1,15}',c['x_handle']):raise ValueError('Invalid X handle')
        if c.get('ig_handle') and not re.fullmatch(r'[A-Za-z0-9_.]{1,30}',c['ig_handle']):raise ValueError('Invalid Instagram handle')
        if count(c.get('x_followers')) and count(c.get('ig_followers')) and not count(c['x_followers']+c['ig_followers']):raise ValueError('Count overflow')
        if c.get('x_id') and s.get('x_id') and str(c['x_id'])!=str(s['x_id']):raise ValueError('Stable X identity changed; review required')
        c['x_checked_at']=s.get('x_checked_at') or s.get('fetched_at',latest['fetched_at'])
        for k in ['x_id','x_carried_forward','ig_id','ig_checked_at','ig_as_of','ig_carried_forward','ig_status','ig_source']:
            if k in s:c[k]=s[k]
    source['as_of']=latest['date'];return source


AVATAR_RE=re.compile(r'^https://pbs\.twimg\.com/profile_images/[0-9]+/[A-Za-z0-9_-]+_400x400\.(?:jpg|jpeg|png|webp)$')


def load_avatars(root):
    """avatars.json -> {lowercase x handle: url}. Only SFW-reviewed pbs.twimg.com _400x400 URLs survive."""
    path=root/'avatars.json'
    if not path.exists():return {}
    doc=json.loads(path.read_text());out={}
    for h,v in (doc.get('avatars') or {}).items():
        url=v.get('url') if isinstance(v,dict) else None
        if isinstance(url,str) and AVATAR_RE.match(url) and re.fullmatch(r'[a-z0-9_]{1,15}',h):out[h]=url
    return out


def avatar_html(c,avatars):
    initials=html.escape(''.join(w[0] for w in c['name'].split()[:2]))
    url=avatars.get(c['x_handle'].lower())
    if not url:return f'<div class="avatar" aria-hidden="true">{initials}</div>'
    alt=html.escape(c['name']+' on X')
    return f'<div class="avatar">{initials}<img src="{html.escape(url)}" alt="{alt}" width="64" height="64" loading="lazy" decoding="async" referrerpolicy="no-referrer"></div>'


def fmt(n):
    return f'{n/1e6:.1f}M' if n>=1e6 else f'{n/1000:.1f}K' if n>=1000 else str(n)


def prerender(data,avatars={}):
    valid=[c for c in data['creators'] if count(c.get('x_followers')) and count(c.get('ig_followers')) and c.get('ig_status')=='verified']
    rows=[]
    for rank,c in ranked(valid,lambda c:c['x_followers']+c['ig_followers'])[:8]:
        name=html.escape(c['name']);initials=html.escape(''.join(w[0] for w in c['name'].split()[:2]));total=c['x_followers']+c['ig_followers'];p=[]
        for platform,label,host in [('x','X','x.com'),('ig','Instagram','www.instagram.com')]:
            handle=html.escape(c[platform+'_handle']);date=html.escape(c.get(platform+'_checked_at') or c.get(platform+'_as_of') or 'Date unknown')
            p.append(f'<div class="platform"><a class="handle" href="https://{host}/{handle}" rel="noopener noreferrer nofollow" target="_blank">{label} · @{handle}</a><span class="platform-count">{c[platform+"_followers"]:,} follows</span><span class="observed">Checked · {date}</span></div>')
        rows.append(f'<li class="rank-card"><div class="rank-number">{rank:02}</div>{avatar_html(c,avatars)}<div class="creator-info"><h3 class="creator-name">{name}</h3><div class="platforms">{"".join(p)}</div></div><div class="rank-total"><strong>{fmt(total)}</strong><span>summed follows</span><small class="exact-count">{total:,}</small></div></li>')
    return ''.join(rows)


def favicon_ico(n=32):
    """32x32 ICO (BMP payload) drawn from favicon.svg colors: dark rounded square, gold 8."""
    import struct
    bg=(11,11,11);gold=(55,175,212)
    rows=[]
    for y in range(n-1,-1,-1):
        row=b''
        for x in range(n):
            cx,cy=x+.5,y+.5;r=6
            dx=max(r-cx,0,cx-(n-r));dy=max(r-cy,0,cy-(n-r))
            if dx*dx+dy*dy>r*r:row+=bytes((0,0,0,0));continue
            ink=False
            for oy,ry in ((10.5,6),(21.5,7)):
                ex=(cx-16)/(ry-.5);ey=(cy-oy)/ry;d=(ex*ex+ey*ey)**.5
                if .55<=d<=1.05:ink=True
            row+=bytes(gold if ink else bg)+b'\xff'
        rows.append(row)
    xor=b''.join(rows);mask=b'\x00'*(4*n)
    bmp=struct.pack('<IiiHHIIiiII',40,n,2*n,1,32,0,len(xor)+len(mask),0,0,0,0)+xor+mask
    return struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',n,n,0,0,1,32,len(bmp),22)+bmp


def build(root,output):
    if output.resolve()==root.resolve():raise ValueError('Build output must not overwrite the source root')
    data=enrich(root);insights=build_insights(read_snapshots(root),read_snapshots(root,'emerging'),json.loads((root/'rising_pool.json').read_text()))
    # Standard dated snapshots are a documented public data export linked from
    # rankings.json. Emerging snapshots and the pool are build inputs only.
    public_snapshots=sorted((root/'snapshots').glob('????-??-??.json'))
    expected=set(FILES+['data.json','data.js','insights.json','rankings.json','favicon.ico','avatars.js']) | {str(p.relative_to(root)) for p in public_snapshots}
    if output.exists():
        unexpected=[str(p.relative_to(output)) for p in output.rglob('*') if (p.is_file() or p.is_symlink()) and (p.is_symlink() or str(p.relative_to(output)) not in expected)]
        if unexpected:raise ValueError('Unexpected files in build output; use a new empty output directory: '+', '.join(unexpected))
    output.mkdir(parents=True,exist_ok=True)
    replacements={'{{TOTAL}}':fmt(sum(c['x_followers']+c['ig_followers'] for c in data['creators'] if count(c.get('x_followers')) and count(c.get('ig_followers')) and c.get('ig_status')=='verified')),'{{COUNT}}':str(len(data['creators'])),'{{DATE}}':data['as_of'],'{{SOURCE_NOTE}}':html.escape(data.get('as_of_note','')),'<!--RANKINGS-->':prerender(data,load_avatars(root))}
    rendered={}
    for f in FILES:
        if f.endswith('.html'):
            text=(root/f).read_text()
            for old,new in replacements.items():text=text.replace(old,new)
            if f=='index.html':
                entries=[{'@type':'ListItem','position':rank,'item':{'@type':'Person','name':c['name'],'sameAs':['https://x.com/'+c['x_handle'],'https://www.instagram.com/'+c['ig_handle']]}} for rank,c in ranked([c for c in data['creators'] if count(c.get('x_followers')) and count(c.get('ig_followers')) and c.get('ig_status')=='verified'],lambda c:c['x_followers']+c['ig_followers'])[:8]]
                text=text.replace('</head>','<script type="application/ld+json">'+safe_json({'@context':'https://schema.org','@type':'ItemList','name':'Hottest8 tracked Combined ranking','dateModified':data['as_of'],'itemListElement':entries})+'</script></head>')
            if re.search(r'\{\{[^{}]+\}\}|<!--RANKINGS-->',text):raise ValueError('Unresolved template marker in '+f)
            rendered[f]=text
    for f in FILES:
        if f in rendered:(output/f).write_text(rendered[f])
        else:shutil.copyfile(root/f,output/f)
    (output/'favicon.ico').write_bytes(favicon_ico())
    (output/'avatars.js').write_text('window.H8_AVATARS='+safe_json(load_avatars(root))+';\n')
    (output/'data.json').write_text(json.dumps(data,indent=2)+'\n')
    avatars=json.loads((root/'approved-avatars.json').read_text())
    (output/'data.js').write_text('window.TC_DATA='+safe_json(data)+';\nwindow.H8_AVATARS='+safe_json(avatars)+';\n')
    (output/'insights.json').write_text(json.dumps(insights,indent=2)+'\n')
    rankings=json.loads((root/'rankings.json').read_text());rankings['last_updated']=data['as_of'];rankings['tracked_count']=len(data['creators']);rankings['top8']=[]
    valid=[c for c in data['creators'] if count(c.get('x_followers')) and count(c.get('ig_followers')) and c.get('ig_status')=='verified']
    combined=[]
    for rank,c in ranked(valid,lambda c:c['x_followers']+c['ig_followers']):combined.append({'rank':rank,**{k:v for k,v in c.items() if k!='avatar'},'combined_followers':c['x_followers']+c['ig_followers'],'x_url':'https://x.com/'+c['x_handle'],'ig_url':'https://www.instagram.com/'+c['ig_handle']})
    rankings.update(top8=combined[:8],also_ranked=combined[8:],combined_ranked_count=len(valid),hero_total_combined=sum(c['combined_followers'] for c in combined),as_of_note=data.get('as_of_note','See per-platform observation dates.'),pending_instagram=[{k:v for k,v in c.items() if k!='avatar'} for c in data['creators'] if c not in valid],x_only_ranking=[{'rank':rank,'name':c['name'],'x_handle':c['x_handle'],'x_followers':c['x_followers']} for rank,c in ranked([c for c in data['creators'] if count(c.get('x_followers'))],lambda c:c['x_followers'])])
    rankings['sources']={'x':data.get('x_source','See x_checked_at per account.'),'instagram':data.get('ig_source','Instagram API (Muse research); see per-account observation dates.')}
    rankings['snapshots']=['https://hottest8.com/'+str(p.relative_to(root)) for p in sorted((root/'snapshots').glob('????-??-??.json'))]
    rankings['changes_note']='Week-over-week changes are not computed by this build. Rising entries carry their own actual observation window.'
    for k in ['rising8','milestones','closest_battles']:rankings[k]={a:b for a,b in insights[k].items() if a!='all'}
    (output/'rankings.json').write_text(json.dumps(rankings,indent=2)+'\n')
    for source in public_snapshots:
        target=output/source.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    print(f'Built {output}: {len(data["creators"])} creators, {len(insights["rising8"]["items"])} Rising entries. Offline; no external services called.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();root=Path(__file__).resolve().parents[1];build(root,args.output or root/'dist')
