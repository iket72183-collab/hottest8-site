const {test}=require('node:test');const assert=require('node:assert/strict');const H=require('../core.js');
const creator=(handle,x,ig)=>({name:'Fixture '+handle,x_handle:handle,x_followers:x,ig_handle:ig==null?null:handle,ig_followers:ig,ig_status:ig==null?'pending_verification':'verified'});
const data=creators=>({as_of:'2026-10-23',creators});
test('combined follows sum without claiming uniqueness',()=>assert.equal(H.score(creator('a',100,200),'combined'),300));
test('missing is not zero and zero is a valid observation',()=>{assert.equal(H.score(creator('a',100,null),'combined'),null);assert.equal(H.score(creator('b',0,0),'combined'),0);assert.equal(H.score(creator('a',null,3),'x'),null);});
test('separate platform membership',()=>{const c=[creator('a',5,null),creator('b',2,100)];assert.equal(H.rank(c,'x')[0].creator.x_handle,'a');assert.equal(H.rank(c,'ig')[0].creator.x_handle,'b');assert.equal(H.rank(c)[0].creator.x_handle,'b');});
test('competition ties and deterministic boundary order',()=>{const c=[creator('z',10,0),creator('B',10,0),creator('c',9,0)];assert.deepEqual(H.rank(c).map(r=>r.rank),[1,1,3]);assert.equal(H.rank(c)[0].creator.x_handle,'B');assert.equal(H.rank(c)[0].tied,true);assert.equal(H.rank(Array.from({length:10},(_,i)=>creator('a'+i,10,0))).length,8);});
test('empty snapshot is a legitimate empty state',()=>assert.equal(H.validateData(data([])).creators.length,0));
for(const value of [-1,NaN,Infinity,1.5,'100',true,Number.MAX_SAFE_INTEGER+1])test('reject bad count '+String(value),()=>assert.throws(()=>H.validateData(data([creator('a',value,0)]))));
test('reject sum overflow',()=>assert.throws(()=>H.validateData(data([creator('a',Number.MAX_SAFE_INTEGER,1)]))));
test('reject duplicate identity case-insensitively',()=>assert.throws(()=>H.validateData(data([creator('a',1,1),creator('A',2,2)]))));
test('reject URL/attribute injection in handles',()=>{for(const h of ['a/../../b','a" onmouseover="x','javascript:foo','a?token=x'])assert.throws(()=>H.validateData(data([creator(h,1,1)])));});
test('profile links require a known platform and a valid handle',()=>{
 assert.equal(H.profileUrl('x','Fixture_1'),'https://x.com/Fixture_1');
 assert.equal(H.profileUrl('ig','fixture.1'),'https://www.instagram.com/fixture.1');
 for(const [platform,value] of [['x','javascript:alert(1)'],['x','a" onclick="x'],['ig','a/b'],['ig','a?next=evil'],['other','fixture']])assert.equal(H.profileUrl(platform,value),null);
});
test('name text can contain markup without becoming a URL',()=>{const c=creator('fixture',1,1);c.name='<img src=x onerror=alert(1)>';assert.equal(H.validateData(data([c])).creators[0].name,c.name);});
test('unknown avatars never load, including changed URLs',()=>{const c=creator('a',1,1);c.avatar='https://pbs.twimg.com/profile_images/1/a.jpg';assert.equal(H.approvedAvatar(c,{a:c.avatar}),c.avatar);assert.equal(H.approvedAvatar(c,{}),null);c.avatar='javascript:alert(1)';assert.equal(H.approvedAvatar(c,{a:c.avatar}),null);});
test('avatar URLs reject changed scheme, host, credentials, controls and attributes even if allowlisted',()=>{
 const c=creator('a',1,1);
 for(const avatar of ['http://pbs.twimg.com/profile_images/1/a.jpg','https://pbs.twimg.com.evil.test/profile_images/1/a.jpg','https://user@pbs.twimg.com/profile_images/1/a.jpg','https://pbs.twimg.com/profile_images/1/a.jpg?x=1','https://pbs.twimg.com/profile_images/1/a.jpg#part','https://pbs.twimg.com/profile_images/1/a.jpg\n','https://pbs.twimg.com/profile_images/1/a.jpg" onerror="x']){
   c.avatar=avatar;assert.equal(H.approvedAvatar(c,{a:avatar}),null,avatar);
 }
});
test('freshness uses observation time',()=>{assert.equal(H.stale('2026-10-20',Date.parse('2026-10-24')),true);assert.equal(H.stale('2026-10-23',Date.parse('2026-10-24')),false);assert.equal(H.stale('bad'),true);});
test('explicit mode validation',()=>assert.throws(()=>H.rank([creator('a',1,1)],'bad')));
test('format preserves exact count separately',()=>{assert.equal(H.format(35170639),'35.2M');assert.equal(H.exact(35170639),'35,170,639');assert.equal(H.format(null),'Unknown');});

test('insights reject invented weekly windows and inconsistent percentages',()=>{
 const fixture={latest_snapshot:'2026-10-23',rising8:{status:'partial_window',window:{from:'2026-10-22T12:00:00Z',to:'2026-10-23T12:00:00Z',hours:24},items:[{name:'Synthetic',x_handle:'fixture',rank:1,start:10000,growth:100,growth_pct:1}]}};
 assert.equal(H.validateInsights(fixture),fixture);
 for(const mutate of [d=>d.rising8.status='published',d=>d.rising8.window.hours=168,d=>d.rising8.items[0].growth_pct=99]){const d=structuredClone(fixture);mutate(d);assert.throws(()=>H.validateInsights(d));}
});

test('an unknown or rejected Instagram status is not verified',()=>{for(const status of [undefined,'rejected','unknown']){const c={...creator('fixture',2,3),ig_status:status};assert.equal(H.score(c,'combined'),null);assert.equal(H.score(c,'ig'),null);}});
