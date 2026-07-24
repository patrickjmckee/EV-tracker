"""
Autotrader search via nodriver (bypasses Cloudflare).
Listing data is in __NEXT_DATA__ -> props.pageProps.__eggsState.inventory dict.
Each key in inventory is a listing ID; values contain full vehicle data.
"""
import json

from bs4 import BeautifulSoup

BASE_URL = "https://www.autotrader.com/cars-for-sale/all-cars"

# URL slugs for makes and models used in criteria.yaml
_MODEL_SLUGS: dict[tuple[str, str], str] = {
    ("Hyundai", "Ioniq 5"): "hyundai/ioniq-5",
    ("Hyundai", "Ioniq 6"): "hyundai/ioniq-6",
    ("Kia", "EV6"): "kia/ev6",
    ("Kia", "Niro EV"): "kia/niro-ev",
    ("Chevrolet", "Bolt"): "chevrolet/bolt-ev",
    ("Chevrolet", "Bolt EUV"): "chevrolet/bolt-euv",
    ("Chevrolet", "Equinox EV"): "chevrolet/equinox-ev",
    ("Nissan", "Leaf"): "nissan/leaf",
    ("Tesla", "Model 3"): "tesla/model-3",
}


def _build_url(make: str, model: str, criteria: dict) -> str:
    slug = _MODEL_SLUGS.get((make, model))
    if not slug:
        # Fallback: derive from make/model name
        make_slug = make.lower().replace(" ", "-")
        model_slug = model.lower().replace(" ", "-")
        slug = f"{make_slug}/{model_slug}"

    params = (
        f"?zip={criteria['zip_code']}"
        f"&searchRadius={criteria['radius_miles']}"
        f"&minPrice={criteria['price_min']}"
        f"&maxPrice={criteria['price_max']}"
        f"&startYear={criteria['year_min']}"
        f"&allListingType=all-cars"
    )
    return f"{BASE_URL}/{slug}{params}"


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    next_data_tag = soup.find("script", id="__NEXT_DATA__")
    if not next_data_tag:
        return []

    try:
        data = json.loads(next_data_tag.get_text())
    except json.JSONDecodeError:
        return []

    try:
        eggs = data["props"]["pageProps"]["__eggsState"]
        inventory = eggs.get("inventory", {})
    except (KeyError, TypeError):
        return []

    listings = []
    for listing_id, item in inventory.items():
        if not isinstance(item, dict):
            continue

        pricing = item.get("pricingDetail", {})
        price = (
            pricing.get("salePrice")
            or pricing.get("internetPrice")
            or pricing.get("msrp")
        )

        mileage_raw = item.get("mileage")
        if isinstance(mileage_raw, dict):
            mileage = str(mileage_raw.get("value", ""))
        elif mileage_raw is not None:
            mileage = str(mileage_raw)
        else:
            mileage = None

        vdp_base = item.get("vdpBaseUrl", "")
        if vdp_base.startswith("/"):
            url = f"https://www.autotrader.com{vdp_base}"
        else:
            url = vdp_base or f"https://www.autotrader.com/cars-for-sale/vehicle/{listing_id}"

        # Strip search params from VDP URL -- keep it clean
        url = url.split("?")[0]

        listings.append({
            "source": "autotrader",
            "id": str(listing_id),
            "title": item.get("title") or item.get("titleLong", ""),
            "price": str(price) if price else None,
            "mileage": mileage,
            "year": str(item.get("year", "")),
            "vin": item.get("vin"),
            "stock_type": item.get("listingType"),
            "url": url,
            "dealer": item.get("ownerName"),
            "location": None,
        })

    return listings


async def search(browser, make: str, model: str, criteria: dict) -> list[dict]:
    from browser_fetch import fetch_page
    url = _build_url(make, model, criteria)
    html = await fetch_page(browser, url, wait_seconds=15)
    return _parse(html)
