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
    candidates = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        # Windows (local dev): Chrome, then Edge (also Chromium, works with CDP)
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    # Fall back to Playwright Chromium
    for playwright_dir in [
        Path.home() / ".cache" / "ms-playwright",
        Path(os.path.expandvars("%LOCALAPPDATA%")) / "ms-playwright",
    ]:
        for path in sorted(playwright_dir.glob("chromium-*/chrome-linux64/chrome")):
            return str(path)
        for path in sorted(playwright_dir.glob("chromium-*/chrome-win*/chrome.exe")):
            return str(path)
    raise RuntimeError(
        "No Chrome/Chromium binary found. "
        "Install system Chrome or run: python3 -m playwright install chromium"
    )


async def start_browser() -> uc.Browser:
    # Attach to an already-running Chrome instead of spawning one. Needed for
    # local dev on Windows, where nodriver's own spawn never sees the CDP
    # socket (Chrome re-execs as a launcher that exits immediately). Launch
    # Chrome yourself with --remote-debugging-port=<port> and a scratch
    # --user-data-dir, then set NODRIVER_ATTACH=127.0.0.1:<port>.
    attach = os.environ.get("NODRIVER_ATTACH")
    if attach:
        host, _, port = attach.partition(":")
        return await uc.start(
            host=host,
            port=int(port),
            browser_executable_path=_find_chrome(),
        )

    # On a cold machine (fresh CI runner), Chrome's first launch can take
    # longer to expose its DevTools socket than nodriver waits, raising
    # "Failed to connect to browser". Retry: the relaunch hits warm caches.
    last_exc = None
    for attempt in range(1, 4):
        try:
            return await uc.start(
                headless=False,
                browser_executable_path=_find_chrome(),
                browser_args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking"],
            )
        except Exception as e:
            last_exc = e
            print(f"Browser start attempt {attempt}/3 failed: {e}")
            await asyncio.sleep(5)
    raise last_exc


async def stop_browser(browser: uc.Browser) -> None:
    # An attached browser isn't ours to kill; leave it running.
    if os.environ.get("NODRIVER_ATTACH"):
        return
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
