const fmt=n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(0)+'K':n;
const ini=n=>n.split(' ').map(w=>w[0]).slice(0,2).join('');
const av=c=>`<img class="av" src="${c.avatar}" alt="${c.name}" referrerpolicy="no-referrer" onerror="this.outerHTML='<div class=&quot;av&quot;>${ini(c.name)}</div>'">`;
let D,mode='combined';
const key={combined:c=>c.x_followers+c.ig_followers,x:c=>c.x_followers,ig:c=>c.ig_followers};
function card(c,i){const t=key[mode](c);return `<li class="card"><div class="rank">${i+1}</div>${av(c)}<div><div class="nm">${c.name}${c.retired?'<span class="badge">Retired</span>':''}</div>
<div class="sub"><a href="https://x.com/${c.x_handle}" target="_blank" rel="noopener nofollow">𝕏 @${c.x_handle}</a> ${fmt(c.x_followers)} · <a href="https://instagram.com/${c.ig_handle}" target="_blank" rel="noopener nofollow">IG @${c.ig_handle}</a> ${fmt(c.ig_followers)}</div></div>
<div class="tot"><b>${fmt(t)}</b><small>${{combined:'combined',x:'X followers',ig:'IG followers'}[mode]}</small></div></li>`}
function render(){const s=[...D.creators].sort((a,b)=>key[mode](b)-key[mode](a));
list.innerHTML=s.slice(0,8).map(card).join('');list2.innerHTML=s.slice(8).map((c,i)=>card(c,i+8)).join('')}
fetch('data.json').then(r=>r.json()).catch(()=>window.TC_DATA).then(d=>{D=d;
document.querySelectorAll('[data-sitename]').forEach(e=>e.textContent=d.site_name);
document.querySelectorAll('.adlink').forEach(a=>a.href='mailto:'+d.contact_email);
document.getElementById("s-total").textContent=fmt(d.creators.reduce((a,c)=>a+c.x_followers+c.ig_followers,0));
document.getElementById("s-date").textContent=new Date(d.as_of+'T12:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
asof.textContent=d.as_of_note;
const by=Object.fromEntries(d.creators.map(c=>[c.x_handle,c]));
render();});
document.querySelectorAll('.toggle button').forEach(b=>b.onclick=()=>{document.querySelector('.toggle .on').classList.remove('on');b.classList.add('on');mode=b.dataset.sort;render()});
