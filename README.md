# Hottest8

Strictly SFW, adults-only rankings for a tracked creator set. Grok Bot is the lead maintainer. This branch proposes a black/gold editorial redesign and validated offline data builds; it does **not** deploy them.

## Run locally

Python 3.9+ builds and previews without installing anything. Node 18+ runs JavaScript regression tests. The only npm dependency is optional development-only `axe-core@4.14.0` for browser accessibility audits.

```sh
python3 tools/sync_data.py --check
python3 tools/build_site.py
python3 tools/preview.py --port 8768
# Open http://127.0.0.1:8768/
node --test tests/*.test.cjs
python3 -m unittest discover -s tests -v
# Optional browser audit dependency:
npm ci --ignore-scripts
npm audit
```

Serve **dist/**, never the repository root. HTML source templates contain build markers. The allowlisted artifact excludes tools, tests, docs and dependencies. Local previews disable production newsletter and analytics scripts. Existing allowlisted avatar URLs can still load after age confirmation; block external browser requests when testing complete offline behavior.

## Maintainer map

- `core.js`: validated counts, independent platform rankings, competition ties and historical payload validation.
- `app.js`: safe DOM ranking cards, platform dates, fallback and retry.
- `site.js`: shared age controls and immediate newsletter loading, one bounded retry, and the existing Fake Check event.
- `insights.js`: historical chart display and failure states.
- `style.css`: shared black/gold design, mobile layouts, focus and reduced-motion rules. No remote fonts.
- `tools/sync_data.py`: regenerate `data.json` and `data.js` from the latest dated snapshot; `--check` validates without writing. Preserves reviewed editorial fields and rejects identity conflicts.
- `tools/build_site.py`: deterministic, offline `dist/` build; SSR Combined ranking and JSON-LD; validates current data against the latest snapshot.
- `tools/build_insights.py`: pure historical calculations. Its standalone CLI refreshes root insights JSON for compatibility; the site build always recomputes artifacts independently.
- `data.json`, `snapshots/`, `rising_pool.json`: maintainer-supplied inputs. Root `data.js` is generated with `data.json` by the sync command. Root `insights.json` and `rankings.json` remain legacy exports for the existing workflow; **dist versions are generated**. Never hand-edit dist.
- `approved-avatars.json`: exact baseline avatar URL allowlist. Adding/replacing imagery requires SFW and permission review; URL membership alone is not proof of rights.

## Daily data handoff to Grok Bot

The maintainer reports an external daily routine around **07:00 America/Chicago** that commits to `main`. No fetch credentials, API implementation, scheduler or production database exists in this repository. This audit did not run that routine or verify its account permissions.

1. Fetch current `main` before starting a data update or integrating this branch. Preserve newer snapshots; do not force-push main.
2. Append a real timezone-aware snapshot, then run the commands below to regenerate both current exports and commit them together; keep original per-platform observation times. Record stable platform IDs when available, verification status, changed identities and carried-forward flags. Do not advance an Instagram date just because X refreshed. Treat a reused handle as a new identity requiring review.
3. Update the emerging pool only with verified eligibility evidence. Append real emerging snapshots. Unknown IG cannot establish the combined eligibility cap. Never replace missing data with zero or sample growth.
4. Run tests and `python3 tools/build_site.py`. Mismatched source counts/membership fail the build. Review changed rankings and each actual Rising window; a sparse interval is not automatically a week.
5. Review locally. Future production integration requires Isaac's approval and the coordinated deployment changes below.

Daily-job sequence (no API calls or automatic commit/push in the script):

```sh
# After the daily collector has written snapshots/YYYY-MM-DD.json:
python3 tools/sync_data.py
python3 tools/sync_data.py --check
npm test
python3 tools/build_site.py
# Review changes, then stage the actual dated snapshot and BOTH exports together:
git add snapshots/YYYY-MM-DD.json data.json data.js
# Include an emerging snapshot/pool change only when the collector actually produced one.
# Commit and push under the existing approved daily-job workflow.
```

The date in that git command is a placeholder for the actual new file. The sync validates all content before writing, atomically replaces each export, carries observation metadata from the snapshot (never the previous export), preserves approved avatar/retirement fields, and retains Muse research credits. It does not create snapshots or infer missing IG counts. A failed sync/build must stop the daily job before commit. The pair is committed together by the job; filesystem replacements are individually atomic, not a two-file transaction.

Combined follows are summed platform counts, not unique people. Ties use competition ranks, then alphabetical X handle for deterministic eight-slot display. IG participates in growth only when comparable independently rechecked observations exist. Seven-day labels require 165–171 elapsed hours; all other windows show their actual length. Legacy snapshots without stable IDs have weaker identity evidence.

## Newsletter and privacy

On the homepage and Fake Check page, the EmailOctopus form loads automatically right after 18+ age confirmation (or on page load when age was already confirmed). Before age confirmation, the site does not insert the provider script or create a newsletter-provider request. A failed or non-rendering embed shows a retry button (which clears the previous embed before reinserting) and a mailto fallback. Local previews disable production scripts; test scenarios substitute local mocks.

Fake Check retains its early-access signup and main's exact `fakecheck-signup` payload (`title: 'Fake Check signup', event: true`), delegated from `.eoform` submissions with a single 500 ms retry if GoatCounter is late. **This event measures an attempted submission, not accepted subscription or delivery.** It carries no email/name. The existing GoatCounter is the only analytics integration; no additional trackers were added.

The weekly newsletter remains Top 8 + Industry Dispatch; the restored Fake Check signup also promises launch updates. The owner must ensure the existing EmailOctopus form/list's consent records, segmentation and permitted email purposes support that promise. Account settings, double opt-in, retention, suppression, CAPTCHA/rate limits and end-to-end unsubscribe delivery are unverified. No production signup or email was sent. The restored test-scan copy is maintainer-provided wording from main, not a result reproduced by this change.

## Release and rollback — approval required

Read-only Render verification on 2026-10-23 confirmed service `srv-dbc31ujrjlhs73al9icg`, repo `iket72183-collab/hottest8-site`, branch `main`, automatic deploy on commit, build `python3 tools/build_site.py`, publish `dist`, and **PR previews disabled**. These settings already match the allowlisted build; no hosting setting change is required for this patch. Opening a PR does not enable previews. `render.yaml` is a proposed reference; editing it alone does not establish that dashboard settings will change.

**Do not merge this branch without Isaac’s release approval.** The live service already reports build command `python3 tools/build_site.py` and publish directory `dist`; verify both remain unchanged immediately before release. Recheck main first because the daily job may have moved it. Mirror the exact dashboard settings below; stage the real provider form before enforcing CSP. No account setting was changed during this task.

### Exact Render dashboard settings for the owner

`render.yaml` is **not Blueprint-synced**. Mirror these in the existing static service's dashboard only as part of the owner-approved release; no Render access or changes occurred in this follow-up.

- Build command: `python3 tools/build_site.py`
- Publish directory: `dist`
- Production branch: `main` (unchanged)
- PR previews: disabled (unchanged)
- Rewrite: source `/*`, destination `/404.html`, action **Rewrite** (retained from main). Existing files take precedence. Verify the HTTP status of an unknown path after release; this local server's real 404 is not proof of Render rewrite status.

Headers, each with path `/*`:

| Header | Value |
|---|---|
| Strict-Transport-Security | `max-age=31536000; includeSubDomains` |
| X-Content-Type-Options | `nosniff` |
| Referrer-Policy | `strict-origin-when-cross-origin` |
| X-Frame-Options | `DENY` |
| Permissions-Policy | `camera=(), microphone=(), geolocation=()` |

HSTS `includeSubDomains` is retained as requested; the owner is responsible for HTTPS on any subdomains. CSP remains deferred until the real EmailOctopus/reCAPTCHA resource requirements can be checked without breaking signup. The build validates **every HTML file before writing any HTML**, fails on unknown template markers, and tests ensure `{{TOTAL}}`, `{{COUNT}}`, `{{DATE}}` and `<!--RANKINGS-->` are absent from dist. Never publish the source root or merge before coordinating the build/publish settings.

Rollback after an approved release: use Render's prior known-good deployment for immediate artifact rollback, then revert the redesign commit through a reviewed PR (preserve intervening data commits) and restore the old build/publish settings if returning to the original root-served site. Do not reset main or overwrite new snapshots.

No new runtime dependencies, services, paid scans or operating costs are introduced. Existing Render, email and data-provider costs remain account-dependent and were not changed. See [test record](docs/TESTING.md), [ranked findings](docs/AUDIT.md), and [FakeCheck evaluation gate](docs/FAKECHECK.md).
