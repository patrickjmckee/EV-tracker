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

### 3. Bright Data (only needed for Autotrader/CarGurus)

- Sign up at brightdata.com, create a Web Unlocker zone.
- Get API key + zone name.
- If you'd rather skip this cost, set `ENABLE_AUTOTRADER`/`ENABLE_CARGURUS` to `false` in the workflow and rely on Cars.com only.

### 4. GitHub repo

- Push this folder to a new GitHub repo.
- Repo Settings > Secrets and variables > Actions > New repository secret. Add:
  - `NTFY_TOPIC`
  - `DISCORD_WEBHOOK_URL`
  - `BRIGHTDATA_API_KEY` (if using Autotrader/CarGurus)
- The workflow in `.github/workflows/daily-search.yml` runs daily at 8am Mountain and on manual trigger.

### 5. First run

- Go to repo's Actions tab > "Daily EV Search" > "Run workflow" to test manually before waiting for the schedule.

## Known limitations (read this)

- The `carscom.py` and `unlocker_sites.py` parsers use placeholder selectors. Cars.com/Autotrader/CarGurus change their HTML/JSON structure regularly. **First real run will likely need selector fixes** -- inspect actual response with `bdata scrape <url> -f html` or browser devtools and adjust `_parse_autotrader` / `_parse_cargurus` / the Cars.com JSON handling accordingly.
- `seen_listings.json` dedup relies on listing IDs being stable across runs -- verify this holds for each site.
- Dealership-only inventory (not on any aggregator) isn't covered. Add specific dealer scrapers if needed.
