#!/usr/bin/env python3
"""Send Solis Watch alerts to Cursor Mobile via Automations webhook."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
SITE_URL = "https://poulsbopete.github.io/solis/"


def load_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def cursor_webhook_config() -> tuple[Optional[str], Optional[str]]:
    """Return (webhook_url, bearer_token) from env or .env file."""
    file_env = load_env_file()
    url = os.environ.get("CURSOR_AUTOMATION_WEBHOOK_URL") or file_env.get(
        "CURSOR_AUTOMATION_WEBHOOK_URL"
    )
    token = os.environ.get("CURSOR_AUTOMATION_TOKEN") or file_env.get(
        "CURSOR_AUTOMATION_TOKEN"
    )
    if not url or not token:
        return None, None
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    return url.rstrip("/"), token


def build_payload(new_listings: list[dict], *, max_drive_miles: int = 200) -> dict:
    lines = []
    for item in new_listings:
        price = item.get("price")
        price_s = f"${price:,}" if price else "price TBD"
        dist = item.get("distanceMiles")
        dist_s = f"{dist} mi" if dist is not None else "? mi"
        lines.append(
            f"- {item.get('title', 'Listing')} · {price_s} · "
            f"{item.get('city', '?')} ({dist_s}) · {item.get('url', '')}"
        )

    count = len(new_listings)
    headline = (
        f"{count} new driveable Winnebago listing{'s' if count != 1 else ''} "
        f"within {max_drive_miles} mi"
    )
    return {
        "event": "solis_watch.new_listings",
        "headline": headline,
        "count": count,
        "siteUrl": SITE_URL,
        "maxDriveMiles": max_drive_miles,
        "listings": new_listings,
        "summary": "\n".join(lines),
        "message": f"{headline}:\n" + "\n".join(lines),
    }


def notify_cursor(
    new_listings: list[dict],
    *,
    max_drive_miles: int = 200,
    timeout: int = 20,
) -> bool:
    """
    POST to a Cursor Automation webhook. When the cloud agent finishes,
    Cursor Mobile pushes a notification to your phone.

    Requires CURSOR_AUTOMATION_WEBHOOK_URL and CURSOR_AUTOMATION_TOKEN
    in the environment or .env at repo root.
    """
    if not new_listings:
        return False

    url, token = cursor_webhook_config()
    if not url or not token:
        return False

    payload = build_payload(new_listings, max_drive_miles=max_drive_miles)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"Cursor notify failed: {exc}", file=__import__("sys").stderr)
        return False


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Test Cursor Mobile alert webhook")
    parser.add_argument(
        "--from-pulse",
        action="store_true",
        help="Read newListings from data/watch-pulse.json",
    )
    args = parser.parse_args()

    if args.from_pulse:
        pulse_path = ROOT / "data" / "watch-pulse.json"
        if not pulse_path.exists():
            print("No watch-pulse.json — run local_watch.py first.", file=sys.stderr)
            return 1
        pulse = json.loads(pulse_path.read_text())
        items = pulse.get("newListings") or []
        max_mi = pulse.get("maxDriveMiles", 200)
    else:
        items = [
            {
                "title": "2021 Solis 59PX test alert",
                "price": 69900,
                "city": "Smyrna",
                "distanceMiles": 2500,
                "url": SITE_URL,
            }
        ]
        max_mi = 200

    if not items:
        print("No new listings to notify.")
        return 0

    url, token = cursor_webhook_config()
    if not url or not token:
        print(
            "Set CURSOR_AUTOMATION_WEBHOOK_URL and CURSOR_AUTOMATION_TOKEN in .env",
            file=sys.stderr,
        )
        return 1

    ok = notify_cursor(items, max_drive_miles=max_mi)
    print("Cursor webhook sent — check Cursor Mobile." if ok else "Send failed.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
