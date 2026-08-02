# EV Tracker **Operational: daily GitHub Actions run verified end-to-end 2026-08-01**

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

## Done (2026-07-31 / 2026-08-01)

- [x] Built `.github/workflows/daily-search.yml` -- daily run at 13:00 UTC (7am MDT) + manual `workflow_dispatch`, commits `seen_listings.json` back to main, Autotrader disabled in CI pending unlocker
- [x] Added repo secrets `NTFY_TOPIC` and `DISCORD_WEBHOOK_URL`; verified both fire (test message + real run)
- [x] Fixed first CI run failure: Chrome's first launch on a cold runner exposes DevTools slower than nodriver waits -- `start_browser()` now retries 3x (attempt 1 still fails in CI, retry succeeds; see run 30725281994)
- [x] Verified full CI run end-to-end: 9 models, 239 listings, 99 new, notifications received, bot committed seen_listings.json
- [x] Added `.github/workflows/debug-browser.yml` (manual dispatch) -- keep for diagnosing future Chrome/nodriver breakage on runners

## Done (2026-08-01, evening)

- [x] Radius now enforced: 145 out-of-market "delivery" listings dropped in validation dry run (was the El Paso/Las Vegas noise)
- [x] CarMax source added, scoped to Salt Lake South Jordan store (`carmax_store_id: 7167`); found 12 cars in validation
- [x] Notifications include location + distance
- [x] `dry_run` workflow input for safe testing

## Next steps

- [ ] Tighten criteria if volume still too high after radius fix (levers: mileage cap, drop `also_consider` models, narrower price/year)
- [ ] Watch Cars.com per-page flakiness -- several models returned 0 in the 2026-08-01 dry run that CarGurus covered
- [ ] Watch CarMax tile-count variance between runs (Ioniq 5: 1 vs 8 in back-to-back dry runs; likely lazy-render timing). Dedup self-heals across days; bump carmax wait_seconds if it persists
- [ ] Add an unlocker (Bright Data or alternative) for Autotrader, then flip `ENABLE_AUTOTRADER` back on in the workflow and add `BRIGHTDATA_API_KEY` secret
- [ ] Re-check CarGurus entity IDs periodically -- confirmed correct as of 2026-07-24 but noted as liable to drift
