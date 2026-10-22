#!/usr/bin/env python3
"""Build insights.json (Rising 8 from the emerging pool in rising_pool.json + snapshots/emerging/, milestones, closest battles) from snapshots/*.json
and merge it into rankings.json. Run from the repo root after adding a daily snapshot.
Never estimates: a creator needs two real data points; Instagram growth counts only
when the Instagram figure was actually re-checked (ig_as_of differs)."""
import json, glob, os, datetime as dt
from zoneinfo import ZoneInfo
CT = ZoneInfo("America/Chicago")
snaps = sorted((json.load(open(p)) for p in glob.glob("snapshots/????-??-??.json")), key=lambda s: s["date"])
latest = snaps[-1]
def ts(s): return dt.datetime.fromisoformat(s["fetched_at"])
def lbl(s): return ts(s).astimezone(CT).strftime("%b %-d, %-I:%M %p CT")
# baseline: snapshot closest to 7 days before latest, else the earliest
target = ts(latest) - dt.timedelta(days=7)
older = [s for s in snaps[:-1] if ts(s) <= target]
base = older[-1] if older else (snaps[0] if len(snaps) > 1 else None)
full_week = bool(older)
out = {"generated_from": [s["date"] for s in snaps], "latest_snapshot": latest["date"]}
by = lambda s: {c["x_handle"].lower(): c for c in s["creators"]}
L = by(latest)
def combined(c): return c["x_followers"] + c["ig_followers"]
def has_ig(c): return c.get("ig_followers") is not None
# ---- Rising 8 (emerging talent only)
# Pool: rising_pool.json; data: snapshots/emerging/YYYY-MM-DD.json (X counts; Instagram optional).
# Rules: exclude current Top 8 and anyone over 1,000,000 combined followers; floor 10,000
# followers at window start; needs >= 2 snapshots; ranked by % growth (absolute gain shown).
POOL = json.load(open("rising_pool.json"))
RULES = POOL["rules"]
esnaps = sorted((json.load(open(p)) for p in glob.glob("snapshots/emerging/????-??-??.json")), key=lambda s: s["date"])
top8 = {t.get("x_handle", "").lower() for t in json.load(open("rankings.json")).get("top8", [])}
pool_h = {c["x_handle"].lower() for c in POOL["creators"]}
rows = []; excluded = []
if len(esnaps) >= RULES["min_snapshots"]:
    elatest = esnaps[-1]
    etarget = ts(elatest) - dt.timedelta(days=7)
    eolder = [s for s in esnaps[:-1] if ts(s) <= etarget]
    base = eolder[-1] if eolder else esnaps[0]; full_week = bool(eolder)
    B = by(base); EL = by(elatest); hours = (ts(elatest) - ts(base)).total_seconds() / 3600
    for h, c in EL.items():
        b = B.get(h)
        if h not in pool_h or not b or b.get("x_followers") is None or c.get("x_followers") is None: continue
        ig_fresh = has_ig(c) and has_ig(b) and c.get("ig_as_of") != b.get("ig_as_of") and not c.get("ig_carried_forward")
        comb_now = c["x_followers"] + (c.get("ig_followers") or 0)
        start = b["x_followers"] + (b["ig_followers"] if ig_fresh else 0)
        why = ("in Top 8" if h in top8 else "over 1M combined" if comb_now > RULES["max_combined_followers"]
               else "under 10k floor" if start < RULES["min_followers"] else None)
        if why: excluded.append({"name": c["name"], "x_handle": c["x_handle"], "reason": why}); continue
        dx = c["x_followers"] - b["x_followers"]
        dig = (c["ig_followers"] - b["ig_followers"]) if ig_fresh else None
        d = dx + (dig or 0)
        rows.append({"name": c["name"], "x_handle": c["x_handle"], "start": start, "growth": d,
                     "growth_pct": round(100 * d / start, 4), "x_growth": dx, "ig_growth": dig, "ig_included": ig_fresh})
    rows.sort(key=lambda r: (-r["growth_pct"], -r["growth"]))
    for i, r in enumerate(rows): r["rank"] = i + 1
    out["rising8"] = {
        "status": "published" if full_week else "partial_window",
        "pool": "emerging creators (10k to 1M combined followers, not in the Top 8)", "pool_size": len(pool_h),
        "window": {"from": base["fetched_at"], "to": elatest["fetched_at"], "hours": round(hours, 1),
                   "label": ("7-day growth" if full_week else f"since {lbl(base)} ({round(hours)} hrs)")},
        "metric": "ranked by % follower growth; absolute gain shown. X only unless Instagram was re-checked in the window (Instagram growth unknown, not zero).",
        "items": [x for x in rows if x["growth"] > 0][:8], "excluded": excluded, "all": rows}
