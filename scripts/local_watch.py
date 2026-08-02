#!/usr/bin/env python3
"""
Light local watcher for driveable Winnebago Solis / Travato listings.

Compares current in-radius inventory to the last run and alerts on NEW listings.
Designed for hourly launchd/cron on your laptop — not the GitHub Pages report.

Usage:
  python3 scripts/local_watch.py              # check + alert if new
  python3 scripts/local_watch.py --verbose    # print all local matches
  python3 scripts/local_watch.py --no-notify  # skip desktop notification
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from cudl_client import search_vehicles  # noqa: E402

CONFIG_PATH = ROOT / "scripts" / "watch_config.json"
REPORT_PATH = ROOT / "data" / "report.json"
CUDL_DEALERS_PATH = ROOT / "data" / "cudl-dealers.json"


@dataclass
class Listing:
    id: str
    source: str
    model: str
    title: str
    year: Optional[int]
    price: Optional[int]
    miles: Optional[int]
    city: str
    distanceMiles: Optional[float]
    url: str
    seller: str = ""

    def key(self) -> str:
        return f"{self.source}:{self.id}"

    def to_public(self) -> dict:
        return asdict(self)


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def load_config() -> dict:
    cfg = load_json(CONFIG_PATH, {})
    cfg.setdefault("zipCode", "98370")
    cfg.setdefault("maxDriveMiles", 200)
    cfg.setdefault("models", ["Solis", "Travato"])
    cfg.setdefault("stateFile", ".local/watch-state.json")
    cfg.setdefault("logFile", ".local/watch-log.jsonl")
    cfg.setdefault("notify", True)
    cfg.setdefault("sources", {})
    return cfg


def matches_model(text: str, models: list[str]) -> bool:
    t = (text or "").lower()
    return any(m.lower() in t for m in models)


def normalize_listing(
    *,
    id_,
    source,
    title,
    url,
    model="",
    year=None,
    price=None,
    miles=None,
    city="",
    distance=None,
    seller="",
    models_filter=None,
) -> Optional[Listing]:
    if models_filter and not matches_model(f"{title} {model}", models_filter):
        return None
    if distance is not None and distance > load_config().get("maxDriveMiles", 200):
        return None
    detected = model
    if not detected and models_filter:
        for m in models_filter:
            if m.lower() in (title or "").lower():
                detected = m
                break
    return Listing(
        id=str(id_),
        source=source,
        model=detected or "Winnebago",
        title=title or "",
        year=year,
        price=int(price) if price is not None else None,
        miles=int(miles) if miles is not None else None,
        city=city,
        distanceMiles=round(distance, 1) if distance is not None else None,
        url=url,
        seller=seller,
    )


def cudl_vehicle_to_listing(v: dict, models: list[str]) -> Optional[Listing]:
    name = v.get("ItemName") or v.get("MakeModel") or ""
    return normalize_listing(
        id_=v.get("ItemID"),
        source="cudl",
        title=name,
        url=f"https://becu.cudlautosmart.com/VehicleDetails?ItemID={v.get('ItemID')}",
        year=v.get("ItemYear"),
        price=v.get("PriceRetail"),
        miles=v.get("Usage"),
        city=(v.get("OwnerCityState") or "").split(",")[0],
        distance=v.get("Distance"),
        seller=v.get("OwnerName") or v.get("DealerName"),
        models_filter=models,
    )


def fetch_cudl_local(session: requests.Session, cfg: dict) -> list[Listing]:
    if not cfg.get("sources", {}).get("cudlNetwork", True):
        return []
    zip_code = cfg["zipCode"]
    radius = cfg["maxDriveMiles"]
    models = cfg["models"]
    found: dict[str, Listing] = {}

    for make in cfg.get("makes", ["Winnebago"]):
        for v in search_vehicles(session, zip_code, radius, make=make):
            item = cudl_vehicle_to_listing(v, models)
            if item:
                found[item.key()] = item

    for term in models:
        for v in search_vehicles(session, zip_code, radius, search_string=f"Winnebago {term}"):
            item = cudl_vehicle_to_listing(v, models)
            if item:
                found[item.key()] = item

    return list(found.values())


def priority_dealer_codes(cfg: dict) -> list[tuple[str, str]]:
    patterns = [p.lower() for p in cfg.get("priorityDealerNamePatterns", [])]
    max_mi = cfg["maxDriveMiles"]
    dealers = load_json(CUDL_DEALERS_PATH, {}).get("dealers", [])
    out = []
    for d in dealers:
        if d.get("distanceMiles", 999) > max_mi:
            continue
        name = (d.get("name") or "").lower()
        if patterns and not any(p in name for p in patterns):
            continue
        out.append((d["clientCode"], d["name"]))
    return out


def fetch_cudl_dealers(session: requests.Session, cfg: dict) -> list[Listing]:
    if not cfg.get("sources", {}).get("cudlPriorityDealers", True):
        return []
    zip_code = cfg["zipCode"]
    radius = cfg["maxDriveMiles"]
    models = cfg["models"]
    found: dict[str, Listing] = {}

    for code, dealer_name in priority_dealer_codes(cfg):
        for v in search_vehicles(session, zip_code, radius, dealer_client_code=code):
            item = cudl_vehicle_to_listing(v, models)
            if item:
                item.seller = dealer_name
                found[item.key()] = item

    return list(found.values())


def fetch_report_locals(cfg: dict, session: requests.Session) -> list[Listing]:
    if not cfg.get("sources", {}).get("reportSnapshot", True):
        return []
    report = load_json(REPORT_PATH, {})
    models = cfg["models"]
    max_mi = cfg["maxDriveMiles"]
    out = []
    for c in report.get("candidates", []):
        if c.get("status") != "active":
            continue
        if (c.get("distanceMiles") or 0) > max_mi:
            continue
        model = c.get("model", "Solis")
        if model not in models:
            continue
        url = c.get("url", "")
        if url:
            try:
                r = session.head(url, allow_redirects=True, timeout=15)
                if r.status_code >= 400:
                    continue
            except requests.RequestException:
                continue
        item = normalize_listing(
            id_=c["id"],
            source="report",
            title=f"{c.get('year')} {model} {c.get('trim')}",
            url=url,
            model=model,
            year=c.get("year"),
            price=c.get("price"),
            miles=c.get("miles"),
            city=c.get("city", ""),
            distance=c.get("distanceMiles"),
            seller=c.get("seller", ""),
        )
        if item:
            out.append(item)
    return out


def fetch_craigslist(cfg: dict, session: requests.Session) -> list[Listing]:
    if not cfg.get("sources", {}).get("craigslistRss", True):
        return []
    models = cfg["models"]
    out = []
    query = quote("winnebago solis OR winnebago travato")
    for site in cfg.get("craigslistSites", ["seattle"]):
        url = f"https://{site}.craigslist.org/search/rva?query={query}&max_distance={cfg['maxDriveMiles']}&postal={cfg['zipCode']}&format=rss"
        try:
            r = session.get(url, timeout=20, headers={"User-Agent": "SolisWatch/1.0"})
            if r.status_code != 200 or "<rss" not in r.text[:500]:
                continue
            root = ET.fromstring(r.text)
            ns = {"r": "http://web.resource.org/rss/1.0/"}
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item"):
                title = item.findtext("title") or ""
                link = item.findtext("link") or ""
                guid = item.findtext("guid") or link
                if not matches_model(title, models):
                    continue
                price = None
                m = re.search(r"\$([\d,]+)", title)
                if m:
                    price = int(m.group(1).replace(",", ""))
                listing = normalize_listing(
                    id_=guid,
                    source=f"craigslist-{site}",
                    title=title,
                    url=link,
                    city=site.title(),
                    price=price,
                    models_filter=None,
                )
                if listing:
                    out.append(listing)
        except (requests.RequestException, ET.ParseError):
            continue
    return out


def merge_listings(*groups: list[Listing]) -> list[Listing]:
    merged: dict[str, Listing] = {}
    for group in groups:
        for item in group:
            merged[item.key()] = item
    return sorted(merged.values(), key=lambda x: (x.distanceMiles or 9999, x.price or 999999))


def load_state(path: Path) -> dict:
    return load_json(path, {"seen": {}, "lastRun": None})


def save_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def append_log(path: Path, entry: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def diff_listings(previous: dict, current: list[Listing]) -> tuple[list[Listing], list[str]]:
    current_keys = {x.key(): x for x in current}
    new_items = [x for k, x in current_keys.items() if k not in previous]
    removed = [k for k in previous if k not in current_keys]
    return new_items, removed


def desktop_notify(title: str, message: str):
    try:
        if sys.platform == "darwin":
            script = f'display notification {json.dumps(message)} with title {json.dumps(title)}'
            subprocess.run(["osascript", "-e", script], check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["notify-send", title, message], check=False)
    except FileNotFoundError:
        pass


def fmt_listing(x: Listing) -> str:
    dist = f"{x.distanceMiles} mi" if x.distanceMiles is not None else "? mi"
    price = f"${x.price:,}" if x.price else "price TBD"
    return f"{x.title} · {price} · {x.city} ({dist}) · {x.url}"


def main():
    parser = argparse.ArgumentParser(description="Local driveable Solis/Travato watcher")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print all local matches")
    parser.add_argument("--no-notify", action="store_true", help="Skip desktop notification")
    args = parser.parse_args()

    cfg = load_config()
    state_path = ROOT / cfg["stateFile"]
    log_path = ROOT / cfg["logFile"]
    state = load_state(state_path)
    previous_seen = state.get("seen", {})

    session = requests.Session()
    session.headers.update({"User-Agent": "SolisWatch-Local/1.0 (+personal buyer)"})

    listings = merge_listings(
        fetch_cudl_local(session, cfg),
        fetch_cudl_dealers(session, cfg),
        fetch_report_locals(cfg, session),
        fetch_craigslist(cfg, session),
    )

    new_items, removed = diff_listings(previous_seen, listings)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for item in listings:
        previous_seen[item.key()] = {**item.to_public(), "lastSeen": now}

    for key in removed:
        previous_seen.pop(key, None)

    state["seen"] = previous_seen
    state["lastRun"] = now
    state["localCount"] = len(listings)
    save_state(state_path, state)

    log_entry = {
        "at": now,
        "localCount": len(listings),
        "newCount": len(new_items),
        "removedCount": len(removed),
        "new": [x.to_public() for x in new_items],
    }
    append_log(log_path, log_entry)

    print(f"[{now}] Local driveable ({cfg['maxDriveMiles']} mi): {len(listings)} active, {len(new_items)} new")

    if args.verbose:
        for x in listings:
            print(" ", fmt_listing(x))

    if new_items:
        print("\nNEW listings:")
        for x in new_items:
            line = fmt_listing(x)
            print(" ", line)
        if cfg.get("notify") and not args.no_notify:
            summary = new_items[0].title
            if len(new_items) > 1:
                summary += f" (+{len(new_items) - 1} more)"
            desktop_notify("Solis Watch — new local listing", summary)
    elif not args.verbose:
        print("  No new local listings since last run.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
