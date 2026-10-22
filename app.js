const fmt=n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(0)+'K':n;
const ini=n=>n.split(' ').map(w=>w[0]).slice(0,2).join('');
const av=c=>!c.avatar?`<div class="av">${ini(c.name)}</div>`:`<img class="av" src="${c.avatar}" alt="${c.name}" referrerpolicy="no-referrer" onerror="this.outerHTML='<div class=&quot;av&quot;>${ini(c.name)}</div>'">`;
let D,mode='combined';
const hasIG=c=>c.ig_followers!=null;
const key={combined:c=>c.x_followers+c.ig_followers,x:c=>c.x_followers,ig:c=>c.ig_followers};
const pool=()=>mode==='x'?D.creators:D.creators.filter(hasIG);
function card(c,i){const t=key[mode](c);return `<li class="card"><div class="rank">${i+1}</div>${av(c)}<div><div class="nm">${c.name}${c.retired?'<span class="badge">Retired</span>':''}</div>
<div class="sub"><a href="https://x.com/${c.x_handle}" target="_blank" rel="noopener nofollow">𝕏 @${c.x_handle}</a> <span title="${c.x_followers.toLocaleString('en-US')}">${fmt(c.x_followers)}</span> · ${hasIG(c)?`<a href="https://instagram.com/${c.ig_handle}" target="_blank" rel="noopener nofollow">IG @${c.ig_handle}</a> <span title="${c.ig_followers.toLocaleString('en-US')}">${fmt(c.ig_followers)}</span>`:'<span class="pend">IG pending verification</span>'}</div></div>
<div class="tot"><b title="${t.toLocaleString('en-US')} exact">${fmt(t)}</b><small>${{combined:'combined',x:'X followers',ig:'IG followers'}[mode]}</small></div></li>`}
function render(){const s=[...pool()].sort((a,b)=>key[mode](b)-key[mode](a));
const L=document.getElementById('list');if(L)L.innerHTML=s.slice(0,8).map(card).join('');
const n=D.creators.length,v=D.creators.filter(hasIG).length,P=D.creators.filter(c=>!hasIG(c)).sort((a,b)=>b.x_followers-a.x_followers);
const tn=document.getElementById('topnote');if(tn)tn.textContent={combined:'Ranked by combined X + Instagram followers',x:'Ranked by X followers',ig:'Ranked by Instagram followers'}[mode];
const pw=document.getElementById('pending');if(pw){pw.hidden=mode==='x'||!P.length;document.getElementById('pendlist').innerHTML=P.map(c=>`<li class="card"><div class="rank">–</div>${av(c)}<div><div class="nm">${c.name}${c.retired?'<span class="badge">Retired</span>':''}</div><div class="sub"><a href="https://x.com/${c.x_handle}" target="_blank" rel="noopener nofollow">𝕏 @${c.x_handle}</a> <span title="${c.x_followers.toLocaleString('en-US')}">${fmt(c.x_followers)}</span> · <span class="pend">IG pending verification</span></div></div><div class="tot"><b>—</b><small>not ranked</small></div></li>`).join('')}}
let FB=false;
fetch('data.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw 0;return r.json()}).then(j=>{if(!j||!j.creators||!j.creators.length)throw 0;return j}).catch(()=>{FB=true;return window.TC_DATA}).then(d=>{if(!d)return;D=d;
const fbn=document.getElementById('fallback');if(fbn&&FB){fbn.textContent='Showing backup data from '+new Date(d.as_of+'T12:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})+' ('+d.as_of_note+'); live data unavailable.';fbn.hidden=false}
const a2=document.getElementById('asof2');if(a2)a2.textContent=d.as_of_note;
document.querySelectorAll('[data-sitename]').forEach(e=>e.textContent=d.site_name);
document.querySelectorAll('.adlink').forEach(a=>a.href='mailto:'+d.contact_email);
const st=document.getElementById("s-total");if(st)st.textContent=fmt(d.creators.filter(hasIG).reduce((a,c)=>a+c.x_followers+c.ig_followers,0));
const su=document.getElementById("s-upd");if(su)su.textContent=new Date(d.as_of+'T12:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
const sd=document.getElementById("s-date");if(sd)sd.textContent=new Date(d.as_of+'T12:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
const ao=document.getElementById('asof');if(ao)ao.textContent=d.as_of_note;
const by=Object.fromEntries(d.creators.map(c=>[c.x_handle,c]));
const tc=document.getElementById("s-count");if(tc)tc.textContent=d.creators.length;
render();});
document.querySelectorAll('.toggle button').forEach(b=>b.onclick=()=>{document.querySelector('.toggle .on').classList.remove('on');b.classList.add('on');mode=b.dataset.sort;render()});
