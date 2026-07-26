#!/usr/bin/env python3
"""Verify Elasticsearch credentials are available to automation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def main() -> None:
    load_env()
    url = os.environ.get("ELASTICSEARCH_URL")
    key = os.environ.get("ELASTICSEARCH_API_KEY") or os.environ.get(
        "ELASTICSEARCH_WRITE_API_KEY"
    )
    sources = []
    if (ROOT / ".elastic-credentials").exists():
        sources.append(".elastic-credentials")
    if (ROOT / ".env").exists():
        sources.append(".env")
    if os.environ.get("ELASTICSEARCH_URL") and not sources:
        sources.append("process environment")

    missing = []
    if not url:
        missing.append("ELASTICSEARCH_URL")
    if not key:
        missing.append("ELASTICSEARCH_API_KEY")

    if missing:
        print("Elasticsearch credentials are NOT configured for this runtime.", file=sys.stderr)
        print(f"Checked: {', '.join(sources) if sources else 'no local files; process env only'}", file=sys.stderr)
        print(f"Missing: {', '.join(missing)}", file=sys.stderr)
        print(
            "\nFor Cursor Cloud automation, add Runtime Secrets to the Solis environment:\n"
            "  https://cursor.com/dashboard/cloud-agents\n"
            "  1. Open Environments → create or edit the environment for poulsbopete/solis\n"
            "  2. Secrets tab → add ELASTICSEARCH_URL and ELASTICSEARCH_API_KEY (write key)\n"
            "  3. Attach that environment to the Solis Watch automation\n"
            "  4. Re-run the automation\n"
            "\nNever commit .env or API keys to git.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        {
            "ok": True,
            "elasticsearchUrl": url,
            "credentialSource": sources or ["process environment"],
            "writeKeyConfigured": bool(key),
        }
    )


if __name__ == "__main__":
    main()
