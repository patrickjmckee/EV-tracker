# EV-tracker state

**Status: OPERATIONAL** (2026-08-01)

## Current state

- Daily GitHub Actions run at 13:00 UTC (7am MDT), verified end-to-end:
  scrape -> radius filter -> notify (ntfy + Discord) -> commit seen_listings.json.
- Sources: Cars.com, CarGurus, CarMax (store 7167). Autotrader disabled
  (bot-blocked, unlocker undecided).
- 6 models tracked (also_consider block commented out in config/criteria.yaml).
- Notifications carry location, distance, and extras (deal rating, EV range,
  CPO, drivetrain, CarMax transfer cost).
- Secrets NTFY_TOPIC + DISCORD_WEBHOOK_URL set in repo Actions secrets and
  verified firing. gh CLI on this machine authenticated as patrickjmckee.
- Last validation dry run: 52 in-radius listings, 108 out-of-radius dropped,
  14 would-notify (all CarMax backfill).

## Next session

1. Patrick reviews the 2026-08-02 morning run output (expects ~14 CarMax
   backfill notifications + any genuinely new listings).
2. Decide additional criteria tweaks from real output. Levers discussed:
   mileage cap (none exists today), narrower price/year, radius change.
3. Standing watch items and remaining TODOs: see TODO.md "Next steps".

## Testing without side effects

Actions > "Daily EV search" > Run workflow > check `dry_run` -- prints
would-be notifications, sends nothing, leaves seen_listings.json untouched.
Probe workflow (`test-sources.yml`) dumps raw site data for parser work.
