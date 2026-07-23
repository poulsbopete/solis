# Solis Watch — agent instructions

Keep the GitHub Pages buyer report current for a used **Winnebago Solis** search.

## Buyer criteria

- Model: Winnebago Solis (59P, 59PX, Pocket OK to note)
- Target budget: about **$40,000** (track up to ~$55k as stretch / negotiation)
- Age: **at least 5 years old** → model year **≤ 2021** as of mid/late 2026
- Geography: prefer **≤ 500 miles of Washington State** (Seattle as anchor for distance)
- Flying elsewhere is allowed for clear under-market deals — tag those `tier: "fly"`
- Planning horizon: project prices to **2026-10-01**

## What to do each run

1. Search current listings on:
   - RVs on Autotrader / RV Trader
   - Johnson RV (Fife WA, Sandy OR, Medford OR)
   - Winnebago RV Source / RVUSA aggregators
   - Vanlife Trader
   - Optional: Facebook Marketplace / Craigslist Seattle + Portland (summarize if scrapable)
2. Update `data/report.json`:
   - Refresh `generatedAt` (ISO UTC)
   - Update `marketSummary` floors/averages when available
   - Upsert candidates (stable `id`s when same VIN/stock/URL)
   - Set `previousPrice` / `priceChange` when an ask moves
   - Recompute `projectedOct` using scenarios in `projections.scenarios`
   - Re-rank: primary (age-eligible + in radius) first, then watchlist, then fly
3. Append a daily snapshot to `data/history.json` (`snapshots` + per-candidate `priceSeries`)
4. Keep `index.html` / assets working — only change them if the report schema needs UI support
5. Commit and push to `main` so GitHub Pages updates:
   - Commit message style: `Update Solis Watch report (YYYY-MM-DD)`
   - Do not force-push
   - Do not commit secrets

## Projection rules

For each candidate price `P`:

- mild = round(P * 0.97)
- expected = round(P * 0.93)
- aggressive = round(P * 0.88)

Round to nearest $100. Refresh `gapToBudget` vs NW age-eligible floor.

## Ranking heuristics

Score higher when:

- year ≤ 2021
- distance ≤ 500
- lower price / larger recent markdown
- lower miles / private seller
- clear listing URL still live

Mark sold/missing listings `status: "sold"` or remove after two consecutive missing runs.

## Output

End the run with:

- count of primary / watchlist / fly candidates
- best current deal (price, year, city)
- whether any listing is within $10k of budget
- GitHub Pages URL confirmation
