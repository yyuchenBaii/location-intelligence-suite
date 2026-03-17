import json
import sys

from amap_client import (
    direction_driving,
    direction_transit,
    direction_walking,
    place_around,
    regeo,
    require_key,
    parse_duration_distance,
)


def _extract_business_areas(addr_comp):
    biz_areas = addr_comp.get("businessAreas") or []
    if isinstance(biz_areas, dict):
        biz_areas = [biz_areas]
    elif not isinstance(biz_areas, list):
        biz_areas = []
    return [item.get("name", "") for item in biz_areas[:3] if isinstance(item, dict) and item.get("name")]


def _extract_landmarks(regeo_data):
    pois = regeo_data.get("pois") or []
    if not isinstance(pois, list):
        pois = []
    landmarks = []
    for item in pois[:4]:
        name = item.get("name", "")
        dist = item.get("distance", "")
        direction = item.get("direction", "")
        if name and dist:
            landmarks.append(f"{direction}{dist}米处{name}" if direction else f"距{name}{dist}米")
    return landmarks


def fetch_regeo_context(location):
    result = regeo(location)
    if result.get("status") != "1":
        return None, result.get("info") or result.get("_error") or "逆地理编码失败"

    regeo_data = result.get("regeocode") or {}
    addr_comp = regeo_data.get("addressComponent") or {}
    if isinstance(addr_comp, list):
        addr_comp = {}

    district = addr_comp.get("district") if isinstance(addr_comp.get("district"), str) else ""
    city = addr_comp.get("city")
    if isinstance(city, list):
        city = district
    province = addr_comp.get("province") if isinstance(addr_comp.get("province"), str) else ""
    adcode = addr_comp.get("adcode") if isinstance(addr_comp.get("adcode"), str) else ""
    township = addr_comp.get("township") if isinstance(addr_comp.get("township"), str) else ""
    street_num = addr_comp.get("streetNumber") or {}
    if isinstance(street_num, list):
        street_num = {}
    street = street_num.get("street") if isinstance(street_num.get("street"), str) else ""
    number = street_num.get("number") if isinstance(street_num.get("number"), str) else ""
    formatted = regeo_data.get("formatted_address") if isinstance(regeo_data.get("formatted_address"), str) else ""
    aois = regeo_data.get("aois") if isinstance(regeo_data.get("aois"), list) else []
    primary_aoi = aois[0] if aois else {}

    return {
        "province": province,
        "city": city if isinstance(city, str) else district,
        "district": district,
        "adcode": adcode,
        "township": township,
        "street_address": f"{street}{number}" if street else "",
        "formatted_address": formatted,
        "business_areas": _extract_business_areas(addr_comp),
        "nearby_landmarks": _extract_landmarks(regeo_data),
        "aoi_name": primary_aoi.get("name", ""),
        "aoi_area_sqm": primary_aoi.get("area", ""),
    }, None


def fetch_nearest_poi(location, *, keywords=None, types=None, radius=1500):
    result = place_around(
        location,
        keywords=keywords,
        types=types,
        radius=radius,
        extensions="all",
        offset=5,
        page=1,
    )
    if result.get("status") != "1":
        return None

    pois = result.get("pois") or []
    if not pois:
        return None
    return pois[0]


def fetch_route_profile(origin, destination, city):
    walking = direction_walking(origin, destination)
    driving = direction_driving(origin, destination)
    transit = direction_transit(origin, destination, city) if city else {"status": "0"}

    walking_path = (walking.get("route") or {}).get("paths") or []
    driving_path = (driving.get("route") or {}).get("paths") or []
    transit_path = (transit.get("route") or {}).get("transits") or []

    walk_min, walk_m = parse_duration_distance(walking_path[0]) if walking_path else (None, None)
    drive_min, drive_m = parse_duration_distance(driving_path[0]) if driving_path else (None, None)
    transit_min, transit_m = parse_duration_distance(transit_path[0]) if transit_path else (None, None)

    return {
        "walking_minutes": walk_min,
        "walking_meters": walk_m,
        "driving_minutes": drive_min,
        "driving_meters": drive_m,
        "transit_minutes": transit_min,
        "transit_meters": transit_m,
    }


