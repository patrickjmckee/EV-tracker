"""
One-off raw-data probe: dumps raw listing data from each source so we can
design distance filtering (Cars.com / CarGurus) and the CarMax parser.
Run via the test-sources workflow; prints everything to the job log.
"""
import asyncio
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from browser_fetch import start_browser, stop_browser, fetch_page

SEP = "=" * 70


def load_criteria() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "config", "criteria.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


async def probe_carscom(browser, criteria):
    from bs4 import BeautifulSoup
    from sources import carscom

    print(SEP)
    print("CARS.COM")
    url = carscom._build_url("Hyundai", "Ioniq 5", criteria)
    print("url:", url)
    html = await fetch_page(browser, url, wait_seconds=15)
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("fuse-card[data-listing-id]")
    print(f"cards: {len(cards)}")
    for i, card in enumerate(cards[:3]):
        print(f"--- card {i} full HTML (8k cap) ---")
        print(card.prettify()[:8000])


async def probe_cargurus(browser, criteria):
    from sources import cargurus

    print(SEP)
    print("CARGURUS")
    url = cargurus._build_url("Hyundai", "Ioniq 5", criteria)
    print("url:", url)
    html = await fetch_page(browser, url, wait_seconds=12)
    data = cargurus._extract_remix_context(html)
    try:
        tiles = data["state"]["loaderData"]["routes/($intl).search"]["search"].get("tiles", [])
    except (KeyError, TypeError):
        tiles = []
    print(f"tiles: {len(tiles)}")
    for i, tile in enumerate(tiles[:2]):
        print(f"--- tile {i} raw JSON (10k cap) ---")
        print(json.dumps(tile, indent=1, default=str)[:10000])


async def probe_carmax(browser, criteria):
    from nodriver import cdp

    print(SEP)
    print("CARMAX")
    api_calls = []
    tab = await browser.get("about:blank")

    def on_request(ev, *rest):
        u = ev.request.url
        if "carmax.com" in u and ("api" in u.lower() or "search" in u.lower()):
            api_calls.append(u)

    tab.add_handler(cdp.network.RequestWillBeSent, on_request)

    for target in (
        "https://www.carmax.com/cars/7167",
        "https://www.carmax.com/cars/hyundai/ioniq-5",
    ):
        print(f"--- loading {target} ---")
        try:
            await tab.get(target)
            await asyncio.sleep(12)
            print("final url:", await tab.evaluate("location.href"))
            print("title:", await tab.evaluate("document.title"))
            body = await tab.evaluate("document.body.innerText.slice(0, 600)")
            print("body snippet:", repr(body))
        except Exception as e:
            print(f"probe error: {e!r}")

    print(f"--- captured {len(api_calls)} api-ish requests (deduped by path) ---")
    seen = set()
    for u in api_calls:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        print(u[:600])


async def main():
    criteria = load_criteria()
    browser = await start_browser()
    try:
        for probe in (probe_carscom, probe_cargurus, probe_carmax):
            try:
                await probe(browser, criteria)
            except Exception as e:
                print(f"{probe.__name__} failed: {e!r}")
    finally:
        await stop_browser(browser)


if __name__ == "__main__":
    asyncio.run(main())
