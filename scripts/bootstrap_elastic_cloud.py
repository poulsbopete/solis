#!/usr/bin/env python3
"""Bootstrap a durable Elastic Cloud Serverless project for Solis Watch.

Requires EC_API_KEY in .env (Organization owner / Project Admin).
Creates project "solis-watch" if missing, waits for ready, prints next steps.

Scoped API key creation still uses scripts/create_api_keys.py against the
project Elasticsearch endpoint with admin credentials from .elastic-credentials.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = Path(
    "/home/ubuntu/.cursor/plugins/cache/cursor-public/4331/"
    "f25405c0b7b808fcf320c97889d905ae26152f07/skills/cloud"
)
PROJECT_NAME = "solis-watch"
REGION = "gcp-us-central1"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("EC_API_KEY"):
        raise SystemExit(
            "EC_API_KEY missing. Add it to .env from https://cloud.elastic.co/account/keys"
        )
    create_script = SKILL_ROOT / "create-project" / "scripts" / "create-project.py"
    if not create_script.exists():
        raise SystemExit(f"Cloud create-project script not found at {create_script}")

    cmd = [
        sys.executable,
        str(create_script),
        "create",
        "--type",
        "elasticsearch",
        "--name",
        PROJECT_NAME,
        "--region",
        REGION,
        "--optimized-for",
        "general_purpose",
        "--wait",
    ]
    print("Creating Elastic Cloud Serverless project:", PROJECT_NAME)
    # Run from repo root so credentials save to .elastic-credentials here
    subprocess.check_call(cmd, cwd=str(ROOT))
    print(
        "\nNext:\n"
        "  1. eval $(python3 .../manage-project.py load-credentials --name solis-watch --include-admin)\n"
        "  2. python3 scripts/create_api_keys.py --public-endpoint \"$ELASTICSEARCH_URL\"\n"
        "  3. python3 scripts/seed_elastic.py\n"
        "  4. python3 scripts/update_report_elastic.py && commit data/report-live.json\n"
    )


if __name__ == "__main__":
    main()
