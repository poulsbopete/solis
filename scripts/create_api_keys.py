#!/usr/bin/env python3
"""Create scoped read/write API keys for the solis-watch index.

Requires admin-capable credentials:
  ELASTICSEARCH_URL
  ELASTICSEARCH_USERNAME / ELASTICSEARCH_PASSWORD
    or ELASTICSEARCH_API_KEY with manage_security

Writes:
  .elastic-credentials   (write key + endpoint — gitignored)
  .env                   (when keys are minted locally)

Never write API keys into tracked files. Pages loads data/report-live.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.error
import urllib.request
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


def auth_header() -> str:
    api_key = os.environ.get("ELASTICSEARCH_API_KEY")
    if api_key and os.environ.get("USE_API_KEY_FOR_ADMIN") == "1":
        return f"ApiKey {api_key}"
    user = os.environ.get("ELASTICSEARCH_USERNAME")
    password = os.environ.get("ELASTICSEARCH_PASSWORD")
    if user and password:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        return f"Basic {token}"
    if api_key:
        return f"ApiKey {api_key}"
    raise SystemExit(
        "Need ELASTICSEARCH_USERNAME/PASSWORD or ELASTICSEARCH_API_KEY for key creation"
    )


def es_request(method: str, path: str, body: dict | None = None) -> dict:
    base = os.environ["ELASTICSEARCH_URL"].rstrip("/")
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": auth_header(),
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


def create_key(name: str, privileges: list[str]) -> dict:
    body = {
        "name": name,
        "role_descriptors": {
            name.replace("-", "_"): {
                "cluster": ["monitor"],
                "indices": [
                    {
                        "names": [INDEX],
                        "privileges": privileges,
                    }
                ],
            }
        },
    }
    return es_request("POST", "/_security/api_key", body)


def write_credentials(endpoint: str, write_encoded: str, read_encoded: str) -> None:
    cred_path = ROOT / ".elastic-credentials"
    cred_path.write_text(
        "\n".join(
            [
                "# solis-watch",
                f"ELASTICSEARCH_URL={endpoint}",
                f"ELASTICSEARCH_API_KEY={write_encoded}",
                f"ELASTICSEARCH_WRITE_API_KEY={write_encoded}",
                f"ELASTICSEARCH_READ_API_KEY={read_encoded}",
                "",
            ]
        )
    )
    print(f"Wrote {cred_path} (gitignored)")


def is_serverless() -> bool:
    try:
        info = es_request("GET", "/")
        return info.get("version", {}).get("build_flavor") == "serverless"
    except SystemExit:
        return ".elastic.cloud" in os.environ.get("ELASTICSEARCH_URL", "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-endpoint",
        help="Public HTTPS endpoint for Pages (defaults to ELASTICSEARCH_URL)",
    )
    args = parser.parse_args()
    load_env()
    if "ELASTICSEARCH_URL" not in os.environ:
        raise SystemExit("ELASTICSEARCH_URL is required")
    endpoint = os.environ["ELASTICSEARCH_URL"].rstrip("/")
    public_endpoint = (args.public_endpoint or endpoint).rstrip("/")

    if is_serverless() and os.environ.get("ELASTICSEARCH_USERNAME") is None:
        read_key = os.environ.get("ELASTICSEARCH_READ_API_KEY")
        if not read_key:
            kb = endpoint.replace(".es.", ".kb.", 1)
            raise SystemExit(
                "Elastic Serverless + API key auth cannot mint scoped child keys.\n"
                f"Create a read-only API key in Kibana:\n"
                f"  {kb}/app/management/security/api_keys\n"
                "Role descriptor JSON:\n"
                '  {"solis_reader":{"cluster":["monitor"],"indices":[{"names":["solis-watch"],'
                '"privileges":["read","view_index_metadata"]}]}}\n'
                "Add the encoded key to .env as ELASTICSEARCH_READ_API_KEY for sync_pages_cache.py.\n"
                "Never commit API keys to git."
            )
        write_credentials(endpoint, os.environ.get("ELASTICSEARCH_API_KEY", ""), read_key)
        print("Read key loaded from .env. Pages uses data/report-live.json — no git commit needed.")
        return

    write_key = create_key(
        "solis-watch-write",
        [
            "create_index",
            "write",
            "create",
            "index",
            "read",
            "view_index_metadata",
            "manage",
        ],
    )
    read_key = create_key("solis-watch-read", ["read", "view_index_metadata"])
    write_credentials(endpoint, write_key["encoded"], read_key["encoded"])
    # Also refresh .env for local scripts
    env_path = ROOT / ".env"
    existing = env_path.read_text() if env_path.exists() else ""
    lines = [
        f"ELASTICSEARCH_URL={endpoint}",
        f"ELASTICSEARCH_API_KEY={write_key['encoded']}",
        f"ELASTICSEARCH_WRITE_API_KEY={write_key['encoded']}",
        f"ELASTICSEARCH_READ_API_KEY={read_key['encoded']}",
        f"ELASTICSEARCH_PUBLIC_URL={public_endpoint}",
    ]
    # Preserve EC_API_KEY if present
    for line in existing.splitlines():
        if line.startswith("EC_API_KEY=") or line.startswith("EC_BASE_URL="):
            lines.insert(0, line)
    env_path.write_text("\n".join(lines) + "\n")
    print(f"Updated {env_path}")
    print("API keys created.")


if __name__ == "__main__":
    main()
