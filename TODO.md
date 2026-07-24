# EV Tracker **In-Progress: core scraping + notifications working, no scheduling yet**

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

## Next steps

- [ ] Add an unlocker (Bright Data or alternative) for Autotrader, or drop it from the model sweep
- [ ] Build `.github/workflows/daily-search.yml` for the scheduled daily run described in the README -- doesn't exist yet
- [ ] Decide on GitHub Actions secrets setup (`NTFY_TOPIC`, `DISCORD_WEBHOOK_URL`, `BRIGHTDATA_API_KEY`)
- [ ] Re-check CarGurus entity IDs periodically -- confirmed correct as of 2026-07-24 but noted as liable to drift
