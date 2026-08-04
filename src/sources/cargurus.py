"""
CarGurus search via nodriver (bypasses Cloudflare).
Listing data is in window.__remixContext -> state.loaderData["routes/($intl).search"].search.tiles.

URL format uses CarGurus entity IDs for make/model filtering.
Entity IDs discovered 2026-07-17 -- may drift if CarGurus renumbers their taxonomy.
"""
import json
import re
from urllib.parse import urlencode

BASE_URL = "https://www.cargurus.com/search"

# CarGurus entity paths discovered from filter data: "{makeId}/{modelId}"
# Used in the makeModelTrimPaths param as "{makeId}/{modelId},{makeId}"
_ENTITY_MAP: dict[tuple[str, str], str] = {
    ("Hyundai", "Ioniq 5"): "m28/d3120",
    ("Hyundai", "Ioniq 6"): "m28/d3297",
    ("Kia", "EV6"): "m33/d3127",
    ("Kia", "Niro EV"): "m33/d2838",
    ("Chevrolet", "Bolt"): "m1/d2397",
    ("Chevrolet", "Bolt EUV"): "m1/d3116",
    ("Chevrolet", "Equinox EV"): "m1/d3267",
    ("Nissan", "Leaf"): "m12/d2077",
    ("Tesla", "Model 3"): "m112/d2475",
    # Discovered 2026-08-03 from the Toyota-filtered search's filter data
    ("Toyota", "bZ4X"): "m7/d3220",
    ("Toyota", "bZ"): "m7/d3515",
}

_DRIVETRAIN_ABBREV = {
    "All-Wheel Drive": "AWD",
    "Front-Wheel Drive": "FWD",
    "Rear-Wheel Drive": "RWD",
    "Four-Wheel Drive": "4WD",
}

# make-only IDs used as fallback
_MAKE_IDS: dict[str, str] = {
    "Chevrolet": "m1",
    "Hyundai": "m28",
    "Kia": "m33",
    "Nissan": "m12",
    "Tesla": "m112",
    "Toyota": "m7",
}


def _build_url(make: str, model: str, criteria: dict) -> str:
    entity_path = _ENTITY_MAP.get((make, model))
    if entity_path:
        make_id = entity_path.split("/")[0]
        trim_path = f"{entity_path},{make_id}"
    else:
        make_id = _MAKE_IDS.get(make, "")
        trim_path = make_id

    params = {
        "zip": criteria["zip_code"],
        "distance": criteria["radius_miles"],
        "minPrice": criteria["price_min"],
        "maxPrice": criteria["price_max"],
        "startYear": criteria["year_min"],
    }
    if trim_path:
        params["makeModelTrimPaths"] = trim_path

    return BASE_URL + "?" + urlencode(params)


def _extract_remix_context(html: str) -> dict:
    idx = html.find("window.__remixContext")
    if idx == -1:
        return {}

    chunk = html[idx:]
    start = chunk.index("=") + 1
    chunk = chunk[start:].lstrip()

    depth = 0
    in_str = False
    escape_next = False
    for i, c in enumerate(chunk):
        if escape_next:
            escape_next = False
            continue
        if c == "\\" and in_str:
            escape_next = True
            continue
        if c == '"' and not escape_next:
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(chunk[: i + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


def _parse(html: str) -> list[dict]:
    data = _extract_remix_context(html)
    if not data:
        return []

    try:
        search = data["state"]["loaderData"]["routes/($intl).search"]["search"]
        tiles = search.get("tiles", [])
    except (KeyError, TypeError):
        return []

    listings = []
    for tile in tiles:
        item = tile.get("data", {})
        if not isinstance(item, dict) or "id" not in item:
            continue

        listing_id = item["id"]
        price_data = item.get("priceData", {})
        price = price_data.get("current")
        mileage_data = item.get("mileageData", {})
        mileage = mileage_data.get("value")
        ontology = item.get("ontologyData", {})
        seller = item.get("sellerData", {})

        # listingTitle is "2024 Hyundai Ioniq 5" -- append the trim if known
        title = item.get("listingTitle", "")
        trim = ontology.get("trimName")
        if trim and trim.lower() not in title.lower():
            title = f"{title} {trim}"

        extras = []
        rating = item.get("dealRating")
        if rating:
            extras.append(rating.replace("_", " ").capitalize())
        ev_range = (item.get("evBatteryData") or {}).get("range")
        if ev_range:
            extras.append(f"{ev_range} range")
        if item.get("isCpo"):
            extras.append("CPO")
        drivetrain = item.get("localizedDrivetrain")
        if drivetrain:
            extras.append(_DRIVETRAIN_ABBREV.get(drivetrain, drivetrain))

        listings.append({
            "source": "cargurus",
            "id": str(listing_id),
            "title": title,
            "price": str(price) if price is not None else None,
            "mileage": str(mileage) if mileage is not None else None,
            "year": ontology.get("carYear"),
            "vin": item.get("vin"),
            "stock_type": "New" if item.get("isNew") else "Used",
            "url": (
                f"https://www.cargurus.com/Cars/inventorylisting/"
                f"viewDetailsFilterViewInventoryListing.action#listing={listing_id}"
            ),
            "dealer": seller.get("sellerName"),
            "location": seller.get("displayLocation"),
            # Site-computed miles from the search zip; present on normal
            # tiles, may be absent on delivery/featured ones.
            "distance_miles": item.get("distance"),
            "extras": extras,
        })

    return listings


async def search(browser, make: str, model: str, criteria: dict) -> list[dict]:
    from browser_fetch import fetch_page
    url = _build_url(make, model, criteria)
    html = await fetch_page(browser, url, wait_seconds=12)
    return _parse(html)
