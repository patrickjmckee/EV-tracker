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
