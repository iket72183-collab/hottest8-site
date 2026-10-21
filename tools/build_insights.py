#!/usr/bin/env python3
"""Build insights.json (Rising 8, milestones, closest battles) from snapshots/*.json
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
# ---- Rising 8
rows = []
if base:
    B = by(base); hours = (ts(latest) - ts(base)).total_seconds() / 3600
    for h, c in L.items():
        b = B.get(h)
        if not b or b.get("x_followers") is None or c.get("x_followers") is None: continue
        dx = c["x_followers"] - b["x_followers"]
        ig_fresh = c.get("ig_as_of") != b.get("ig_as_of") and not c.get("ig_carried_forward")
        dig = (c["ig_followers"] - b["ig_followers"]) if ig_fresh else None
        start = b["x_followers"] + (b["ig_followers"] if ig_fresh else 0)
        d = dx + (dig or 0)
        rows.append({"name": c["name"], "x_handle": c["x_handle"], "growth": d, "growth_pct": round(100 * d / start, 4),
                     "x_growth": dx, "ig_growth": dig, "ig_included": ig_fresh})
    rows.sort(key=lambda r: (-r["growth_pct"], -r["growth"]))
    for i, r in enumerate(rows): r["rank"] = i + 1
    any_ig = any(r["ig_included"] for r in rows)
    out["rising8"] = {
        "status": "published" if full_week else "partial_window",
        "window": {"from": base["fetched_at"], "to": latest["fetched_at"], "hours": round(hours, 1),
                   "label": ("7-day growth" if full_week else f"since {lbl(base)} ({round(hours)} hrs)")},
        "metric": "ranked by % growth; absolute growth shown. " + ("Combined X + Instagram." if any_ig else "X only: Instagram counts were not re-checked in this window, so Instagram growth is unknown, not zero."),
        "items": [x for x in rows if x["growth"] > 0][:8], "all": rows}
else:
    out["rising8"] = {"status": "not_published", "items": [], "note": "Needs two dated snapshots."}
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
        v = c[k]; m = (v // 1_000_000 + 1) * 1_000_000
        nxt.append({"name": c["name"], "platform": plat, "next_milestone": m, "to_go": m - v, "current": v, "as_of": c.get("ig_as_of") if plat == "Instagram" else latest["date"]})
nxt.sort(key=lambda r: r["to_go"])
out["milestones"] = {"crossed": ms, "closest_next": nxt[:5],
                     "note": "Round-million crossings between consecutive dated snapshots. Instagram counts carried forward are not treated as new data."}
# ---- Closest battles: smallest gaps between adjacent ranks
def gaps(keyf, plat):
    s = sorted(L.values(), key=keyf, reverse=True); g = []
    for i in range(len(s) - 1):
        g.append({"platform": plat, "ranks": [i + 1, i + 2], "leader": s[i]["name"], "chaser": s[i + 1]["name"],
                  "gap": keyf(s[i]) - keyf(s[i + 1]), "leader_count": keyf(s[i]), "chaser_count": keyf(s[i + 1])})
    return g
allg = gaps(combined, "Combined") + gaps(lambda c: c["x_followers"], "X") + gaps(lambda c: c["ig_followers"], "Instagram")
allg.sort(key=lambda g: g["gap"])
out["closest_battles"] = {"items": allg[:5], "note": "Smallest follower gaps between adjacent ranks, by combined total or a single platform (labeled)."}
json.dump(out, open("insights.json", "w"), indent=2)
r = json.load(open("rankings.json"))
r["rising8"] = out["rising8"] | {"all": None}; r["rising8"].pop("all")
r["milestones"] = out["milestones"]; r["closest_battles"] = out["closest_battles"]
r["insights_url"] = "https://hottest8.com/insights.json"
r["snapshots"] = [f"https://hottest8.com/snapshots/{s['date']}.json" for s in snaps]
json.dump(r, open("rankings.json", "w"), indent=2)
print(json.dumps({"rising8": [(x["name"], x["growth"], x["growth_pct"]) for x in out["rising8"]["items"]], "label": out["rising8"].get("window"), "ms": ms, "next": nxt[:3], "battles": [(g["platform"], g["leader"], g["chaser"], g["gap"]) for g in allg[:5]]}, indent=1))
