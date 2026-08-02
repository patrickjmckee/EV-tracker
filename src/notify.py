import os
import requests

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")  # e.g. "patrick-ev-alerts-x7k2"
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh")  # override for self-hosted/local testing
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

DISCORD_MESSAGE_LIMIT = 2000
DISCORD_HEADER = "New EV matches:"


def notify_new_listings(listings: list[dict]) -> None:
    if not listings:
        return

    for listing in listings:
        try:
            _send_ntfy(listing)
        except requests.RequestException as e:
            print(f"ntfy notification failed for listing {listing.get('id')}: {e}")

    _send_discord(listings)


def _where(listing: dict) -> str:
    where = str(listing.get("location") or "?")
    d = listing.get("distance_miles")
    if isinstance(d, (int, float)):
        where += f", {d:.0f} mi"
    return where


def _send_ntfy(listing: dict) -> None:
    if not NTFY_TOPIC:
        return
    title = listing.get("title", "New EV listing")
    price = listing.get("price", "?")
    requests.post(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=f"{title} - {price} ({_where(listing)})".encode("utf-8"),
        headers={
            "Title": "New EV match",
            "Click": listing.get("url", ""),
            "Priority": "default",
        },
        timeout=10,
    )


def _chunk_discord_lines(lines: list[str]) -> list[str]:
    # Groups lines into multiple messages so nothing is silently dropped past the 2000 char limit.
    chunks = []
    current: list[str] = []
    current_len = len(DISCORD_HEADER) + 1

    for line in lines:
        line_len = len(line) + 1  # + newline
        if current and current_len + line_len > DISCORD_MESSAGE_LIMIT:
            chunks.append(current)
            current = []
            current_len = 0
        if line_len > DISCORD_MESSAGE_LIMIT:
            line = line[: DISCORD_MESSAGE_LIMIT - 1]
            line_len = len(line) + 1
        current.append(line)
        current_len += line_len

    if current:
        chunks.append(current)

    messages = []
    for i, chunk_lines in enumerate(chunks):
        prefix = f"{DISCORD_HEADER}\n" if i == 0 else ""
        messages.append(prefix + "\n".join(chunk_lines))
    return messages


def _send_discord(listings: list[dict]) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    lines = [
        f"**{l.get('title')}** - {l.get('price')} - {_where(l)} - [{l.get('source')}]({l.get('url')})"
        for l in listings
    ]
    for i, content in enumerate(_chunk_discord_lines(lines)):
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": content}, timeout=10)
        except requests.RequestException as e:
            print(f"Discord notification failed (message {i + 1}): {e}")
