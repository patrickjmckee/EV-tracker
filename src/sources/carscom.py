"""
Cars.com search via nodriver (bypasses Cloudflare Turnstile).
Listing data is embedded as JSON in data-vehicle-details attributes on fuse-card elements.
"""
import json
from urllib.parse import urlencode

from bs4 import BeautifulSoup

BASE_URL = "https://www.cars.com/shopping/results/"

_MAKE_SLUG = {
    "chevrolet": "chevrolet",
    "hyundai": "hyundai",
    "kia": "kia",
    "nissan": "nissan",
    "tesla": "tesla",
}


def _build_url(make: str, model: str, criteria: dict) -> str:
    make_key = make.lower().replace(" ", "_")
    model_key = f"{make_key}-{model.lower().replace(' ', '_')}"
    params = {
        "makes[]": make_key,
        "models[]": model_key,
        "list_price_max": criteria["price_max"],
        "list_price_min": criteria["price_min"],
        "maximum_distance": criteria["radius_miles"],
        "year_min": criteria["year_min"],
        "zip": criteria["zip_code"],
        "stock_type": "all",
        "page_size": 100,
    }
    return BASE_URL + "?" + urlencode(params)


def _parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for card in soup.select("fuse-card[data-listing-id]"):
        listing_id = card["data-listing-id"]
        try:
            details = json.loads(card.get("data-vehicle-details", "{}"))
        except (json.JSONDecodeError, KeyError):
            continue

        year = details.get("year", "")
        make = details.get("make", "")
        model = details.get("model", "")
        trim = details.get("trim", "")

        listings.append({
            "source": "cars.com",
            "id": listing_id,
            "title": f"{year} {make} {model} {trim}".strip(),
            "price": details.get("price"),
            "mileage": details.get("mileage"),
            "year": year,
            "vin": details.get("vin"),
            "stock_type": details.get("stockType"),
            "url": f"https://www.cars.com/vehicledetail/{listing_id}/",
            "dealer": details.get("seller", {}).get("customerId"),
            "location": details.get("seller", {}).get("zip"),
        })
    return listings


async def search(browser, make: str, model: str, criteria: dict) -> list[dict]:
    from browser_fetch import fetch_page
    url = _build_url(make, model, criteria)
    html = await fetch_page(browser, url, wait_seconds=15)
    return _parse(html)