def fetch_poi_count(location, types, radius=500):
    result = place_around(
        location,
        types=types,
        radius=radius,
        extensions="base",
        offset=1,
        page=1,
    )
    if result.get("status") != "1":
        return 0
    return int(result.get("count", 0))


def _metro_summary(nearest_metro, route_profile):
    if not nearest_metro:
        return {
            "nearest_metro": "1500m内无地铁站",
            "metro_flow_capture": False,
            "metro_flow_label": "❌ 无地铁覆盖，客流依赖周边自然人流",
        }

    walk_min = route_profile.get("walking_minutes")
    summary = {
        "nearest_metro": nearest_metro.get("name", "未知地铁站"),
        "nearest_metro_location": nearest_metro.get("location", ""),
        "metro_access": route_profile,
    }
    if walk_min is None:
        summary["metro_flow_capture"] = False
        summary["metro_flow_label"] = "⚠️ 地铁站已识别，但步行路径计算失败"
        return summary

    summary["metro_walk_minutes"] = walk_min
    summary["metro_walk_meters"] = route_profile.get("walking_meters")
    summary["metro_flow_capture"] = walk_min <= 5
    summary["metro_flow_label"] = (
        f"✅ 地铁截流位（步行{walk_min}分钟）"
        if walk_min <= 5
        else f"⚠️ 非截流位（步行{walk_min}分钟，地铁自然客流有限）"
    )
    return summary


def _anchor_summary(anchor, route_profile):
    if not anchor:
        return {
            "nearest_commercial_anchor": "1500m内未识别大型商业锚点",
            "anchor_access_label": "周边未识别出明确商业综合体锚点",
        }

    walk = route_profile.get("walking_minutes")
    drive = route_profile.get("driving_minutes")
    transit = route_profile.get("transit_minutes")
    parts = []
    if walk is not None:
        parts.append(f"步行 {walk} 分钟")
    if drive is not None:
        parts.append(f"驾车 {drive} 分钟")
    if transit is not None:
        parts.append(f"公交 {transit} 分钟")

    return {
        "nearest_commercial_anchor": anchor.get("name", ""),
        "nearest_commercial_anchor_distance_m": int(anchor.get("distance", 0)) if str(anchor.get("distance", "")).isdigit() else None,
        "nearest_commercial_anchor_location": anchor.get("location", ""),
        "nearest_commercial_anchor_address": anchor.get("address", ""),
        "anchor_access": route_profile,
        "anchor_access_label": " / ".join(parts) if parts else "商业锚点路径信息暂缺",
    }


def fetch_location_context(location):
    key_error = require_key()
    if key_error:
        return key_error

    regeo_data, err = fetch_regeo_context(location)
    if err:
        return {"error": f"逆地理编码失败: {err}"}

    city = regeo_data.get("city") or regeo_data.get("district")

    nearest_metro = fetch_nearest_poi(location, keywords="地铁站", types="150500", radius=1500)
    metro_route = (
        fetch_route_profile(location, nearest_metro.get("location"), city)
        if nearest_metro and nearest_metro.get("location")
        else {}
    )

    nearest_anchor = fetch_nearest_poi(location, keywords="购物中心|商业广场|商场", radius=2000)
    anchor_route = (
        fetch_route_profile(location, nearest_anchor.get("location"), city)
        if nearest_anchor and nearest_anchor.get("location")
        else {}
    )

    office_count = fetch_poi_count(location, "120200", radius=500)
    residential_count = fetch_poi_count(location, "120300", radius=500)

    return {
        **regeo_data,
        **_metro_summary(nearest_metro, metro_route),
        **_anchor_summary(nearest_anchor, anchor_route),
        "office_count": office_count,
        "residential_count": residential_count,
        "_note": "以上数据来源：高德逆地理编码、POI 搜索、步行/驾车/公交路径规划，均为真实 API 数据。",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "用法: python fetch_location_context.py <经度,纬度>"}))
        sys.exit(1)

    result = fetch_location_context(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
