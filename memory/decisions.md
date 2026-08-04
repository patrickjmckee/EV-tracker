# EV-tracker decisions

Why-records for choices that aren't obvious from the code. Operational
state lives in README.md / TODO.md; session snapshot in memory/state.md.

## 2026-08-01: Radius enforced client-side, not via URL params

**Decision:** Drop listings with a known distance beyond `radius_miles` in
`main.py` after collection, instead of trusting the sites' radius URL params.

**Why:** Cars.com and CarGurus both return out-of-market "delivery" listings
regardless of the radius param (observed: El Paso TX, Las Vegas NV, Forney TX
in a 100 mi Utah search). Cars.com cards carry only the seller zip, so distance
is computed locally via the static `zipcodes` package (`src/geo.py`); CarGurus
tiles carry a site-computed `distance` field used directly. Listings with
unknown distance are kept (fail-open) so a parser drift degrades to noise, not
silence.

## 2026-08-01: CarMax scoped to one store, parsed from rendered DOM

**Decision:** CarMax source fetches `/cars/{storeId}/{make}/{model-slug}`
(store 7167 = Salt Lake South Jordan) and parses rendered tiles keyed by
`/car/{stockNumber}` links.

**Why:** No search API was discoverable (CDP request capture and the page's
resource-timing log both came up empty), and the generic `/cars/{make}/{model}`
pages geolocate by IP -- a GitHub runner searches from Virginia, not Utah.
Store-scoping pins the location and makes results inherently in-radius.
Year/price are filtered in code because CarMax URLs carry no filter params;
"similar match" tiles (other models) are dropped by requiring the model name in
the tile title. Transfer cars ("$X Shipping" tiles) are kept deliberately --
they're buyable at the local store.

## 2026-08-01: Browser start retried 3x in CI

**Decision:** `start_browser()` retries `uc.start()` up to 3 times, plus a
throwaway headless Chrome warm-up in the workflow.

**Why:** On a cold GitHub runner, Chrome's first launch exposes its DevTools
socket slower than nodriver waits, raising "Failed to connect to browser". A
diagnostic run proved all configs work once caches are warm. The retry fired
on attempt 1 in the very first fixed run -- it is load-bearing, not paranoia.

## 2026-08-01: Autotrader stays disabled; also_consider models dropped

**Decision:** `ENABLE_AUTOTRADER=false` in CI until an unlocker is chosen
(Bright Data undecided, alternatives being evaluated). `also_consider` models
(Model 3, Niro EV, Bolt EUV) commented out in criteria.yaml.

**Why:** Autotrader is bot-blocked under nodriver alone (captcha page, verified
2026-07-24). Model 3 alone produced 30+ matches per sweep and dominated alert
volume; Patrick chose to cut it and re-evaluate criteria after observing the
2026-08-02 morning run.

## 2026-08-03: Carvana filters via cvnaid, exempt from the radius filter

**Decision:** Carvana source builds `/cars/filters?cvnaid=<base64 JSON>` URLs
({makes/parentModels, price{min,max}, year{min}}), parses per-tile JSON-LD
(`data-testid="vehicle-ld"`), paginates with `&page=N` until a page renders
zero tiles (8-page cap). Listings carry `distance_miles: None` so the radius
filter keeps them (fail-open) -- intentionally: Carvana is national
delivery-only inventory with no store or distance concept.

**Why:** Plain query params are ignored by Carvana's SRP (`?price=`,
`?sortBy=` -- verified live), and pretty slugs only exist for popular models
(`/cars/toyota-bz4x` silently falls back to the ~54k-car all-cars page, which
is why the parser guards on results-count > 10000). The `cvnaid` mechanism was
reverse-engineered from the page's applied-filters state and verified to
filter server-side (Ioniq 5: 161 -> 111 with price band, -> 98 with year).
Filter takes the PARENT model name (parent "bZ" covers bZ + bZ4X, "Bolt"
covers Bolt EV + EUV), so exact model matching happens per-tile in code.
Patrick chose Carvana knowing it is delivery-based, and confirmed 2026-08-03
that it stays national -- he filters those alerts manually. Verified live: no
ZIP key exists (cvnaid `zip`/`zipCode`/`location` keys and a `&zip=` query
param are all silently ignored; unknown cvnaid keys don't break the filter).
Carvana's delivery market comes only from the `CVCurrentZip` cookie
(IP-geolocated), so a radius proxy would need cookie injection -- not worth
it for a manual-filter workflow.

## 2026-08-03: Toyota bZ4X and bZ tracked as two models

**Decision:** Both `bZ4X` and `bZ` entries in criteria.yaml.

**Why:** Toyota renamed the bZ4X to "bZ" for the 2026 model year; used
inventory carries both names. Sites treat them as distinct models (CarGurus
m7/d3220 vs m7/d3515). Tracking only one would miss the other's listings.

## 2026-08-03: Within-run dedup by listing id in main.py

**Decision:** After collection, keep the first listing per id before the
radius filter and seen-check.

**Why:** Three observed/known overlap paths: CarGurus returned the same tile
twice in one search (featured + organic, seen live with a Provo bZ4X);
CarMax's substring title match lets a "bZ" search claim bZ4X tiles; Carvana's
bZ and bZ4X searches share the same parent filter. Without this, one car can
alert twice in the same run (the seen-file only dedups across runs).

## 2026-08-03: Windows local dev attaches to a hand-launched Chrome

**Decision:** `NODRIVER_ATTACH=host:port` makes `start_browser()` attach to an
existing browser instead of spawning; `stop_browser()` leaves attached
browsers running. `_find_chrome()` also knows Windows Chrome/Edge/Playwright
paths.

**Why:** nodriver's own spawn is broken on Windows (this machine): Chrome
re-execs as a launcher that exits immediately, and nodriver's short CDP poll
gives up -- verified that the identical spawn works when polled independently.
Attach sidesteps it. Headed Chrome is required regardless; `--headless=new`
advertises HeadlessChrome in the UA and Cloudflare blocks it.
