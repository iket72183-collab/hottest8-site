# Hottest8 QA checklist

Checked by: Grok Bot (executor agent) on 2026-10-21, America/Chicago. Reviews requested by Riverdale Crew and Dot.
Method key: **executed** = ran in headless Chrome or a live tool; **curl** = live HTTP check against hottest8.com; **code-read** = reviewed source only, not run.

| # | Check | Revision | Method | Result / evidence | Gaps |
|---|---|---|---|---|---|
| 1 | Live files match repo | 09cbb09 and later | curl | md5 of served index.html, style.css, llms.txt, data.*, rankings.json and snapshots matched the committed files after each deploy | — |
| 2 | Styled 404 | d6c19f2 | curl | `/nope-xyz` returns HTTP 404 with the styled 404.html body | — |
| 3 | og:image / large Twitter card | 7aff179 | curl | Tags present; `/og-image.png` returns 200 image/png | Not checked in X's or Facebook's card validators |
| 4 | JSON-LD sameAs | d6c19f2 | curl | X and IG URLs for each Top 8 entry, built from data.js handles | Not run through Google's Rich Results test |
| 5 | Mobile nav (390px) | 09cbb09 | executed (headless screenshot) | 6 links wrap onto 2 lines; no overflow | One viewport only |
| 6 | Ranking toggles (Combined / X / IG) | 09cbb09 | code-read | Native buttons; sort keys correct in app.js | **PENDING: runtime click test** |
| 7 | Profile links | 09cbb09 | curl | All 10 x.com profile URLs return 200; IG sample returns 200 | IG pages need login to view; only reachability checked |
| 8 | Age gate keyboard | 09cbb09 | code-read | Focus starts on Enter button; Tab/Shift+Tab trapped; Enter/Space native; focus moves to the h1 after entry; Esc deliberately does nothing (no bypass) | Not run with a screen reader |
| 9 | Data fallback | this revision (see git log) | executed | Loaded from file:// (data.json fetch fails): the gold "Showing backup data from Oct 21, 2026 (...); live data unavailable." note appeared; prerendered list and as-of line carry their own timestamps | — |
| 10 | Error states | this revision | code-read + executed (#9) | Fetch failure or empty data.json → data.js; no JS → prerendered list | — |
| 11 | Privacy info present | 09cbb09 | curl | `#privacy` section present (EmailOctopus, GoatCounter, localStorage, deletion contact) | — |
| 12 | Ranking copy (universe, timestamps, cadence, follows ≠ people) | 09cbb09 | curl | On site (#method, list note) and in llms.txt | — |
| 13 | Profile identity (X) | 2026-10-21 | executed (x get_users_by_usernames) | All 10 handles resolve, blue-verified, name/bio match the intended creator | — |
| 14 | Profile identity (IG) | 2026-10-21 | curl of creator-linked pages + X bios | Confirmed by creator-linked source: theangelawhite (Linktree), waifuviolet (violetmyers.business), corinnakopf and letrileylive (X bios) | Not independently confirmed (rely on Muse research): miakhalifa, miamalkova, sophieraiin, dangershewrote, kendralust, lenatheplug |
| 15 | Newsletter unsubscribe | adult-site/newsletter-issue-1.html (box) | code-read | Uses EmailOctopus `{{UnsubscribeURL}}` and `{{SenderInfoLine}}` | **PENDING: end-to-end check from an EmailOctopus test send** (no one unsubscribed) |
| 16 | HSTS + Referrer-Policy | live | curl | Only `x-content-type-options: nosniff` is served | **OPEN:** add in Render dashboard → Settings → Headers (the connector can't set headers) |
| 17 | Daily snapshots | daaaaaa | executed | snapshots/2026-10-20.json (backfill) and 2026-10-21.json are live | The daily routine starts 2026-10-22; Instagram counts are carried forward until Muse refreshes them |
