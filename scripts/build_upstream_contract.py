import argparse
import json
from pathlib import Path


def _load_optional_json(path_str):
    if not path_str:
        return None
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def _parse_lnglat(value):
    if not value:
        return None, None
    if isinstance(value, str) and "," in value:
        lng, lat = value.split(",", 1)
        return float(lng), float(lat)
    raise ValueError("lnglat must be formatted as 'lng,lat'")


def _build_contract(args, resolve_data, context, poi):
    location_point = {"lng": None, "lat": None}
    lng, lat = _parse_lnglat(args.lnglat)
    if lng is not None and lat is not None:
        location_point = {"lng": lng, "lat": lat}

    selected = (resolve_data or {}).get("selected_candidate") or {}
    nearest_metro_name = context.get("nearest_metro")
    nearest_anchor_name = context.get("nearest_commercial_anchor")
    top_threats = poi.get("top_threats") or []
    map_points = poi.get("top_competitors_for_map") or []

    return {
        "contract_version": "1.0",
        "provider": {
            "name": args.provider_name,
            "kind": args.provider_kind,
            "adapter": args.adapter_name,
        },
        "request": {
            "location_query": args.location_query,
            "business_type": args.business_type,
            "scan": {
                "mode": poi.get("search_mode"),
                "radius_meters": poi.get("search_radius_meters"),
                "polygon": poi.get("search_polygon"),
                "city": poi.get("search_city"),
                "adcode": poi.get("search_adcode") or context.get("adcode"),
            },
        },
        "location": {
            "label": args.location_label or context.get("formatted_address") or selected.get("address") or args.location_query,
            "point": location_point,
            "formatted_address": context.get("formatted_address", ""),
            "province": context.get("province", ""),
            "city": context.get("city", ""),
            "district": context.get("district", ""),
            "adcode": context.get("adcode", ""),
            "township": context.get("township", ""),
            "street_address": context.get("street_address", ""),
            "business_areas": context.get("business_areas") or [],
            "nearby_landmarks": context.get("nearby_landmarks") or [],
            "aoi": {
                "name": context.get("aoi_name", ""),
                "area_sqm": context.get("aoi_area_sqm", ""),
            },
            "resolved_by": selected.get("source", ""),
        },
        "mobility": {
            "nearest_metro": {
                "name": nearest_metro_name,
                "location": context.get("nearest_metro_location", ""),
                "walk_minutes": context.get("metro_walk_minutes"),
                "walk_meters": context.get("metro_walk_meters"),
            },
            "metro_capture": {
                "captured": context.get("metro_flow_capture", False),
                "label": context.get("metro_flow_label", ""),
            },
            "metro_access": context.get("metro_access") or {},
            "nearest_commercial_anchor": {
                "name": nearest_anchor_name,
                "location": context.get("nearest_commercial_anchor_location", ""),
                "address": context.get("nearest_commercial_anchor_address", ""),
                "distance_m": context.get("nearest_commercial_anchor_distance_m"),
            },
            "anchor_access": context.get("anchor_access") or {},
            "anchor_access_label": context.get("anchor_access_label", ""),
        },
        "supply": {
            "office_count_500m": context.get("office_count", 0),
            "residential_count_500m": context.get("residential_count", 0),
        },
        "competition": {
            "keyword": poi.get("search_keyword") or args.business_type,
            "search_mode": poi.get("search_mode"),
            "search_radius_meters": poi.get("search_radius_meters"),
            "search_polygon": poi.get("search_polygon"),
            "search_city": poi.get("search_city"),
            "search_adcode": poi.get("search_adcode"),
            "total_poi": poi.get("total_competitors_found", 0),
            "fetched_sample_size": poi.get("fetched_sample_size", 0),
            "level_label": poi.get("competition_level"),
            "price_distribution": poi.get("price_distribution") or {},
            "price_insight": poi.get("price_insight"),
            "rating_avg": poi.get("rating_avg"),
            "high_quality_count": poi.get("high_quality_count", 0),
            "nearest_competitor": poi.get("closest_competitor") or {},
            "top_threats": top_threats,
            "top_threats_count": poi.get("top_threats_count", len(top_threats)),
            "business_areas_covered": poi.get("business_areas_covered") or [],
            "map_points": map_points,
        },
        "notes": [
            "This contract is the normalized upstream input for downstream business analysis and HTML report generation.",
            "Adapters may source data from upstream skills or local fallback scripts, but downstream steps must read this shape only.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_path")
    parser.add_argument("--context-path", required=True)
    parser.add_argument("--poi-path", required=True)
    parser.add_argument("--resolve-path")
    parser.add_argument("--lnglat", required=True)
    parser.add_argument("--location-query")
    parser.add_argument("--location-label")
    parser.add_argument("--business-type")
    parser.add_argument("--provider-name", default="local-python-fallback")
    parser.add_argument("--provider-kind", choices=["skill", "script", "adapter"], default="script")
    parser.add_argument("--adapter-name", default="legacy-script-adapter")
    args = parser.parse_args()

    context = _load_optional_json(args.context_path) or {}
    poi = _load_optional_json(args.poi_path) or {}
    resolve_data = _load_optional_json(args.resolve_path) or {}

    contract = _build_contract(args, resolve_data, context, poi)
    Path(args.output_path).write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(Path(args.output_path).resolve()))


if __name__ == "__main__":
    main()
