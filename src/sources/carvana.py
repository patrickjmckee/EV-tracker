"""
Carvana search via nodriver.
Carvana is national delivery-only inventory -- no store or radius scoping.
Listings carry no distance, so main.py's radius filter keeps them all
(unknown distances are kept); that's intentional for this source.

Filtering is server-side via /cars/filters?cvnaid=<base64 JSON>
(discovered 2026-08-03): {"makes":[{"name":<make>,"parentModels":
[{"name":<parent>}]}],"price":{"min":..,"max":..},"year":{"min":..}}.
Plain ?price= / ?sortBy= query params are ignored; &page=N composes with
cvnaid. Listing data is per-tile JSON-LD blocks
(<script type="application/ld+json" data-testid="vehicle-ld">).

Carvana's filter takes the PARENT model name, which can cover several
models (parent "bZ" covers bZ and bZ4X; parent "Bolt" covers Bolt EV and
Bolt EUV), so tiles are matched against the exact model name in code.
"""
import base64
import json
import re

BASE_URL = "https://www.carvana.com/cars/filters"

# criteria.yaml (make, model) -> (Carvana parentModel filter, exact tile
# model name). Names lifted from Carvana's embedded filter taxonomy
# 2026-08-03; unmapped models fall back to (model, model).
_MODEL_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ("Hyundai", "Ioniq 5"): ("IONIQ 5", "IONIQ 5"),
    ("Hyundai", "Ioniq 6"): ("IONIQ 6", "IONIQ 6"),
    ("Kia", "EV6"): ("EV6", "EV6"),
    ("Kia", "Niro EV"): ("Niro EV", "Niro EV"),
    ("Chevrolet", "Bolt"): ("Bolt", "Bolt EV"),
    ("Chevrolet", "Bolt EUV"): ("Bolt", "Bolt EUV"),
    ("Chevrolet", "Equinox EV"): ("Equinox EV", "Equinox EV"),
    ("Nissan", "Leaf"): ("LEAF", "LEAF"),
    ("Toyota", "bZ4X"): ("bZ", "bZ4X"),
    ("Toyota", "bZ"): ("bZ", "bZ"),
    ("Tesla", "Model 3"): ("Model 3", "Model 3"),
}

_LD_RE = re.compile(
    r'<script type="application/ld\+json" data-testid="vehicle-ld">(.*?)</script>',
    re.S,
)
_COUNT_RE = re.compile(r'data-testid="results-count">([\d,]+)')

# A page whose results-count is this large means the filter wasn't applied
# (Carvana silently falls back to all-cars); parsing it would yield noise.
_MAX_PLAUSIBLE_COUNT = 10000

_MAX_PAGES = 8


def _build_url(make: str, model: str, criteria: dict, page: int) -> str:
    parent, _ = _MODEL_MAP.get((make, model), (model, model))
    filters = {
        "makes": [{"name": make, "parentModels": [{"name": parent}]}],
        "price": {"min": criteria["price_min"], "max": criteria["price_max"]},
        "year": {"min": criteria["year_min"]},
    }
    cvnaid = base64.b64encode(json.dumps(filters).encode()).decode()
    url = f"{BASE_URL}?cvnaid={cvnaid}"
    if page > 1:
        url += f"&page={page}"
    return url


def _parse(html: str, make: str, model: str, criteria: dict) -> tuple[list[dict], int]:
    """Returns (listings, raw_tile_count). raw_tile_count is pre-filter so
    the pagination loop can tell an empty page from a filtered-out one."""
    count_m = _COUNT_RE.search(html)
    if count_m and int(count_m.group(1).replace(",", "")) > _MAX_PLAUSIBLE_COUNT:
        print(f"    carvana: filter not applied for {make} {model} (all-cars fallback), skipping")
        return [], 0

    _, want_model = _MODEL_MAP.get((make, model), (model, model))

    listings = []
    raw = 0
    for m in _LD_RE.finditer(html):
        try:
            v = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        raw += 1

        if str(v.get("model", "")).lower() != want_model.lower():
            continue

        year = v.get("modelDate")
        price = (v.get("offers") or {}).get("price")
        if year and year < criteria["year_min"]:
            continue
        if price and not (criteria["price_min"] <= price <= criteria["price_max"]):
            continue

        url = (v.get("offers") or {}).get("url", "")
        vid_m = re.search(r"/vehicle/(\d+)", url)
        if not vid_m:
            continue
        vid = vid_m.group(1)

        # description is "Used 2024 Hyundai IONIQ 5 SE with 13781 miles - $27,990";
        # the trim is the piece between the model name and " with".
        title = v.get("name", "")
        desc = v.get("description", "")
        prefix = f"Used {year} {v.get('manufacturer', '')} {v.get('model', '')} "
        if desc.startswith(prefix):
            trim = desc[len(prefix):].split(" with ")[0].strip()
            if trim:
                title = f"{title} {trim}"

        extras = []
        if v.get("color"):
            extras.append(v["color"])
        extras.append("Delivery")

        listings.append({
            "source": "carvana",
            "id": f"carvana-{vid}",
            "title": title,
            "price": f"${price:,}" if price else None,
            "mileage": str(v.get("mileageFromOdometer", "")) or None,
            "year": str(year) if year else None,
            "vin": v.get("vehicleIdentificationNumber"),
            "stock_type": v.get("itemCondition") or "Used",
            "url": url,
            "dealer": "Carvana",
            "location": "Carvana (national delivery)",
            "distance_miles": None,
            "extras": extras,
        })
    return listings, raw


async def search(browser, make: str, model: str, criteria: dict) -> list[dict]:
    from browser_fetch import fetch_page

    all_listings = []
    for page in range(1, _MAX_PAGES + 1):
        url = _build_url(make, model, criteria, page)
        html = await fetch_page(browser, url, wait_seconds=12)
        listings, raw = _parse(html, make, model, criteria)
        all_listings += listings
        # Past-the-end pages render zero tiles; that's the stop signal.
        if raw == 0:
            break
    else:
        print(f"    carvana: hit {_MAX_PAGES}-page cap for {make} {model}; deeper inventory unseen")
    return all_listings
