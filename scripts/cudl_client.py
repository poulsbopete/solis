"""Minimal BECU AutoSmart / CUDL API client for local scripts."""
import json
import re
import uuid

BASE = "https://becu.cudlautosmart.com"
CLIENT_WEBSITE_ID = 9261
DEFAULT_LAT, DEFAULT_LON = 47.7359, -122.6465


def token(session, path):
    r = session.get(f"{BASE}{path}")
    r.raise_for_status()
    m = re.search(r'name="__RequestVerificationToken"[^>]+value="([^"]+)"', r.text)
    if not m:
        raise RuntimeError("CSRF token not found on CUDL page")
    return m.group(1), r.url


def post(session, path, token, referer, criteria):
    r = session.post(
        f"{BASE}{path}",
        data={"__RequestVerificationToken": token, "criteria": json.dumps(criteria)},
        headers={"Referer": referer},
    )
    r.raise_for_status()
    return r.json()


def vehicle_search_criteria(
    zip_code,
    radius,
    make=None,
    search_string=None,
    dealer_client_code=None,
    lat=DEFAULT_LAT,
    lon=DEFAULT_LON,
):
    return {
        "IsLoadMoreSearch": False,
        "ItemType": 8,
        "ItemTypes": [8],
        "ClientWebsiteId": CLIENT_WEBSITE_ID,
        "SearchString": search_string,
        "Latitude": lat,
        "Longitude": lon,
        "DistanceRadius": radius,
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
        "DealerClientCode": dealer_client_code,
        "ZipCode": zip_code,
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


def search_vehicles(session, zip_code, radius, **kwargs):
    path = f"/UsedVehicle?ItemType=8&ZipCode={zip_code}&Distance={radius}&Condition=Used"
    if kwargs.get("make"):
        path += f"&Makes={kwargs['make']}"
    tok, ref = token(session, path)
    data = post(
        session,
        "/SearchService/PostSearch",
        tok,
        ref,
        vehicle_search_criteria(zip_code, radius, **kwargs),
    )
    return data.get("SearchResults") or []
