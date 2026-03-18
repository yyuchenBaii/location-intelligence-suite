---
name: location-scout-ultimate
description: Use for commercial site selection, multi-location comparison, district exploration, and reverse workflows that must combine AMap-backed data, local Python scripts, and the bundled HTML report templates.
---

# Location Scout Ultimate

Use this skill when the user wants a commercial real-estate style site-selection assessment, competitor scan, multi-location comparison, vague district exploration, or reverse recommendation.

The value of this skill is not generic analysis. It is a strict workflow:

1. Route the request into the correct scenario.
2. Use real local scripts when keys and inputs are available.
3. Follow the bundled HTML templates instead of inventing a new layout.
4. Clearly separate confirmed API facts from model inference.

## First Response

Before doing analysis, check whether `AMAP_WEB_KEY` is available. If the task will end in a full HTML report, also verify whether the JS map placeholders can be replaced with the user's real web key and security code.

Required env vars for full real-data HTML delivery:

- `AMAP_WEB_KEY`
- `AMAP_JSAPI_KEY`
- `AMAP_SEC_CODE`

- If the key is missing, tell the user that real AMap-backed analysis is unavailable and offer two paths:
  - provide the key so the skill can fetch real location data
  - continue in demo mode with clearly labeled mock data
- If the user chooses demo mode, do not run the scripts. Make it explicit that all numeric results are illustrative.
- If the key exists, continue with real-data mode.

## Route The Request

Classify the request into one of these four scenarios before generating a report:

- `single-defense`: one concrete address or coordinate plus business type
- `multi-compare`: multiple candidate locations to compare
- `fuzzy-explore`: no exact location yet, only budget / city / business intent
- `reverse-leasing`: an idle storefront that needs a recommended business type

See [references/routing-and-output.md](references/routing-and-output.md) for the detailed routing rules, required follow-up questions, and expected deliverable shape for each scenario.

## Real Data Workflow

When working in real-data mode and the location has been identified, do not invent numeric facts. Run the local scripts in this order:

1. If the user gives a vague address or mall name, resolve it first:
   `python scripts/resolve_location.py "<query>" "<city>"`
2. Run location context:
   `python scripts/fetch_location_context.py "<lng,lat>"`
3. Run the relevant POI scan:
   - point scan: `python scripts/fetch_amap_poi.py "<lng,lat>" "<business_keyword>"`
   - district scan: `python scripts/fetch_amap_poi.py "<business_keyword>" --mode text --adcode <adcode>`
   - bounded commercial body scan: `python scripts/fetch_amap_poi.py "<lng,lat>" "<business_keyword>" --mode polygon --polygon "<polyline>"`

If a script fails, a path is wrong, or the API returns insufficient data, explain the limitation to the user instead of fabricating numbers.

See [references/data-contracts.md](references/data-contracts.md) for:

- which output fields must be quoted directly
- which conclusions are allowed only as inference
- how to handle uncertainty in the report

## Report Generation Rules

Every full assessment should end in an HTML report, not just a plain Markdown summary.

Do not freehand-edit large sections of HTML when the report can be generated from structured data.

Before generating any HTML, read the relevant local template:

- single-location report: `resources/report_template.html`
- multi-location comparison: `resources/location_report_comparison.html`

If the template cannot be read, warn the user that the report will be a degraded fallback HTML version.

Do not casually redesign the UI. Prefer filling the existing template structure and reserved containers.

See [references/template-rules.md](references/template-rules.md) for:

- required template-reading behavior
- single-report injection rules
- strict multi-location `locationData` replacement rules
- map data injection requirements
- final reminder text about JSAPI key / security code

Use [references/report-payloads.md](references/report-payloads.md) and the local builder:

1. run the AMap data scripts
2. run `python scripts/assemble_report_payload.py single spec.json payload.json` or `python scripts/assemble_report_payload.py compare spec.json payload.json`
3. run `python scripts/build_report.py single payload.json output.html` or `python scripts/build_report.py compare payload.json output.html`
4. if build validation fails, fix the payload or template issue and rebuild; do not deliver the broken HTML
5. return the absolute output path

Success means the final HTML passes template-structure validation. A file that does not preserve the tabbed layout or required payload markers is not an acceptable deliverable.

## Output Standard

Preferred delivery order:

1. write an HTML file locally and return the absolute path
2. if file writing is blocked, output complete HTML source

Do not return meaningless `localhost` links.

Before final output, run through the quality checks in [references/report-checklist.md](references/report-checklist.md).

## Style

Maintain a professional commercial real-estate tone. Be concise, specific, and numerically grounded. Avoid hype when presenting conclusions; the strength of the report should come from the data, the structure, and the template fidelity.
