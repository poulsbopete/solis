#!/usr/bin/env python3
"""Pull report-current from Elasticsearch and write data/report-live.json for GitHub Pages.

Elastic Serverless does not expose cluster CORS settings, so browsers on GitHub Pages
cannot call the ES endpoint directly. This same-origin cache is updated by automation
after each Elasticsearch upsert.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = "solis-watch"
REPORT_ID = "report-current"
DEFAULT_OUT = ROOT / "data" / "report-live.json"


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


def fetch_report_payload() -> dict:
    base = os.environ["ELASTICSEARCH_URL"].rstrip("/")
    api_key = (
        os.environ.get("ELASTICSEARCH_READ_API_KEY")
        or os.environ.get("ELASTICSEARCH_API_KEY")
        or os.environ.get("ELASTICSEARCH_WRITE_API_KEY")
    )
    if not api_key:
        raise SystemExit(
            "Set ELASTICSEARCH_READ_API_KEY or ELASTICSEARCH_API_KEY in the environment/.env"
        )
    req = urllib.request.Request(
        f"{base}/{INDEX}/_doc/{REPORT_ID}",
        headers={
            "Authorization": f"ApiKey {api_key}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            doc = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Elasticsearch GET failed: {exc.code} {detail}") from exc
    payload = doc.get("_source", {}).get("payload")
    if not doc.get("found") or not payload:
        raise SystemExit("report-current missing payload")
    return payload


def write_pages_cache(report: dict, out_path: Path = DEFAULT_OUT) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output path (default: data/report-live.json)",
    )
    args = parser.parse_args()
    load_env()
    if "ELASTICSEARCH_URL" not in os.environ:
        raise SystemExit("ELASTICSEARCH_URL is required")
    report = fetch_report_payload()
    path = write_pages_cache(report, args.out)
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(path.relative_to(ROOT)),
                "generatedAt": report.get("generatedAt"),
                "candidateCount": len(report.get("candidates", [])),
            }
        )
    )


if __name__ == "__main__":
    main()
