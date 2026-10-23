# Reproducible test record

Executed on 2026-10-23, macOS, Node v24.22.1, Python 3.14.3, Chrome via the connected browser. No production signups, messages, accounts, paid scans, API load or deployments occurred.

## Commands and results

From the repository root:

```sh
node --check core.js
node --check app.js
node --check site.js
node --check insights.js
npm test
npm run build
npm audit
```

Results: all syntax checks passed; **57 tests passed (22 Node + 35 Python)**; offline build succeeded with 20 tracked creators and 8 Rising entries from the existing real snapshots; npm audit reported **0 vulnerabilities** for the pinned dev-only axe dependency. Public artifact approximately 230 KB (including existing images and public snapshots, excluding external avatar responses). No new runtime dependency or font download.

Tests cover independent platform membership, sums versus missing/zero values, safe integers/overflow, malformed input, duplicates, deterministic ties, stale data, URL validation, avatar allowlisting, real historical recomputation, short/sparse/exact-week windows, renamed/reused/mixed-ID accounts, carried/repeated X timestamps, timezone-aware IG comparisons, unverified cap eligibility, floors/caps, negative/zero growth and milestone boundaries. Build checks cover links/fragments, one h1, unique IDs, artifact boundaries, SSR/JSON agreement, and escaped JSON. Source data is not mutated by tests/build.

Baseline `5f84c23`: `node --check app.js`, `node --check insights.js` and `python3 -m py_compile tools/build_insights.py` passed. Its original generator reproduced the committed insights in a temporary directory. No baseline test suite existed; deployed build was `echo ok`.

## Browser checks

Production was visited only for baseline inspection/screenshots. All interaction and abuse tests used localhost, with external network URLs blocked during fixture testing. Local production email/analytics are disabled independently in code.

| Check | Observed result |
|---|---|
| Four main pages at 390 and 1280 px | No horizontal overflow; one h1; axe-core 4.14.0 WCAG 2 A/AA, 2.1 AA and 2.2 AA: zero violations in all eight page/viewport combinations |
| Final home axe recheck | Zero violations; color-contrast retained as an incomplete/manual check |
| Four main pages at 320 px; home at 768 px | No horizontal overflow |
| Age acknowledgement | Initial focus on Enter; Tab and Shift+Tab wrap; Escape does not bypass; background inert; Enter restores content and focuses heading |
| Keyboard ranking filters | All three modes correct; visible focus; pressed state changes; exact totals remain separate from rounded summaries |
| Empty data | Explicit empty state, no fake ranks |
| Invalid JSON | Eight bundled entries and clear dated fallback notice |
| Complete data outage | No estimated counts; filters disabled; retry available |
| Delayed response | Filters disabled while pending; six-second abort leads to dated bundled fallback |
| Malformed insights | No growth displayed; error and retry available |
| Long/injection-like name, bad avatar at 320 px | Name appears literally, no injected image or execution, no overflow |
| Newsletter mock | Disabled before consent; exactly one local form after consent; malformed email invalid; synthetic `fixture@example.invalid` accepted locally without sending email |
| Mock provider 503 | Clear failure text; no fake success; one script, no duplicate form |
| Unknown page | Styled 404; local HTTP status 404 |
| JavaScript disabled | Age gate remains; explains JS needed to confirm age; background not exposed through navigation |
| Reduced motion | Computed scroll behavior becomes auto |

Automated checks do not establish full WCAG conformance. Core text palette contrast was independently calculated: cream/background 16.61:1, muted/background 9.46:1, gold/background 9.83:1, muted/panel 9.02:1. Disabled controls, visual texture, real provider forms, screen readers and device-specific rendering still need human review. External profile identity/availability, real CAPTCHA and email delivery were not exercised.

## Bounded local load / abuse test

Predefined limits live in `tools/load_smoke.py`: loopback only, synthetic data, concurrency **4**, **80** JSON requests plus **8** abuse probes (maximum 88 total), request timeout **2 s**, wall budget **20 s**, stop after **3 failures** or observed **p95 > 1,000 ms**. No external API calls.

Reproduce in a disposable local preview:

```sh
python3 tools/build_site.py
python3 tools/preview.py --port 8768 --test-scenarios
# In another terminal:
curl -fsS -X POST http://127.0.0.1:8768/__test__/scenario -d '{"scenario":"synthetic"}'
python3 tools/load_smoke.py
curl -fsS -X POST http://127.0.0.1:8768/__test__/scenario -d '{"scenario":"normal"}'
```

Observed: 80/80 successful reads; p50 **0.85 ms**, p95 **2.11 ms**, max **6.09 ms**. Eight abuse probes returned expected 404/405/400/413 responses; no stop condition fired. This is a small static-server smoke test, **not** Render scalability, sustained load or provider rate-limit evidence.

Other fixture names: `empty`, `malformed`, `outage`, `slow`, `long-names`, `insights-malformed`, `newsletter-success`, `newsletter-outage`. Newsletter scenarios substitute only local mock scripts; they do not prove actual provider behavior. Restore `normal`, and restart the ordinary preview without `--test-scenarios` before handoff. Test controls and tools are never included in dist.

## Evidence and screenshots

Machine-readable baseline hashes, browser dimensions, axe summaries, load results, palette ratios and limited secret scan are in [evidence/](evidence/). Secret scan: 138 reachable Git blobs plus current text source, common key/token patterns, zero matches; not an exhaustive audit. The original [QA checklist](../QA-CHECKLIST.md) is retained as historical maintainer evidence, not represented as tests rerun in this task.

- [Before desktop](screenshots/before-desktop.jpg) / [after desktop](screenshots/after-desktop.jpg)
- [Before mobile](screenshots/before-mobile.jpg) / [after mobile](screenshots/after-mobile.jpg)

Before screenshots are production at the baseline. After screenshots are local preview with external requests blocked; existing profile images gracefully fall back to initials. Four compressed JPEGs total under 1 MB and are excluded from the public build.
