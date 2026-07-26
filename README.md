# Solis Watch

Living buyer report for a used **Winnebago Solis** near Washington State.

**Live report:** https://poulsbopete.github.io/solis/

## How it works

```text
Update data/report.json → git push to main → GitHub Pages
```

No Elasticsearch, API keys, or cloud automation required. The site loads `data/report.json` from the repo.

## Criteria

| Field | Value |
| --- | --- |
| Budget | ~$60,000 |
| Down payment | ~$20,000 |
| Age | Soft preference ≤ 2021 — list any year if it’s a good deal |
| Radius | Prefer ≤ 500 miles of Washington |
| Horizon | Price outlook to October 2026 |

## Repo layout

- `index.html` / `assets/` — GitHub Pages UI
- `data/report.json` — live report data
- `data/history.json` — daily price snapshots
- `AGENTS.md` — instructions for refreshing the report (Cursor agent or manual)

## Local preview

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

## Updating the report

Ask a Cursor agent to follow `AGENTS.md`, or edit `data/report.json` yourself and push:

```bash
git add data/report.json data/history.json
git commit -m "Update Solis Watch report (YYYY-MM-DD)"
git push origin main
```
