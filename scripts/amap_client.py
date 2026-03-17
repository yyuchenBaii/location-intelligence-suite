import json
import os
import ssl
import urllib.request
from urllib.parse import urlencode


SSL_CTX = ssl._create_unverified_context()
AMAP_WEB_KEY = os.environ.get("AMAP_WEB_KEY")
BASE = "https://restapi.amap.com"


def amap_get(path, params):
    req_params = {"key": AMAP_WEB_KEY, **params}
    req_url = f"{BASE}{path}?{urlencode(req_params)}"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(req_url), context=SSL_CTX, timeout=8
        ) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"status": "0", "_error": str(exc)}


def require_key():
    if not AMAP_WEB_KEY:
        return {"error": "缺少环境变量 AMAP_WEB_KEY，无法查询真实高德数据。"}
    return None


def geocode(address, city=None):
    params = {"address": address, "output": "json"}
    if city:
        params["city"] = city
    return amap_get("/v3/geocode/geo", params)


def regeo(location, radius=500):
    return amap_get(
        "/v3/geocode/regeo",
        {
            "location": location,
            "extensions": "all",
            "radius": radius,
            "output": "json",
        },
    )


def inputtips(keywords, city=None, datatype="all"):
    params = {"keywords": keywords, "datatype": datatype, "output": "json"}
    if city:
        params["city"] = city
        params["citylimit"] = "true"
    return amap_get("/v3/assistant/inputtips", params)


def place_text(keywords, city=None, citylimit=False, types=None, offset=20, page=1):
    params = {
        "keywords": keywords,
        "extensions": "all",
        "offset": offset,
        "page": page,
        "output": "json",
    }
    if city:
        params["city"] = city
        params["citylimit"] = "true" if citylimit else "false"
    if types:
        params["types"] = types
    return amap_get("/v3/place/text", params)


def place_around(
    location,
    keywords=None,
    types=None,
    radius=1000,
    sortrule="distance",
    extensions="all",
    offset=20,
    page=1,
):
    params = {
        "location": location,
        "radius": radius,
        "extensions": extensions,
        "offset": offset,
        "page": page,
        "output": "json",
        "sortrule": sortrule,
    }
    if keywords:
        params["keywords"] = keywords
    if types:
        params["types"] = types
    return amap_get("/v3/place/around", params)


def place_polygon(polygon, keywords=None, types=None, offset=20, page=1):
    params = {
        "polygon": polygon,
        "extensions": "all",
        "offset": offset,
        "page": page,
        "output": "json",
    }
    if keywords:
        params["keywords"] = keywords
    if types:
        params["types"] = types
    return amap_get("/v3/place/polygon", params)


def place_detail(poiid):
    return amap_get("/v3/place/detail", {"id": poiid, "output": "json"})


def direction_walking(origin, destination):
    return amap_get(
        "/v3/direction/walking",
        {"origin": origin, "destination": destination, "output": "json"},
    )


def direction_driving(origin, destination):
    return amap_get(
        "/v3/direction/driving",
        {"origin": origin, "destination": destination, "output": "json"},
    )


def direction_transit(origin, destination, city):
    return amap_get(
        "/v3/direction/transit/integrated",
        {
            "origin": origin,
            "destination": destination,
            "city": city,
            "output": "json",
        },
    )


def parse_duration_distance(route):
    try:
        duration = int(route.get("duration", 0))
        distance = int(route.get("distance", 0))
        return round(duration / 60, 1), distance
    except (TypeError, ValueError):
        return None, None
