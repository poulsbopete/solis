# Solis Watch — agent instructions

Keep the GitHub Pages buyer report current for used **Winnebago Solis and Travato** searches (same ProMaster Class B platform).

**Source of truth:** `data/report.json` in git. Push to `main` and GitHub Pages updates.

## Buyer criteria

- Models: Winnebago **Solis** (59P, 59PX, Pocket OK to note) and **Travato** (59G, 59K, 59KL, 59GL)
- Each candidate must include `"model": "Solis"` or `"model": "Travato"`
- Target budget: about **$60,000** (track up to ~$70k as stretch / negotiation)
- Age: **soft preference only** for model year ≤ 2021 — there is **no “too new” cutoff**. If it looks like a good deal on price/miles/condition, **list it**
- Geography: prefer **≤ 500 miles of Washington State** (Seattle as anchor for distance)
- Flying elsewhere is allowed for clear under-market deals — tag those `tier: "fly"`
- Planning horizon: project prices to **2026-10-01**
- Financing plan: **BECU lead lender** — $0 down under $100k, ≤10 model years, ≤75k miles; savings go to early payoff (keep `financing` section current). Track `financing.cudlNotes` when BECU AutoSmart/CUDL is searched.

## What to do each run

1. Search current listings on:
   - RVs on Autotrader / RV Trader
   - Johnson RV (Fife WA, Sandy OR, Medford OR)
   - Winnebago RV Source / RVUSA aggregators
   - Vanlife Trader
   - **BECU AutoSmart / CUDL RV dealers** within 200 mi of 98370 — refresh `data/cudl-dealers.json` via `scripts/fetch_cudl_dealers.py`; scan each dealer's CUDL feed and website for Solis/Travato
   - Optional: Facebook Marketplace / Craigslist Seattle + Portland (summarize if scrapable)
   - **Local laptop watcher:** `scripts/local_watch.py` hourly via `scripts/install-local-watch.sh` — driveable radius only (see `scripts/watch_config.json`)
2. Update `data/report.json`:
   - Refresh `generatedAt` (ISO UTC)
   - Update `marketSummary` floors/averages when available (`solisNationalUsedFloor`, `travatoNationalUsedFloor`, and combined `nationalUsedFloor`)
   - **Active listings only** in `candidates` — omit sold/missing; track removals in `data/history.json` `priceSeries` and optional `runAnalysis`
   - Set `previousPrice` / `priceChange` when an ask moves
   - Recompute `projectedOct` using scenarios in `projections.scenarios`
   - Re-rank **deal-first**: primary = in-radius strong deals (any year), watchlist = uncertain/availability risk, fly = out-of-radius bargains. Soft +score for ≤2021 only when otherwise equal — never exclude for being newer
   - Set `marketSummary.nwDealFloor` to the lowest active in-radius ask (any year) and refresh `gapToBudget`
   - Refresh `financing.paymentScenarios` with **$0 down** (BECU under $100k), 120-month term, APRs 6.5 / 7.5 / 9 / 11:
     - budget = $60k ask
     - fly ≈ lowest national/fly ask near budget
     - stretch = $70k
     - nw_floor = current `marketSummary.nwDealFloor`
     - monthly payment = standard amortizing installment; round to nearest dollar
   - Preserve lender guidance / next steps unless market advice clearly changes
3. Append a daily snapshot to `data/history.json` (`snapshots` + per-candidate `priceSeries`)
4. Commit and push **directly to `main`** (no pull request):
   - Commit message: `Update Solis Watch report (YYYY-MM-DD)`
   - Do not force-push
   - Do not commit secrets (`.env` stays gitignored)

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

Mark sold/missing listings in history, then **drop from `candidates`** on the next run (do not display). Use two consecutive missing runs before removing unverified syndicated feeds.

## Output

End the run with:

- count of primary / watchlist / fly candidates
- best current deal (price, year, city)
- whether any listing is at or within $10k of the $60k budget
- GitHub Pages URL confirmation (Updated timestamp matches `generatedAt`)
