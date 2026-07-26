#!/usr/bin/env python3
"""Deprecated: GitHub Pages no longer loads Elasticsearch from the browser.

Pages reads data/report-live.json (same-origin cache). Keys must stay in .env only.
"""

from __future__ import annotations

import sys


def main() -> None:
    sys.exit(
        "write_pages_config.py is deprecated.\n"
        "Pages loads data/report-live.json — do not commit API keys to git.\n"
        "After upsert: python3 scripts/update_report_elastic.py (writes the cache)."
    )


if __name__ == "__main__":
    main()
