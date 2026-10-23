(() => {
  'use strict';
  const $=id=>document.getElementById(id), make=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e;};
  let loading=false;
  function render(d) {
    const r=d.rising8;
    if($('r8win'))$('r8win').textContent=r.status==='published'?'Seven-day observations':r.status==='partial_window'?'Early observations':r.status==='observed_window'?'Extended observations':'Awaiting history';
    if($('r8note'))$('r8note').textContent=r.metric||r.note;
    if($('r8dates'))$('r8dates').textContent=r.window?new Intl.DateTimeFormat('en-US',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Chicago'}).format(new Date(r.window.from))+' → '+new Intl.DateTimeFormat('en-US',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Chicago'}).format(new Date(r.window.to))+' CT · '+r.window.hours+' observed hours.':'';
    if($('r8list')) {
      const rows=r.items.map(c=>{const li=make('li','rank-card rising-card');li.append(make('span','rank-number',String(c.rank).padStart(2,'0')));const info=make('div','creator-info');info.append(make('h3','creator-name',c.name));const detail=make('p','rising-detail');const href=H8.profileUrl('x',c.x_handle);if(href){const a=make('a','','X · @'+c.x_handle);a.href=href;a.rel='noopener noreferrer nofollow';a.target='_blank';detail.append(a);}detail.append(make('br'),document.createTextNode((c.ig_included?'X + Instagram':'X only')+' · from '+H8.exact(c.start)+' follows'));info.append(detail);li.append(info);const total=make('div','rank-total');total.append(make('strong','', '+'+c.growth_pct.toFixed(3)+'%'),make('span','','+'+H8.exact(c.growth)+' follows'));li.append(total);return li;});
      $('r8list').replaceChildren(...rows);if(!rows.length)$('r8list').append(make('li','empty-state','No qualifying positive growth can be established from the available snapshots. We do not estimate it.'));
    }
    if($('btlist')) {
      const rows=(d.closest_battles?.items||[]).map(c=>{if(!H8.count(c.gap))throw new Error('Invalid gap');const li=make('li');li.append(make('strong','',c.leader+' / '+c.chaser),make('span','',c.platform+' · '+(c.gap===0?'Tied':H8.exact(c.gap)+' follows apart')));return li;});$('btlist').replaceChildren(...rows);
      if(!rows.length)$('btlist').append(make('li','','No comparable neighbouring ranks available.'));
    }
    if($('mslist')) {
      const rows=(d.milestones?.crossed||[]).slice(-20).map(c=>{const li=make('li');li.append(make('strong','',c.name+' · '+c.platform),make('span','',(c.direction==='up'?'Reached ':'Fell below ')+H8.exact(c.milestone)+' · '+c.date));return li;});
      if(!rows.length)rows.push(make('li','','No round-million crossings in the recorded history.'));
      for(const c of (d.milestones?.closest_next||[]).slice(0,3)){const li=make('li');li.append(make('strong','',c.name+' · '+c.platform),make('span','',H8.exact(c.to_go)+' follows to '+H8.exact(c.next_milestone)+' · observation: '+c.as_of));rows.push(li);}$('mslist').replaceChildren(...rows);
    }
    if(H8.stale(d.latest_snapshot)){$('insights-state').hidden=false;$('insights-state').textContent='These observations are more than three days old. The chart retains their original dates.';}
  }
  async function load(){if(loading)return;loading=true;if($('retry-insights'))$('retry-insights').disabled=true;const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),6000);
    try{const response=await fetch('insights.json',{cache:'no-cache',signal:abort.signal});if(!response.ok)throw new Error('Unavailable');const d=H8.validateInsights(await response.json());if($('insights-state'))$('insights-state').hidden=true;render(d);if($('retry-insights'))$('retry-insights').hidden=true;}
    catch {if($('insights-state')){$('insights-state').hidden=false;$('insights-state').textContent='Historical data is unavailable or could not be validated. No estimated growth is shown.';}if($('r8win'))$('r8win').textContent='Unavailable';if($('r8note'))$('r8note').textContent='Please retry after the data provider recovers.';for(const id of ['r8list','btlist','mslist'])$(id)?.replaceChildren();if($('retry-insights'))$('retry-insights').hidden=false;}
    finally{loading=false;clearTimeout(timer);if($('retry-insights'))$('retry-insights').disabled=false;}}
  $('retry-insights')?.addEventListener('click',load);load();
})();
