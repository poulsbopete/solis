#!/usr/bin/env python3
"""Upsert the current Solis Watch report (+ daily history point) into Elasticsearch.

Intended for the Cursor cloud automation. Reads data/report.json and data/history.json
from the workspace (or paths passed as args) and writes to the solis-watch index.
Does not commit to git.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = "solis-watch"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def es_request(method: str, path: str, body: dict | None = None) -> dict:
    base = os.environ["ELASTICSEARCH_URL"].rstrip("/")
    api_key = os.environ.get("ELASTICSEARCH_API_KEY") or os.environ.get(
        "ELASTICSEARCH_WRITE_API_KEY"
    )
    if not api_key:
        raise SystemExit(
            "Set ELASTICSEARCH_API_KEY or ELASTICSEARCH_WRITE_API_KEY in the environment/.env"
        )
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Elasticsearch {method} {path} failed: {exc.code} {detail}") from exc


def upsert_report(report: dict) -> None:
    body = {
        "doc_type": "report",
        "updated_at": report.get("generatedAt")
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": report,
    }
    es_request("PUT", f"/{INDEX}/_doc/report-current", body)


def upsert_history_point(history: dict, report: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ms = report.get("marketSummary", {})
    snap = {
        "date": today,
        "nationalFloor": ms.get("nationalUsedFloor"),
        "nationalAverage": ms.get("nationalUsedAverage"),
        "nwDealFloor": ms.get("nwDealFloor") or ms.get("nwAgeEligibleFloor"),
        "candidateCount": len(report.get("candidates", [])),
        "primaryCount": sum(1 for c in report.get("candidates", []) if c.get("tier") == "primary"),
        "watchlistCount": sum(
            1 for c in report.get("candidates", []) if c.get("tier") == "watchlist"
        ),
        "flyCount": sum(1 for c in report.get("candidates", []) if c.get("tier") == "fly"),
        "notes": f"Automation snapshot {today}",
    }
    # Prefer an existing same-day snapshot from history.json if present
    for existing in history.get("snapshots", []):
        if existing.get("date") == today:
            snap = existing
            break
    es_request(
        "PUT",
        f"/{INDEX}/_doc/history-{today}",
        {
            "doc_type": "history_point",
            "date": today,
            "updated_at": report.get("generatedAt")
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "payload": snap,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "report.json")
    parser.add_argument("--history", type=Path, default=ROOT / "data" / "history.json")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    if "ELASTICSEARCH_URL" not in os.environ:
        raise SystemExit("ELASTICSEARCH_URL is required")
    report = json.loads(args.report.read_text())
    history = json.loads(args.history.read_text()) if args.history.exists() else {}
    upsert_report(report)
    upsert_history_point(history, report)
    es_request("POST", f"/{INDEX}/_refresh")
    print(
        json.dumps(
            {
                "ok": True,
                "generatedAt": report.get("generatedAt"),
                "candidateCount": len(report.get("candidates", [])),
                "index": INDEX,
            }
        )
    )


if __name__ == "__main__":
    main()