else:
    out["rising8"] = {"status": "not_published", "items": [], "pool_size": len(pool_h),
                      "note": "Rising 8 = fastest-growing up-and-coming creators by % growth; needs two dated snapshots of the emerging pool."}
# ---- Milestones: crossed a round million between consecutive snapshots
ms = []
for a, b in zip(snaps, snaps[1:]):
    A = by(a)
    for h, c in by(b).items():
        p = A.get(h)
        if not p: continue
        for plat, k in (("X", "x_followers"), ("Instagram", "ig_followers")):
            if plat == "Instagram" and c.get("ig_carried_forward"): continue
            if p.get(k) is None or c.get(k) is None: continue
            lo, hi = sorted((p[k], c[k]))
            for m in range(lo // 1_000_000 + 1, hi // 1_000_000 + 1):
                ms.append({"date": b["date"], "name": c["name"], "platform": plat, "milestone": m * 1_000_000,
                           "direction": "up" if c[k] > p[k] else "down", "from": p[k], "to": c[k]})
nxt = []
for c in L.values():
    for plat, k in (("X", "x_followers"), ("Instagram", "ig_followers")):
        v = c.get(k)
        if v is None: continue
        m = (v // 1_000_000 + 1) * 1_000_000
        nxt.append({"name": c["name"], "platform": plat, "next_milestone": m, "to_go": m - v, "current": v, "as_of": c.get("ig_as_of") if plat == "Instagram" else latest["date"]})
nxt.sort(key=lambda r: r["to_go"])
out["milestones"] = {"crossed": ms, "closest_next": nxt[:5],
                     "note": "Round-million crossings between consecutive dated snapshots. Instagram counts carried forward are not treated as new data."}
# ---- Closest battles: smallest gaps between adjacent ranks
def gaps(keyf, plat, pool=None):
    s = sorted(pool if pool is not None else L.values(), key=keyf, reverse=True); g = []
    for i in range(len(s) - 1):
        g.append({"platform": plat, "ranks": [i + 1, i + 2], "leader": s[i]["name"], "chaser": s[i + 1]["name"],
                  "gap": keyf(s[i]) - keyf(s[i + 1]), "leader_count": keyf(s[i]), "chaser_count": keyf(s[i + 1])})
    return g
withig = [c for c in L.values() if has_ig(c)]  # unverified Instagram: X-only battles
allg = gaps(combined, "Combined", withig) + gaps(lambda c: c["x_followers"], "X") + gaps(lambda c: c["ig_followers"], "Instagram", withig)
allg.sort(key=lambda g: g["gap"])
out["closest_battles"] = {"items": allg[:5], "note": "Smallest follower gaps between adjacent ranks, by combined total or a single platform (labeled)."}
json.dump(out, open("insights.json", "w"), indent=2)
r = json.load(open("rankings.json"))
r["rising8"] = {k: v for k, v in out["rising8"].items() if k != "all"}
r["milestones"] = out["milestones"]; r["closest_battles"] = out["closest_battles"]
r["insights_url"] = "https://hottest8.com/insights.json"
r["snapshots"] = [f"https://hottest8.com/snapshots/{s['date']}.json" for s in snaps]
json.dump(r, open("rankings.json", "w"), indent=2)
print(json.dumps({"rising8": [(x["name"], x["growth"], x["growth_pct"]) for x in out["rising8"]["items"]], "label": out["rising8"].get("window"), "ms": ms, "next": nxt[:3], "battles": [(g["platform"], g["leader"], g["chaser"], g["gap"]) for g in allg[:5]]}, indent=1))
