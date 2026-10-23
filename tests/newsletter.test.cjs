const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require.resolve('../site.js'),'utf8');

function page({host='hottest8.com',path='/',form=false,ageGate=false,accepted=false}={}) {
  const timers=[],events={},fallback={hidden:true},providerScripts=[],otherScripts=[];
  let present=form,gateNode=ageGate?{remove(){gateNode=null},addEventListener(){}}:null;
  const button={hidden:true,disabled:false,textContent:'Retry loading signup form',addEventListener:(type,fn)=>events['load:'+type]=fn};
  const box={textContent:'',children:[],cleared:0,querySelector:()=>present?{}:null,append(s){providerScripts.push(s);this.children.push(s)},replaceChildren(){this.children=[];this.cleared++}};
  const document={
    body:{classList:{add(){},remove(){}},append:s=>otherScripts.push(s)},
    getElementById:id=>id==='agegate'?gateNode:id==='agein'?{focus(){},addEventListener:(type,fn)=>events['age:'+type]=fn}:id==='site-shell'?{removeAttribute(){}}:id==='nlfb'?fallback:null,
    querySelector:q=>q==='#newsletter .eoform'?box:q==='[data-load-newsletter]'?button:q==='main h1'?{focus(){}}:null,
    addEventListener:(type,fn)=>events[type]=fn,
    createElement:()=>({dataset:{},setAttribute(k,v){this[k]=v},addEventListener(type,fn){this['on'+type]=fn}})
  };
  const window={goatcounter:null,addEventListener:(type,fn)=>events['window:'+type]=fn,dispatchEvent:e=>{events['window:'+e.type]?.(e)}};
  const location={hostname:host,pathname:path,reload(){}};
  vm.runInNewContext(source,{document,window,location,localStorage:{getItem:()=>accepted? '1':null,setItem(){}},setTimeout:(fn,ms)=>{timers.push({fn,ms});return timers.length},clearTimeout(){},Date,Event});
  return {timers,events,fallback,providerScripts,otherScripts,button,box,window,render:()=>present=true};
}

test('no provider request before age confirmation',()=>{
  const p=page({ageGate:true});assert.equal(p.providerScripts.length,0);assert.equal(p.button.hidden,true);assert.equal(p.fallback.hidden,true);
});
test('form loads automatically right after age confirmation, once',()=>{
  const p=page({ageGate:true});p.events['age:click']();assert.equal(p.providerScripts.length,1);
  p.events['load:click']();assert.equal(p.providerScripts.length,1);
});
test('already-confirmed age loads the form immediately without a click',()=>{
  const p=page({accepted:true});assert.equal(p.providerScripts.length,1);assert.equal(p.button.hidden,true);
});
test('rendered form keeps retry hidden and suppresses failure fallback',()=>{
  const p=page({accepted:true});p.render();p.providerScripts[0].onload();
  assert.equal(p.timers[0].ms,7000);p.timers[0].fn();assert.equal(p.button.hidden,true);assert.equal(p.fallback.hidden,true);
});
test('provider failure offers retry and mailto; retry replaces the prior embed',()=>{
  const p=page({accepted:true});p.providerScripts[0].onerror();
  assert.equal(p.providerScripts.length,1);assert.equal(p.timers.length,0);assert.equal(p.button.hidden,false);assert.equal(p.button.disabled,false);assert.equal(p.button.textContent,'Retry loading signup form');assert.equal(p.fallback.hidden,false);
  p.events['load:click']();assert.equal(p.providerScripts.length,2);assert.equal(p.box.children.length,1);assert.equal(p.box.cleared,2);assert.equal(p.fallback.hidden,true);
  p.events['load:click']();assert.equal(p.providerScripts.length,2);
});
test('non-rendering embed after load offers retry without duplicates',()=>{
  const p=page({accepted:true});p.providerScripts[0].onload();p.timers[0].fn();assert.equal(p.fallback.hidden,false);
  p.events['load:click']();assert.equal(p.box.children.length,1);
});
test('localhost never loads the production email provider',()=>{
  const p=page({host:'127.0.0.1'});assert.equal(p.providerScripts.length,0);assert.equal(p.timers.length,0);assert.match(p.box.textContent,/disabled/);assert.equal(p.button.disabled,true);
});
test('Fake Check submission-attempt event remains delegated and exact',()=>{const p=page({path:'/verify.html',accepted:true}),sent=[];p.window.goatcounter={count:e=>sent.push(JSON.parse(JSON.stringify(e)))};assert.equal(p.window.h8fcTrack,1);p.events.submit({target:{closest:q=>q==='.eoform'}});assert.deepEqual(sent,[{path:'fakecheck-signup',title:'Fake Check signup',event:true}]);assert.equal(p.providerScripts.length,1);});
test('Fake Check retries analytics event once when analytics is late',()=>{const p=page({path:'/verify.html'}),sent=[];p.events.submit({target:{closest:()=>true}});const t=p.timers.find(x=>x.ms===500);assert.ok(t);p.window.goatcounter={count:e=>sent.push(e)};t.fn();assert.equal(sent.length,1);});
test('unrelated forms and other pages do not emit Fake Check event',()=>{assert.equal(page().events.submit,undefined);const p=page({path:'/verify.html'});p.events.submit({target:{closest:()=>false}});assert.equal(p.timers.filter(x=>x.ms===500).length,0);});
