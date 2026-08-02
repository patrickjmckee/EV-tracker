"""
CarMax store-scoped search via nodriver.
Inventory pages are /cars/{storeId}/{make}/{model-slug}; tiles are rendered
client-side (React/MUI), keyed by /car/{stockNumber} detail links. Results
are store-scoped, so they're inherently within radius.

CarMax URLs carry no price/year filters, and pages with no exact matches can
show "similar" vehicles of other models -- both are filtered here in code.
"""
import re

from bs4 import BeautifulSoup

BASE_URL = "https://www.carmax.com/cars"

_PRICE_RE = re.compile(r"\$([\d,]+)")
_MILEAGE_RE = re.compile(r"([\d.]+)K\s*mi", re.I)
_YEAR_RE = re.compile(r"^(?:19|20)\d{2}\b")
_STOCK_RE = re.compile(r"/car/(\d+)")
# Smallest ancestor holding a price is the tile root; anything with this much
# text is a grid/page container we climbed past, not a tile.
_MAX_TILE_TEXT = 800


def _slug(text: str) -> str:
    return re.sub(r"\s+", "-", text.strip().lower())


def _build_url(make: str, model: str, criteria: dict) -> str:
    store = criteria["carmax_store_id"]
    return f"{BASE_URL}/{store}/{_slug(make)}/{_slug(model)}"


def _store_name(soup: BeautifulSoup) -> str | None:
    # <title>Used Hyundai Ioniq 5 at CarMax Salt Lake (South Jordan) for sale</title>
    title = soup.title.string if soup.title else ""
    m = re.search(r"at (CarMax .+?) for sale", title or "")
    return m.group(1) if m else None


def _parse(html: str, make: str, model: str, criteria: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    store_name = _store_name(soup) or f"CarMax store {criteria['carmax_store_id']}"

    tiles: dict[str, dict] = {}
    for a in soup.select('a[href*="/car/"]'):
        m = _STOCK_RE.search(a.get("href", ""))
        if not m:
            continue
        stock = m.group(1)
        info = tiles.setdefault(stock, {"title": None, "text": ""})
        img = a.find("img")
        if img and img.get("alt") and not info["title"]:
            info["title"] = img["alt"].strip()
        if not info["text"]:
            for parent in a.parents:
                text = parent.get_text(" ", strip=True)
                if len(text) > _MAX_TILE_TEXT:
                    break
                if "$" in text:
                    info["text"] = text
                    break

    model_words = _slug(model).replace("-", " ")
    listings = []
    for stock, info in tiles.items():
        title = info["title"] or ""
        # "Similar matches" tiles are other models entirely; skip them.
        if model_words not in title.lower():
            continue

        price_m = _PRICE_RE.search(info["text"])
        price = int(price_m.group(1).replace(",", "")) if price_m else None
        mileage_m = _MILEAGE_RE.search(info["text"])
        mileage = int(float(mileage_m.group(1)) * 1000) if mileage_m else None
        year_m = _YEAR_RE.match(title)
        year = int(year_m.group(0)) if year_m else None

        if year and year < criteria["year_min"]:
            continue
        if price and not (criteria["price_min"] <= price <= criteria["price_max"]):
            continue

        listings.append({
            "source": "carmax",
            "id": f"carmax-{stock}",
            "title": title,
            "price": f"${price:,}" if price else None,
            "mileage": str(mileage) if mileage is not None else None,
            "year": str(year) if year else None,
            "vin": None,
            "stock_type": "Used",
            "url": f"https://www.carmax.com/car/{stock}",
            "dealer": store_name,
            "location": store_name,
            "distance_miles": None,
        })
    return listings


async def search(browser, make: str, model: str, criteria: dict) -> list[dict]:
    from browser_fetch import fetch_page

    if not criteria.get("carmax_store_id"):
        return []
    url = _build_url(make, model, criteria)
    html = await fetch_page(browser, url, wait_seconds=12)
    return _parse(html, make, model, criteria)
