#!/usr/bin/env python3
"""Assemble report.json snapshot — run manually when refreshing market data."""
import json
from pathlib import Path

def proj(p):
    return {
        "mild": round(round(p * 0.97) / 100) * 100,
        "expected": round(round(p * 0.93) / 100) * 100,
        "aggressive": round(round(p * 0.88) / 100) * 100,
    }


def c(
    id_,
    model,
    tier,
    rank,
    year,
    trim,
    price,
    miles,
    city,
    state,
    seller,
    seller_type,
    distance,
    url,
    status,
    notes,
    prev=None,
    vin=None,
    stock=None,
    preferred_age=None,
):
    age_eligible = year <= 2021 if preferred_age is None else preferred_age
    preferred = year <= 2021
    change = 0 if prev == price else (price - prev if prev is not None else None)
    return {
        "id": id_,
        "model": model,
        "tier": tier,
        "rank": rank,
        "year": year,
        "trim": trim,
        "price": price,
        "previousPrice": prev,
        "priceChange": change,
        "miles": miles,
        "vin": vin,
        "stock": stock,
        "city": city,
        "state": state,
        "seller": seller,
        "sellerType": seller_type,
        "distanceMiles": distance,
        "url": url,
        "status": status,
        "ageEligible": age_eligible,
        "withinRadius": distance <= 500,
        "notes": notes,
        "preferredAge": preferred,
        "projectedOct": proj(price),
        "score": 0,
    }


report = {
    "generatedAt": "2026-08-02T23:45:00Z",
    "criteria": {
        "models": ["Winnebago Solis", "Winnebago Travato"],
        "model": "Winnebago Solis & Travato",
        "maxBudget": 60000,
        "maxAgeYears": 5,
        "maxModelYear": None,
        "anchor": "Washington State",
        "preferredRadiusMiles": 500,
        "targetDate": "2026-10-01",
        "notes": "Track used Winnebago Solis (59P, 59PX, Pocket) and Travato (59G, 59K, 59KL, 59GL) on the same ProMaster Class B platform. No hard age cutoff — soft preference for ≤2021 when equal.",
        "preferredMaxModelYear": 2021,
        "ageRule": "soft_preference",
    },
    "marketSummary": {
        "solisNationalUsedFloor": 73000,
        "travatoNationalUsedFloor": 68000,
        "nationalUsedFloor": 68000,
        "nationalUsedAverage": 98500,
        "nationalUsedHigh": 180607,
        "nwAgeEligibleFloor": 73800,
        "gapToBudget": 17899,
        "verdict": "Aug 2 refresh: Winnebago Solis and Travato only. Renton Solis Craigslist gone (404). Johnson Fife Solis 59P appears sold. Best Solis fly: Smyrna 59PX at $69,900. Best NW Travato: Liberty Lake 2021 59G at $84,990. Verified in-radius floor: Kent Solis at $77,899.",
        "sources": [
            "RVs on Autotrader Solis & Travato aggregates",
            "Johnson RV Fife / Sandy / Medford inventory",
            "RnR RV Center Liberty Lake WA",
            "Parkview RV Smyrna DE",
            "Seattle / Renton Craigslist private listings",
        ],
        "nwDealFloor": 77899,
        "nwPreferredAgeFloor": 69900,
    },
    "projections": {
        "asOf": "2026-08-02",
        "target": "2026-10-01",
        "monthsAhead": 2.0,
        "scenarios": [
            {
                "id": "mild",
                "label": "Mild softening",
                "changePct": -0.03,
                "rationale": "Light late-summer dealer discounting only.",
            },
            {
                "id": "expected",
                "label": "Expected (base case)",
                "changePct": -0.07,
                "rationale": "End-of-season Class B softness plus typical 60–90 day price cuts on aged dealer stock.",
            },
            {
                "id": "aggressive",
                "label": "Aggressive / motivated seller",
                "changePct": -0.12,
                "rationale": "High-mileage rental fleet dumps or year-end clear-outs; could push some 2022+ units near or under $60k.",
            },
        ],
        "budgetReachability": "A $60k Winnebago is still a stretch on Solis/Travato — best paths are Smyrna fly Solis ($69,900), negotiating Seattle private or Kent Indie toward the high $60ks, or the high-mile Pottstown Solis fly ($63,994, BECU mileage risk).",
    },
    "candidates": [],
    "alternatives": [],
    "alerts": [],
    "financing": {},
}

