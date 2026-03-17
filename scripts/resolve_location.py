import json
import sys

from amap_client import geocode, inputtips, place_text, require_key


def _pick_geocode_candidates(result):
    geocodes = result.get("geocodes") or []
    candidates = []
    for item in geocodes[:5]:
        location = item.get("location", "")
        if not location:
            continue
        candidates.append(
            {
                "source": "geocode",
                "name": item.get("formatted_address", ""),
                "address": item.get("formatted_address", ""),
                "location": location,
                "adcode": item.get("adcode", ""),
                "city": item.get("city", ""),
                "district": item.get("district", ""),
                "type": "address",
            }
        )
    return candidates


def _pick_tip_candidates(result):
    tips = result.get("tips") or []
    candidates = []
    for item in tips[:8]:
        location = item.get("location", "")
        if not location:
            continue
        district = item.get("district", "")
        address = item.get("address", "")
        display = f"{district}{address}{item.get('name', '')}".strip() or item.get("name", "")
        candidates.append(
            {
                "source": "inputtips",
                "name": item.get("name", ""),
                "address": display,
                "location": location,
                "adcode": item.get("adcode", ""),
                "district": district,
                "type": item.get("type", ""),
            }
        )
    return candidates


def _pick_text_candidates(result):
    pois = result.get("pois") or []
    candidates = []
    for item in pois[:8]:
        location = item.get("location", "")
        if not location:
            continue
        candidates.append(
            {
                "source": "place_text",
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "address": item.get("address", ""),
                "location": location,
                "adcode": item.get("adcode", ""),
                "district": item.get("adname", ""),
                "type": item.get("type", ""),
                "business_area": item.get("business_area", ""),
            }
        )
    return candidates


def _dedupe(candidates):
    seen = set()
    result = []
    for item in candidates:
        key = (item.get("location"), item.get("name"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def resolve_location(query, city=None):
    key_error = require_key()
    if key_error:
        return key_error

    tip_result = inputtips(query, city=city)
    geocode_result = geocode(query, city=city)
    text_result = place_text(query, city=city, citylimit=bool(city), offset=10, page=1)

    candidates = _dedupe(
        _pick_tip_candidates(tip_result)
        + _pick_geocode_candidates(geocode_result)
        + _pick_text_candidates(text_result)
    )

    return {
        "query": query,
        "city": city,
        "candidates": candidates,
        "selected_candidate": candidates[0] if candidates else None,
        "_note": "候选结果来自高德输入提示、地理编码和关键字搜索的综合去重排序。",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: python resolve_location.py <地点描述> [城市]"}))
        sys.exit(1)

    query = sys.argv[1]
    city = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(resolve_location(query, city), ensure_ascii=False, indent=2))
