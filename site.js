/* Shared age controls and opt-in third-party loading. No production services in local previews. */
(() => {
  'use strict';
  const gate=document.getElementById('agegate'), shell=document.getElementById('site-shell');
  const production=['hottest8.com','www.hottest8.com'].includes(location.hostname);
  function enter() {
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
  const button=document.getElementById('load-newsletter'), consent=document.getElementById('newsletter-consent'), box=document.getElementById('newsletter-form'), status=document.getElementById('newsletter-status');
  if(!button)return;
  consent.addEventListener('change',()=>{button.disabled=!consent.checked;});
  let started=false;
  button.addEventListener('click',()=>{
    if(started||!consent.checked)return;
    if(!production){status.textContent='Local preview: email services are disabled. No address is collected or sent.';return;}
    started=true;button.disabled=true;consent.disabled=true;status.textContent='Loading the secure signup form…';
    const script=document.createElement('script');script.src='https://eomail5.com/form/a10ae064-cd08-11f1-b060-c974730c96d2.js';script.async=true;script.dataset.form='a10ae064-cd08-11f1-b060-c974730c96d2';
    const fail=()=>{status.textContent='The signup provider did not load. You can reload this page to try again, or contact hello@hottest8.com for help. Nothing has been submitted here.';};
    const observer=new MutationObserver(()=>{if(box.querySelector('input[type="email"]')){status.textContent='Complete the provider’s form below to subscribe.';clearTimeout(timer);observer.disconnect();}});
    const timer=setTimeout(()=>{observer.disconnect();fail();},10000);observer.observe(box,{childList:true,subtree:true});script.addEventListener('error',()=>{clearTimeout(timer);observer.disconnect();fail();},{once:true});box.append(script);
  });
})();
