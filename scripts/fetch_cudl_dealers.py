#!/usr/bin/env python3
"""Fetch BECU AutoSmart / CUDL RV dealers near 98370 and Winnebago inventory counts."""
import json
import re
import uuid
from pathlib import Path

import requests

BASE = "https://becu.cudlautosmart.com"
ZIP = "98370"
RADIUS = 200
LAT, LON = 47.7359, -122.6465
CLIENT_WEBSITE_ID = 9261


def token(session, path):
    r = session.get(f"{BASE}{path}")
    r.raise_for_status()
    m = re.search(r'name="__RequestVerificationToken"[^>]+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("CSRF token not found")
    return m.group(1), r.url


def post(session, path, token, referer, criteria):
    r = session.post(
        f"{BASE}{path}",
        data={"__RequestVerificationToken": token, "criteria": json.dumps(criteria)},
        headers={"Referer": referer},
    )
    r.raise_for_status()
    return r.json()


def dealer_criteria(show_inventory=True):
    return {
        "IsLoadMoreSearch": False,
        "ItemType": "8",
        "ItemTypes": [],
        "Condition": None,
        "ClientWebsiteId": CLIENT_WEBSITE_ID,
        "SearchString": None,
        "SearchSellersByMakeId": None,
        "Latitude": LAT,
        "Longitude": LON,
        "DistanceRadius": RADIUS,
        "DistanceUnit": 0,
        "TopCount": 250,
        "SortBy": 1,
        "UserGuid": str(uuid.uuid4()),
        "PageNumber": -1,
        "IsUserSearchTerm": False,
        "DoNotLogSearch": False,
        "LanguageId": 2,
        "TransactionGuid": str(uuid.uuid4()),
        "MakeModels": [],
        "DealerClientCode": None,
        "ShowSpecficInventoryCount": show_inventory,
        "SourcePlatform": 1,
        "SourceSection": 1,
        "ZipCode": ZIP,
        "SearchRequestType": 1,
        "YearMax": None,
        "OnlyPreferredDealers": False,
        "ComesFromDealerSRP": True,
        "OnlyAutoPremierDealers": False,
    }


def vehicle_criteria(make=None, search_string=None, nationwide=False):
    return {
        "IsLoadMoreSearch": False,
        "ItemType": 8,
        "ItemTypes": [8],
        "ClientWebsiteId": CLIENT_WEBSITE_ID,
        "SearchString": search_string,
        "Latitude": LAT,
        "Longitude": LON,
        "DistanceRadius": 1001 if nationwide else RADIUS,
        "DistanceUnit": 0,
        "TopCount": 100,
        "SortBy": 1,
        "Condition": "Used",
        "UserGuid": str(uuid.uuid4()),
        "PageNumber": -1,
        "IsUserSearchTerm": bool(search_string),
        "DoNotLogSearch": False,
        "LanguageId": 2,
        "TransactionGuid": str(uuid.uuid4()),
        "MakeModels": [{"Make": make}] if make else [],
        "ZipCode": ZIP,
        "SearchRequestType": 1,
        "SourcePlatform": 1,
        "SourceSection": 1,
        "NewChecked": False,
        "UsedChecked": True,
        "UsageMax": 0,
        "IsNonTextBasedSearch": True,
        "IncludeSpotlightResults": True,
        "LoanRate": 6.99,
        "LoanTerm": 120,
        "OnlyPreferredDealers": False,
        "OnlyAutoPremierDealers": False,
    }


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    token_val, referer = token(session, f"/Dealer?ItemType=8&ZipCode={ZIP}&Distance={RADIUS}")
    dealer_data = post(session, "/SearchService/PostDealerSearch", token_val, referer, dealer_criteria())
    owners = dealer_data.get("Owners", [])

    vtoken, vref = token(session, f"/UsedVehicle?ItemType=8&ZipCode={ZIP}&Condition=Used&Makes=Winnebago")
    winnebago = post(session, "/SearchService/PostSearch", vtoken, vref, vehicle_criteria(make="Winnebago", nationwide=True))
    vehicles = winnebago.get("SearchResults", [])

    solis_travato = [
        v
        for v in vehicles
        if any(t in (v.get("ItemName") or "").lower() for t in ("solis", "travato"))
    ]

    dealers = []
    for d in sorted(owners, key=lambda x: x.get("Distance", 999)):
        cc = str(d.get("ClientCode"))
        wb = [v for v in vehicles if str(v.get("ClientCode")) == cc]
        inv = d.get("InventoryCount") or 0
        name = (d.get("OwnerName") or "").replace("&amp;", "&")
        dealers.append(
            {
                "name": name,
                "clientCode": cc,
                "distanceMiles": round(d.get("Distance", 0), 1),
                "city": (d.get("OwnerAddress2") or "").split(",")[0].strip(),
                "state": ((d.get("OwnerAddress2") or "").split(",")[-1].strip().split() or [""])[0],
                "phone": d.get("OwnerPhone"),
                "address": d.get("OwnerAddress1"),
                "cudlInventory": inv,
                "winnebagoCount": len(wb),
                "isBecuPlus": bool(d.get("IsAutoSmartXLive")),
                "isPreferred": bool(d.get("IsPreferred")),
                "searchUrl": f"{BASE}/search?dealerclientcode2={cc}&ItemType=8&Condition=Used",
                "note": (
                    "; ".join(sorted({v.get("ItemName", "") for v in wb}))[:160]
                    if wb
                    else ("Synced RV stock on AutoSmart" if inv else "Enrolled — inventory not synced")
                ),
            }
        )

    out = {
        "asOf": "2026-08-02",
        "sourceUrl": f"{BASE}/Dealer?ItemType=8&ZipCode={ZIP}&Distance={RADIUS}",
        "zipCode": ZIP,
        "radiusMiles": RADIUS,
        "dealerCount": len(dealers),
        "withSyncedInventory": sum(1 for d in dealers if d["cudlInventory"] > 0),
        "withWinnebago": sum(1 for d in dealers if d["winnebagoCount"] > 0),
        "winnebagoSolisTravatoCount": len(solis_travato),
        "dealers": dealers,
    }

    path = Path("data/cudl-dealers.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(
        f"Wrote {path}: {out['dealerCount']} dealers, "
        f"{out['withSyncedInventory']} with synced inventory, "
        f"{out['withWinnebago']} with Winnebago (0 Solis/Travato)"
    )


if __name__ == "__main__":
    main()