candidates = [
    c(
        "smyrna-2021-59px-6149b",
        "Solis",
        "fly",
        1,
        2021,
        "59PX",
        69900,
        None,
        "Smyrna",
        "DE",
        "Parkview RV Center",
        "dealer",
        2850,
        "https://www.parkviewrv.com/product/used-2021-winnebago-solis-59px-3711796-13",
        "active",
        "Verified Aug 2 at $69,900 after $10k discount — best priced Solis in tracker, ~$10k over budget. Fly tier but strongest Winnebago Class B deal nationally.",
        69900,
        "3C6MRVJGXME546051",
        "6149B",
    ),
    c(
        "liberty-lake-2021-59g",
        "Travato",
        "primary",
        2,
        2021,
        "59G",
        84990,
        30421,
        "Liberty Lake",
        "WA",
        "RnR RV Center",
        "dealer",
        280,
        "https://www.rvingplanet.com/product/used-2021-winnebago-travato-59g-3701231-13",
        "active",
        "Best verified NW Travato Aug 2: 2021 59G at $84,990 ($5k off MSRP), 30,421 mi, full-size rear bed + wet bath, 215W solar. ~$25k over budget.",
        None,
        "3C6FRVJG4ME509814",
        "90694",
    ),
    c(
        "kent-2022-59px-indie",
        "Solis",
        "primary",
        3,
        2022,
        "59PX",
        77899,
        62600,
        "Kent",
        "WA",
        "Indie Campers (ex-rental resale)",
        "dealer",
        25,
        "https://www.craigslist.org/view/d/seattle-2022-winnebago-solis-59px-ram/nfZ8rNMXgcTqvcmdQGGTUG",
        "active",
        "In-radius Solis still live Aug 2 at $77,899. Verify odometer (listing vs ad copy) and rental history; BECU may disqualify if true miles exceed 75k.",
        None,
        "3C6MRVJG9NE103889",
        None,
        preferred_age=False,
    ),
    c(
        "seattle-2021-59p-private",
        "Solis",
        "watchlist",
        4,
        2021,
        "59P",
        82000,
        14700,
        "Seattle",
        "WA",
        "Private seller",
        "private",
        10,
        "https://www.craigslist.org/view/d/seattle-2021-winnebago-solis-59p/ihTMynGEFTxWSxi2q8d54a",
        "active",
        "Craigslist live Aug 2: 14,700 mi, Victron/solar upgrades, no pets/smoke. Ultra-low miles but ~$22k over budget — negotiate if condition is priority.",
        None,
    ),
    c(
        "medford-2021-59px-25437r",
        "Solis",
        "watchlist",
        5,
        2021,
        "59PX",
        73800,
        None,
        "Medford",
        "OR",
        "Johnson RV Medford via Autotrader",
        "dealer",
        430,
        "https://rvs.autotrader.com/rvs/2021/winnebago/solis/59px/300655018",
        "active",
        "Autotrader still shows $73,800 but corrupt mileage syndication; stock absent from Johnson site — confirm before travel.",
        73800,
        "3C6LRVDG5ME530928",
        "25437R",
    ),
    c(
        "fife-2021-59px-25185b",
        "Solis",
        "watchlist",
        6,
        2021,
        "59PX",
        89900,
        None,
        "Fife",
        "WA",
        "Johnson RV Fife via Autotrader",
        "dealer",
        30,
        "https://rvs.autotrader.com/rvs/2021/winnebago/solis/59px/300665140",
        "active",
        "Syndicated at $89,900; likely stale — not on Johnson searchable inventory.",
        89900,
        "3C6MRVJG2ME511231",
        "25185B",
    ),
    c(
        "pottstown-2022-59px",
        "Solis",
        "fly",
        7,
        2022,
        "59PX",
        63994,
        93000,
        "Pottstown",
        "PA",
        "Optimum RV",
        "dealer",
        2700,
        "https://www.winnebagorvsource.com/2022-winnebago-class-b-solis-59px-pottstown-pennsylvania-5146441",
        "active",
        "Lowest Solis ask (~$4k over budget) but 93k miles — over BECU 75k cap. Confirm still available.",
        63994,
        "3C6MRVJG0ME541800",
        "1CR800",
        preferred_age=False,
    ),
    c(
        "wind-lake-2021-59px",
        "Solis",
        "fly",
        8,
        2021,
        "59PX",
        70000,
        25000,
        "Wind Lake",
        "WI",
        "Private seller via RV Trader",
        "private",
        1950,
        "https://www.rvtrader.com/listing/2021-Winnebago-SOLIS+59PX-5035999090",
        "active",
        "Private fly at $70k / 25k mi — assumed active; corroborate by phone.",
        70000,
    ),
    c(
        "forestville-2021-59p",
        "Solis",
        "fly",
        9,
        2021,
        "59P",
        70998,
        55000,
        "Forestville",
        "CA",
        "Private seller via RV Trader",
        "private",
        800,
        "https://www.rvtrader.com/listing/2021-Winnebago-SOLIS+59P-5035527422",
        "active",
        "Age-eligible private fly ~$11k over target at 55k miles.",
        70998,
    ),
    c(
        "golden-2021-59p",
        "Solis",
        "fly",
        10,
        2021,
        "59P",
        76000,
        36143,
        "Golden",
        "CO",
        "Private consignment via Next Step Pro Sales",
        "private",
        1300,
        "https://rvs.autotrader.com/rvs/2021/winnebago/solis/59p/300678276",
        "active",
        "Autotrader indexed Aug 2 at $76k / 36k mi.",
        76000,
        "3C6TRVDG1LE127723",
        "1749",
    ),
    c(
        "renton-2022-59p",
        "Solis",
        "primary",
        11,
        2022,
        "59P",
        68000,
        43000,
        "Renton",
        "WA",
        "Private seller",
        "private",
        15,
        "https://www.craigslist.org/view/d/renton-winnebago-solis-59p/w9JqGCLnhVeNpdSdhnpuxc",
        "sold",
        "Craigslist 404 Aug 2 — listing removed. Was $68k / 43k mi.",
        68000,
        preferred_age=False,
    ),
    c(
        "fife-2021-59p",
        "Solis",
        "primary",
        12,
        2021,
        "59P",
        80100,
        20997,
        "Fife",
        "WA",
        "Johnson RV Fife",
        "dealer",
        30,
        "https://johnsonrv.com/inventory/Used-2021-Winnebago-Solis-59P-3C6LRVDG1ME523264",
        "sold",
        "Johnson detail page missing Aug 2 — treated as sold. Was $80,100 / 20,997 mi.",
        80100,
        "3C6LRVDG1ME523264",
        "26556R",
    ),
    c(
        "medford-2021-59px",
        "Solis",
        "primary",
        13,
        2021,
        "59PX",
        77800,
        28620,
        "Medford",
        "OR",
        "Johnson RV Medford",
        "dealer",
        430,
        "https://johnsonrv.com/inventory/Used-2021-Winnebago-Solis-59PX-3C6MRVJG3ME504756",
        "sold",
        "Sold (confirmed Jul 27). Johnson page may linger in search indexes.",
        77800,
        "3C6MRVJG3ME504756",
        "25254G",
    ),
]

