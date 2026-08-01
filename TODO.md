# EV Tracker **In-Progress: core scraping + notifications working, daily GitHub Actions run scheduled**

## Done (2026-07-24)

- [x] Verified full 9-model sweep against live sites (Cars.com, Autotrader, CarGurus)
- [x] Confirmed Autotrader is bot-blocked without an unlocker (not a parser bug)
- [x] Confirmed Bolt/Bolt EUV zero-results on CarGurus/Cars.com are genuine (not entity-ID bugs)
- [x] Verified notify.py Discord webhook end-to-end
- [x] Verified notify.py ntfy push end-to-end (via self-hosted local ntfy instance -- `ntfy.sh` itself unreachable from the dev sandbox)
- [x] Verified dedup logic (`seen_listings.json`) -- repeat run correctly found 0 new
- [x] Fixed: `notify.py` no longer crashes the whole run on a single failed ntfy/Discord request
- [x] Fixed: Discord messages now split into multiple sends instead of silently truncating past 2000 chars
- [x] Added `NTFY_SERVER` env var so ntfy target can be overridden (self-hosted/testing)
- [x] Repo created and pushed: `https://github.com/patrickjmckee/EV-tracker`

## Done (2026-07-31)

- [x] Built `.github/workflows/daily-search.yml` -- daily run at 13:00 UTC (7am MDT) + manual `workflow_dispatch`, commits `seen_listings.json` back to main, Autotrader disabled in CI pending unlocker

## Next steps

- [ ] Add repo secrets `NTFY_TOPIC` and `DISCORD_WEBHOOK_URL` (Settings > Secrets and variables > Actions) -- without them the run still works but sends no notifications
- [ ] Add an unlocker (Bright Data or alternative) for Autotrader, then flip `ENABLE_AUTOTRADER` back on in the workflow and add `BRIGHTDATA_API_KEY` secret
- [ ] Re-check CarGurus entity IDs periodically -- confirmed correct as of 2026-07-24 but noted as liable to drift
