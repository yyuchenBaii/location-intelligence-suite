# Report Payloads

Use `scripts/build_report.py` to generate final HTML from structured payloads.

Recommended end-to-end flow:

1. run the AMap scripts and save their JSON output
2. run `scripts/assemble_report_payload.py` to build a dense payload
3. run `scripts/build_report.py` to generate final HTML

## Single Report

Command:

`python scripts/build_report.py single payload.json output.html`

To assemble the payload automatically from script results:

`python scripts/assemble_report_payload.py single spec.json payload.json`

The payload must be assigned to `reportData` and should include:

- `header`: title, tag, locationLabel, businessType, statusText
- `intentHtml`
- `radar`
- `metrics`: `trafficLabel`, `trafficValue`, `trafficSub`, `conversionLabel`, `conversionValue`, `conversionSub`
- `insights`: `trafficAnalysisHtml`, `flowConclusionHtml`, `competitionWarningHtml`, `competitionRiskHtml`, `roiHtml`, `revenueHtml`, `complianceHtml`, `negotiationHtml`, `globalConclusionHtml`, `decisionReasonHtml`
- `flow`: `officeLabel`, `officeCount`, `residentialLabel`, `residentialCount`
- `competition`: progress rows with `label`, `valueText`, `pct`, `colorClass`
- `finance`: `rentLabel`, `rentValue`, `rentSub`, `breakevenLabel`, `breakevenValue`, `breakevenSub`
- `decision`: `score`, `grade`, `gradeClass`
- `map`: `targetPoint`, `targetTitle`, `targetDescriptionHtml`, `circles`, `pois`, `heatData`, `legendItems`

The single-report `spec.json` should include:

- `lnglat`
- `location_name`
- `business_type`
- `context_path`
- `poi_path`
- optional rent / breakeven / title overrides

## Comparison Report

Command:

`python scripts/build_report.py compare payload.json output.html`

To assemble the payload automatically from script results:

`python scripts/assemble_report_payload.py compare spec.json payload.json`

The payload must be assigned to `comparisonData` and should include:

- `header`: title, tag, subtitle, dataSourceText
- `globalConclusionHtml`
- `locations`: object keyed by location id, each entry including all fields used by the template:
  - `id`, `name`, `recommend`, `latlng`
  - `score`, `grade`, `gradeClass`, `color`
  - `radar`
  - `intent`, `metric1Label`, `metric1`, `m1sub`, `metric2Label`, `metric2`, `m2sub`
  - `insight1`, `progress`, `insight2`
  - `finance1Label`, `finance1`, `finance2Label`, `finance2`, `insight3`
  - `flowOffice`, `flowResi`, `flowInsight`
  - `compInsight`, `compNeg`, `reason`
  - `circles`, `pois`, `heatData`, `legendItems`

The compare `spec.json` should include a `locations` array, and each item should include:

- `id`
- `name`
- `lnglat`
- `context_path`
- `poi_path`
- optional rent / breakeven / business_type overrides

## Map Keys

`scripts/build_report.py` checks:

- `AMAP_JSAPI_KEY`
- `AMAP_SEC_CODE`

If they are missing, HTML generation fails by default. Use `--allow-missing-map-keys` only for demo output.

## Recommendation

Let the model produce the JSON payload first. Then use the builder script to generate the final HTML. This keeps the output format fixed and avoids partial template edits.
