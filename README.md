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
- The page loads live data from Elastic; `data/report.json` is a fallback only

```text
Cursor automation → Elasticsearch (solis-watch)
GitHub Pages      → reads report-current with a read-only API key
```

## Repo layout

- `index.html` / `assets/` — GitHub Pages UI
- `assets/elastic-config.js` — public endpoint + **read-only** API key
- `data/*.json` — seed / offline fallback (not the live source of truth)
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
3. Create scoped keys: `python3 scripts/create_api_keys.py --public-endpoint "$ELASTICSEARCH_URL"`
4. Seed: `python3 scripts/seed_elastic.py`
5. Commit `assets/elastic-config.js` (read-only key only). Never commit `.env` / `.elastic-credentials`.

## Automation

A Cursor cloud automation refreshes listings on a schedule, updates Elasticsearch, and does **not** open PRs or commit JSON. Run status is visible in the Cursor mobile app under Automations.
