# EV Tracker

Daily search across Cars.com, Autotrader, CarGurus for matching EVs. Pushes new matches via ntfy.sh (phone push) and Discord webhook.

## Setup

### 1. ntfy.sh (phone push)

- Install the ntfy app (iOS/Android).
- Pick a unique topic name, e.g. `patrick-ev-alerts-x7k2` (must be unique globally, no signup needed).
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

## Verified status (2026-07-24)

Full 9-model sweep run against live sites:

| Site | Result |
| --- | --- |
| Cars.com | Works -- 8/9 models returned results (Bolt EUV genuinely has 0 matching inventory) |
| CarGurus | Works -- 7/9 models returned results (Bolt/Bolt EUV genuinely have 0 matching inventory, confirmed via CarGurus's own `totalListings: 0`) |
| Autotrader | Bot-blocked -- 0/9 models, confirmed via captcha page, not a parser bug |

Notifications: Discord webhook confirmed firing end-to-end. `notify.py` now splits large batches into multiple Discord messages (was silently truncating past 2000 chars) and catches per-listing/per-chunk send failures so one bad request no longer aborts the run before `seen_listings.json` is saved.

## Known limitations (read this)

- Autotrader needs a working unlocker (Bright Data or similar) -- nodriver alone is bot-blocked. See "Bright Data" section above.
- `seen_listings.json` dedup relies on listing IDs being stable across runs -- verify this holds for each site.
- Dealership-only inventory (not on any aggregator) isn't covered. Add specific dealer scrapers if needed.
