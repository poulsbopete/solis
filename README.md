# Solis Watch

Living buyer report for a used **Winnebago Solis** near Washington State.

**Live report:** https://poulsbopete.github.io/solis/

## Criteria

| Field | Value |
| --- | --- |
| Budget | ~$60,000 |
| Down payment | ~$20,000 |
| Age | Soft preference ≤ 2021 — list any year if it’s a good deal |
| Radius | Prefer ≤ 500 miles of Washington |
| Horizon | Price outlook to October 2026 |
| Data store | Elasticsearch index `solis-watch` |

## Architecture

- GitHub Pages hosts the static UI only
- Cursor cloud automation refreshes listings and **upserts Elasticsearch** (`report-current`)
- The page loads `data/report-live.json` (same-origin cache synced after each upsert)

```text
Cursor automation → Elasticsearch (solis-watch) → data/report-live.json → GitHub Pages
```

## Repo layout

- `index.html` / `assets/` — GitHub Pages UI
- `data/report-live.json` — Pages cache (committed after each automation run)
- `data/*.json` — seed / offline fallback
- `scripts/seed_elastic.py` — create index + seed from JSON
- `scripts/update_report_elastic.py` — automation upsert helper
- `scripts/create_api_keys.py` — create scoped read/write keys
- `scripts/bootstrap_elastic_cloud.py` — create a durable Elastic Cloud Serverless project
- `AGENTS.md` — instructions for the Cursor cloud automation

## Local preview

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

## Elastic setup

1. Copy `.env.example` → `.env` and set `EC_API_KEY` (from https://cloud.elastic.co/account/keys) for a durable personal project, **or** point `ELASTICSEARCH_URL` at an existing personal cluster.
2. For a new Serverless project: `python3 scripts/bootstrap_elastic_cloud.py`
3. Add `ELASTICSEARCH_URL` and `ELASTICSEARCH_API_KEY` (write) to `.env`
4. Seed (or re-seed): `python3 scripts/seed_elastic.py`
5. Never commit `.env`, `.elastic-credentials`, or any API key

## Automation

A Cursor cloud automation refreshes listings on a schedule, updates Elasticsearch, and pushes `data/report-live.json` to `main`.

**Required:** attach a [Cursor Cloud Environment](https://cursor.com/dashboard/cloud-agents) to the automation with Runtime Secrets:

- `ELASTICSEARCH_URL`
- `ELASTICSEARCH_API_KEY` (write key)

See `AGENTS.md` → “Cursor Cloud automation setup” and run `python3 scripts/check_elastic_credentials.py` to verify.
