const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require.resolve('../site.js'),'utf8');
function page({host='hottest8.com',path='/',form=false}={}) {
  const timers=[],scripts=[],events={},fallback={hidden:true};let present=form;
  const box={textContent:'',querySelector:()=>present?{}:null,append:s=>scripts.push(s)};
  const document={body:{classList:{remove(){}}},getElementById:id=>id==='nlfb'?fallback:null,querySelector:q=>q==='#newsletter .eoform'?box:null,addEventListener:(type,fn)=>events[type]=fn,createElement:()=>({setAttribute(k,v){this[k]=v}})};
  const window={};const location={hostname:host,pathname:path,reload(){}};
  vm.runInNewContext(source,{document,window,location,localStorage:{getItem:()=>null},setTimeout:(fn,ms)=>{timers.push({fn,ms});},Date});
  return {timers,scripts,events,fallback,box,window,render:()=>present=true};
}
test('production signup loads immediately without a checkbox or click',()=>{
  const p=page();assert.equal(p.scripts.length,1);assert.equal(p.scripts[0].src,'https://eomail5.com/form/a10ae064-cd08-11f1-b060-c974730c96d2.js');assert.equal(p.timers[0].ms,6000);
});
test('a rendered form suppresses retry and fallback',()=>{const p=page();p.render();p.timers[0].fn();assert.equal(p.scripts.length,1);assert.equal(p.timers.length,1);assert.equal(p.fallback.hidden,true);});
test('blocked form retries once after 6s then shows fallback after 7s',()=>{const p=page();p.timers[0].fn();assert.equal(p.scripts.length,2);assert.match(p.scripts[1].src,/\.js\?r=\d+$/);assert.equal(p.timers[1].ms,7000);assert.equal(p.fallback.hidden,true);p.timers[1].fn();assert.equal(p.fallback.hidden,false);assert.equal(p.timers.length,2);});
test('successful retry suppresses fallback',()=>{const p=page();p.timers[0].fn();p.render();p.timers[1].fn();assert.equal(p.fallback.hidden,true);});
test('localhost never loads production email',()=>{const p=page({host:'127.0.0.1'});assert.equal(p.scripts.length,0);assert.equal(p.timers.length,0);assert.match(p.box.textContent,/disabled/);});
test('Fake Check restores exact delegated submission event payload',()=>{const p=page({path:'/verify.html'}),sent=[];p.window.goatcounter={count:e=>sent.push(JSON.parse(JSON.stringify(e)))};assert.equal(p.window.h8fcTrack,1);p.events.submit({target:{closest:q=>q==='.eoform'}});assert.deepEqual(sent,[{path:'fakecheck-signup',title:'Fake Check signup',event:true}]);});
test('Fake Check retries the event once after 500ms when analytics is late',()=>{const p=page({path:'/verify.html'}),sent=[];p.events.submit({target:{closest:()=>true}});const t=p.timers.find(x=>x.ms===500);assert.ok(t);p.window.goatcounter={count:e=>sent.push(e)};t.fn();assert.equal(sent.length,1);});
test('unrelated forms and other pages do not emit Fake Check event',()=>{assert.equal(page().events.submit,undefined);const p=page({path:'/verify.html'});p.events.submit({target:{closest:()=>false}});assert.equal(p.timers.filter(x=>x.ms===500).length,0);});
