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
    # v3: store+model URL confirmed working; no API discoverable, so dump
    # the listing-tile DOM structure to design an HTML parser.
    print(SEP)
    print("CARMAX v3")
    tab = await browser.get("https://www.carmax.com/cars/7167/hyundai/ioniq-5")
    await asyncio.sleep(15)
    print("title:", await tab.evaluate("document.title"))

    js = r"""
    (() => {
      const out = {};
      const link = document.querySelector('a[href*="/car/"]');
      if (!link) { out.noLinks = true; return JSON.stringify(out); }
      let tile = null;
      const chain = [];
      for (let p = link; p && p !== document.body; p = p.parentElement) {
        chain.push(p.tagName + '.' + String(p.className).slice(0, 60));
        if (!tile && /\$\s?[\d,]+/.test(p.innerText || '')) tile = p;
      }
      out.chain = chain;
      if (tile) {
        out.tileText = (tile.innerText || '').slice(0, 800);
        out.tileHTML = tile.outerHTML.slice(0, 9000);
      }
      return JSON.stringify(out);
    })()
    """
    result = await tab.evaluate(js)
    print(result if isinstance(result, str) else json.dumps(result, default=str)[:12000])


async def main():
    criteria = load_criteria()
    browser = await start_browser()
    try:
        # carscom/cargurus probes answered (seller zip / tile distance field);
        # only CarMax still needs API discovery.
        for probe in (probe_carmax,):
            try:
                await probe(browser, criteria)
            except Exception as e:
                print(f"{probe.__name__} failed: {e!r}")
    finally:
        await stop_browser(browser)


if __name__ == "__main__":
    asyncio.run(main())
