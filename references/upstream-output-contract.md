# Upstream Output Contract

This skill is an orchestration layer. Downstream business analysis and HTML generation must not depend on whether the upstream facts came from:

- `amap-lbs-skill`
- `amap-jsapi-skill`
- local Python fallback scripts

All upstream providers must be normalized into one contract before running commercial analysis or report building.

## Why This Exists

Without a normalized contract, the outer skill becomes tightly coupled to one implementation path:

- one field name for local scripts
- another field name for an upstream skill
- custom branching inside the report builder

That makes the orchestrator brittle.

The correct architecture is:

1. upstream provider returns raw data
2. adapter normalizes it into this contract
3. business analysis reads only this contract
4. HTML payload assembly reads only this contract or a derived payload

## Required Top-Level Shape

```json
{
  "contract_version": "1.0",
  "provider": {},
  "request": {},
  "location": {},
  "mobility": {},
  "supply": {},
  "competition": {},
  "notes": []
}
```

## Required Sections

### `provider`

Describe where the facts came from.

```json
{
  "name": "amap-lbs-skill",
  "kind": "skill",
  "adapter": "upstream-skill-adapter"
}
```

Allowed `kind` values:

- `skill`
- `script`
- `adapter`

### `request`

Describe what the upstream layer was asked to scan.

```json
{
  "location_query": "静安寺",
  "business_type": "咖啡馆",
  "scan": {
    "mode": "around",
    "radius_meters": 2000,
    "polygon": null,
    "city": "上海",
    "adcode": "310106"
  }
}
```

### `location`

Confirmed location facts only.

```json
{
  "label": "上海静安寺",
  "point": { "lng": 121.445, "lat": 31.223 },
  "formatted_address": "上海市静安区...",
  "province": "上海市",
  "city": "上海市",
  "district": "静安区",
  "adcode": "310106",
  "township": "",
  "street_address": "",
  "business_areas": ["静安寺"],
  "nearby_landmarks": ["距静安寺站420米"],
  "aoi": {
    "name": "静安嘉里中心",
    "area_sqm": "120000"
  },
  "resolved_by": "geocode"
}
```

### `mobility`

Transport and anchor accessibility facts.

```json
{
  "nearest_metro": {
    "name": "静安寺站",
    "location": "121.445,31.223",
    "walk_minutes": 6,
    "walk_meters": 420
  },
  "metro_capture": {
    "captured": false,
    "label": "⚠️ 非截流位（步行6分钟，地铁自然客流有限）"
  },
  "metro_access": {
    "walking_minutes": 6,
    "walking_meters": 420,
    "driving_minutes": 3,
    "driving_meters": 980,
    "transit_minutes": 5,
    "transit_meters": 1200
  },
  "nearest_commercial_anchor": {
    "name": "静安嘉里中心",
    "location": "121.446,31.225",
    "address": "南京西路...",
    "distance_m": 600
  },
  "anchor_access": {},
  "anchor_access_label": "步行 8 分钟 / 驾车 4 分钟"
}
```

### `supply`

Use explicit numeric fields for the local supply base.

```json
{
  "office_count_500m": 63,
  "residential_count_500m": 78
}
```

### `competition`

All structured competition facts must live here.

```json
{
  "keyword": "咖啡馆",
  "search_mode": "around",
  "search_radius_meters": 2000,
  "search_polygon": null,
  "search_city": "上海",
  "search_adcode": "310106",
  "total_poi": 374,
  "fetched_sample_size": 120,
  "level_label": "🔥 极度红海",
  "price_distribution": {
    "cheap": 12,
    "moderate": 48,
    "expensive": 17,
    "unknown": 43
  },
  "price_insight": "区域内12家低价 / 48家中档 / 17家高端",
  "rating_avg": 4.1,
  "high_quality_count": 45,
  "nearest_competitor": {},
  "top_threats": [],
  "top_threats_count": 5,
  "business_areas_covered": ["静安寺", "南京西路"],
  "map_points": []
}
```

## Fact vs Inference

This contract is only for upstream facts and normalized structured results.

Do not store business inference in this contract.

Correct:

- competitor count
- metro walk minutes
- nearby landmarks
- high-threat competitor list

Incorrect:

- "this site will probably break even in 7 months"
- "white-collar traffic accounts for 62%"
- "weekend conversion will outperform weekdays"

Those belong in downstream analysis.

## Default Build Path

Preferred path:

1. upstream skill or fallback script gathers raw data
2. adapter writes one contract JSON
3. `assemble_report_payload.py` reads the contract
4. `build_report.py` writes final HTML

Recommended local helper:

```bash
python scripts/build_upstream_contract.py contract.json \
  --context-path context.json \
  --poi-path poi.json \
  --resolve-path resolve.json \
  --lnglat "121.445,31.223" \
  --location-query "静安寺" \
  --business-type "咖啡馆"
```

## Backward Compatibility

Legacy `context_path + poi_path + lnglat` inputs may still be used during transition.

But new orchestration work should prefer:

- `upstream_contract_path` for single reports
- `upstream_contract_path` inside each compare entry
