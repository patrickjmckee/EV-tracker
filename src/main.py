import asyncio
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))

from sources import carscom, autotrader, cargurus
from notify import notify_new_listings

SEEN_FILE = os.path.join(os.path.dirname(__file__), "..", "seen_listings.json")

ENABLE_CARSCOM = os.environ.get("ENABLE_CARSCOM", "true").lower() == "true"
ENABLE_AUTOTRADER = os.environ.get("ENABLE_AUTOTRADER", "true").lower() == "true"
ENABLE_CARGURUS = os.environ.get("ENABLE_CARGURUS", "true").lower() == "true"


def load_criteria() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "config", "criteria.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


async def run_async():
    criteria = load_criteria()
    seen = load_seen()
    all_models = criteria["models"] + criteria.get("also_consider", [])

    from browser_fetch import start_browser, stop_browser
    browser = await start_browser()

    try:
        all_listings = []
        for entry in all_models:
            make, model = entry["make"], entry["model"]
            print(f"  Searching {make} {model}...")

            if ENABLE_CARSCOM:
                try:
                    results = await carscom.search(browser, make, model, criteria)
                    all_listings += results
                    print(f"    cars.com: {len(results)}")
                except Exception as e:
                    print(f"    cars.com error: {e}")

            if ENABLE_AUTOTRADER:
                try:
                    results = await autotrader.search(browser, make, model, criteria)
                    all_listings += results
                    print(f"    autotrader: {len(results)}")
                except Exception as e:
                    print(f"    autotrader error: {e}")

            if ENABLE_CARGURUS:
                try:
                    results = await cargurus.search(browser, make, model, criteria)
                    all_listings += results
                    print(f"    cargurus: {len(results)}")
                except Exception as e:
                    print(f"    cargurus error: {e}")
    finally:
        await stop_browser(browser)

    new_listings = [l for l in all_listings if l.get("id") not in seen]

    if new_listings:
        notify_new_listings(new_listings)
        seen.update(l["id"] for l in new_listings if l.get("id"))
        save_seen(seen)

    print(
        f"Checked {len(all_models)} models, found {len(all_listings)} total, "
        f"{len(new_listings)} new."
    )


def run():
    asyncio.run(run_async())


if __name__ == "__main__":
    run()