# simple score for sorting
for x in candidates:
    if x["status"] == "sold":
        x["score"] = 0
        continue
    s = 100
    s += max(0, 60 - (x["price"] - 60000) / 500)
    if x["withinRadius"]:
        s += 20
    if x["preferredAge"]:
        s += 5
    if x["sellerType"] == "private":
        s += 3
    x["score"] = int(s)

active = [x for x in candidates if x["status"] != "sold"]
active.sort(key=lambda x: (-x["score"], x["price"]))
for i, x in enumerate(active, 1):
    x["rank"] = i
for x in candidates:
    if x["status"] == "sold":
        x["rank"] = 99

report["candidates"] = candidates

report["alternatives"] = []

report["alerts"] = [
    {"level": "info", "text": "Report now tracks Winnebago Solis and Travato on the same ProMaster Class B platform."},
    {"level": "info", "text": "Renton Solis Craigslist removed (404 Aug 2). Johnson Fife 2021 Solis 59P detail page gone — likely sold."},
    {"level": "info", "text": "Best Solis deal: Smyrna 2021 59PX fly at $69,900. Best NW Travato: Liberty Lake 2021 59G at $84,990."},
    {"level": "warning", "text": "NW verified in-radius floor ~$77,899 (Kent Solis) vs $60k target (gap ~$17,900). Best national Winnebago ask: Smyrna fly at $69,900."},
]

# Load existing financing block from current report and refresh dates
fin_path = Path("data/report.json")
if fin_path.exists():
    existing = json.loads(fin_path.read_text())
    report["financing"] = existing.get("financing", {})
def monthly_payment(principal, apr_pct, months=120):
    r = apr_pct / 100 / 12
    if r == 0:
        return round(principal / months)
    return round(principal * r * (1 + r) ** months / ((1 + r) ** months - 1))


def pay_scenario(id_, label, price):
    return {
        "id": id_,
        "label": label,
        "purchasePrice": price,
        "downPayment": 0,
        "loanAmount": price,
        "ltvPct": 100,
        "termMonths": 120,
        "monthly": {
            "apr6_5": monthly_payment(price, 6.5),
            "apr7_5": monthly_payment(price, 7.5),
            "apr9_0": monthly_payment(price, 9.0),
            "apr11_0": monthly_payment(price, 11.0),
        },
    }


report["financing"]["asOf"] = "2026-08-02"
report["financing"]["paymentScenarios"] = [
    pay_scenario("best_deal", "Best deal Smyrna $69.9k", 69900),
    pay_scenario("budget", "Budget ask $60k", 60000),
    pay_scenario("fly", "Fly deal ~$70k", 69900),
    pay_scenario("stretch", "Stretch $70k", 70000),
    pay_scenario("nw_floor", "NW deal floor", report["marketSummary"]["nwDealFloor"]),
]
report["financing"]["recommendation"] = (
    "Winnebago-only tracker. Lead candidates: Smyrna fly Solis ($69,900) and Liberty Lake Travato ($84,990). "
    "BECU: $0 down under $100k, ≤10 years, ≤75k miles."
)
report["financing"]["nextSteps"] = [
    "Call Parkview RV on Smyrna Solis 6149B ($69,900 fly) — confirm availability and negotiate",
    "Call RnR RV Center on Liberty Lake Travato 90694 ($84,990) if comparing Travato vs Solis",
    "Verify Kent Indie Campers odometer and rental history before BECU application",
    "Complete BECU preapproval for target purchase + tax/fees",
    "Pre-purchase inspection before any fly or private-party deal",
]

Path("data/report.json").write_text(json.dumps(report, indent=2) + "\n")
print("Wrote data/report.json with", len(active), "active candidates")
