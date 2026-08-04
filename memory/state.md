# EV-tracker state

**Status: OPERATIONAL** (2026-08-03; Carvana source not yet CI-validated)

## Current state

- Daily GitHub Actions run at 13:00 UTC (7am MDT), verified end-to-end:
  scrape -> radius filter -> within-run dedup -> notify (ntfy + Discord) ->
  commit seen_listings.json.
- Sources: Cars.com, CarGurus, CarMax (store 7167), Carvana (added
  2026-08-03, validated locally, first CI run pending). Autotrader disabled
  (bot-blocked, unlocker undecided).
- 8 models tracked: Ioniq 5/6, EV6, Bolt, Equinox EV, Leaf, and (new
  2026-08-03) Toyota bZ4X + bZ. also_consider block still commented out.
- Criteria tightened 2026-08-03: price band now $20k-$30k (was $20k-$55k),
  year 2024+, 100 mi radius.
- Carvana is national delivery inventory: no distance data, bypasses the
  radius filter by design, filters server-side via base64 `cvnaid` URL param,
  parses JSON-LD tiles, paginates to 8 pages max.
- Secrets NTFY_TOPIC + DISCORD_WEBHOOK_URL set in repo Actions secrets and
  verified firing. gh CLI on this machine authenticated as patrickjmckee.

## Next session

1. Review the first CI run after the 2026-08-03 changes. Carvana on a
   GitHub runner is the open question (bot-detection unknown); if it's
   blocked, set `ENABLE_CARVANA: "false"` in daily-search.yml. Full local
   dry run: 143 would-notify (one-time backfill: ~130 Carvana nationwide,
   13 local dealer listings). CarMax was 0 across all models -- plausibly
   the $30k cap, but eyeball the store page once.
2. DECIDED 2026-08-03: Carvana stays national; Patrick filters those
   alerts manually. Verified live that no ZIP key exists (cvnaid zip/
   zipCode/location keys and &zip= param all ignored; location comes from
   the CVCurrentZip cookie, IP-geolocated).
3. Standing watch items and remaining TODOs: see TODO.md "Next steps".

## Testing without side effects

Actions > "Daily EV search" > Run workflow > check `dry_run` -- prints
would-be notifications, sends nothing, leaves seen_listings.json untouched.
Probe workflow (`test-sources.yml`) dumps raw site data for parser work.

Local on Windows: launch Chrome with `--remote-debugging-port=9333` and a
scratch profile, set `NODRIVER_ATTACH=127.0.0.1:9333` + `DRY_RUN=true`, run
`python src\main.py` (details in README "Local dev on Windows").
