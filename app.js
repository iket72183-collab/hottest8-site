/* No HTML interpolation: snapshot strings are always text, never markup. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const el = (tag, cls, text) => {const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n;};
  const dateText = value => H8.date(value) ? new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'America/Chicago'}).format(new Date(value.length===10?value+'T12:00:00Z':value)) : 'Date unknown';
  let data, mode='combined', loading=false;
  function platform(c, p) {
    const n=c[p+'_followers'], h=c[p+'_handle'], label=p==='x'?'X':'Instagram';
    const href=H8.profileUrl(p,h);
    if (H8.count(n) && href && (p==='x'||c.ig_status==='verified')) {
      const box=el('a','platform platform-link');box.href=href;box.target='_blank';box.rel='noopener noreferrer nofollow';box.setAttribute('aria-label','Open @'+h+' on '+label);
      box.append(el('span','handle',label+' · @'+h));
      box.append(el('span','platform-count',H8.exact(n)+' follows'));
      const stamp=c[p+'_checked_at'] || c[p+'_as_of'];
      box.append(el('span','observed',(c[p+'_carried_forward']?'Carried forward · ':'Checked · ')+dateText(stamp)));
      return box;
    }
    const box=el('div','platform');box.append(el('span','observed',label+' · not verified'));
    return box;
  }
  function card(row) {
    const c=row.creator, li=el('li','rank-card'), num=el('div','rank-number',String(row.rank).padStart(2,'0'));
    li.append(num);
    li.append(H8.avatarEl(el,c));
    const info=el('div','creator-info'), heading=el('h3','creator-name',c.name);if(c.retired)heading.append(el('span','badge','Retired'));info.append(heading);
    const platforms=el('div','platforms');platforms.append(platform(c,'x'),platform(c,'ig'));info.append(platforms);li.append(info);
    const total=el('div','rank-total');total.append(el('strong','',H8.format(row.value)),el('span','',mode==='combined'?'summed follows':mode==='x'?'X follows':'Instagram follows'),el('small','exact-count',H8.exact(row.value)+(row.tied?' · tied':'')));li.append(total);return li;
  }
  function render() {
    if(!data)return;
    const rows=H8.rank(data.creators,mode), list=$('list');
    if(list)list.replaceChildren(...rows.map(card));
    if(list&&!rows.length)list.append(el('li','empty-state','No verified counts for this view. Try another platform or check back after the next refresh.'));
    const pending=data.creators.filter(c=>H8.score(c,'combined')==null);
    if($('pendlist'))$('pendlist').replaceChildren(...pending.map(c=>{const li=el('li','pending-row');li.append(el('strong','',c.name),el('span','','Combined rank unavailable · '+H8.exact(c.x_followers)+' X follows'));return li;}));
    if($('pending-empty'))$('pending-empty').hidden=pending.length>0;
    const set=(id,text)=>{if($(id))$(id).textContent=text;};
    set('s-count',data.creators.length);set('s-date',dateText(data.as_of));set('s-total',H8.format(data.creators.reduce((n,c)=>n+(H8.score(c,'combined')||0),0)));
    set('topnote',{combined:'X + Instagram · summed follows, not unique people',x:'X follows · ranked independently',ig:'Instagram follows · verified counts only'}[mode]);
    set('coverage',rows.length+' ranked entries from '+data.creators.length+' tracked creators. '+pending.length+' awaiting complete counts.');
    set('asof',data.as_of_note||'See each platform’s observation date.');
    if($('ranking-status'))$('ranking-status').textContent='Showing '+rows.length+' entries, '+{combined:'combined',x:'X',ig:'Instagram'}[mode]+' ranking.';
    document.querySelectorAll('[data-sort]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.sort===mode));b.classList.toggle('on',b.dataset.sort===mode);});
    if($('stale-note')){$('stale-note').hidden=!H8.stale(data.as_of);$('stale-note').textContent='This ranking snapshot is more than three days old. Counts remain dated; a scheduled refresh is not a guarantee of fresh data.';}
  }
  async function load() {
    if(loading)return;loading=true;
    const controller=new AbortController(), timeout=setTimeout(()=>controller.abort(),6000);
    if($('ranking-status'))$('ranking-status').textContent='Checking the latest snapshot…';
    if($('retry-data'))$('retry-data').disabled=true;
    try {
      const response=await fetch('data.json',{cache:'no-cache',signal:controller.signal});if(!response.ok)throw new Error('Unavailable');
      data=H8.validateData(await response.json());if($('fallback'))$('fallback').hidden=true;
    } catch {
      try {data=H8.validateData(window.TC_DATA);}catch {data=null;}
      if($('fallback')){$('fallback').hidden=false;$('fallback-message').textContent=data?'Live data unavailable. Showing the bundled snapshot from '+dateText(data.as_of)+'.':'Ranking data unavailable. Please try again later.';}
    } finally {clearTimeout(timeout);loading=false;if($('retry-data'))$('retry-data').disabled=false;}
    if(data)render();
    else if($('list'))$('list').replaceChildren(el('li','empty-state','We cannot verify the ranking data right now. No estimated counts are shown.'));
    document.querySelectorAll('[data-sort]').forEach(b=>b.disabled=!data);
  }
  document.querySelectorAll('[data-sort]').forEach(b=>b.addEventListener('click',()=>{if(!data)return;mode=b.dataset.sort;render();}));
  $('retry-data')?.addEventListener('click',load);
  if($('list')||$('pendlist')) { if(document.getElementById('agegate')) window.addEventListener('h8:entered',load,{once:true}); else load(); }
})();
