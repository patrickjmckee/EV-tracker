"""
Shared nodriver browser for bypassing Cloudflare on all three sources.
Finds the Playwright Chromium binary automatically.
"""
import asyncio
import os
from pathlib import Path

import nodriver as uc


def _find_chrome() -> str:
    # Check common system Chrome locations first
    for path in ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"]:
        if os.path.isfile(path):
            return path
    # Fall back to Playwright Chromium
    playwright_dir = Path.home() / ".cache" / "ms-playwright"
    for path in sorted(playwright_dir.glob("chromium-*/chrome-linux64/chrome")):
        return str(path)
    raise RuntimeError(
        "No Chrome/Chromium binary found. "
        "Install system Chrome or run: python3 -m playwright install chromium"
    )


async def start_browser() -> uc.Browser:
    return await uc.start(
        headless=False,
        browser_executable_path=_find_chrome(),
        browser_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking"],
    )


async def stop_browser(browser: uc.Browser) -> None:
    try:
        browser.stop()
    except Exception:
        pass
    # Give the event loop a tick to flush pending callbacks
    await asyncio.sleep(0)


async def fetch_page(browser: uc.Browser, url: str, wait_seconds: int = 12) -> str:
    tab = await browser.get(url)
    await asyncio.sleep(wait_seconds)
    return await tab.get_content()
