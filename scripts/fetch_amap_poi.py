import argparse
import json
import time

from amap_client import place_around, place_detail, place_polygon, place_text, require_key


def _classify_price(cost_str):
    try:
        cost = float(cost_str)
        if cost < 20:
            return "cheap"
        if cost <= 50:
            return "moderate"
        return "expensive"
    except (ValueError, TypeError):
        return "unknown"


def _threat_level(rating, distance_m):
    try:
        r = float(rating)
        d = int(distance_m)
    except (ValueError, TypeError):
        return "未知"

    if r >= 4.5 and d <= 200:
        return "极高"
    if r >= 4.0 and d <= 500:
        return "高"
    if r >= 3.5 and d <= 1000:
        return "中"
    return "低"


def _fetch_pages(mode, *, location=None, keywords=None, radius=2000, polygon=None, city=None, adcode=None):
    all_pois = []
    total_count = 0
    last_exception = None

    for page in range(1, 4):
        if page > 1:
            time.sleep(0.4)

        if mode == "polygon":
            result = place_polygon(polygon, keywords=keywords, offset=50, page=page)
        elif mode == "text":
            target_city = adcode or city
            result = place_text(keywords, city=target_city, citylimit=True, offset=50, page=page)
        else:
            result = place_around(
                location,
                keywords=keywords,
                radius=radius,
                extensions="all",
                offset=50,
                page=page,
            )

        if result.get("status") != "1":
            last_exception = result.get("info") or result.get("_error") or "高德接口失败"
            break

        pois = result.get("pois") or []
        if page == 1:
            total_count = int(result.get("count", 0))
        all_pois.extend(pois)
        if len(pois) < 50:
            break

    return all_pois, total_count, last_exception


def _fetch_detail_map(pois):
    details = {}
    for item in pois[:8]:
        poiid = item.get("id")
        if not poiid:
            continue
        detail = place_detail(poiid)
        if detail.get("status") != "1":
            continue
        detailed_pois = detail.get("pois") or []
        if detailed_pois:
            details[poiid] = detailed_pois[0]
    return details


def fetch_poi_data(location=None, keywords=None, radius=2000, polygon=None, city=None, adcode=None, mode="around"):
    key_error = require_key()
    if key_error:
        return key_error

    if mode == "polygon" and not polygon:
        return {"error": "polygon 模式必须提供 --polygon"}
    if mode == "around" and not location:
        return {"error": "around 模式必须提供 location"}
    if mode == "text" and not (city or adcode):
        return {"error": "text 模式必须提供 --city 或 --adcode"}

    all_pois, total_count, last_exception = _fetch_pages(
        mode,
        location=location,
        keywords=keywords,
        radius=radius,
        polygon=polygon,
        city=city,
        adcode=adcode,
    )

    if not all_pois:
        return {
            "error": "未找到符合条件的 POI" if not last_exception else "高德请求失败，未能完成 POI 扫描",
            "search_keyword": keywords,
            "details": last_exception,
        }

    price_dist = {"expensive": 0, "moderate": 0, "cheap": 0, "unknown": 0}
    ratings = []
    business_areas = set()

    for poi in all_pois:
        biz = poi.get("biz_ext", {})
        price_dist[_classify_price(biz.get("cost", ""))] += 1
        rating = biz.get("rating", "")
        if rating and rating not in ("[]", "暂无"):
            try:
                ratings.append(float(rating))
            except ValueError:
                pass
        if poi.get("business_area"):
            business_areas.add(poi.get("business_area"))

    rating_avg = round(sum(ratings) / len(ratings), 1) if ratings else None
    top_threats = []
    for poi in all_pois:
        biz = poi.get("biz_ext", {})
        dist = poi.get("distance", "9999")
        rating = biz.get("rating", "")
        cost = biz.get("cost", "")
        try:
            if int(dist) <= 500 and float(rating) >= 4.0:
                top_threats.append(
                    {
                        "id": poi.get("id", ""),
                        "name": poi["name"],
                        "distance_m": int(dist),
                        "rating": float(rating),
                        "avg_cost_yuan": float(cost) if cost else None,
                        "business_area": poi.get("business_area", ""),
                        "threat_level": _threat_level(rating, dist),
                        "location": poi.get("location", ""),
                    }
                )
        except (ValueError, TypeError):
            continue

    top_threats.sort(
        key=lambda item: (
            -{"极高": 4, "高": 3, "中": 2, "低": 1}.get(item["threat_level"], 0),
            item["distance_m"],
        )
    )

    detail_map = _fetch_detail_map(all_pois)
    closest = all_pois[0]
    closest_biz = closest.get("biz_ext", {})

    return {
        "search_keyword": keywords,
        "search_mode": mode,
        "search_radius_meters": radius if mode == "around" else None,
        "search_polygon": polygon if mode == "polygon" else None,
        "search_city": city,
        "search_adcode": adcode,
        "total_competitors_found": total_count,
        "fetched_sample_size": len(all_pois),
        "closest_competitor": {
            "id": closest.get("id", ""),
            "name": closest["name"],
            "distance_m": int(closest.get("distance", 0)) if str(closest.get("distance", "")).isdigit() else None,
            "rating": closest_biz.get("rating", "暂无"),
            "avg_cost_yuan": closest_biz.get("cost", "暂无"),
            "business_area": closest.get("business_area", ""),
            "location": closest.get("location", ""),
            "detail": detail_map.get(closest.get("id", ""), {}),
        },
        "competition_level": (
            "🔥 极度红海" if total_count > 50 else "⚠️ 存在显著竞争" if total_count > 20 else "🟢 局部蓝海"
        ),
        "price_distribution": price_dist,
        "price_insight": (
            f"区域内{price_dist['cheap']}家低价(<20元) / "
            f"{price_dist['moderate']}家中档(20-50元) / "
            f"{price_dist['expensive']}家高端(>50元)"
        ),
        "rating_avg": rating_avg,
        "high_quality_count": len([rating for rating in ratings if rating >= 4.0]),
        "top_threats": [
            {
                **item,
                "detail": detail_map.get(item.get("id", ""), {}),
            }
            for item in top_threats[:8]
        ],
        "top_threats_count": len(top_threats),
        "business_areas_covered": list(business_areas),
        "top_competitors_for_map": [
            {
                "id": poi.get("id", ""),
                "name": poi["name"],
                "location": poi.get("location", ""),
                "type": "competitor",
                "distance_m": int(poi.get("distance", 0)) if str(poi.get("distance", "")).isdigit() else None,
                "rating": poi.get("biz_ext", {}).get("rating", ""),
                "avg_cost": poi.get("biz_ext", {}).get("cost", ""),
                "business_area": poi.get("business_area", ""),
            }
            for poi in all_pois[:60]
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("location_or_keyword")
    parser.add_argument("keyword", nargs="?")
    parser.add_argument("radius", nargs="?", type=int, default=2000)
    parser.add_argument("--mode", choices=["around", "polygon", "text"], default="around")
    parser.add_argument("--polygon")
    parser.add_argument("--city")
    parser.add_argument("--adcode")
    args = parser.parse_args()

    if args.mode == "text":
        result = fetch_poi_data(
            keywords=args.location_or_keyword,
            mode="text",
            city=args.city,
            adcode=args.adcode,
        )
    else:
        result = fetch_poi_data(
            location=args.location_or_keyword,
            keywords=args.keyword,
            radius=args.radius,
            polygon=args.polygon,
            city=args.city,
            adcode=args.adcode,
            mode=args.mode,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
