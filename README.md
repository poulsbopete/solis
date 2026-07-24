# Solis Watch

Living buyer report for a used **Winnebago Solis** near Washington State.

**Live report:** https://poulsbopete.github.io/solis/

## Criteria

| Field | Value |
| --- | --- |
| Budget | ~$60,000 |
| Down payment | ~$20,000 |
| Age | 5+ years (model year ≤ 2021) |
| Radius | Prefer ≤ 500 miles of Washington |
| Horizon | Price outlook to October 2026 |

## Repo layout

- `index.html` — GitHub Pages report shell
- `assets/` — styles + renderer
- `data/report.json` — current candidates + projections
- `data/history.json` — price snapshots over time
- `AGENTS.md` — instructions for the Cursor cloud automation

## Local preview

```bash
python3 -m http.server 8080
# open http://localhost:8080
```

## Automation

A Cursor cloud automation refreshes listings on a schedule, updates `data/*.json`, commits, and pushes to `main` so Pages stays current. Run status is visible in the Cursor mobile app under Automations.
