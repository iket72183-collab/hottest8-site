/* Pure ranking rules shared by the browser and Node's built-in test runner. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.H8 = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const count = n => Number.isSafeInteger(n) && n >= 0;
  const handle = (s, platform) => typeof s === 'string' && (platform === 'x' ? /^[A-Za-z0-9_]{1,15}$/ : /^[A-Za-z0-9_.]{1,30}$/).test(s);
  function profileUrl(platform, value) {
    if ((platform !== 'x' && platform !== 'ig') || !handle(value, platform)) return null;
    const host = platform === 'x' ? 'x.com' : 'www.instagram.com';
    return 'https://' + host + '/' + encodeURIComponent(value);
  }
  const date = s => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}(T.*)?$/.test(s) && Number.isFinite(Date.parse(s));
  function validateData(data) {
    if (!data || !date(data.as_of) || !Array.isArray(data.creators) || data.creators.length > 500) throw new Error('Invalid ranking snapshot');
    const seen = new Set();
    for (const c of data.creators) {
      if (!c || typeof c.name !== 'string' || !c.name.trim() || c.name.length > 160 || !handle(c.x_handle, 'x')) throw new Error('Invalid creator identity');
      const id = c.x_handle.toLowerCase();
      if (seen.has(id)) throw new Error('Duplicate creator');
      seen.add(id);
      for (const k of ['x_followers', 'ig_followers']) if (c[k] != null && !count(c[k])) throw new Error('Invalid follower count');
      if (c.ig_followers != null && !handle(c.ig_handle, 'ig')) throw new Error('Invalid Instagram identity');
      if (count(c.x_followers) && count(c.ig_followers) && !count(c.x_followers + c.ig_followers)) throw new Error('Count overflow');
      for (const k of ['x_checked_at', 'ig_checked_at', 'ig_as_of']) if (c[k] != null && !date(c[k])) throw new Error('Invalid observation date');
    }
    return data;
  }
  function validateInsights(d) {
    if(!d||!date(d.latest_snapshot)||!d.rising8||!Array.isArray(d.rising8.items)||d.rising8.items.length>8)throw new Error('Malformed insights');
    const r=d.rising8;
    if(r.items.length&&(!r.window||!date(r.window.from)||!date(r.window.to)||Date.parse(r.window.to)<=Date.parse(r.window.from)))throw new Error('Invalid observation window');
    if(r.window){const hours=(Date.parse(r.window.to)-Date.parse(r.window.from))/3600000;if(!Number.isFinite(r.window.hours)||Math.abs(hours-r.window.hours)>.011||hours<=0||(r.status==='published'&&(hours<165||hours>171)))throw new Error('Inconsistent observation window');}
    for(const row of r.items)if(typeof row.name!=='string'||row.name.length>160||!handle(row.x_handle,'x')||!count(row.rank)||row.rank<1||!count(row.start)||!row.start||!count(row.growth)||row.growth<=0||!Number.isFinite(row.growth_pct)||Math.abs(row.growth_pct-100*row.growth/row.start)>.00011)throw new Error('Invalid growth');
    return d;
  }
  function score(c, mode) {
    const x = count(c.x_followers), ig = count(c.ig_followers) && c.ig_status === 'verified';
    if (mode === 'x') return x ? c.x_followers : null;
    if (mode === 'ig') return ig ? c.ig_followers : null;
    if (mode !== 'combined') throw new Error('Unknown ranking mode');
    return x && ig ? c.x_followers + c.ig_followers : null;
  }
  function rank(creators, mode = 'combined', limit = 8) {
    const rows = creators.map(c => ({creator:c, value:score(c, mode)})).filter(r => r.value != null);
    rows.sort((a,b) => b.value-a.value || a.creator.x_handle.toLowerCase().localeCompare(b.creator.x_handle.toLowerCase(), 'en'));
    let last, position;
    return rows.map((r,i) => { if(r.value !== last) position=i+1; last=r.value; return {...r,rank:position,tied:rows.filter(x=>x.value===r.value).length>1}; }).slice(0,limit);
  }
  function format(n) {
    if (!count(n)) return 'Unknown';
    return n >= 1e6 ? (n/1e6).toFixed(1)+'M' : n >= 1000 ? (n/1000).toFixed(1).replace(/\.0$/,'')+'K' : String(n);
  }
  const exact = n => count(n) ? n.toLocaleString('en-US') : 'Unknown';
  function stale(s, now=Date.now(), days=3) { return !date(s) || now-Date.parse(s) > days*86400000; }
  function approvedAvatar(c, allowlist) {
    if (!c || !handle(c.x_handle, 'x') || typeof c.avatar !== 'string' || !allowlist || allowlist[c.x_handle.toLowerCase()] !== c.avatar) return null;
    if (!/^https:\/\/pbs\.twimg\.com\/profile_images\/[A-Za-z0-9/_-]+\.(?:jpg|png|webp)$/.test(c.avatar)) return null;
    const url = new URL(c.avatar);
    return url.protocol === 'https:' && url.hostname === 'pbs.twimg.com' && !url.username && !url.password && !url.search && !url.hash ? c.avatar : null;
  }
  return {count,handle,profileUrl,date,validateData,validateInsights,score,rank,format,exact,stale,approvedAvatar};
});
