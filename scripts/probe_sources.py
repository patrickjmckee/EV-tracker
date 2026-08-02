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
    # v2: CDP request capture caught nothing; read the page's own resource
    # timing log instead, then re-fetch the search API from page context.
    print(SEP)
    print("CARMAX v2")
    tab = await browser.get("https://www.carmax.com/cars/7167")
    await asyncio.sleep(15)

    js = r"""
    (async () => {
      const urls = performance.getEntriesByType('resource').map(e => e.name);
      const interesting = urls.filter(u =>
        /carmax\.com/.test(u)
        && /api|search|inventory|vehicles|graphql/i.test(u)
        && !/\.(js|css|png|jpe?g|svg|woff2?|gif)([?#]|$)/i.test(u));
      const out = {total_resources: urls.length, interesting: interesting.slice(0, 40)};
      const cand = interesting.find(u => /search|vehicles|inventory/i.test(u));
      if (cand) {
        try {
          const r = await fetch(cand, {headers: {accept: 'application/json'}});
          out.candidate = cand;
          out.status = r.status;
          out.body = (await r.text()).slice(0, 4000);
        } catch (e) { out.fetchError = String(e); }
      }
      return JSON.stringify(out);
    })()
    """
    result = await tab.evaluate(js, await_promise=True)
    print(result if isinstance(result, str) else json.dumps(result, default=str)[:8000])

    print("--- combined store+model path test ---")
    await tab.get("https://www.carmax.com/cars/7167/hyundai/ioniq-5")
    await asyncio.sleep(8)
    print("final url:", await tab.evaluate("location.href"))
    print("title:", await tab.evaluate("document.title"))


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
