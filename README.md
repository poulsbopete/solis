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

## Local hourly watcher (your laptop)

Light check for **new driveable** Solis/Travato listings within 200 mi of Poulsbo (configurable). Ignores fly deals; alerts when something new appears.

```bash
# one-off check (verbose)
python3 scripts/local_watch.py -v

# install hourly schedule (macOS launchd)
chmod +x scripts/install-local-watch.sh
./scripts/install-local-watch.sh
```

**Sources scanned each run:** BECU CUDL network (local radius), priority CUDL dealers (Johnson, Poulsbo RV, Apache, etc.), live URLs from `data/report.json` within range, Craigslist RSS (Seattle/Portland/Spokane when not blocked).

**State/logs (gitignored):** `.local/watch-state.json`, `.local/watch-log.jsonl`

Edit `scripts/watch_config.json` to change `maxDriveMiles` (default 200), zip code, or disable sources.

**Live site banner:** when the watcher finds something new, it updates `data/watch-pulse.json`. Commit and push that file (or run `./scripts/publish-pulse.sh`) to show a sticky alert on https://poulsbopete.github.io/solis/. The page also polls hourly while open and can send browser notifications if you click **Enable browser alerts**.

### Cursor Mobile (iPhone push)

When the local watcher finds a **new** driveable listing, it can ping a **Cursor Automation** webhook. The cloud agent finishes quickly and Cursor Mobile pushes to your iPhone (same alerts you get when an agent completes or needs input).

**One-time setup**

1. Open [cursor.com/automations](https://cursor.com/automations) → **New automation**
2. **Trigger:** Webhook (save to generate URL + auth header)
3. **Repository:** None (no code changes needed)
4. **Instructions** (paste something like):

   ```text
   Solis Watch buyer alert. The webhook JSON lists new local Winnebago Solis/Travato
   listings within driving distance. Reply in 2–3 sentences with year, price, city,
   and link. Do not edit code or open PRs.
   ```

5. Activate the automation
6. Copy webhook URL + Bearer token into `.env`:

   ```bash
   cp .env.example .env
   # edit .env — CURSOR_AUTOMATION_WEBHOOK_URL and CURSOR_AUTOMATION_TOKEN
   ```

7. Test from your laptop:

   ```bash
   python3 scripts/cursor_notify.py          # sends a sample alert
   python3 scripts/local_watch.py -v         # real scan; pings on new finds
   ```

The hourly launchd job (`./scripts/install-local-watch.sh`) runs `run-local-watch.sh`, which loads `.env`, scans, pushes the site pulse when needed, and fires the Cursor webhook.

**Alternative:** add a **Push to branch `main`** trigger on the same repo filtered to commits whose message contains `Watch pulse` — then `./scripts/publish-pulse.sh` alone will wake the agent after each push.
