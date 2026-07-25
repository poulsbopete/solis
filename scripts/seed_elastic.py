#!/usr/bin/env python3
"""Create/seed the solis-watch Elasticsearch index from local JSON files."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = "solis-watch"


def load_dotenv(path: Path, override: bool = False) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override or key not in os.environ:
            os.environ[key] = value


def load_env() -> None:
    load_dotenv(ROOT / ".elastic-credentials")
    load_dotenv(ROOT / ".env", override=True)


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


def ensure_index() -> None:
    try:
        es_request("GET", f"/{INDEX}")
        print(f"Index {INDEX} already exists")
        return
    except SystemExit as exc:
        if "404" not in str(exc):
            raise
    mapping = {
        "mappings": {
            "properties": {
                "doc_type": {"type": "keyword"},
                "updated_at": {"type": "date"},
                "date": {"type": "date", "format": "yyyy-MM-dd||strict_date_optional_time"},
                "payload": {"type": "object", "enabled": True},
            }
        },
    }
    es_request("PUT", f"/{INDEX}", mapping)
    print(f"Created index {INDEX}")


def seed_report(report_path: Path) -> None:
    report = json.loads(report_path.read_text())
    body = {
        "doc_type": "report",
        "updated_at": report.get("generatedAt"),
        "payload": report,
    }
    es_request("PUT", f"/{INDEX}/_doc/report-current", body)
    print(f"Upserted report-current generatedAt={report.get('generatedAt')}")


def seed_history(history_path: Path) -> None:
    history = json.loads(history_path.read_text())
    count = 0
    for snap in history.get("snapshots", []):
        date = snap["date"]
        body = {
            "doc_type": "history_point",
            "date": date,
            "updated_at": f"{date}T12:00:00Z",
            "payload": snap,
        }
        es_request("PUT", f"/{INDEX}/_doc/history-{date}", body)
        count += 1
    for series in history.get("priceSeries", []):
        cid = series["id"]
        for point in series.get("points", []):
            date = point["date"]
            doc_id = f"price-{cid}-{date}"
            body = {
                "doc_type": "price_point",
                "date": date,
                "candidate_id": cid,
                "updated_at": f"{date}T12:00:00Z",
                "payload": point,
            }
            es_request("PUT", f"/{INDEX}/_doc/{doc_id}", body)
            count += 1
    print(f"Upserted {count} history/price documents")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "data" / "report.json",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=ROOT / "data" / "history.json",
    )
    args = parser.parse_args()
    load_env()
    if "ELASTICSEARCH_URL" not in os.environ:
        raise SystemExit("ELASTICSEARCH_URL is required")
    ensure_index()
    seed_report(args.report)
    seed_history(args.history)
    es_request("POST", f"/{INDEX}/_refresh")
    print("Seed complete")


if __name__ == "__main__":
    main()
