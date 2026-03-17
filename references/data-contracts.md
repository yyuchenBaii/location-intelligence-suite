# Data Contracts

Use the local scripts as the source of truth when real-data mode is enabled.

## Script Order

Run these in order:

1. optional resolve step:
   `python scripts/resolve_location.py "<query>" "<city>"`
2. `python scripts/fetch_location_context.py "<lng,lat>"`
3. one of:
   - `python scripts/fetch_amap_poi.py "<lng,lat>" "<business_keyword>"`
   - `python scripts/fetch_amap_poi.py "<business_keyword>" --mode text --adcode <adcode>`
   - `python scripts/fetch_amap_poi.py "<lng,lat>" "<business_keyword>" --mode polygon --polygon "<polyline>"`

## `fetch_location_context.py`

Primary fields:

- `district`
- `business_areas`
- `nearby_landmarks`
- `nearest_metro`
- `metro_walk_minutes`
- `metro_walk_meters`
- `metro_flow_capture`
- `metro_flow_label`
- `office_count`
- `residential_count`
- `adcode`
- `aoi_name`
- `nearest_commercial_anchor`
- `anchor_access`
- `metro_access`

Typical use:

- administrative and business-area naming
- landmark description
- metro accessibility
- multi-mode accessibility
- commuter-capture judgment
- office vs residential mix for tide-pattern inference
- nearby commercial-anchor judgment

## `fetch_amap_poi.py`

Primary fields:

- `total_competitors_found`
- `closest_competitor`
- `competition_level`
- `price_distribution`
- `price_insight`
- `rating_avg`
- `high_quality_count`
- `top_threats`
- `top_threats_count`
- `business_areas_covered`
- `top_competitors_for_map`
- `search_mode`
- `closest_competitor.detail`
- `top_threats[].detail`

Typical use:

- quantify competition density
- name the closest competitor with distance, rating, and average cost
- summarize the price band structure
- identify high-threat competitors inside 500m
- inject full competitor map data into the report
- distinguish point scan vs boundary scan vs district scan
- use POI detail data to avoid shallow competitor descriptions

## What Can Be Stated As Fact

These can be presented as confirmed facts when returned by the scripts:

- competitor count
- closest competitor name and distance
- rating and average spend from API results
- metro walking time and walking distance
- office and residential counts
- named business areas and nearby landmarks

## What Must Be Marked As Inference

These may be derived from the structure of the data, but must be labeled as inference, estimate, or judgment:

- customer-flow composition
- likely purchasing-power tier
- shade / frontage / obstruction judgments
- monthly revenue ceiling
- conversion-rate assumptions
- rent-sales ratio estimates when no rent data is supplied

Do not present invented percentages or fabricated hard numbers as if they came from the API.

Correct pattern:

- "Based on the POI mix, this appears to be a commuter-led location."
- "Inference only: the office-heavy surroundings suggest lunch demand is stronger than late-evening demand."

Incorrect pattern:

- "Office commuters account for 45% of customer flow."
- "Expected monthly revenue is 180,000 yuan" unless the number is explicitly framed as an estimate.

## Failure Handling

If a script fails, returns empty data, or cannot be executed:

- explain the limitation plainly
- ask whether the user wants to adjust the input
- do not backfill precise figures from general knowledge
