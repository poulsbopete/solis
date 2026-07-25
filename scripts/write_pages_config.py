#!/usr/bin/env python3
"""Write assets/elastic-config.js from .env (public URL + read-only API key)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for path in (ROOT / ".elastic-credentials", ROOT / ".env"):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def main() -> None:
    load_env()
    endpoint = (
        os.environ.get("ELASTICSEARCH_PUBLIC_URL")
        or os.environ.get("ELASTICSEARCH_URL")
        or ""
    ).rstrip("/")
    api_key = os.environ.get("ELASTICSEARCH_READ_API_KEY") or os.environ.get(
        "ELASTICSEARCH_API_KEY"
    )
    if not endpoint:
        raise SystemExit("Set ELASTICSEARCH_URL or ELASTICSEARCH_PUBLIC_URL in .env")
    if not api_key:
        raise SystemExit(
            "Set ELASTICSEARCH_READ_API_KEY (recommended) or ELASTICSEARCH_API_KEY in .env"
        )
    using_write = "ELASTICSEARCH_READ_API_KEY" not in os.environ and bool(
        os.environ.get("ELASTICSEARCH_API_KEY")
    )
    if using_write:
        print(
            "WARNING: Using ELASTICSEARCH_API_KEY for Pages. Create a read-only key in "
            "Kibana and set ELASTICSEARCH_READ_API_KEY instead."
        )
    config_path = ROOT / "assets" / "elastic-config.js"
    config_path.write_text(
        "\n".join(
            [
                "// Public read config for GitHub Pages. Read-only API key scoped to solis-watch.",
                "window.SOLIS_ELASTIC = {",
                f'  endpoint: "{endpoint}",',
                '  index: "solis-watch",',
                '  reportId: "report-current",',
                f'  apiKey: "{api_key}"',
                "};",
                "",
            ]
        )
    )
    print(f"Wrote {config_path}")


if __name__ == "__main__":
    main()
