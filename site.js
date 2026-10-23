/* Shared age controls and newsletter loading right after age confirmation. No production services in local previews. */
(() => {
  'use strict';
  const gate=document.getElementById('agegate'), shell=document.getElementById('site-shell');
  let ageConfirmed=!gate;
  const production=['hottest8.com','www.hottest8.com'].includes(location.hostname);
  function enter() {
    ageConfirmed=true;
    try {localStorage.setItem('h8age','1');}catch {}
    gate?.remove();shell?.removeAttribute('inert');shell?.removeAttribute('aria-hidden');
    document.body.classList.remove('age-locked');
    const heading=document.querySelector('main h1');heading?.focus();
    if(production&&!document.querySelector('[data-goatcounter]')) {const s=document.createElement('script');s.async=true;s.dataset.goatcounter='https://hottest8.goatcounter.com/count';s.src='https://gc.zgo.at/count.js';document.body.append(s);}
    window.dispatchEvent(new Event('h8:entered'));
  }
  let accepted=false;try {accepted=localStorage.getItem('h8age')==='1';}catch {}
  if(accepted)enter();else if(gate){document.body.classList.add('age-locked');document.getElementById('agein').focus();}
  document.getElementById('agein')?.addEventListener('click',enter);
  gate?.addEventListener('keydown',e=>{if(e.key==='Tab'){const buttons=[...gate.querySelectorAll('button,a')];e.preventDefault();const i=buttons.indexOf(document.activeElement);buttons[(i+(e.shiftKey?-1:1)+buttons.length)%buttons.length].focus();}if(e.key==='Escape')e.preventDefault();});
  document.getElementById('copyprompt')?.addEventListener('click',async e=>{try{await navigator.clipboard.writeText(document.getElementById('aiprompt').textContent);e.target.textContent='Copied';}catch{e.target.textContent='Select and copy the text';}});
  // Preserve main's delegated submission event: an attempt, not provider acceptance.
  if(location.pathname.endsWith('/verify.html')) {
    document.addEventListener('submit',function(e){var f=e.target;if(!f||!f.closest||!f.closest('.eoform'))return;
      function c(){if(window.goatcounter&&window.goatcounter.count){window.goatcounter.count({path:'fakecheck-signup',title:'Fake Check signup',event:true});return true}}
      if(!c())setTimeout(c,500)},true);window.h8fcTrack=1;
  }
  const box=document.querySelector('#newsletter .eoform'), fallback=document.getElementById('nlfb');
  const loadButton=document.querySelector('[data-load-newsletter]');
  if(!box)return;
  if(!production){box.textContent='Local preview: email services are disabled. No address is collected or sent.';if(loadButton)loadButton.disabled=true;return;}
  const id='a10ae064-cd08-11f1-b060-c974730c96d2';
  const rendered=()=>!!box.querySelector('form input[type="email"]');
  let state='idle';
  function failed(){state='failed';if(loadButton){loadButton.hidden=false;loadButton.disabled=false;loadButton.textContent='Retry loading signup form';}if(fallback)fallback.hidden=false;}
  function insert(){
    if(!ageConfirmed||!production||state==='loading'||state==='loaded')return;
    box.replaceChildren();
    state='loading';if(fallback)fallback.hidden=true;
    if(loadButton){loadButton.disabled=true;loadButton.textContent='Loading signup form…';}
    const script=document.createElement('script');script.async=true;script.src='https://eomail5.com/form/'+id+'.js';script.setAttribute('data-form',id);
    script.addEventListener('error',failed,{once:true});
    script.addEventListener('load',()=>{state='loaded';setTimeout(()=>{if(rendered()){if(loadButton)loadButton.hidden=true;}else failed();},7000);},{once:true});
    box.append(script);
  }
  loadButton?.addEventListener('click',insert);
  if(ageConfirmed)insert();else window.addEventListener('h8:entered',insert,{once:true});
})();
