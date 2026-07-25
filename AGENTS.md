# Solis Watch — agent instructions

Keep the buyer report current for a used **Winnebago Solis** search.

**Source of truth is Elasticsearch**, not git. The GitHub Pages site reads
`solis-watch/_doc/report-current` at load time.

## Buyer criteria

- Model: Winnebago Solis (59P, 59PX, Pocket OK to note)
- Target budget: about **$60,000** (track up to ~$70k as stretch / negotiation)
- Age: **soft preference only** for model year ≤ 2021 — there is **no “too new” cutoff**. If it looks like a good deal on price/miles/condition, **list it**
- Geography: prefer **≤ 500 miles of Washington State** (Seattle as anchor for distance)
- Flying elsewhere is allowed for clear under-market deals — tag those `tier: "fly"`
- Planning horizon: project prices to **2026-10-01**
- Financing plan: about **$20,000** down payment (keep `financing` section current)

## Elasticsearch layout

- Index: `solis-watch`
- Current report doc id: `report-current`  
  Body shape: `{ "doc_type": "report", "updated_at": "<ISO>", "payload": { ...same as data/report.json... } }`
- Daily history doc id: `history-YYYY-MM-DD`  
  Body shape: `{ "doc_type": "history_point", "date": "YYYY-MM-DD", "updated_at": "<ISO>", "payload": { ...snapshot... } }`

Credentials:

- Read `ELASTICSEARCH_URL` + write key from `.env` or `.elastic-credentials` (never commit write keys)
- Public Pages read key lives in `assets/elastic-config.js` (read-only, index-scoped)

## What to do each run

1. Search current listings on:
   - RVs on Autotrader / RV Trader
   - Johnson RV (Fife WA, Sandy OR, Medford OR)
   - Winnebago RV Source / RVUSA aggregators
   - Vanlife Trader
   - Optional: Facebook Marketplace / Craigslist Seattle + Portland (summarize if scrapable)
2. Build the updated report object (same schema as `data/report.json`):
   - Refresh `generatedAt` (ISO UTC)
   - Update `marketSummary` floors/averages when available
   - Upsert candidates (stable `id`s when same VIN/stock/URL)
   - Set `previousPrice` / `priceChange` when an ask moves
   - Recompute `projectedOct` using scenarios in `projections.scenarios`
   - Re-rank **deal-first**: primary = in-radius strong deals (any year), watchlist = uncertain/availability risk, fly = out-of-radius bargains. Soft +score for ≤2021 only when otherwise equal — never exclude for being newer
   - Set `marketSummary.nwDealFloor` to the lowest active in-radius ask (any year) and refresh `gapToBudget`
   - Refresh `financing.paymentScenarios` with $20k down, 120-month term, APRs 6.5 / 7.5 / 9 / 11:
     - budget = $60k ask
     - fly ≈ lowest national/fly ask near budget
     - stretch = $70k
     - nw_floor = current `marketSummary.nwDealFloor`
     - monthly payment = standard amortizing installment; round to nearest dollar
   - Preserve lender guidance / next steps unless market advice clearly changes
3. Optionally write the assembled JSON to `data/report.json` / append `data/history.json` **locally in the workspace for the upload scripts** — but do **not** commit or push those data files.
4. Upsert Elasticsearch:
   - Preferred: `python3 scripts/update_report_elastic.py`
   - Or PUT `solis-watch/_doc/report-current` and `solis-watch/_doc/history-YYYY-MM-DD` directly with the write API key
5. Verify https://poulsbopete.github.io/solis/ shows the new `generatedAt` and “Data source: Elasticsearch (live)”
6. **Do not open a pull request. Do not commit report data to git.** Only commit/push if UI/scripts/AGENTS need a code change.

## Projection rules

For each candidate price `P`:

- mild = round(P * 0.97)
- expected = round(P * 0.93)
- aggressive = round(P * 0.88)

Round to nearest $100. Refresh `gapToBudget` vs NW deal floor.

## Ranking heuristics

Score higher when:

- lower price / closer to the $60k budget
- distance ≤ 500
- larger recent markdown
- lower miles / private seller
- clear listing URL still live
- year ≤ 2021 **only as a small tie-breaker** — never drop a strong newer deal

Do **not** label candidates “too new.” Use notes like “newer year, listed for deal value.”

Mark sold/missing listings `status: "sold"` or remove after two consecutive missing runs.

## Output

End the run with:

- count of primary / watchlist / fly candidates
- best current deal (price, year, city)
- whether any listing is at or within $10k of the $60k budget
- confirmation that Elasticsearch `report-current` was updated
- GitHub Pages URL confirmation (live date moved without a git commit)
