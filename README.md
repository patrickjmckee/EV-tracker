# EV Tracker

Daily search across Cars.com, CarGurus, CarMax, Carvana (and Autotrader, currently disabled) for matching EVs. Pushes new matches via ntfy.sh (phone push) and Discord webhook. Listings beyond `radius_miles` are dropped even when sites return them as "delivery" inventory; CarMax is scoped to one store (`carmax_store_id` in `config/criteria.yaml`). Carvana is the deliberate exception: it's national delivery-only inventory with no distance data, so its listings bypass the radius filter.

## Setup

### 1. ntfy.sh (phone push)

- Install the ntfy app (iOS/Android).
- Pick a unique topic name, e.g. `my-ev-alerts-a1b2c3` (must be unique globally, no signup needed). Treat it like a password -- anyone who knows it can push notifications to your phone.
- Subscribe to that topic in the app.

### 2. Discord webhook

- Create/use a Discord server, pick a channel.
- Channel Settings > Integrations > Webhooks > New Webhook > copy URL.

### 3. Bright Data (only confirmed needed for Autotrader)

- Sign up at brightdata.com, create a Web Unlocker zone.
- Get API key + zone name.
- Verified 2026-07-24: current code has no Bright Data integration -- it runs on `nodriver` alone. CarGurus and Cars.com both pass their bot-detection this way with no unlocker. Autotrader does not -- it returns a captcha/block page (`Autotrader - page unavailable`) every time under nodriver alone. Bright Data (or an equivalent unlocker) is required to make Autotrader work; until then, expect 0 results from it and treat that as a known gap, not a bug.

### 4. GitHub repo

- Repo created and pushed: `https://github.com/patrickjmckee/EV-tracker` (2026-07-24).
- Repo Settings > Secrets and variables > Actions > New repository secret. Add:
  - `NTFY_TOPIC`
  - `DISCORD_WEBHOOK_URL`
  - `BRIGHTDATA_API_KEY` (if/when Autotrader unlocking is added)
- `.github/workflows/daily-search.yml` runs the search daily at 13:00 UTC (7am MDT) and can be triggered manually from the Actions tab (`workflow_dispatch`). It commits the updated `seen_listings.json` back to `main` after each run so dedup persists across runs. Autotrader is skipped in CI (`ENABLE_AUTOTRADER=false`) until an unlocker is added.
- Note: GitHub disables scheduled workflows after ~60 days without repository activity. If alerts stop, check the Actions tab for a "workflow disabled" banner and re-enable it.

### 5. First run

- Manual run: `NTFY_TOPIC=... DISCORD_WEBHOOK_URL=... python3 src/main.py` from the repo root.
- Optional: set `NTFY_SERVER` to point at a self-hosted ntfy instance instead of `https://ntfy.sh` (defaults to ntfy.sh if unset).

## Verified status (2026-08-01 CI dry run; 2026-08-03 local full dry run)

Full 9-model sweep on GitHub Actions (run 30726763294): 210 listings found, 145 dropped as beyond the 100 mi radius, 65 kept, 14 new.

| Site | Result |
| --- | --- |
| Cars.com | Works, but flaky per-page -- returned 0 for several models this run that CarGurus covered (Cloudflare roulette; watch, don't panic on single-run zeros) |
| CarGurus | Works -- site-provided tile distance used for radius filtering |
| CarMax | Works -- store-scoped (Salt Lake South Jordan), year/price filtered in code, "similar match" tiles skipped |
| Carvana | Works (validated locally 2026-08-03, first CI run pending) -- server-side filters via base64 `cvnaid` URL param, JSON-LD tile data, paginated. National delivery inventory, so no radius filtering applies |
| Autotrader | Bot-blocked, disabled in CI (`ENABLE_AUTOTRADER=false`) pending an unlocker |

To test changes safely: Actions > Daily EV search > Run workflow > check `dry_run` -- prints would-be notifications without sending or updating `seen_listings.json`.

Notifications: Discord webhook confirmed firing end-to-end. `notify.py` now splits large batches into multiple Discord messages (was silently truncating past 2000 chars) and catches per-listing/per-chunk send failures so one bad request no longer aborts the run before `seen_listings.json` is saved.

## Known limitations (read this)

- Autotrader needs a working unlocker (Bright Data or similar) -- nodriver alone is bot-blocked. See "Bright Data" section above.
- `seen_listings.json` dedup relies on listing IDs being stable across runs -- verify this holds for each site.
- Dealership-only inventory (not on any aggregator) isn't covered. Add specific dealer scrapers if needed.
- Carvana is national delivery inventory: no location/distance, so every match nationwide alerts (the radius filter keeps unknown distances). Its `cvnaid` filter mechanism (base64 JSON in the URL) is undocumented and could change without warning -- if Carvana counts explode or hit the all-cars fallback guard, re-probe with `scripts/probe_sources.py`.
- Carvana pagination is capped at 8 pages (~170 tiles) per model; the run prints a warning if the cap is hit.

## Local dev on Windows

nodriver's own browser spawn doesn't work on Windows (Chrome re-execs as a
launcher that exits before nodriver sees the CDP socket). Instead, launch a
browser yourself and attach:

```powershell
& "$env:LOCALAPPDATA\ms-playwright\chromium-1234\chrome-win64\chrome.exe" `
  --remote-debugging-port=9333 --user-data-dir=$env:TEMP\probe-profile about:blank
$env:NODRIVER_ATTACH = '127.0.0.1:9333'
$env:DRY_RUN = 'true'
python src\main.py
```

Headed (non-headless) Chrome is required for the Cloudflare-protected sites;
`--headless=new` changes the UA to HeadlessChrome and gets blocked.
