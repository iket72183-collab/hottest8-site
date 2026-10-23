# Hottest8

Strictly SFW, adults-only rankings for a tracked creator set. Grok Bot is the lead maintainer. This branch proposes a black/gold editorial redesign and validated offline data builds; it does **not** deploy them.

## Run locally

Python 3.9+ builds and previews without installing anything. Node 18+ runs JavaScript regression tests. The only npm dependency is optional development-only `axe-core@4.14.0` for browser accessibility audits.

```sh
python3 tools/build_site.py
python3 tools/preview.py --port 8768
# Open http://127.0.0.1:8768/
node --test tests/core.test.cjs
python3 -m unittest discover -s tests -v
# Optional browser audit dependency:
npm ci --ignore-scripts
npm audit
```

Serve **dist/**, never the repository root. HTML source templates contain build markers. The allowlisted artifact excludes tools, tests, docs and dependencies. Local previews disable production newsletter and analytics scripts. Existing allowlisted avatar URLs can still load after age confirmation; block external browser requests when testing complete offline behavior.

## Maintainer map

- `core.js`: validated counts, independent platform rankings, competition ties and historical payload validation.
- `app.js`: safe DOM ranking cards, platform dates, fallback and retry.
- `site.js`: shared age controls and consent-gated newsletter loading.
- `insights.js`: historical chart display and failure states.
- `style.css`: shared black/gold design, mobile layouts, focus and reduced-motion rules. No remote fonts.
- `tools/build_site.py`: deterministic, offline `dist/` build; SSR Combined ranking and JSON-LD; validates current data against the latest snapshot.
- `tools/build_insights.py`: pure historical calculations. Its standalone CLI refreshes root insights JSON for compatibility; the site build always recomputes artifacts independently.
- `data.json`, `snapshots/`, `rising_pool.json`: maintainer-supplied inputs. Root `data.js`, `insights.json`, `rankings.json` are legacy exports retained for the existing refresh workflow; **dist versions are generated**. Never hand-edit dist.
- `approved-avatars.json`: exact baseline avatar URL allowlist. Adding/replacing imagery requires SFW and permission review; URL membership alone is not proof of rights.

## Daily data handoff to Grok Bot

The maintainer reports an external daily routine around **07:00 America/Chicago** that commits to `main`. No fetch credentials, API implementation, scheduler or production database exists in this repository. This audit did not run that routine or verify its account permissions.

1. Fetch current `main` before starting a data update or integrating this branch. Preserve newer snapshots; do not force-push main.
2. Commit a real timezone-aware snapshot and matching `data.json`; keep original per-platform observation times. Record stable platform IDs when available, verification status, changed identities and carried-forward flags. Do not advance an Instagram date just because X refreshed. Treat a reused handle as a new identity requiring review.
3. Update the emerging pool only with verified eligibility evidence. Append real emerging snapshots. Unknown IG cannot establish the combined eligibility cap. Never replace missing data with zero or sample growth.
4. Run tests and `python3 tools/build_site.py`. Mismatched source counts/membership fail the build. Review changed rankings and each actual Rising window; a sparse interval is not automatically a week.
5. Review locally. Future production integration requires Isaac's approval and the coordinated deployment changes below.

Combined follows are summed platform counts, not unique people. Ties use competition ranks, then alphabetical X handle for deterministic eight-slot display. IG participates in growth only when comparable independently rechecked observations exist. Seven-day labels require 165–171 elapsed hours; all other windows show their actual length. Legacy snapshots without stable IDs have weaker identity evidence.

## Newsletter and privacy

The only signup integration is the pre-existing public EmailOctopus form, loaded on hottest8.com/www.hottest8.com after an unchecked 18+/weekly-newsletter choice. That click loads a form; it is **not** a subscription or a success metric. EmailOctopus handles actual submission, confirmation, delivery, suppression and unsubscribe. The app does not store addresses or send messages. The checkbox itself is not a durable consent log: the provider's form/list setup must preserve consent evidence.

Content scope remains weekly Top 8 + Industry Dispatch. FakeCheck has no separate waitlist or working detector. GoatCounter loads only after the age acknowledgement, only on production hosts. Account settings, double opt-in, retention, consent records, email templates, CAPTCHA/rate limits and unsubscribe delivery remain unverified. See [audit](docs/AUDIT.md) before claiming those protections.

## Release and rollback — approval required

Read-only Render verification on 2026-10-23 confirmed service `srv-dbc31ujrjlhs73al9icg`, repo `iket72183-collab/hottest8-site`, branch `main`, automatic deploy on commit, build `echo ok`, publish `./`, and **PR previews disabled**. Opening a PR does not enable previews. `render.yaml` is a proposed reference; editing it alone does not establish that dashboard settings will change.

**Do not merge this branch into the current auto-deploy configuration.** After Isaac approves a release, coordinate build command `python3 tools/build_site.py` and publish directory `dist` with the merge. Recheck main first because the daily job may have moved it. Apply/review security headers separately; stage the real provider form before enforcing CSP. No account setting was changed during this task.

Rollback after an approved release: use Render's prior known-good deployment for immediate artifact rollback, then revert the redesign commit through a reviewed PR (preserve intervening data commits) and restore the old build/publish settings if returning to the original root-served site. Do not reset main or overwrite new snapshots.

No new runtime dependencies, services, paid scans or operating costs are introduced. Existing Render, email and data-provider costs remain account-dependent and were not changed. See [test record](docs/TESTING.md), [ranked findings](docs/AUDIT.md), and [FakeCheck evaluation gate](docs/FAKECHECK.md).
